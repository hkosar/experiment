"""Judging component: computed-actual vs parsed-expected + pass rule + forbidden list.

P2S-01 requirements 4, 5 and 8:
  4 compare the computed actual result against the expected result and pass rule
  5 evaluate EVERY forbidden outcome
  8 fail on missing, unclassifiable, or unexecuted cases

This module and `oracle.py` are the only oracle-side readers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import engine_core as core
import oracle
from fixture_io import OracleCase, Stimulus
from scenarios import ScenarioSpec
from simulate import ComputedResult


@dataclass
class Judgement:
    fixture_id: str
    shape: str
    passed: bool
    forbidden_evaluated: int
    forbidden_violated: List[str] = field(default_factory=list)
    check_results: Dict[str, bool] = field(default_factory=dict)
    failures: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    unclassifiable: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "fixture": self.fixture_id,
            "shape": self.shape,
            "passed": self.passed,
            "forbidden_evaluated": self.forbidden_evaluated,
            "forbidden_violated": self.forbidden_violated,
            "checks": self.check_results,
            "failures": self.failures,
            "notes": self.notes,
            "unclassifiable": self.unclassifiable,
        }


def judge(result: ComputedResult, oc: OracleCase, stim: Stimulus,
          spec: ScenarioSpec) -> Judgement:
    ctx = {"result": result, "stim": stim, "spec": spec, "oracle": oc}
    j = Judgement(fixture_id=result.fixture_id, shape=result.shape, passed=True,
                  forbidden_evaluated=0)

    # Requirement 8 — an unexecuted or unfoldable case fails, never skipped.
    if result.fold_error:
        j.passed = False
        j.failures.append("fold error: %s" % result.fold_error)

    if result.folded is None:
        j.passed = False
        j.failures.append("case produced no folded state (unexecuted)")
    elif result.folded.causal_violations:
        # D-B9 P2S-06: causal edges are the only ordering authority.
        j.passed = False
        j.failures.extend("causal order: %s" % v
                          for v in result.folded.causal_violations[:5])
    j.check_results["causal_order"] = bool(
        result.folded is not None and not result.folded.causal_violations)

    # P2S-07 structural invariant (D-B2 P2G-13 §4): no proposal class may be emitted
    # from untrusted content without an explicit approved eligibility policy.
    trust0 = str(stim.envelopes[0].get("trust_class", "")).lower()
    if trust0.startswith("external-untrusted"):
        approved = {c for p in spec.eligibility for c in p.permitted_proposal_classes}
        illegal = [c for c in result.proposals_emitted if c not in approved]
        ok = not illegal
        j.check_results["p2s07_proposal_eligibility"] = ok
        if not ok:
            j.passed = False
            j.failures.append(
                "P2S-07: proposal class(es) %s emitted from untrusted content with no "
                "approved eligibility policy" % ",".join(sorted(illegal)))

    # Requirement 5 — every forbidden outcome evaluated as a computable predicate.
    for phrase in oc.forbidden:
        try:
            pred = oracle.forbidden_predicate(phrase)
        except oracle.UnclassifiableExpectation as exc:
            j.passed = False
            j.unclassifiable = str(exc)
            j.failures.append(str(exc))
            continue
        j.forbidden_evaluated += 1
        try:
            violated = bool(pred(ctx))
        except Exception as exc:                      # a predicate that cannot run fails the case
            j.passed = False
            j.failures.append("predicate error for %r: %s" % (phrase, exc))
            continue
        if violated:
            j.passed = False
            j.forbidden_violated.append(phrase)

    if j.forbidden_evaluated != len(oc.forbidden):
        j.passed = False
        j.failures.append("forbidden coverage %d/%d"
                          % (j.forbidden_evaluated, len(oc.forbidden)))

    # Requirement 4 — computed actual vs expected authority / quarantine / receipt.
    exp_auth = oracle.expected_exercised_authority(oc.expected)
    if exp_auth is not None:
        acts = [e for e in result.events if e.event_type == "ActionRequest"]
        executed = list(result.folded.executed_actions) if result.folded else []
        if exp_auth in ("none", "read-only"):
            # Authority EXERCISED means an action actually executed, or an
            # un-halted action request was authorized. Pre-existing in-flight work
            # that the scenario's own event halts is not authority exercised — it is
            # the premise the halt acts on (A15's active T2 batch).
            halted = {str(e.payload.get("halted_action")) for e in result.events
                      if e.event_type == "RefusalEvent" and e.payload.get("halted_action")}
            live_acts = [e for e in acts if e.event_id not in halted]
            ok = not live_acts and not executed and not result.outbound_authorized
            j.check_results["expected_authority_exercised"] = ok
            if not ok:
                j.passed = False
                j.failures.append(
                    "expected '%s' authority but computed %d live ActionRequest(s), "
                    "%d executed, outbound_authorized=%s"
                    % (exp_auth, len(live_acts), len(executed), result.outbound_authorized))
        elif exp_auth == "suspended":
            # Authority is asserted to be reduced: the computed ceiling must sit
            # strictly below act-with-receipt, and nothing consequential may execute.
            ok = (core.CEILING_ORDER[result.ceiling]
                  < core.CEILING_ORDER[core.CEILING_ACT_WITH_RECEIPT]
                  and not executed)
            j.check_results["expected_authority_exercised"] = ok
            if not ok:
                j.passed = False
                j.failures.append(
                    "expected suspended authority; computed ceiling %s with %d executed"
                    % (result.ceiling, len(executed)))
        elif exp_auth == "receipt-bearing":
            ok = core.CEILING_ORDER[result.ceiling] >= core.CEILING_ORDER[
                core.CEILING_ACT_WITH_RECEIPT]
            j.check_results["expected_authority_exercised"] = ok
            if not ok:
                j.passed = False
                j.failures.append("expected receipt-bearing authority; computed ceiling %s"
                                  % result.ceiling)
        elif exp_auth == "step-up":
            ok = result.step_up_required
            j.check_results["expected_authority_exercised"] = ok
            if not ok:
                j.passed = False
                j.failures.append("expected step-up-gated authority; engine did not require it")

    if oracle.expected_requires_quarantine(oc.expected):
        ok = result.quarantined or result.ceiling == core.CEILING_NONE
        j.check_results["expected_quarantine"] = ok
        if not ok:
            j.passed = False
            j.failures.append("expected quarantine/fail-closed not computed")

    # Requirement 6 — external-receipt ownership.
    if result.receipt_violations:
        j.passed = False
        j.failures.extend("receipt ownership: %s" % v for v in result.receipt_violations)
    j.check_results["receipt_ownership"] = not result.receipt_violations

    # pass_rule decomposition
    for check in oracle.pass_rule_predicates(oc.pass_rule):
        if check == "no_write_on_read":
            ok = not result.state_written_on_read
        elif check == "receipt_required":
            f = result.folded
            ok = (not f) or all(a in f.receipts_by_action
                                for a in (f.executed_actions + f.verified_actions))
        elif check == "external_receipt_ownership":
            ok = not result.receipt_violations
        elif check == "step_up_enforced":
            ok = (not result.step_up_required) or result.step_up_satisfied \
                 or result.ceiling == core.CEILING_NONE
        elif check == "fail_closed":
            ok = result.quarantined or result.ceiling == core.CEILING_NONE
        elif check == "dedup":
            ok = True  # dedup modelled as DuplicateDeliveryEvent presence
            if spec.duplicate_delivery:
                ok = any(e.event_type == "DuplicateDeliveryEvent" for e in result.events)
        elif check == "conflict_recorded":
            ok = (not spec.concurrent_conflict) or any(
                e.event_type == "ConflictRecord" for e in result.events)
        elif check == "masked_render":
            ok = any(p.render_class for p in spec.policies if p.protection_floor)
        else:
            ok = True
        j.check_results["pass_rule:" + check] = ok
        if not ok:
            j.passed = False
            j.failures.append("pass-rule check failed: %s" % check)

    # required_evidence — the computed basis must carry evidence of the NAMED kinds
    # (RW-10: `len(events) > 0` was materially weaker than the requirement).
    if oc.required_evidence:
        present, missing = oracle.match_required_evidence(oc.required_evidence, result)
        j.check_results["required_evidence_kinds"] = not missing
        j.notes.append("required_evidence matched %d/%d named kinds"
                       % (len(present), len(oc.required_evidence)))
        if missing:
            j.passed = False
            j.failures.append("required evidence kind(s) absent from the computed basis: %s"
                              % ", ".join(missing))

    return j

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
import oracle_schema
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
    # P2T-01: per-dimension classification (mapped / unmappable / not-applicable),
    # so the accounting is per dimension and cannot be averaged into one number.
    dimension_results: Dict[str, str] = field(default_factory=dict)

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
            "dimensions": self.dimension_results,
        }


def _compare_dimension(exp, result):
    """Compare one typed expectation against the computed result.

    Returns (ok, why). `ok is None` means the expectation carries no comparable
    claim (NOT_APPLICABLE / UNMAPPED) — the caller records it as a note, and the
    fail-closed floor is what stops that from being a free pass.
    """
    if exp.kind in (oracle_schema.KIND_NOT_APPLICABLE, oracle_schema.KIND_UNMAPPED):
        return None, ""

    problems = []
    for feat in exp.requires:
        if not oracle_schema.feature(feat, result):
            problems.append("computed result lacks required feature %r" % feat)
    for feat in exp.forbids:
        if oracle_schema.feature(feat, result):
            problems.append("computed result shows forbidden feature %r" % feat)

    if exp.dimension == "route":
        if exp.kind == oracle_schema.KIND_EXACT and result.tier != exp.values[0]:
            problems.append("expected tier %s, computed %s" % (exp.values[0], result.tier))
        elif exp.kind == oracle_schema.KIND_ALTERNATIVES and result.tier not in exp.values:
            problems.append("expected tier in %s, computed %s"
                            % (list(exp.values), result.tier))
        elif exp.kind == oracle_schema.KIND_RELATIONAL:
            norms = result.extras.get("normalizers") or {}
            c1 = str((norms.get("M1") or {}).get("ceiling") or "")
            c2 = str((norms.get("M2") or {}).get("ceiling") or "")
            if not (c1 and c2 and c1 == c2):
                problems.append("normalizer ceilings differ: M1=%s M2=%s"
                                % (c1 or "-", c2 or "-"))

    elif exp.dimension == "authority":
        got = oracle_schema.computed_authority_class(result)
        order = oracle_schema.AUTH_ORDER
        if exp.kind == oracle_schema.KIND_EXACT and got != exp.values[0]:
            problems.append("expected authority class %s, computed %s"
                            % (exp.values[0], got))
        elif exp.kind == oracle_schema.KIND_CEILING and order[got] > order[exp.values[0]]:
            problems.append("expected authority at most %s, computed %s"
                            % (exp.values[0], got))
        elif exp.kind == oracle_schema.KIND_RELATIONAL:
            norms = result.extras.get("normalizers") or {}
            m1, m2 = norms.get("M1") or {}, norms.get("M2") or {}
            if not m1 or not m2:
                problems.append("no recorded normalizer pair to compare")
            elif core.CEILING_ORDER[str(m2.get("ceiling"))] > core.CEILING_ORDER[
                    str(m1.get("ceiling"))]:
                problems.append("M2 raised the ceiling above M1 (%s > %s)"
                                % (m2.get("ceiling"), m1.get("ceiling")))

    return (not problems), "; ".join(problems)

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

    # Requirement 4 — computed actual vs expected quarantine / receipt.
    #
    # The former partial `expected_exercised_authority` comparison is RETIRED here.
    # It mapped 36 of 81 combinations and is exactly what the verifier's authority
    # probe walked through; the typed schema below compares the same dimension for
    # 72 of 81 with the remaining 9 declared not-applicable by the corpus itself.
    # Keeping both would leave two comparisons of one dimension that can disagree —
    # the same two-incompatible-snapshots defect P2T-05 found in the ledger.
    # ------------------------------------------------------------------
    # P2T-01 — the COMPLETE expected result. Route, authority and receipt had no
    # comparison at all before TASK-0004; attention had one. Each dimension now
    # resolves through the typed schema in `oracle_schema.py` and is compared, and
    # the per-fixture classification is checked against the fail-closed floor so a
    # corrupted or unrecognised expected value cannot degrade to a coverage note.
    # ------------------------------------------------------------------
    j.dimension_results = {}
    for dim in ("route", "authority", "receipt"):
        exp = oracle_schema.parse_dimension(dim, oc.id, oc.expected)
        j.dimension_results[dim] = exp.classification
        floor_msg = oracle_schema.classification_regression(dim, oc.id, exp.classification)
        if floor_msg:
            j.passed = False
            j.failures.append("coverage floor: " + floor_msg)
        ok, why = _compare_dimension(exp, result)
        if ok is None:
            j.notes.append("expected.%s %s (%r): %s"
                           % (dim, exp.kind, exp.raw, exp.rationale or "-"))
            continue
        j.check_results["expected_" + dim] = ok
        if not ok:
            j.passed = False
            j.failures.append("expected.%s %r: %s" % (dim, exp.raw, why))

    # RW-27 — the attention dimension. All 27 fixtures carry `expected.attention`
    # and none was compared before R4; the S3 focus work surfaced that. An unmapped
    # expectation is REPORTED, never silently skipped and never counted as compared.
    att = oracle.expected_attention(oc.expected, oc.id)
    _att_class = ("not-applicable" if not att.raw
                  else "mapped" if att.mapped else "unmappable")
    j.dimension_results["attention"] = _att_class
    _att_floor = oracle_schema.classification_regression("attention", oc.id, _att_class)
    if _att_floor:
        j.passed = False
        j.failures.append("coverage floor: " + _att_floor)
    if not att.mapped:
        j.notes.append("expected.attention %s (%r): %s"
                       % ("UNRESOLVED — CHANGE REQUEST" if att.unresolved
                          else "UNMAPPED", att.raw, att.rationale))
    elif att.relational:
        # E2E-1: "same or escalated, never relaxed by M2" — a constraint between the
        # two recorded normalizer paths, not a band literal.
        norms = result.extras.get("normalizers") or {}
        m1 = str((norms.get("M1") or {}).get("attention") or "")
        m2 = str((norms.get("M2") or {}).get("attention") or "")
        ok = bool(m1 and m2) and (core.ATTENTION_ORDER[m2] >= core.ATTENTION_ORDER[m1])
        j.check_results["expected_attention"] = ok
        if not ok:
            j.passed = False
            j.failures.append(
                "expected attention '%s': M2 path computed %s below M1's %s"
                % (att.raw, m2 or "-", m1 or "-"))
    elif len(att.bands) > 1:
        # One band per input (A8's "Critical / Briefing"). Compared against the
        # per-envelope bands, which is where a multi-input expectation lives; the
        # governing band alone cannot express it.
        computed = sorted(set(result.per_envelope_attention))
        ok = computed == sorted(set(att.bands))
        j.check_results["expected_attention"] = ok
        if not ok:
            j.passed = False
            j.failures.append(
                "expected per-input attention %s; computed %s"
                % (sorted(set(att.bands)), computed))
    else:
        want = att.bands[0]
        if att.hub_update:
            # D-B7 ATT-03 (`27_` ruling): a hub update is the Record-only band PLUS
            # the hub-visibility flag. Both parts, or it is not a hub update — which
            # is why this is an equality and not the ceiling used for a bare "None".
            ok = (result.attention == core.ATT_NONE and bool(result.hub_visibility))
        elif att.conditional:
            # "Needs Owner if unresolved" — the band is required when the condition
            # holds and is a ceiling otherwise.
            pending = bool(result.uncertain_outcome) and not any(
                e.event_type == "ReconciliationEvent" for e in result.events)
            ok = (result.attention == want if pending
                  else core.ATTENTION_ORDER[result.attention]
                  <= core.ATTENTION_ORDER[want])
        elif att.ceiling_only:
            # "None" / "Record-only" / a display surface assert that the item does
            # NOT consume owner attention — see oracle's grounding note. Compared as
            # a ceiling against the demanding bands, and reported as a ceiling.
            ok = (core.ATTENTION_ORDER[result.attention]
                  < core.ATTENTION_ORDER[core.ATT_NEEDS_OWNER])
        else:
            ok = result.attention == want
        j.check_results["expected_attention"] = ok
        if not ok:
            j.passed = False
            if att.hub_update:
                j.failures.append(
                    "expected '%s' = hub update (band %s + hub-visibility flag, "
                    "D-B7 ATT-03); computed band %s, hub_visibility=%s"
                    % (att.raw, core.ATT_NONE, result.attention, result.hub_visibility))
            else:
                j.failures.append(
                    "expected attention '%s' (%s %s%s); computed %s"
                    % (att.raw, "ceiling below" if att.ceiling_only else "band",
                       core.ATT_NEEDS_OWNER if att.ceiling_only else want,
                       ", conditional on %s" % att.conditional if att.conditional else "",
                       result.attention))
        # Surface qualifiers are compared only where the harness computes the
        # surface; the rest are carried and named, per ATTENTION_MAPPING_LIMITS.
        if att.surface:
            if "display" in att.surface.lower():
                sok = not result.state_written_on_read
                j.check_results["expected_attention_surface"] = sok
                if not sok:
                    j.passed = False
                    j.failures.append(
                        "expected display-only surface; state was written on the read path")
            else:
                j.notes.append(
                    "expected.attention surface qualifier carried, not computed: %r"
                    % att.surface)

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
            settled = (list(f.executed_actions) + list(f.verified_actions)) if f else []
            if not settled:
                # RW-21: nothing to check. Recording True here counts a check that
                # cannot discriminate as evidence — the defect this suite exists to
                # exclude. On this corpus the prose decomposition selects
                # `receipt_required` for S3 ("focus pointer unchanged after receipt"),
                # where "receipt" is the owner-facing capture receipt, not an external
                # action receipt, and S3 emits no action at all.
                j.notes.append(
                    "pass-rule check receipt_required is vacuous on this case "
                    "(no executed or verified action) — not counted as evidence")
                continue
            ok = all(a in f.receipts_by_action for a in settled)
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
            # RW-14: read the COMPUTED render application, not the scenario's own
            # declaration. An engine that ignored the mask now fails here.
            applied = [e for e in result.events
                       if e.payload.get("record") == "render-policy-application"]
            ok = (bool(applied)
                  and all(str(e.payload.get("render_class")) != "full-content"
                          for e in applied)
                  and result.notify_render_class != "full-content")
        elif check == "hearsay_provenance":
            ok = any(e.event_type == "ProvenanceRecord"
                     and e.payload.get("provenance_class") == "hearsay-attributed"
                     and not e.payload.get("verified")
                     for e in result.events)
        elif check == "interrupt_policy_cited":
            # RW-20: presence is not the rule. D-B7 §3 (as quoted in `24_`) permits a
            # PENDING policy to be cited AS pending and forbids citing it as ratified.
            #
            # RW-26(a): BOTH legs are now anchored to the stimulus. The R3 version
            # derived the expected status from the fixture text but built its search
            # out of the engine-emitted policy id, so a wholly fabricated citation
            # (`ZZ-9 / ratified`) passed: no fabricated id appears in the start_state,
            # so the pending test was False, and "ratified" agreed with it. The
            # expected id and status are now BOTH read from the fixture, and the
            # emitted citation has to match both.
            decisions = [e for e in result.events if e.event_type == "DecisionEvent"]
            expected_citation = oracle.expected_interrupt_policy(stim.start_state)
            ok = bool(decisions)
            for e in decisions:
                pid = str(e.payload.get("interrupt_policy") or "")
                status = str(e.payload.get("interrupt_policy_status") or "")
                if expected_citation is None:
                    # The stimulus names no interrupt policy; citing one is invention.
                    if pid or status:
                        ok = False
                        j.notes.append(
                            "interrupt policy %s/%s cited but the stimulus names none"
                            % (pid or "-", status or "-"))
                        break
                    continue
                if (pid, status) != expected_citation:
                    ok = False
                    j.notes.append(
                        "interrupt policy cited as %s/%s; the stimulus records %s/%s"
                        % (pid or "-", status or "-",
                           expected_citation[0], expected_citation[1]))
                    break
        elif check == "no_restricted_token_on_any_surface":
            ok = result.notify_render_class != "full-content" and all(
                str(e.payload.get("render_class", "")) != "full-content"
                for e in result.events)
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

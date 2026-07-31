"""The behavioral simulator: stimulus -> computed events, records, state, projections.

P2S-01 requirements implemented here:
  1 start from the fixture's explicit initial state and control envelope
  2 apply candidate-specific transition and storage/projection rules for S1/S2/S3
  3 produce actual events/records/state/projections/ceilings/actions WITHOUT
    copying the fixture's expected result
  6 enforce external-receipt ownership before executed/verified state can appear
  7 replay the full multi-store basis from recorded inputs and model outputs
  9 produce candidate-specific divergences

Nothing in this module — or anything it imports besides `fixture_io.load_stimuli`
— can reach a fixture oracle field.
"""

from __future__ import annotations

import copy
import hashlib
import re
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Tuple

import engine_core as core
import scenarios as scen
from events import Event, SHAPES, shape_divergences
from fixture_io import Stimulus
from fold import FoldError, fold, receipt_ownership_violations


# Action classes treated as consequential for the D-B5 degradation rule (RW-15).
CONSEQUENTIAL_CLASSES = ("payment", "deploy", "outbound")

# Fixed logical evaluation instant — deterministic, never a wall-clock read.
EVAL_INSTANT = 1000


@dataclass
class Defects:
    """Seeded-defect switches. All False on production runs (P2S-01 falsifier)."""

    authority_raise: bool = False
    drop_receipt: bool = False
    causal_reorder: bool = False
    admit_forbidden: bool = False
    stale_projection: bool = False
    engine_authored_receipt: bool = False
    skip_eligibility_check: bool = False
    normalizer_authority_leak: bool = False
    ignore_degradation: bool = False      # RW-15 counterfactual, wired by RW-19
    render_leak: bool = False             # RW-14 counterfactual, wired by RW-21

    def any_active(self) -> bool:
        return any(getattr(self, f) for f in self.__dataclass_fields__)


@dataclass
class ComputedResult:
    fixture_id: str
    shape: str
    tier: str
    ceiling: str
    attention: str
    quarantined: bool
    step_up_required: bool
    step_up_satisfied: bool
    reasons: List[str]
    proposal_notes: List[str]
    eligible_proposal_classes: List[str]
    proposals_emitted: List[str]
    events: List[Event]
    folded: object = None
    receipt_violations: List[str] = field(default_factory=list)
    storage_summary: Dict[str, object] = field(default_factory=dict)
    state_written_on_read: bool = False
    outbound_authorized: bool = False
    executed_without_receipt: bool = False
    fold_error: Optional[str] = None
    uncertain_outcome: bool = False
    halted_actions: List[str] = field(default_factory=list)
    notify_render_class: Optional[str] = None
    composition_refused: List[str] = field(default_factory=list)
    composition_reasons: List[str] = field(default_factory=list)
    composition_attention_min: str = "none"   # RW-12(1): the computed floor
    # RW-27: the model-free band computed for EACH input, before the multi-input
    # governing rule collapses them. A8 expects "Critical / Briefing" — two inputs,
    # two bands — which the governing band alone cannot express.
    per_envelope_attention: List[str] = field(default_factory=list)
    extras: Dict[str, object] = field(default_factory=dict)

    def digest(self) -> str:
        return self.folded.digest() if self.folded is not None else "-"


# --------------------------------------------------------------------------
# Derivation writers (RW-20 / RW-22 / RW-24)
#
# Every function below is the SINGLE production writer for a derived field. The
# defect catalogue calls these same writers after perturbing an *input* to the
# derivation, so a seeded defect can never author a derived answer directly — the
# failure this suite exists to exclude. See `run_defects.witness_channel_integrity`.
# --------------------------------------------------------------------------

# RW-20 — the interrupt-policy citation is a stimulus fact, not a constant. A8's
# `start_state` reads "quiet hours active; OD-1 policy PENDING"; the engine reads
# that text and cites what it finds, at the status it finds. A stimulus naming no
# interrupt policy produces NO citation, which is what makes the citation's
# presence discriminating rather than universal.
_INTERRUPT_POLICY_RE = re.compile(
    r"\b([A-Z]{2,5}-\d{1,3})\s+policy\s+(pending|ratified|approved)\b", re.IGNORECASE)


def interrupt_policy_citation(start_state: str) -> Optional[Tuple[str, str]]:
    """(policy_id, status) named by the stimulus, or None if none is named."""
    m = _INTERRUPT_POLICY_RE.search(start_state or "")
    if not m:
        return None
    return m.group(1).upper(), ("pending" if m.group(2).lower() == "pending"
                                else "ratified")


def focus_preserved(attention: str) -> bool:
    """RW-24 — focus preservation is COMPUTED from the disposition, not asserted.

    The named foreground focus is displaced exactly when the computed band is the
    INTERRUPTING one. `needs-owner` routes an item to the owner's queue; only
    `critical` seizes the surface the owner is currently working on (ATT-01 reserves
    that band for confirmed danger), and seizing the surface is what loses the
    pointer. D-B6 §2.3 hands the computed band to the B7 Desk projection; this is
    that projection's rule.

    The earlier version asserted `preserved: True` whenever a focus existed, so no
    engine behavior could disturb it.
    """
    return core.ATTENTION_ORDER[attention] < core.ATTENTION_ORDER[core.ATT_CRITICAL]


def recompute_focus_pointer(result: "ComputedResult") -> None:
    """Re-derive the emitted focus pointer from the (possibly perturbed) band."""
    for i, e in enumerate(result.events):
        if e.event_type == "FocusPointerEvent":
            p = dict(e.payload)
            p["preserved"] = focus_preserved(result.attention)
            result.events[i] = replace(e, payload=p)


def recompute_normalizer_invariants(extras: Dict[str, object]) -> None:
    """RW-22 — the E2E-1 invariant flags are DERIVED from the recorded results.

    `authority_invariant` and `risk_suggestions_differ` are functions of the
    per-normalizer records. Production and the defect catalogue both call this, so
    the `normalizer-authority-leak` mutation perturbs M2's recorded ceiling and the
    flag follows; it can no longer write `authority_invariant=False` — the key its
    own predicate reads.
    """
    r = extras.get("normalizers")
    if not isinstance(r, dict) or "M1" not in r or "M2" not in r:
        return
    extras["authority_invariant"] = (
        r["M1"]["ceiling"] == r["M2"]["ceiling"] and r["M1"]["tier"] == r["M2"]["tier"])
    extras["risk_suggestions_differ"] = (
        r["M1"]["risk_suggestion"] != r["M2"]["risk_suggestion"])


def set_normalizer_ceiling(result: "ComputedResult", model_name: str,
                           ceiling: str) -> None:
    """Perturb one recorded normalizer's authorized ceiling; re-derive the flags."""
    ex = copy.deepcopy(result.extras)
    norms = ex.get("normalizers")
    if not isinstance(norms, dict) or model_name not in norms:
        return
    norms[model_name]["ceiling"] = ceiling
    recompute_normalizer_invariants(ex)
    result.extras = ex


# --------------------------------------------------------------------------
# E2E-1 — two genuinely distinct deterministic normalizers over one raw input
# --------------------------------------------------------------------------

RAW_EMAIL_E2E1 = (
    "Subject: invoice 44821 settlement\n"
    "Please remit payment of $12,400.00 to the account on file by Friday.\n"
    "Wire details attached. Regards, Accounts Receivable\n"
)


def normalizer_m1(raw: str) -> core.ModelProposal:
    """M1: keyword+amount detector. Classifies the payment request correctly."""
    low = raw.lower()
    money = ("$" in raw) or ("remit" in low) or ("wire" in low)
    risk = "payment-request" if money else "routine-note"
    return core.ModelProposal(
        placement="finance/invoices" if money else "notes",
        action_class_suggestion="payment" if money else "file",
        risk_suggestion=risk,
        summary="invoice settlement request",
        confidence=0.91,
    )


def normalizer_m2(raw: str) -> core.ModelProposal:
    """M2: length/greeting heuristic. UNDERSTATES risk — calls it a routine note.

    Genuinely different computation (no shared code path with M1), which is the
    point of the substitution test: a weaker model must not be able to move
    authority, because authority is not model-derived.
    """
    lines = [ln for ln in raw.strip().splitlines() if ln.strip()]
    short = len(lines) <= 4
    risk = "routine-note" if short else "needs-review"
    return core.ModelProposal(
        placement="notes",
        action_class_suggestion="file",
        risk_suggestion=risk,
        summary="short note",
        confidence=0.62,
        # A defective normalizer would try to raise authority; the ceiling rule
        # must refuse it. The seeded-defect variant flips allow_raise on.
        proposed_ceiling=None,
    )


# --------------------------------------------------------------------------


def _eid(fixture_id: str, shape: str, tag: str, n: int = 0) -> str:
    return "%s/%s/%s%s" % (fixture_id, shape, tag, ("#%d" % n) if n else "")


def simulate(stim: Stimulus, shape: str, defects: Optional[Defects] = None,
             spec: Optional[scen.ScenarioSpec] = None) -> ComputedResult:
    """Compute one fixture x shape combination end to end.

    `spec` is supplied ONLY by harness self-tests (RW-19), which drive a synthetic
    stimulus through this same production path rather than through the corpus. Every
    fixture-driven run leaves it None and the scenario registry resolves it.
    """
    d = defects or Defects()
    if spec is None:
        spec = scen.get(stim.id)       # KeyError => unclassifiable => run FAILS

    required_fields = (
        "origin", "source_id", "source_type", "trust_class", "instruction_authority",
        "sensitivity_class", "data_class", "verification_state",
        "identity_session_state", "policy_version", "schema_version",
    )

    # AUT-05 inputs travel with the derived facts so the tier discriminator is
    # computed from stimulus rather than a hand flag (rework finding RW-05).
    derived = dict(spec.derived)
    if spec.placement_scope is not None:
        derived["placement_scope"] = spec.placement_scope
    if spec.proposed_action_class is not None:
        derived["proposed_action_class"] = spec.proposed_action_class
    if spec.hearsay_attribution is not None:
        derived["hearsay_attribution"] = spec.hearsay_attribution

    # --- stage 1-3: per-envelope verification and model-free base disposition ---
    per_env: List[core.BaseDisposition] = []
    all_reasons: List[str] = []
    for idx, env in enumerate(stim.envelopes):
        env_check = core.verify_envelope(env, required_fields)
        base = core.base_disposition(env, env_check, derived)
        per_env.append(base)
        for r in base.reasons:
            all_reasons.append("env[%d] %s" % (idx, r))

    # Governing disposition across a multi-input case = the most restrictive
    # ceiling with the highest attention (D-B8 P2G-10 rules 1 and 3).
    gov = min(per_env, key=lambda b: core.CEILING_ORDER[b.ceiling])
    attention = max((b.attention for b in per_env),
                    key=lambda a: core.ATTENTION_ORDER[a])
    tier = max((b.tier for b in per_env), key=lambda t: core.TIER_ORDER[t])
    gov = core.BaseDisposition(
        tier=tier, ceiling=gov.ceiling, attention=attention, reasons=tuple(all_reasons),
        quarantined=any(b.quarantined for b in per_env),
        step_up_required=any(b.step_up_required for b in per_env),
        step_up_satisfied=all(b.step_up_satisfied for b in per_env if b.step_up_required),
    )

    # --- stage 2: policy composition (D-B8 P2G-10) ---
    # RW-13: the evaluation instant and envelope are supplied, so PC-4 window
    # filtering, D-B8 §2 scope and applicability predicates are live paths rather
    # than dead schema. EVAL_INSTANT is a fixed logical clock (no wall-clock).
    comp = core.compose_policies(spec.policies, at_time=EVAL_INSTANT,
                                 envelope=stim.envelopes[0])
    ceiling = gov.ceiling
    if core.CEILING_ORDER[comp.ceiling] < core.CEILING_ORDER[ceiling]:
        ceiling = comp.ceiling
    if comp.failed_closed:
        ceiling = core.CEILING_NONE
        all_reasons.extend(comp.reasons)
        all_reasons.append("policy-composition failed closed -> no-action + T3 escalation")
        tier = core.T3
    if core.ATTENTION_ORDER[comp.attention_min] > core.ATTENTION_ORDER[gov.attention]:
        attention = comp.attention_min
    if comp.tier_max is not None and core.TIER_ORDER[comp.tier_max] < core.TIER_ORDER[tier]:
        tier = comp.tier_max

    disp = core.BaseDisposition(
        tier=tier, ceiling=ceiling, attention=attention, reasons=tuple(all_reasons),
        quarantined=gov.quarantined, step_up_required=gov.step_up_required,
        step_up_satisfied=gov.step_up_satisfied,
    )

    # --- stage 4: model-proposal integration (lower/escalate only) ---
    notes: List[str] = []
    for i, prop in enumerate(spec.proposals):
        disp, n = core.integrate_proposal(disp, prop, allow_raise=d.authority_raise)
        notes.extend("proposal[%d] %s" % (i, x) for x in n)

    # RW-02 — the owner completing the step-up is an input-side fact where the
    # fixture narrative says the owner approves. Without it the consequential
    # lifecycle is refused and every predicate on that chain is vacuous.
    if spec.owner_step_up_provided and disp.step_up_required:
        disp = core.BaseDisposition(
            tier=disp.tier, ceiling=core.CEILING_CONSEQUENTIAL,
            attention=disp.attention,
            reasons=disp.reasons + ("owner step-up completed (IDN-02) -> "
                                    "consequential chain authorized",),
            quarantined=disp.quarantined, step_up_required=True,
            step_up_satisfied=True,
        )

    # --- IDN-03 / D-KR §1.2: a kill revokes action authority immediately ---
    # The owner's authority to ISSUE the kill is not the authority available AFTER
    # it. Post-kill the system enters emergency read-only (D-KR §1.3): write and
    # outbound authority are revoked, in-flight work halts, reads survive.
    if spec.kill_triggered:
        disp = core.BaseDisposition(
            tier=disp.tier,
            ceiling=core.CEILING_RECORD_ONLY,
            attention=core.ATT_CRITICAL,
            reasons=disp.reasons + (
                "IDN-03 kill executed -> action authority revoked; "
                "emergency read-only retained (D-KR §1.2/§1.3)",),
            quarantined=disp.quarantined,
            step_up_required=disp.step_up_required,
            step_up_satisfied=disp.step_up_satisfied,
        )

    # --- P2S-07 proposal eligibility ---
    trust0 = stim.envelopes[0].get("trust_class", "")
    eligible = list(core.eligible_proposal_classes(trust0, spec.eligibility))
    if d.skip_eligibility_check:
        eligible = ["filing", "placement", "summary"]
        notes.append("DEFECT: eligibility check skipped")
    proposals_emitted: List[str] = []
    if spec.proposals or trust0.lower().startswith("external-untrusted"):
        for cls in ("filing", "placement", "summary"):
            if cls in eligible:
                proposals_emitted.append(cls)

    uncertain_outcome = False

    # --- event construction (D-B9 §2 taxonomy) ---
    events: List[Event] = []
    seq = 0

    def add(etype: str, tag: str, *, caused_by: Tuple[str, ...] = (),
            payload: Optional[Dict[str, object]] = None,
            external: bool = False, object_key: str = "-", n: int = 0) -> str:
        nonlocal seq
        seq += 1
        eid = _eid(stim.id, shape, tag, n)
        events.append(Event(
            event_id=eid, event_type=etype, partition="business",
            object_key=object_key, store_seq=seq, caused_by=caused_by,
            payload=payload or {}, externally_authored=external,
        ))
        return eid

    pol_ev = add("PolicyVersionEvent", "policy", payload={"version": "P1"}, object_key="policy")

    ingest_ids: List[str] = []
    for i, env in enumerate(stim.envelopes):
        ingest_ids.append(add("IngestionEvent", "ingest", n=i + 1,
                              payload={"envelope_index": i, "origin": env.get("origin")},
                              object_key="intake"))

    if spec.duplicate_delivery:
        # D-B4 scenario 5: both appends succeed; dedup resolves post-intake.
        dup = add("DuplicateDeliveryEvent", "dup", caused_by=(ingest_ids[0],),
                  payload={"dedup_basis": "source-native-event-id"
                           if spec.native_event_id else "content-hash"},
                  object_key="intake")
        ingest_ids.append(dup)

    model_ids: List[str] = []
    for i, prop in enumerate(spec.proposals):
        if prop is None:
            continue
        basis = (ingest_ids[i],) if i < len(ingest_ids) else (ingest_ids[0],)
        model_ids.append(add("RecordedModelOutput", "model", n=i + 1, caused_by=basis,
                             payload={"placement": prop.placement,
                                      "risk": prop.risk_suggestion,
                                      "confidence": prop.confidence},
                             object_key="model"))

    eval_id = add("PolicyEvaluationRecord", "eval",
                  caused_by=tuple([pol_ev] + ingest_ids + model_ids),
                  payload={"policy_version": "P1", "applied": ",".join(comp.applied)},
                  object_key="case")

    decision_payload: Dict[str, object] = {
        "disposition": disp.tier, "ceiling": disp.ceiling,
        "basis_policy_version": "P1",
        "falsifier_status": "identified"
        if disp.tier in (core.T3, core.T4) else "none_identified"}
    # RW-16 / RW-20: an interrupt policy that the stimulus records as PENDING is
    # citable as pending, never as ratified (D-B7 §3, per packet). Both the policy
    # id and its status come from the stimulus, so the citation is conditioned on
    # the input rather than stamped on every decision of every fixture.
    _cite = interrupt_policy_citation(stim.start_state)
    if _cite is not None:
        decision_payload["interrupt_policy"] = _cite[0]
        decision_payload["interrupt_policy_status"] = _cite[1]
    decision_id = add("DecisionEvent", "decision", caused_by=(eval_id,),
                      payload=decision_payload, object_key="case")

    # RW-12(3) — the engine records WHICH input origin drove the band, so
    # "email interrupting sleep" is detectable from computed state.
    driving = max(range(len(per_env)),
                  key=lambda i: core.ATTENTION_ORDER[per_env[i].attention])
    add("AttentionChangeEvent", "attn", caused_by=(decision_id,),
        payload={"object": stim.id, "band": disp.attention,
                 "source_origin": str(stim.envelopes[driving].get("origin", "")),
                 "source_trust": str(stim.envelopes[driving].get("trust_class", "")),
                 "quiet_hours": bool(spec.quiet_hours)}, object_key="case")

    # RW-24 — the suppression record is COMPUTED. During quiet hours every input
    # whose OWN band sits below the interrupting threshold is held to the morning
    # briefing, and the record names which input was held. The previous matcher
    # accepted any AttentionChangeEvent, which every run emits, so "suppression
    # record present" was satisfied vacuously.
    if spec.quiet_hours:
        for idx, b in enumerate(per_env):
            if core.ATTENTION_ORDER[b.attention] >= core.ATTENTION_ORDER[core.ATT_CRITICAL]:
                continue
            add("AttentionChangeEvent", "suppress", n=idx + 1, caused_by=(decision_id,),
                payload={"object": "%s/suppressed/%d" % (stim.id, idx),
                         "band": b.attention,
                         "record": "suppression",
                         "suppressed_source_id":
                             str(stim.envelopes[idx].get("source_id", "")),
                         "suppressed_until": "morning-briefing",
                         "source_trust": str(stim.envelopes[idx].get("trust_class", "")),
                         "quiet_hours": True}, object_key="attention")

    # Requirement 6 — actions and externally owned receipts.
    executed_without_receipt = False
    for act in spec.actions:
        # RW-15: degradation refuses consequential classes independently of the
        # envelope ceiling, and cites the degradation as the reason.
        degraded_refusal = (bool(spec.degraded_stores)
                            and act.action_class in CONSEQUENTIAL_CLASSES
                            and not d.ignore_degradation)
        if degraded_refusal:
            add("RefusalEvent", "refuse-degraded-" + act.action_id,
                caused_by=(decision_id,),
                payload={"action_class": act.action_class,
                         "reason": "consequential action refused while stores are "
                                   "degraded: %s (D-B5 degraded-operation rule)"
                                   % ",".join(spec.degraded_stores),
                         "refused_due_to_degradation": True,
                         "degraded_stores": ",".join(spec.degraded_stores)},
                object_key="case")
            continue
        # An action may only be emitted if the computed ceiling permits it.
        permitted = core.CEILING_ORDER[disp.ceiling] >= core.CEILING_ORDER[
            core.CEILING_ACT_WITH_RECEIPT]
        if not permitted:
            add("RefusalEvent", "refuse-" + act.action_id, caused_by=(decision_id,),
                payload={"action_class": act.action_class,
                         "reason": "ceiling %s does not authorize %s"
                                   % (disp.ceiling, act.action_class)},
                object_key="case")
            continue
        act_payload: Dict[str, object] = {
            "action_class": act.action_class, "aik": act.action_id}
        if d.drop_receipt and act.receipt_arrives:
            # Seeded defect: the receipt is lost but the candidate still advances the
            # action to executed. Requirement 6 must catch the unevidenced state.
            act_payload["defect_force_executed"] = True
        aid = add("ActionRequest", "action-" + act.action_id, caused_by=(decision_id,),
                  payload=act_payload, object_key="case")
        receipt_arrives = act.receipt_arrives and not d.drop_receipt
        if receipt_arrives:
            add("EvidenceIngestionEvent", "receipt-" + act.action_id, caused_by=(aid,),
                payload={"answers_action": aid, "evidence_kind": act.receipt_kind,
                         "content_hash": hashlib.sha256(aid.encode()).hexdigest()[:16]},
                external=not d.engine_authored_receipt,
                object_key="evidence")
            if act.verification_arrives:
                vid = add("EvidenceIngestionEvent", "verify-" + act.action_id,
                          caused_by=(aid,),
                          payload={"answers_action": aid,
                                   "evidence_kind": "verification"},
                          external=True, object_key="evidence")
                add("ReconciliationEvent", "recon-" + act.action_id,
                    caused_by=(aid, vid),
                    payload={"reason": "post-state reconciled against this action's "
                                       "own external verification record"},
                    object_key="case")
            if act.receipt_kind == "verification":
                # ACT-01: the consequential chain reconciles post-state once the
                # external verification lands (S6/A12 require the reconciliation
                # record as part of the full typed-record chain).
                add("ReconciliationEvent", "recon-" + act.action_id, caused_by=(aid,),
                    payload={"reason": "post-state reconciled against external "
                                       "verification record"}, object_key="case")
        else:
            # ACT-01: uncertain outcome halts automatic retry and raises Needs Review.
            add("ReconciliationEvent", "recon-" + act.action_id, caused_by=(aid,),
                payload={"reason": "no receipt recorded; reconcile before retry",
                         "outbox_residue": aid}, object_key="case")
            executed_without_receipt = True
            uncertain_outcome = True

    # RW-15 — D-B5 degraded-operation rule (quoted in Rework Packet R2): consequential
    # actions are REFUSED during the relevant degradations, regardless of envelope
    # authority, and every such refusal is recorded (DegradationEvent + RefusalEvent).
    # Previously A10's refusal came from its envelope ceiling and the degradation
    # played no role — the hazard was guarded by accident.

    # RW-01 — accomplished external side effects. These already fired; the engine
    # cannot refuse them. With no receipt recorded the outcome is UNCERTAIN, so
    # ACT-01 / D-B4 §2.3 rule 5 requires: halt, raise Needs Review, reconcile before
    # any retry — and the engine must NOT mark the action executed on its own say-so.
    for acc in spec.accomplished_actions:
        aid = add("ActionRequest", "accomplished-" + acc.action_id,
                  caused_by=(decision_id,),
                  payload={"action_class": acc.action_class, "aik": acc.action_id,
                           "already_fired": True,
                           "idempotency_key": acc.idempotency_key},
                  object_key="case")
        if acc.receipt_recorded:
            add("EvidenceIngestionEvent", "receipt-" + acc.action_id, caused_by=(aid,),
                payload={"answers_action": aid, "evidence_kind": "receipt"},
                external=True, object_key="evidence")
        else:
            uncertain_outcome = True
            add("ReconciliationEvent", "recon-" + acc.action_id, caused_by=(aid,),
                payload={"reason": "side effect fired; no receipt at recovery — "
                                   "halt and reconcile before retry (ACT-01)",
                         "outbox_residue": aid, "halted": True,
                         "auto_retry_blocked": True}, object_key="case")
            add("AttentionChangeEvent", "needs-review-" + acc.action_id,
                caused_by=(aid,),
                payload={"object": stim.id, "band": core.ATT_NEEDS_OWNER,
                         "reason": "uncertain external outcome"}, object_key="case")

    # RW-06 — in-flight work halted by a kill (A15's "active T2 batch").
    for inflight in spec.in_flight_actions:
        iid = add("ActionRequest", "inflight-" + inflight.action_id,
                  caused_by=(decision_id,),
                  payload={"action_class": inflight.action_class,
                           "aik": inflight.action_id, "in_flight": True},
                  object_key="case")
        if spec.kill_triggered:
            add("RefusalEvent", "halt-" + inflight.action_id, caused_by=(iid,),
                payload={"reason": "IDN-03 kill: in-flight action halted",
                         "halted_action": iid}, object_key="case")

    # RW-06 — A13's notification-preview surface: a second, stricter enforcement
    # point than in-channel render (D-B2 P2G-13 §6).
    if spec.notification_preview:
        add("AttentionChangeEvent", "notify-preview", caused_by=(decision_id,),
            payload={"object": stim.id, "band": disp.attention,
                     "surface": "notification-preview",
                     "render_class": comp.render_class or "unset"},
            object_key="notify")

    if spec.concurrent_conflict:
        add("ConflictRecord", "conflict", caused_by=(decision_id,),
            payload={"reason": "CAS version miss on concurrent placement"},
            object_key="case")

    if spec.foldback_targets:
        intent = add("IntentEvent", "intent", caused_by=(decision_id,),
                     payload={"targets": spec.foldback_targets}, object_key="case")
        applied = spec.crash_after_applies if spec.crash_after_applies is not None \
            else spec.foldback_targets
        for i in range(applied):
            add("FoldBackEvent", "foldback", n=i + 1, caused_by=(intent,),
                payload={"target": i + 1}, object_key="case")
        if applied < spec.foldback_targets:
            add("ReconciliationEvent", "recon-foldback", caused_by=(intent,),
                payload={"reason": "partial fold-back exposed",
                         "outbox_residue": intent}, object_key="case")

    if spec.correction_requested:
        add("CorrectionEvent", "correction", caused_by=(decision_id,),
            payload={"corrects": decision_id, "weight": "weak-evidence"},
            object_key="case")

    if spec.degraded_stores:
        for s in spec.degraded_stores:
            add("DegradationEvent", "degraded-" + s, caused_by=(pol_ev,),
                payload={"store": s}, object_key="case")

    if spec.kill_triggered:
        add("KillCommandEvent", "kill", caused_by=(pol_ev,),
            payload={"scope": "write+outbound", "read_only_preserved": True},
            object_key="policy")

    if spec.evidence_write_attempt:
        add("RefusalEvent", "refuse-evidence-write", caused_by=(ingest_ids[0],),
            payload={"reason": "append-only evidence store; no engine credential"},
            object_key="case")

    if spec.schedule_envelope_expired:
        add("RefusalEvent", "refuse-stale-schedule", caused_by=(ingest_ids[0],),
            payload={"reason": "SCH-02 control envelope expired -> fail closed"},
            object_key="case")

    if spec.worker_died and spec.checkpoint_current:
        add("CheckpointEvent", "checkpoint", caused_by=(pol_ev,),
            payload={"resumable": True}, object_key="case")

    if spec.aging_ran:
        add("AgingEvent", "aging", caused_by=(pol_ev,), payload={"consolidated": True},
            object_key="case")

    if spec.intents > 1:
        for i in range(spec.intents):
            add("PlacementEvent", "placement", n=i + 1, caused_by=(decision_id,),
                payload={"intent_index": i + 1}, object_key="case")

    # RW-14 — the applied render class is a COMPUTED record, so "DAT masking
    # verified" can be checked against engine output instead of the scenario's
    # own declaration.
    if comp.render_class is not None and not d.render_leak:
        add("PlacementEvent", "render-policy", caused_by=(decision_id,),
            payload={"record": "render-policy-application",
                     "render_class": comp.render_class,
                     "data_class": str(stim.envelopes[0].get("data_class", "")),
                     "restricted_tokens_masked": True}, object_key="render")

    # RW-11 — watchdog liveness (D-KR §3 / RES-02). S1's start_state records a fresh
    # heartbeat; the engine emits the corresponding control-journal signal, so a real
    # defect (a missing heartbeat) is what the predicate detects, not a flag.
    if spec.watchdog_monitored:
        # RW-24: freshness is read from the recorded liveness fact, not hard-coded.
        # A stimulus recording a stale heartbeat now produces a stale signal.
        add("WatchdogHeartbeatEvent", "watchdog", caused_by=(pol_ev,),
            payload={"fresh": bool(spec.derived.get("watchdog_fresh")),
                     "monitor": "control-service"},
            object_key="control")

    # RW-11 — focus pointer. S3's start_state names the foreground focus; preserving
    # it across an interjection is a computed projection, not an asserted flag.
    focus = spec.derived.get("foreground_focus")
    if focus or spec.derived.get("read_only_view"):
        # A reconnect/read view renders the last-focus pointer as part of the Desk
        # projection. RW-24: whether the interjection preserves the named foreground
        # is DERIVED from the computed band (see `focus_preserved`), so an engine
        # that escalates the interjection loses the pointer and the predicate sees it.
        add("FocusPointerEvent", "focus", caused_by=(decision_id,),
            payload={"foreground": str(focus) if focus else "last-focus",
                     "preserved": focus_preserved(disp.attention)}, object_key="case")

    # RW-11 — recall by description. S9's start_state records that the S2 capture
    # exists; the engine computes a hit against that recorded prior capture.
    if spec.recall_query:
        add("RecallResultEvent", "recall", caused_by=(decision_id,),
            payload={"hit": bool(spec.derived.get("prior_capture_exists")),
                     "route": "direct-link"}, object_key="case")

    # RW-16 — S2's attributed third-party mention becomes a provenance-labeled
    # hearsay record on the computed output (D-B2 P2G-13 §2/§3 per-claim provenance).
    if spec.hearsay_attribution:
        add("ProvenanceRecord", "hearsay", caused_by=(decision_id,),
            payload={"claim_type": "topic-candidate",
                     "attributed_to": str(spec.hearsay_attribution),
                     "provenance_class": "hearsay-attributed",
                     "verified": False}, object_key="case")

    # RW-12(4) — S4's override is a recorded event, emitted once. Repeat-confirm
    # nagging is then a genuine defect (more than one) rather than an absent path.
    if spec.override_requested:
        add("OverrideEvent", "override", caused_by=(decision_id,),
            payload={"consequence_summary_shown": True, "acknowledged": True,
                     "prompts": 1}, object_key="case")

    if core.ATTENTION_ORDER[disp.attention] >= core.ATTENTION_ORDER[core.ATT_HUB]:
        add("QueueAdmissionEvent", "queue", caused_by=(decision_id,),
            payload={"item": stim.id}, object_key="queue")

    # --- E2E-1: run BOTH normalizers and compare authorized authority ---
    extras: Dict[str, object] = {}
    if spec.two_normalizers:
        env0 = stim.envelopes[0]
        v0 = core.verify_envelope(env0, required_fields)
        results = {}
        for name, fn in (("M1", normalizer_m1), ("M2", normalizer_m2)):
            prop = fn(RAW_EMAIL_E2E1)
            if d.normalizer_authority_leak and name == "M2":
                prop = core.ModelProposal(
                    placement=prop.placement, risk_suggestion=prop.risk_suggestion,
                    summary=prop.summary, confidence=prop.confidence,
                    proposed_ceiling=core.CEILING_OUTBOUND,
                )
            b = core.base_disposition(env0, v0, spec.derived)
            b2, _ = core.integrate_proposal(
                b, prop, allow_raise=d.authority_raise or d.normalizer_authority_leak)
            # RW-27: the per-normalizer BAND is recorded too, so E2E-1's
            # "same or escalated, never relaxed by M2" is comparable on the
            # attention dimension and not only on ceiling/tier.
            results[name] = {"risk_suggestion": prop.risk_suggestion,
                             "ceiling": b2.ceiling, "tier": b2.tier,
                             "attention": b2.attention}
        extras["normalizers"] = results
        # RW-22: derived through the single production writer, which the defect
        # catalogue also calls after perturbing a recorded ceiling.
        recompute_normalizer_invariants(extras)

    # --- fold the multi-store basis (requirement 7) ---
    fold_error = None
    folded = None
    receipt_problems: List[str] = []
    fold_input = list(events)
    if d.causal_reorder:
        from fold import permute
        fold_input = permute(fold_input, seed=20260730)
    try:
        folded = fold(
            fold_input, shape=shape, case_id=stim.id,
            enforce_causality=not d.causal_reorder,
            enforce_receipt_ownership=not d.engine_authored_receipt,
            rebuild_projections=not d.stale_projection,
        )
        receipt_problems = receipt_ownership_violations(folded, fold_input)
    except FoldError as exc:
        fold_error = str(exc)

    storage_summary = folded.storage.storage_summary() if folded else {}

    state_written_on_read = False
    if spec.derived.get("read_only_view"):
        write_types = {"PlacementEvent", "ActionRequest", "FoldBackEvent",
                       "CorrectionEvent", "ReclassificationEvent"}
        state_written_on_read = any(e.event_type in write_types for e in events)
        if d.admit_forbidden:
            add("PlacementEvent", "illegal-write", caused_by=(decision_id,),
                payload={"note": "DEFECT: state written on a read path"},
                object_key="case")
            state_written_on_read = True

    outbound_authorized = core.CEILING_ORDER[disp.ceiling] >= core.CEILING_ORDER[
        core.CEILING_OUTBOUND]

    return ComputedResult(
        fixture_id=stim.id, shape=shape, tier=disp.tier, ceiling=disp.ceiling,
        attention=disp.attention, quarantined=disp.quarantined,
        step_up_required=disp.step_up_required, step_up_satisfied=disp.step_up_satisfied,
        reasons=list(disp.reasons), proposal_notes=notes,
        eligible_proposal_classes=eligible, proposals_emitted=proposals_emitted,
        events=events, folded=folded, receipt_violations=receipt_problems,
        per_envelope_attention=[b.attention for b in per_env],
        storage_summary=storage_summary, state_written_on_read=state_written_on_read,
        outbound_authorized=outbound_authorized,
        executed_without_receipt=executed_without_receipt,
        fold_error=fold_error,
        uncertain_outcome=uncertain_outcome,
        halted_actions=[e.event_id for e in events
                        if e.event_type == "RefusalEvent" and e.payload.get("halted_action")],
        notify_render_class=next(
            (str(e.payload.get("render_class")) for e in events
             if e.event_type == "AttentionChangeEvent"
             and e.payload.get("surface") == "notification-preview"), None),
        composition_refused=list(comp.refused),
        composition_reasons=list(comp.reasons),
        composition_attention_min=comp.attention_min,
        extras=extras,
    )


def simulate_all_shapes(stim: Stimulus,
                        defects: Optional[Defects] = None) -> Dict[str, ComputedResult]:
    return {shape: simulate(stim, shape, defects) for shape in SHAPES}


def divergences_for(results: Dict[str, ComputedResult]) -> List[Dict[str, object]]:
    """Requirement 9 — candidate-specific divergences computed from computed storage."""
    summaries = {s: r.storage_summary for s, r in results.items() if r.storage_summary}
    div = shape_divergences(summaries)
    # Authority/policy outputs must be shape-invariant (D-B6 §2.1 purity).
    for shape, r in sorted(results.items()):
        ref = results["S2"]
        if (r.tier, r.ceiling, r.attention) != (ref.tier, ref.ceiling, ref.attention):
            div.append({
                "shape": shape, "kind": "authority-divergence",
                "detail": "%s computed (%s,%s,%s) vs S2 (%s,%s,%s) — shape neutrality breach"
                          % (shape, r.tier, r.ceiling, r.attention,
                             ref.tier, ref.ceiling, ref.attention),
            })
    return div

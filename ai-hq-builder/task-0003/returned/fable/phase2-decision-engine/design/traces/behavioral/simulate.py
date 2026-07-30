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

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import engine_core as core
import scenarios as scen
from events import Event, ShapeStorage, SHAPES, shape_divergences
from fixture_io import Stimulus
from fold import FoldError, fold, receipt_ownership_violations


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
    lease_before_policy: bool = False
    normalizer_authority_leak: bool = False

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
    extras: Dict[str, object] = field(default_factory=dict)

    def digest(self) -> str:
        return self.folded.digest() if self.folded is not None else "-"


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


def simulate(stim: Stimulus, shape: str, defects: Optional[Defects] = None) -> ComputedResult:
    """Compute one fixture x shape combination end to end."""
    d = defects or Defects()
    spec = scen.get(stim.id)           # KeyError => unclassifiable => run FAILS

    required_fields = (
        "origin", "source_id", "source_type", "trust_class", "instruction_authority",
        "sensitivity_class", "data_class", "verification_state",
        "identity_session_state", "policy_version", "schema_version",
    )

    # --- stage 1-3: per-envelope verification and model-free base disposition ---
    per_env: List[core.BaseDisposition] = []
    all_reasons: List[str] = []
    for idx, env in enumerate(stim.envelopes):
        env_check = core.verify_envelope(env, required_fields)
        base = core.base_disposition(env, env_check, spec.derived)
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
    comp = core.compose_policies(spec.policies)
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

    decision_id = add("DecisionEvent", "decision", caused_by=(eval_id,),
                      payload={"disposition": disp.tier, "ceiling": disp.ceiling,
                               "basis_policy_version": "P1",
                               "falsifier_status": "identified"
                               if disp.tier in (core.T3, core.T4) else "none_identified"},
                      object_key="case")

    add("AttentionChangeEvent", "attn", caused_by=(decision_id,),
        payload={"object": stim.id, "band": disp.attention}, object_key="case")

    # Requirement 6 — actions and externally owned receipts.
    executed_without_receipt = False
    for act in spec.actions:
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
        else:
            # ACT-01: uncertain outcome halts automatic retry and raises Needs Review.
            add("ReconciliationEvent", "recon-" + act.action_id, caused_by=(aid,),
                payload={"reason": "no receipt recorded; reconcile before retry",
                         "outbox_residue": aid}, object_key="case")
            executed_without_receipt = True

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
            results[name] = {"risk_suggestion": prop.risk_suggestion,
                             "ceiling": b2.ceiling, "tier": b2.tier}
        extras["normalizers"] = results
        extras["authority_invariant"] = (
            results["M1"]["ceiling"] == results["M2"]["ceiling"]
            and results["M1"]["tier"] == results["M2"]["tier"]
        )
        extras["risk_suggestions_differ"] = (
            results["M1"]["risk_suggestion"] != results["M2"]["risk_suggestion"]
        )

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
        storage_summary=storage_summary, state_written_on_read=state_written_on_read,
        outbound_authorized=outbound_authorized,
        executed_without_receipt=executed_without_receipt,
        fold_error=fold_error, extras=extras,
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

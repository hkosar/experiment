"""Candidate-defect mutations — the machinery that makes predicates falsifiable.

Rework finding RW-02: 51 of 56 forbidden predicates could never return True, so the
"171 predicates evaluated" headline could not distinguish a correct engine from a
broken one. A predicate is only evidence if some reachable defect makes it fire.

Each mutation here expresses a PLAUSIBLE CANDIDATE DEFECT as a change to the
computed events/state — never as a direct write to a predicate's answer. The
predicate must still detect the defect on its own terms; otherwise the pairing
would be as circular as the evidence this whole task replaced.

Mutations are applied AFTER `simulate()` so they are independent of the engine's
own code paths, which keeps the seeded-defect suite honest: it perturbs the
engine's *output*, exactly as a real defect would manifest.
"""

from __future__ import annotations

import copy
from dataclasses import replace
from typing import Callable, Dict, List, Optional, Tuple

import engine_core as core
from events import Event

# name -> (description, mutate(result) -> None)
MUTATIONS: Dict[str, Tuple[str, Callable]] = {}


def mutation(name: str, description: str):
    def deco(fn):
        MUTATIONS[name] = (description, fn)
        return fn
    return deco


# ----------------------------------------------------------------- helpers

def _drop(result, etype: str) -> None:
    result.events = [e for e in result.events if e.event_type != etype]


def _dup_first(result, etype: str) -> None:
    for e in list(result.events):
        if e.event_type == etype:
            result.events.append(replace(e, event_id=e.event_id + "#dup",
                                         store_seq=e.store_seq + 1000))
            return


def _add(result, etype: str, tag: str, payload: Dict[str, object],
         caused_by: Tuple[str, ...] = (), external: bool = False,
         object_key: str = "case") -> None:
    result.events.append(Event(
        event_id="%s/%s/mut-%s" % (result.fixture_id, result.shape, tag),
        event_type=etype, partition="business", object_key=object_key,
        store_seq=9000 + len(result.events), caused_by=caused_by,
        payload=payload, externally_authored=external))


def _first_id(result, etype: str) -> Optional[str]:
    for e in result.events:
        if e.event_type == etype:
            return e.event_id
    return None


# ------------------------------------------------------- authority defects

@mutation("authority-raise", "a model proposal raises the ceiling above the model-free base")
def _m_authority_raise(result, spec, stim):
    result.proposal_notes.append("DEFECT: model proposal RAISED ceiling to outbound")
    result.ceiling = core.CEILING_OUTBOUND
    result.outbound_authorized = True


@mutation("untrusted-outbound", "untrusted-content basis reaches an outbound authorization")
def _m_untrusted_outbound(result, spec, stim):
    result.ceiling = core.CEILING_OUTBOUND
    result.outbound_authorized = True


@mutation("channel-trust-action", "an action is authorized on channel trust with identity unbound")
def _m_channel_trust(result, spec, stim):
    _add(result, "ActionRequest", "channel-trust",
         {"action_class": "filing-routing", "aik": "mut-channel"})
    result.ceiling = core.CEILING_NONE


@mutation("default-to-trusted", "unknown mandatory controls are treated as trusted")
def _m_default_trusted(result, spec, stim):
    if result.quarantined:
        result.ceiling = core.CEILING_ACT_WITH_RECEIPT


@mutation("step-up-bypass", "a step-up-gated action proceeds without the step-up")
def _m_step_up_bypass(result, spec, stim):
    if result.step_up_required and not result.step_up_satisfied:
        _add(result, "ActionRequest", "stepup-bypass",
             {"action_class": "payment", "aik": "mut-stepup"})
        result.ceiling = core.CEILING_CONSEQUENTIAL


@mutation("step-up-never-completed",
          "the step-up was never completed yet the approved action still stands")
def _m_step_up_missing(result, spec, stim):
    # The candidate loses the step-up evidence but keeps the authorization —
    # the approve-without-step-up defect the fixture forbids.
    if result.step_up_required:
        result.step_up_satisfied = False


@mutation("post-kill-action", "an action executes after the kill command")
def _m_post_kill(result, spec, stim):
    kill = _first_id(result, "KillCommandEvent")
    if kill:
        aid = "%s/%s/mut-postkill" % (result.fixture_id, result.shape)
        _add(result, "ActionRequest", "postkill",
             {"action_class": "filing-routing", "aik": "mut-postkill"}, caused_by=(kill,))
        _add(result, "EvidenceIngestionEvent", "postkill-receipt",
             {"answers_action": aid, "evidence_kind": "receipt"},
             caused_by=(aid,), external=True, object_key="evidence")


@mutation("kill-ceremony", "the kill requires more than one command to take effect")
def _m_kill_ceremony(result, spec, stim):
    if _first_id(result, "KillCommandEvent"):
        _dup_first(result, "KillCommandEvent")


# -------------------------------------------------------- receipt defects

@mutation("engine-authored-receipt", "the engine authors its own evidence record")
def _m_engine_receipt(result, spec, stim):
    for i, e in enumerate(result.events):
        if e.event_type == "EvidenceIngestionEvent":
            result.events[i] = replace(e, externally_authored=False)
            result.receipt_violations.append("receipt %s is engine-authored" % e.event_id)
            return
    aid = _first_id(result, "ActionRequest")
    if aid:
        _add(result, "EvidenceIngestionEvent", "self-receipt",
             {"answers_action": aid, "evidence_kind": "receipt"},
             caused_by=(aid,), external=False, object_key="evidence")
        result.receipt_violations.append("engine-authored receipt for %s" % aid)


@mutation("executed-without-receipt", "state advances to executed with no receipt")
def _m_exec_no_receipt(result, spec, stim):
    aid = _first_id(result, "ActionRequest")
    if aid and result.folded is not None:
        result.folded.executed_actions.append(aid)
        result.folded.canonical.setdefault(aid, {})["state"] = "executed"
        result.receipt_violations.append(
            "action %s reached executed/verified with no receipt" % aid)


@mutation("receipt-overwrite", "one action accumulates two receipts")
def _m_receipt_overwrite(result, spec, stim):
    _dup_first(result, "EvidenceIngestionEvent")


@mutation("verification-skipped", "an executed action is never verified")
def _m_skip_verification(result, spec, stim):
    if result.folded is not None and result.folded.verified_actions:
        result.folded.verified_actions.clear()
    elif result.folded is not None and not result.folded.executed_actions:
        aid = _first_id(result, "ActionRequest")
        if aid:
            result.folded.executed_actions.append(aid)


@mutation("double-execution", "the same action executes twice")
def _m_double_exec(result, spec, stim):
    if result.folded is not None and result.folded.executed_actions:
        result.folded.executed_actions.append(result.folded.executed_actions[0])
    else:
        aid = _first_id(result, "ActionRequest")
        if aid and result.folded is not None:
            result.folded.executed_actions.extend([aid, aid])


@mutation("acting-while-degraded", "an action executes while its store is degraded")
def _m_degraded_act(result, spec, stim):
    if any(e.event_type == "DegradationEvent" for e in result.events):
        aid = _first_id(result, "ActionRequest") or "mut-degraded"
        if result.folded is not None:
            result.folded.executed_actions.append(aid)


# ------------------------------------------------- reconciliation defects

@mutation("drop-reconciliation", "an uncertain outcome retries without reconciling")
def _m_drop_recon(result, spec, stim):
    _drop(result, "ReconciliationEvent")


@mutation("drop-refusal", "a refusal is never recorded (tamper/stale-rule suppressed)")
def _m_drop_refusal(result, spec, stim):
    _drop(result, "RefusalEvent")


@mutation("drop-conflict-record", "a concurrent conflict is silently resolved")
def _m_drop_conflict(result, spec, stim):
    _drop(result, "ConflictRecord")


@mutation("drop-checkpoint", "resumption proceeds with no checkpoint record")
def _m_drop_checkpoint(result, spec, stim):
    _drop(result, "CheckpointEvent")


@mutation("drop-aging", "the aging ladder leaves no event trail")
def _m_drop_aging(result, spec, stim):
    _drop(result, "AgingEvent")


@mutation("drop-foldback", "a parent is updated with no fold-back event")
def _m_drop_foldback(result, spec, stim):
    _drop(result, "FoldBackEvent")


@mutation("drop-ingestion", "a delivered input is never durably captured")
def _m_drop_ingestion(result, spec, stim):
    for e in list(result.events):
        if e.event_type == "IngestionEvent":
            result.events.remove(e)
            return


@mutation("drop-placement", "one of several captured intents is dropped")
def _m_drop_placement(result, spec, stim):
    for e in list(result.events):
        if e.event_type == "PlacementEvent":
            result.events.remove(e)
            return


@mutation("extra-placement", "a routine recurring item creates its own case each time")
def _m_extra_placement(result, spec, stim):
    _add(result, "PlacementEvent", "extra-case", {"intent_index": 99})
    _add(result, "PlacementEvent", "extra-case-2", {"intent_index": 100})


@mutation("drop-decision", "an override lands with no decision/override record")
def _m_drop_decision(result, spec, stim):
    _drop(result, "DecisionEvent")


@mutation("duplicate-queue-card", "one item is admitted to the queue twice")
def _m_dup_queue(result, spec, stim):
    _dup_first(result, "QueueAdmissionEvent")
    if not any(e.event_type == "QueueAdmissionEvent" for e in result.events):
        _add(result, "QueueAdmissionEvent", "q1", {"item": result.fixture_id},
             object_key="queue")
        _add(result, "QueueAdmissionEvent", "q2", {"item": result.fixture_id},
             object_key="queue")


@mutation("repeat-confirm", "the owner is asked to confirm the same override repeatedly")
def _m_repeat_confirm(result, spec, stim):
    _add(result, "OverrideEvent", "confirm-1", {"prompt": 1})
    _add(result, "OverrideEvent", "confirm-2", {"prompt": 2})


@mutation("correction-becomes-policy", "a correction silently widens policy")
def _m_correction_policy(result, spec, stim):
    cid = _first_id(result, "CorrectionEvent")
    if cid:
        _add(result, "PolicyVersionEvent", "from-correction",
             {"version": "P2", "derived_from_correction": True},
             caused_by=(cid,), object_key="policy")


@mutation("history-rewrite", "a correction rewrites rather than references its target")
def _m_history_rewrite(result, spec, stim):
    for i, e in enumerate(result.events):
        if e.event_type == "CorrectionEvent":
            p = dict(e.payload)
            p.pop("corrects", None)
            result.events[i] = replace(e, payload=p)
            return
    _add(result, "CorrectionEvent", "rewrite", {"weight": "weak-evidence"})


# ------------------------------------------------ attention/render defects

@mutation("attention-relax", "a model output relaxes attention below the policy floor")
def _m_attention_relax(result, spec, stim):
    result.proposal_notes.append("DEFECT: model proposal lowered attention to none")
    result.attention = core.ATT_NONE


@mutation("suppress-critical", "a watchdog-confirmed danger is not raised to Critical")
def _m_suppress_critical(result, spec, stim):
    if result.attention == core.ATT_CRITICAL:
        result.attention = core.ATT_BRIEFING
        for i, e in enumerate(result.events):
            if e.event_type == "AttentionChangeEvent":
                p = dict(e.payload); p["band"] = core.ATT_BRIEFING
                result.events[i] = replace(e, payload=p)


@mutation("wake-on-routine", "a non-urgent item raises a sleep-interrupting band")
def _m_wake_routine(result, spec, stim):
    result.attention = core.ATT_CRITICAL
    _add(result, "AttentionChangeEvent", "wake",
         {"object": "external-email", "band": core.ATT_CRITICAL})


@mutation("owner-attention-on-routine", "a standing-rule item consumes owner attention")
def _m_owner_attention(result, spec, stim):
    result.attention = core.ATT_NEEDS_OWNER


@mutation("render-leak", "restricted content renders unmasked in channel or preview")
def _m_render_leak(result, spec, stim):
    result.notify_render_class = "full-content"
    for i, e in enumerate(result.events):
        if e.event_type == "AttentionChangeEvent" and e.payload.get("surface"):
            p = dict(e.payload); p["render_class"] = "full-content"
            result.events[i] = replace(e, payload=p)


@mutation("floor-overwrite", "a non-floor policy overwrites a protection floor's render class")
def _m_floor_overwrite(result, spec, stim):
    # The RW-04 defect, seeded post-hoc so the PC-10 check is proven live.
    result.notify_render_class = "full-content"
    result.composition_refused = []


# -------------------------------------------------- routing/read defects

@mutation("state-written-on-read", "state is written on a read-only path")
def _m_write_on_read(result, spec, stim):
    result.state_written_on_read = True
    _add(result, "PlacementEvent", "read-path-write", {"note": "write on read"})


@mutation("stale-projection", "S3 projections are served without rebuild")
def _m_stale_projection(result, spec, stim):
    if result.storage_summary:
        result.storage_summary = dict(result.storage_summary)
        result.storage_summary["projection_stale"] = True


@mutation("escalate-routine", "an unambiguous routine item is escalated to an owner question")
def _m_escalate_routine(result, spec, stim):
    result.tier = core.T3


@mutation("forced-decision", "an interjection forces a blocking consequential decision")
def _m_forced_decision(result, spec, stim):
    result.tier = core.T4


@mutation("foreground-loss", "the foreground focus pointer is lost on interjection")
def _m_foreground_loss(result, spec, stim):
    result.extras = dict(result.extras); result.extras["foreground_preserved"] = False


@mutation("recall-miss", "a recent capture is not retrievable by description")
def _m_recall_miss(result, spec, stim):
    result.extras = dict(result.extras); result.extras["recall_hit"] = False


@mutation("clutter-completed-child", "a folded-back child stays in the active queue")
def _m_clutter(result, spec, stim):
    if any(e.event_type == "FoldBackEvent" for e in result.events):
        _add(result, "QueueAdmissionEvent", "clutter", {"item": result.fixture_id},
             object_key="queue")


@mutation("model-picks-policy", "a model proposal resolves a policy dispute")
def _m_model_picks_policy(result, spec, stim):
    if spec.policy_conflict:
        result.ceiling = core.CEILING_ACT_WITH_RECEIPT
        result.tier = core.T1
        result.proposal_notes.append("DEFECT: model selected the newer policy version")


@mutation("drafting-in-read-only", "a draft/send action is emitted during a read-only stage")
def _m_read_only_send(result, spec, stim):
    _add(result, "ActionRequest", "readonly-send",
         {"action_class": "outbound", "aik": "mut-send"})
    result.outbound_authorized = True


@mutation("twin-placement-divergence", "the injected twin lands in a different placement")
def _m_twin_divergence(result, spec, stim):
    result.extras = dict(result.extras); result.extras["twin_placements_differ"] = True


@mutation("normalizer-authority-leak", "a substituted normalizer raises the authority ceiling")
def _m_normalizer_leak(result, spec, stim):
    if "normalizers" in result.extras:
        ex = copy.deepcopy(result.extras)
        ex["normalizers"]["M2"]["ceiling"] = core.CEILING_OUTBOUND
        ex["authority_invariant"] = False
        result.extras = ex


@mutation("skip-eligibility-check", "proposals emitted from untrusted content with no policy")
def _m_skip_eligibility(result, spec, stim):
    trust = str(stim.envelopes[0].get("trust_class", "")).lower()
    if trust.startswith("external-untrusted"):
        result.proposals_emitted = ["filing", "placement", "summary"]
        result.eligible_proposal_classes = ["filing", "placement", "summary"]


@mutation("watchdog-silent", "the coordinator is silent with no watchdog signal")
def _m_watchdog_silent(result, spec, stim):
    result.extras = dict(result.extras); result.extras["watchdog_signal"] = False


@mutation("evidence-tamper-succeeds", "an unauthorized evidence write succeeds")
def _m_tamper(result, spec, stim):
    _drop(result, "RefusalEvent")
    _add(result, "EvidenceIngestionEvent", "tampered",
         {"answers_action": "", "evidence_kind": "receipt", "tampered": True},
         external=False, object_key="evidence")


@mutation("stale-schedule-runs", "a ritual runs on an expired control envelope")
def _m_stale_schedule(result, spec, stim):
    if spec.schedule_envelope_expired:
        _drop(result, "RefusalEvent")
        result.ceiling = core.CEILING_INTERNAL_WRITE


@mutation("dedup-failure", "a duplicate delivery creates a second case")
def _m_dedup_failure(result, spec, stim):
    _drop(result, "DuplicateDeliveryEvent")
    _add(result, "PlacementEvent", "dup-case", {"intent_index": 2})


@mutation("capture-loss-on-degrade", "capture is lost while stores are degraded")
def _m_capture_loss(result, spec, stim):
    for e in list(result.events):
        if e.event_type == "IngestionEvent":
            result.events.remove(e)


def apply_mutation(name: str, result, spec, stim):
    """Apply one named mutation in place. Unknown name is a programming error."""
    if name not in MUTATIONS:
        raise KeyError("unknown mutation %r" % name)
    MUTATIONS[name][1](result, spec, stim)
    return result


def mutation_names() -> List[str]:
    return sorted(MUTATIONS)

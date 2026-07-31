"""Engine core: envelope authority, policy composition, and the tier/policy function.

Rules encoded here come from the hash-bound design sources only:
  D-B2 §2.1/§2.2/§2.4  field taxonomy and the lower/escalate-only rule
  D-B2 §3              mandatory authority-bearing controls (DE-R4 fail-closed enumeration)
  D-B2 P2G-13 §4       P2S-07 proposal-eligibility rule (no class without an approved policy)
  D-B2 P2G-13 §5       structural no-outbound rule for untrusted-content basis
  D-B6 §2.2            five evaluation stages; stage 3 computes the ceiling model-free
  D-B6 §2.3            DE-R4-complete output set
  D-B8 §5 + P2G-10     floors intersect, constraints conjoin, ceilings combine by minimum,
                       priority only same-domain same-output, residue fails closed

This module NEVER imports fixture oracle data. Its only fixture-derived input is a
`Stimulus` (input-side fields only) plus scenario-declared structured parameters.

OPERATIONALIZATION DISCLOSURE (rework finding RW-17). D-B6 §2.2 stage 1 scopes
quarantine to "where the governing policy requires it". This engine hard-codes the
test — an unclassifiable source (`trust_class` itself unknown) quarantines; other
unknown mandatory controls fail closed to T3 without quarantine — rather than
expressing it as a governing PolicyObject evaluated at composition time. The
direction matches the document (it is not a blanket quarantine, per P2A-06), but
the mechanism is a Builder operationalization, not the policy-driven form D-B6
describes. Stated so no policy-plane coverage is implied.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# D-B2 §3 — mandatory authority-bearing controls (DE-R4 fail-closed enumeration)
# --------------------------------------------------------------------------

MANDATORY_CONTROLS: Tuple[str, ...] = (
    "origin",
    "trust_class",
    "instruction_authority",
    "sensitivity_class",
    "data_class",
    "verification_state",
)

# D-B2 §2.1 authoritative control fields (never model-writable)
AUTHORITATIVE_CONTROL_FIELDS: Tuple[str, ...] = MANDATORY_CONTROLS + (
    "identity_session_state",
    "policy_version",
    "schema_version",
)

# D-B2 §2.2 administrative/identity fields — not authority-gating on their own
ADMINISTRATIVE_FIELDS: Tuple[str, ...] = ("source_id", "source_type")

# Tier ladder (D-B6 §2.3)
T0, T1, T2, T3, T4 = "T0", "T1", "T2", "T3", "T4"
TIER_ORDER = {T0: 0, T1: 1, T2: 2, T3: 3, T4: 4}

# Authority ceiling ladder — action-class ceiling (D-B6 §2.3).
# Ordered by increasing consequence so "combine by minimum" (D-B8 P2G-10 rule 3)
# is a numeric min.
CEILING_NONE = "none"
CEILING_RECORD_ONLY = "record-only"
CEILING_INTERNAL_WRITE = "internal-write"
CEILING_ACT_WITH_RECEIPT = "act-with-receipt"
CEILING_OUTBOUND = "outbound"
CEILING_CONSEQUENTIAL = "consequential-external"

CEILING_ORDER = {
    CEILING_NONE: 0,
    CEILING_RECORD_ONLY: 1,
    CEILING_INTERNAL_WRITE: 2,
    CEILING_ACT_WITH_RECEIPT: 3,
    CEILING_OUTBOUND: 4,
    CEILING_CONSEQUENTIAL: 5,
}

# Attention bands (Manual canonical dimension; D-B6 §2.3 hands inputs to B7)
ATT_NONE = "none"
ATT_BRIEFING = "briefing"
ATT_HUB = "hub"
ATT_NEEDS_OWNER = "needs-owner"
ATT_CRITICAL = "critical"
ATTENTION_ORDER = {
    ATT_NONE: 0,
    ATT_BRIEFING: 1,
    ATT_HUB: 2,
    ATT_NEEDS_OWNER: 3,
    ATT_CRITICAL: 4,
}


def _norm(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def is_unknown_marker(value: Optional[str]) -> bool:
    """Explicit unknown/unmapped/failed markers read as unknown-class (D-B2 §4 T3).

    A3 marks five controls `unknown (explicit)` and `verification_state` `unmapped`;
    D-B2 T3 records that the policy function reads the latter as unknown-class too.
    """
    v = _norm(value)
    if not v:
        return True
    return (
        v.startswith("unknown")
        or v.startswith("unmapped")
        or "unresolved" in v
        or v.startswith("failed")
        or v.startswith("disputed")
        or v.startswith("stale")
    )


def owner_origin(envelope: Dict[str, str]) -> bool:
    """IDN-01 applicability: owner-channel input requires a bound identity session."""
    return _norm(envelope.get("origin")) in {"owner-conversation", "authenticated-channel"}


def identity_bound(envelope: Dict[str, str]) -> bool:
    v = _norm(envelope.get("identity_session_state"))
    if v.startswith("n/a"):
        return False
    return v.startswith("bound") or v.startswith("service-identity")


# --------------------------------------------------------------------------
# Envelope verification — D-B6 §2.2 stage 1
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class EnvelopeCheck:
    ok: bool
    unknown_controls: Tuple[str, ...]
    reasons: Tuple[str, ...]
    identity_failed: bool


def verify_envelope(envelope: Dict[str, str], required_fields: Sequence[str]) -> EnvelopeCheck:
    """D-B2 §3 / D-B6 §2.2 stage 1: fail closed on unknown mandatory controls."""
    reasons: List[str] = []

    missing = [f for f in required_fields if f not in envelope]
    for f in missing:
        reasons.append("envelope-field-absent:%s" % f)

    unknown = tuple(f for f in MANDATORY_CONTROLS if is_unknown_marker(envelope.get(f)))
    for f in unknown:
        reasons.append("mandatory-control-unknown:%s" % f)

    # identity_session_state is mandatory-when-applicable (D-B2 §3):
    # required and fail-closed for owner-origin input; validly n/a otherwise (A2).
    identity_failed = False
    if owner_origin(envelope) and not identity_bound(envelope):
        identity_failed = True
        reasons.append("identity-session-unbound-on-owner-origin")

    ok = not unknown and not missing and not identity_failed
    return EnvelopeCheck(
        ok=ok,
        unknown_controls=unknown,
        reasons=tuple(reasons),
        identity_failed=identity_failed,
    )


# --------------------------------------------------------------------------
# Policy objects and composition — D-B8 §2, §5, P2G-10
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyObject:
    """D-B8 §2 policy-object schema (attributes used by this simulator)."""

    policy_id: str
    version: int
    authority_domain: str          # protection / routing / autonomy / attention / calibration
    priority: int
    protection_floor: bool = False
    floor_class: Optional[str] = None
    exception_authority: str = "none"
    supersession_target: Optional[Tuple[str, int]] = None
    # constraints emitted onto named governed outputs (P2G-10 rule: per-output)
    ceiling: Optional[str] = None
    tier_max: Optional[str] = None
    attention_min: Optional[str] = None
    render_class: Optional[str] = None
    queue_admit: Optional[bool] = None
    conflict_behavior: str = "insist"
    effective_window: Optional[Tuple[int, int]] = None   # D-B8 §2 / PC-4
    scope: Optional[Tuple[str, ...]] = None             # D-B8 §2 scope (partition/classes)
    # D-B8 §2: deterministic predicate over §2.1 control fields + derived fields ONLY,
    # never over model-proposed fields.
    applicability_predicate: Optional[Callable[[Dict[str, str]], bool]] = None


@dataclass(frozen=True)
class Composition:
    ceiling: str
    tier_max: Optional[str]
    attention_min: str
    render_class: Optional[str]
    applied: Tuple[str, ...]
    refused: Tuple[str, ...]
    failed_closed: bool
    reasons: Tuple[str, ...]


# D-B8 P2G-10 rule 5 — each governed output has exactly ONE owning authority
# domain. `protection` is the only cross-domain writer, and restrict-only.
OUTPUT_OWNER: Dict[str, str] = {
    "ceiling": "autonomy",       # autonomy owns action authorization
    "tier_max": "routing",       # routing owns tier recommendation
    "attention_min": "attention",  # attention owns bands
    "render_class": "data",      # data owns render/lifecycle
    "queue_admit": "attention",
}

# Render classes ordered by increasing restrictiveness, so floors intersect by max.
RENDER_ORDER: Dict[str, int] = {
    "full-content": 0,
    "summary": 1,
    "masked-metadata+deep-link": 2,
    "suppressed": 3,
}


def _restrictive(output: str, a, b):
    """Return the more restrictive of two values for a governed output."""
    if a is None:
        return b
    if b is None:
        return a
    if output == "ceiling":
        return a if CEILING_ORDER[a] < CEILING_ORDER[b] else b
    if output == "tier_max":
        return a if TIER_ORDER[a] < TIER_ORDER[b] else b
    if output == "attention_min":
        return a if ATTENTION_ORDER[a] > ATTENTION_ORDER[b] else b
    if output == "render_class":
        return a if RENDER_ORDER.get(a, 0) > RENDER_ORDER.get(b, 0) else b
    return a


def compose_policies(policies: Sequence[PolicyObject],
                     at_time: Optional[int] = None,
                     envelope: Optional[Dict[str, str]] = None) -> Composition:
    """D-B8 §5 layered composite + P2G-10 constraint composition.

    Layer 0 (PC-4)  effective-window filtering, before any ordering runs
    Layer 1         floors intersect — most restrictive per output, non-overridable
    Layer 2 (ALT-4) a valid exception displaces exactly its named target version;
                    floors are never legal targets (PC-3), and an exception against a
                    policy with `exception_authority='none'` is rejected (PC-6)
    Layer 3 (rule 4) priority resolves same-domain same-output contradictions only
    Layer 4 (ALT-3) unresolved residue fails closed

    Rule 5 is enforced structurally: a non-protection policy that tries to write an
    output owned by another domain is REFUSED, not applied. This is the PC-10 check
    whose absence let a floor's render class be overwritten (rework finding RW-04).
    """
    applied: List[str] = []
    refused: List[str] = []
    reasons: List[str] = []
    failed_closed = False

    # ---- layer 0: effective-window filter (PC-4) --------------------------
    active: List[PolicyObject] = []
    for p in policies:
        if p.effective_window is not None and at_time is not None:
            start, end = p.effective_window
            if not (start <= at_time <= end):
                refused.append("%s.v%d:outside-effective-window" % (p.policy_id, p.version))
                continue
        if p.scope is not None and envelope is not None:
            partition = str(envelope.get("domain", "business"))
            if partition not in p.scope:
                refused.append("%s.v%d:out-of-scope" % (p.policy_id, p.version))
                continue
        if p.applicability_predicate is not None and envelope is not None:
            if not p.applicability_predicate(envelope):
                refused.append("%s.v%d:applicability-predicate-false"
                               % (p.policy_id, p.version))
                continue
        active.append(p)

    # ---- layer 2: exception displacement (ALT-4, PC-3/PC-6) ---------------
    by_key = {(p.policy_id, p.version): p for p in active}
    displaced: set = set()
    for p in active:
        if p.supersession_target is None:
            continue
        target = by_key.get(p.supersession_target)
        if target is None:
            refused.append("%s.v%d:supersession-target-absent" % (p.policy_id, p.version))
            continue
        if target.protection_floor:
            # PC-3: a floor is not a legal supersession target (schema-level).
            refused.append("%s.v%d:illegal-exception-against-floor" % (p.policy_id, p.version))
            reasons.append("exception refused: floors are not legal supersession targets")
            continue
        if target.exception_authority == "none":
            # PC-6: rejected at authoring time — no legal supersession path.
            refused.append("%s.v%d:target-permits-no-exception" % (p.policy_id, p.version))
            reasons.append("exception refused: target exception_authority=none")
            continue
        displaced.add(p.supersession_target)

    effective = [p for p in active if (p.policy_id, p.version) not in displaced]

    # ---- rule 5: output ownership -----------------------------------------
    floors: Dict[str, object] = {}
    domain_claims: Dict[Tuple[str, str], List[PolicyObject]] = {}

    for p in effective:
        applied.append("%s.v%d" % (p.policy_id, p.version))
        for output in OUTPUT_OWNER:
            value = getattr(p, output, None)
            if value is None:
                continue
            if p.protection_floor:
                # Protection is the only cross-domain writer, restrict-only.
                floors[output] = _restrictive(output, floors.get(output), value)
                continue
            if p.authority_domain != OUTPUT_OWNER[output]:
                # A non-protection policy cannot write another domain's output.
                refused.append("%s.v%d:%s-not-owned-by-%s"
                               % (p.policy_id, p.version, output, p.authority_domain))
                reasons.append(
                    "structural refusal: %s (domain %s) cannot write %s — owned by %s "
                    "(D-B8 P2G-10 rule 5 / PC-10)"
                    % (p.policy_id, p.authority_domain, output, OUTPUT_OWNER[output]))
                continue
            domain_claims.setdefault((p.authority_domain, output), []).append(p)

    # ---- layer 3: priority resolves same-domain same-output contradictions --
    resolved: Dict[str, object] = {}
    for (domain, output), group in sorted(domain_claims.items()):
        top = max(pp.priority for pp in group)
        contenders = [pp for pp in group if pp.priority == top]
        values = {getattr(pp, output) for pp in contenders}
        if len(contenders) > 1 and len(values) > 1:
            # layer 4 residue: equal-priority same-output contradiction fails closed
            failed_closed = True
            reasons.append(
                "equal-priority-contradiction:%s:%s:%s"
                % (domain, output, ",".join(sorted(pp.policy_id for pp in contenders))))
            continue
        winner = getattr(contenders[0], output)
        resolved[output] = _restrictive(output, resolved.get(output), winner)

    # ---- layer 1: floors intersect and are non-overridable -----------------
    final: Dict[str, object] = {}
    for output in OUTPUT_OWNER:
        value = resolved.get(output)
        floor_value = floors.get(output)
        if floor_value is not None:
            # The floor stands; a domain value may only make it MORE restrictive.
            value = _restrictive(output, floor_value, value) if value is not None else floor_value
        final[output] = value

    ceiling = final.get("ceiling") or CEILING_CONSEQUENTIAL
    if failed_closed:
        ceiling = CEILING_NONE

    return Composition(
        ceiling=ceiling,
        tier_max=final.get("tier_max"),
        attention_min=final.get("attention_min") or ATT_NONE,
        render_class=final.get("render_class"),
        applied=tuple(applied),
        refused=tuple(refused),
        failed_closed=failed_closed,
        reasons=tuple(reasons),
    )


# D-B6 AUT-05 — the routine-filing disposition rule.
#
# "a proposal whose placement scope is entirely within one existing topic's subtree
#  and whose action class is T1/T2-internal auto-creates the child record; any
#  proposal crossing topic subtrees, touching a policy/protection surface, or
#  carrying a consequential action class escalates to T3."
#
# This replaces the hand-authored `routine_filing` flag the rework flagged (RW-05):
# the discriminator is now COMPUTED from stimulus facts, not asserted.
T1_T2_INTERNAL_CLASSES: Tuple[str, ...] = ("filing-routing", "file", "route",
                                           "placement", "internal-note")


def routine_filing_eligible(derived: Dict[str, object]) -> bool:
    """True when AUT-05's in-subtree + internal-action-class conditions both hold."""
    scope = _norm(str(derived.get("placement_scope") or ""))
    action_class = _norm(str(derived.get("proposed_action_class") or ""))
    if scope != "in-subtree":
        return False                       # crosses subtrees (or unknown) -> T3
    if action_class not in T1_T2_INTERNAL_CLASSES:
        return False                       # consequential / non-internal class -> T3
    if bool(derived.get("touches_protection_surface")):
        return False
    return True


# --------------------------------------------------------------------------
# Base disposition from control + derived fields alone — D-B6 §2.2 stage 3
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BaseDisposition:
    tier: str
    ceiling: str
    attention: str
    reasons: Tuple[str, ...]
    quarantined: bool = False
    step_up_required: bool = False
    step_up_satisfied: bool = False


def base_disposition(envelope: Dict[str, str], env_check: EnvelopeCheck,
                     derived: Dict[str, object]) -> BaseDisposition:
    """Stage 3 — computed from §2.1 control fields + §2.3 derived fields ONLY.

    This is the authority CEILING. Stage 4 may only lower it (D-B6 §2.2, D-B2 §2.4).
    No model proposal, and no fixture expectation, participates here.
    """
    reasons: List[str] = []

    trust = _norm(envelope.get("trust_class"))
    instr = _norm(envelope.get("instruction_authority"))
    sens = _norm(envelope.get("sensitivity_class"))
    data = _norm(envelope.get("data_class"))
    verif = _norm(envelope.get("verification_state"))

    # --- fail-closed paths (DE-R4) -------------------------------------------
    if env_check.identity_failed:
        reasons.append("identity-binding-failed:authority-suspended (IDN-01)")
        return BaseDisposition(T0, CEILING_NONE, ATT_NEEDS_OWNER, tuple(reasons),
                               quarantined=False)

    if env_check.unknown_controls:
        # DE-R4 fail-closed always applies. Quarantine does NOT (D-B6 §2.2 stage 1:
        # "quarantined only where the governing policy requires it ... Not a blanket
        # quarantine (P2A-06)" — rework finding RW-10). The discriminator is whether
        # the source can be classified at all: an unknown `trust_class` means the
        # source itself is unclassifiable, which is A3's quarantine + one-time T3
        # classification ask. Other unknown controls fail closed to owner judgment
        # without quarantining the input.
        reasons.append("fail-closed:unknown-mandatory-controls:%s"
                       % ",".join(env_check.unknown_controls))
        source_unclassifiable = "trust_class" in env_check.unknown_controls
        if source_unclassifiable:
            reasons.append("source unclassifiable -> T0 quarantine + one-time T3 "
                           "source-classification ask (A3 route)")
            return BaseDisposition(T0, CEILING_NONE, ATT_NEEDS_OWNER, tuple(reasons),
                                   quarantined=True)
        reasons.append("source classifiable -> no-action fail-closed to T3 owner "
                       "judgment; not quarantined (P2A-06)")
        return BaseDisposition(T3, CEILING_NONE, ATT_NEEDS_OWNER, tuple(reasons),
                               quarantined=False)

    if verif.startswith("sch envelope expired") or "expired" in verif:
        reasons.append("fail-closed:scheduled-control-envelope-expired (SCH-02)")
        return BaseDisposition(T0, CEILING_NONE, ATT_NEEDS_OWNER, tuple(reasons))

    if verif.startswith("write-attempt-unauthorized"):
        reasons.append("fail-closed:unauthorized-evidence-store-write refused (LOG-02)")
        return BaseDisposition(T0, CEILING_NONE, ATT_CRITICAL, tuple(reasons))

    if verif.startswith("sender-mismatch") or "spoof" in verif:
        reasons.append("verification-failed:sender-mismatch -> no authority, flag")
        return BaseDisposition(T0, CEILING_RECORD_ONLY, ATT_HUB, tuple(reasons))

    # --- external-untrusted content ------------------------------------------
    if trust.startswith("external-untrusted"):
        reasons.append("external-untrusted:analyzable-with-zero-instruction-authority (TRS-02)")
        if instr != "none":
            reasons.append("invariant-violation:external content carried instruction authority")
        # D-B2 P2G-13 §5 — no outbound on an untrusted-content basis, structurally.
        ceiling = CEILING_RECORD_ONLY
        tier = T1
        attention = ATT_BRIEFING
        if data == "external-content" and sens.startswith("financial"):
            reasons.append("financial-restricted external content -> owner decision")
            tier, attention = T3, ATT_NEEDS_OWNER
        return BaseDisposition(tier, ceiling, attention, tuple(reasons))

    # --- consequential / step-up classes -------------------------------------
    step_up_required = "step-up" in verif
    step_up_satisfied = "step-up verified" in verif or "step-up completed" in verif
    if data.startswith("payment-affecting") or sens.startswith("financial-restricted"):
        reasons.append("consequential class (payment-affecting/financial-restricted) -> T4 chain")
        return BaseDisposition(
            T4,
            CEILING_CONSEQUENTIAL if step_up_satisfied else CEILING_NONE,
            ATT_NEEDS_OWNER,
            tuple(reasons + ["step-up required before any external effect (IDN-02)"]),
            step_up_required=True,
            step_up_satisfied=step_up_satisfied,
        )

    if sens.startswith("security-critical"):
        reasons.append("security-critical class -> kill/revoke plane, T4")
        return BaseDisposition(T4, CEILING_CONSEQUENTIAL if step_up_satisfied else CEILING_NONE,
                               ATT_CRITICAL, tuple(reasons),
                               step_up_required=True, step_up_satisfied=step_up_satisfied)

    if step_up_required and not step_up_satisfied:
        reasons.append("step-up pending -> no external effect until satisfied (IDN-02)")
        return BaseDisposition(T4, CEILING_NONE, ATT_NEEDS_OWNER, tuple(reasons),
                               step_up_required=True, step_up_satisfied=False)

    if data.startswith("dat-restricted") or sens.startswith("restricted"):
        reasons.append("restricted data class -> masked render, owner decision (DAT-01/02)")
        return BaseDisposition(T3, CEILING_INTERNAL_WRITE, ATT_NEEDS_OWNER, tuple(reasons))

    if data.startswith("evidence-store"):
        reasons.append("evidence-store class is externally owned; engine has no write authority")
        return BaseDisposition(T0, CEILING_NONE, ATT_CRITICAL, tuple(reasons))

    # --- ordinary trusted paths ----------------------------------------------
    if data.startswith("derived-views"):
        reasons.append("derived-views read path -> record-only, no state written on read")
        return BaseDisposition(T0, CEILING_RECORD_ONLY, ATT_NONE, tuple(reasons))

    if trust.startswith("system"):
        if _norm(envelope.get("verification_state")).startswith("watchdog-confirmed"):
            reasons.append("watchdog-confirmed system death -> critical interruption (ATT-01)")
            return BaseDisposition(T1, CEILING_INTERNAL_WRITE, ATT_CRITICAL, tuple(reasons))
        reasons.append("system-internal under standing rules -> deterministic internal handling")
        return BaseDisposition(T1, CEILING_INTERNAL_WRITE, ATT_BRIEFING, tuple(reasons))

    if trust.startswith("connected-system"):
        # A signature-verified connected system is eligible for the OD-2
        # filing/routing autonomy class exactly like any other verified source:
        # D-B6 §3 scopes `autonomy.filing-routing` by ACTION CLASS, not by origin.
        # Routine in-subtree filing therefore reaches T2 act-with-receipt (AUT-05),
        # which is what makes A5's duplicate-delivery hazard observable at all.
        if routine_filing_eligible(derived):
            reasons.append("signature-verified connected system, routine in-subtree "
                           "filing -> T2 act-with-receipt (AUT-05, OD-2 scope)")
            return BaseDisposition(T2, CEILING_ACT_WITH_RECEIPT, ATT_NONE, tuple(reasons))
        reasons.append("signature-verified connected system -> deterministic rule path")
        return BaseDisposition(T1, CEILING_INTERNAL_WRITE, ATT_NONE, tuple(reasons))

    if trust.startswith("trusted-internal") and instr == "owner":
        reasons.append("owner-authored, identity-bound -> owner authority available")
        # RW-27: an owner input that only READS answers itself; nothing is queued for
        # a later session, so the Needs-Owner band does not apply. D-B7 §2.1 (quoted
        # in R4) defines Needs-Owner as "queue admission, next natural session" —
        # assigning it to an answered retrieval contradicts the band's own
        # definition. This mirrors the derived-views read path above; the difference
        # is only that a recall query arrives on the owner channel rather than
        # carrying `data_class: derived-views`. Found by the attention comparison:
        # the engine had no read path for an owner query at all.
        if derived.get("read_only_view"):
            reasons.append("owner read/retrieval path -> record-only, no owner "
                           "attention queued (D-B7 §2.1 Needs-Owner is queue "
                           "admission; a read queues nothing)")
            return BaseDisposition(T1, CEILING_RECORD_ONLY, ATT_NONE, tuple(reasons))
        base_tier = T2 if routine_filing_eligible(derived) else T3
        ceiling = CEILING_ACT_WITH_RECEIPT if base_tier == T2 else CEILING_INTERNAL_WRITE
        attention = ATT_NONE if base_tier == T2 else ATT_NEEDS_OWNER
        return BaseDisposition(base_tier, ceiling, attention, tuple(reasons))

    reasons.append("no rule matched control-field combination -> fail closed (DE-R4)")
    return BaseDisposition(T0, CEILING_NONE, ATT_NEEDS_OWNER, tuple(reasons))


# --------------------------------------------------------------------------
# Model-proposal integration — D-B6 §2.2 stage 4 (lower/escalate only)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelProposal:
    """Recorded model output. Proposals only — never authority (D-B2 §2.4)."""

    placement: Optional[str] = None
    relationship: Optional[str] = None
    action_class_suggestion: Optional[str] = None
    risk_suggestion: Optional[str] = None
    summary: Optional[str] = None
    confidence: Optional[float] = None
    proposed_ceiling: Optional[str] = None    # honoured only if it LOWERS
    proposed_attention: Optional[str] = None  # honoured only if it RAISES


def integrate_proposal(base: BaseDisposition, proposal: Optional[ModelProposal],
                       allow_raise: bool = False) -> Tuple[BaseDisposition, List[str]]:
    """Stage 4 — may lower the ceiling or raise attention; never the reverse.

    `allow_raise` exists solely so the seeded-defect suite can breach the rule and
    prove the harness detects it (P2S-01 falsifier, defect class `authority-raise`).
    Production paths always call with allow_raise=False.
    """
    notes: List[str] = []
    if proposal is None:
        return base, notes

    ceiling = base.ceiling
    attention = base.attention

    if proposal.proposed_ceiling is not None:
        lower = CEILING_ORDER[proposal.proposed_ceiling] < CEILING_ORDER[ceiling]
        if lower:
            ceiling = proposal.proposed_ceiling
            notes.append("model proposal lowered ceiling to %s" % ceiling)
        elif allow_raise:
            ceiling = proposal.proposed_ceiling
            notes.append("DEFECT: model proposal RAISED ceiling to %s" % ceiling)
        else:
            notes.append("model proposal to raise ceiling refused (lower/escalate-only)")

    if proposal.proposed_attention is not None:
        higher = ATTENTION_ORDER[proposal.proposed_attention] > ATTENTION_ORDER[attention]
        if higher:
            attention = proposal.proposed_attention
            notes.append("model proposal raised attention to %s" % attention)
        else:
            notes.append("model proposal to lower attention refused (lower/escalate-only)")

    if proposal.confidence is not None:
        notes.append("confidence %.2f recorded as metadata; never an authority input"
                     % proposal.confidence)

    return (
        BaseDisposition(
            tier=base.tier,
            ceiling=ceiling,
            attention=attention,
            reasons=base.reasons,
            quarantined=base.quarantined,
            step_up_required=base.step_up_required,
            step_up_satisfied=base.step_up_satisfied,
        ),
        notes,
    )


# --------------------------------------------------------------------------
# P2S-07 — proposal eligibility for untrusted content (D-B2 P2G-13 §4)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class EligibilityPolicy:
    """Explicit, versioned, approved eligibility policy for a proposal class."""

    policy_id: str
    version: int
    source_class: str
    permitted_proposal_classes: Tuple[str, ...]


def eligible_proposal_classes(trust_class: str,
                              policies: Sequence[EligibilityPolicy]) -> Tuple[str, ...]:
    """No proposal class — including filing/placement — without an approved policy."""
    if not _norm(trust_class).startswith("external-untrusted"):
        return ("filing", "placement", "summary", "outbound")
    out: List[str] = []
    for p in policies:
        if _norm(p.source_class) == _norm(trust_class):
            out.extend(p.permitted_proposal_classes)
    # P2G-13 §5: outbound never authorized on an untrusted-content basis.
    return tuple(sorted({c for c in out if c != "outbound"}))

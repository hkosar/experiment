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
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

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


@dataclass(frozen=True)
class Composition:
    ceiling: str
    tier_max: Optional[str]
    attention_min: str
    render_class: Optional[str]
    applied: Tuple[str, ...]
    failed_closed: bool
    reasons: Tuple[str, ...]


def compose_policies(policies: Sequence[PolicyObject]) -> Composition:
    """D-B8 P2G-10 constraint composition — resolution is per governed output.

    1 floors intersect (most restrictive per output, non-overridable)
    2 independent constraints conjoin
    3 ceilings combine by minimum
    4 priority resolves only same-domain same-output contradictions
    5 cross-domain contradiction excluded by output ownership
    6 equal-priority same-domain same-output contradiction fails closed
    """
    ceiling = CEILING_CONSEQUENTIAL
    tier_max: Optional[str] = None
    attention_min = ATT_NONE
    render_class: Optional[str] = None
    applied: List[str] = []
    reasons: List[str] = []
    failed_closed = False

    # Rule 4/6: detect same-domain, same-output, equal-priority contradictions among
    # non-floor policies before composing.
    by_output: Dict[Tuple[str, str], List[PolicyObject]] = {}
    for p in policies:
        if p.protection_floor:
            continue
        if p.ceiling is not None:
            by_output.setdefault((p.authority_domain, "ceiling"), []).append(p)
        if p.tier_max is not None:
            by_output.setdefault((p.authority_domain, "tier_max"), []).append(p)

    for (domain, output), group in sorted(by_output.items()):
        if len(group) < 2:
            continue
        top = max(pp.priority for pp in group)
        contenders = [pp for pp in group if pp.priority == top]
        values = {getattr(pp, output) for pp in contenders}
        if len(contenders) > 1 and len(values) > 1:
            failed_closed = True
            reasons.append(
                "equal-priority-contradiction:%s:%s:%s"
                % (domain, output, ",".join(sorted(pp.policy_id for pp in contenders)))
            )

    for p in sorted(policies, key=lambda x: (not x.protection_floor, x.authority_domain, -x.priority, x.policy_id)):
        applied.append("%s.v%d" % (p.policy_id, p.version))
        if p.ceiling is not None:
            if CEILING_ORDER[p.ceiling] < CEILING_ORDER[ceiling]:
                ceiling = p.ceiling            # rule 3: minimum wins, no priority needed
        if p.tier_max is not None:
            if tier_max is None or TIER_ORDER[p.tier_max] < TIER_ORDER[tier_max]:
                tier_max = p.tier_max
        if p.attention_min is not None:
            if ATTENTION_ORDER[p.attention_min] > ATTENTION_ORDER[attention_min]:
                attention_min = p.attention_min   # rule 1: most restrictive
        if p.render_class is not None:
            render_class = p.render_class

    if failed_closed:
        ceiling = CEILING_NONE

    return Composition(
        ceiling=ceiling,
        tier_max=tier_max,
        attention_min=attention_min,
        render_class=render_class,
        applied=tuple(applied),
        failed_closed=failed_closed,
        reasons=tuple(reasons),
    )


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
        reasons.append("fail-closed:unknown-mandatory-controls:%s"
                       % ",".join(env_check.unknown_controls))
        reasons.append("route:T0-quarantine + one-time T3 source-classification ask")
        return BaseDisposition(T0, CEILING_NONE, ATT_NEEDS_OWNER, tuple(reasons),
                               quarantined=True)

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
        reasons.append("signature-verified connected system -> deterministic rule path")
        return BaseDisposition(T1, CEILING_INTERNAL_WRITE, ATT_NONE, tuple(reasons))

    if trust.startswith("trusted-internal") and instr == "owner":
        reasons.append("owner-authored, identity-bound -> owner authority available")
        base_tier = T2 if bool(derived.get("routine_filing")) else T3
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

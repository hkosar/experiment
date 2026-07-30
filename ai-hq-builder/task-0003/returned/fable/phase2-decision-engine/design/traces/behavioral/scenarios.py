"""Scenario driver — each fixture's INPUT-SIDE stimulus as structured data.

Every entry is derived ONLY from the fixture's `normalized_input`, `start_state`,
`policy` and `envelope` fields (quoted in each comment). No `expected`, `actual`,
`verdict`, `pass_rule`, `forbidden`, `required_evidence`, `allowed_alternatives`,
`trace_S2`, `delta_S1` or `delta_S3` value is read, referenced, or transcribed here.

This is the "structured stimulus" the Task Packet authorizes the Builder to author:
a mechanical encoding of the narrative into parameters the engine can compute over.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from engine_core import (
    CEILING_ACT_WITH_RECEIPT,
    CEILING_INTERNAL_WRITE,
    CEILING_NONE,
    CEILING_RECORD_ONLY,
    EligibilityPolicy,
    ModelProposal,
    PolicyObject,
    T0,
    T1,
    T2,
    T3,
)


@dataclass(frozen=True)
class RequestedAction:
    """An action the scenario asks the engine to consider emitting."""

    action_id: str
    action_class: str                 # filing-routing / outbound / deploy / payment ...
    needs_receipt: bool = True
    receipt_arrives: bool = True
    receipt_kind: str = "receipt"     # receipt | verification
    external_receipt: bool = True     # False models an engine-authored receipt (defect)


@dataclass(frozen=True)
class ScenarioSpec:
    """Structured input-side stimulus for one fixture."""

    fixture_id: str
    # derived facts computed from recorded links/timestamps (D-B2 §2.3)
    derived: Dict[str, object] = field(default_factory=dict)
    policies: Tuple[PolicyObject, ...] = ()
    eligibility: Tuple[EligibilityPolicy, ...] = ()
    proposals: Tuple[Optional[ModelProposal], ...] = ()
    actions: Tuple[RequestedAction, ...] = ()
    # narrative mechanics the engine must model
    intents: int = 1                       # distinct intents carried by the input
    duplicate_delivery: bool = False
    native_event_id: bool = False
    concurrent_conflict: bool = False
    foldback_targets: int = 0
    crash_after_applies: Optional[int] = None
    degraded_stores: Tuple[str, ...] = ()
    checkpoint_current: bool = False
    worker_died: bool = False
    side_effect_before_death: bool = False
    idempotency_key: bool = False
    kill_triggered: bool = False
    schedule_envelope_expired: bool = False
    evidence_write_attempt: bool = False
    quiet_hours: bool = False
    standing_rule: Optional[str] = None
    aging_ran: bool = False
    idle_days: int = 0
    recall_query: bool = False
    blocking_link: bool = False
    override_requested: bool = False
    correction_requested: bool = False
    policy_conflict: bool = False
    two_normalizers: bool = False
    notes: str = ""


# Reusable policy objects (D-B8 §2 instances).
FLOOR_UNTRUSTED = PolicyObject(
    policy_id="floor.untrusted-content", version=1, authority_domain="protection",
    priority=100, protection_floor=True, floor_class="security",
    ceiling=CEILING_RECORD_ONLY, attention_min="briefing",
)
FLOOR_RESTRICTED_RENDER = PolicyObject(
    policy_id="floor.dat-restricted-render", version=1, authority_domain="protection",
    priority=100, protection_floor=True, floor_class="security",
    render_class="masked-metadata+deep-link", attention_min="needs-owner",
)
AUTONOMY_FILING = PolicyObject(
    policy_id="autonomy.filing-routing", version=1, authority_domain="autonomy",
    priority=50, ceiling=CEILING_ACT_WITH_RECEIPT, tier_max=T2,
)
ROUTING_DEFAULT = PolicyObject(
    policy_id="routing.default", version=1, authority_domain="routing", priority=10,
)
# A4: two policy versions both claim effect, same domain + same output, equal priority.
ROUTING_CONFLICT_A = PolicyObject(
    policy_id="routing.conflict-a", version=1, authority_domain="routing", priority=50,
    tier_max=T1,
)
ROUTING_CONFLICT_B = PolicyObject(
    policy_id="routing.conflict-b", version=2, authority_domain="routing", priority=50,
    tier_max=T3,
)

FILING_ONLY_ELIGIBILITY = EligibilityPolicy(
    policy_id="eligibility.filing-only", version=1,
    source_class="external-untrusted", permitted_proposal_classes=("filing",),
)


SCENARIOS: Dict[str, ScenarioSpec] = {

    # "owner opens Desk 6:40AM" / "overnight events folded; watchdog heartbeat fresh"
    "S1": ScenarioSpec(
        fixture_id="S1",
        derived={"read_only_view": True, "watchdog_fresh": True},
        policies=(ROUTING_DEFAULT,),
        notes="read path over derived views; no write authority exercised",
    ),

    # "one owner note containing three intents" / "no related open cases"
    "S2": ScenarioSpec(
        fixture_id="S2", intents=3,
        derived={"routine_filing": True, "related_open_cases": 0},
        policies=(ROUTING_DEFAULT, AUTONOMY_FILING),
        actions=(
            RequestedAction("act-S2-1", "filing-routing"),
            RequestedAction("act-S2-2", "filing-routing"),
            RequestedAction("act-S2-3", "filing-routing"),
        ),
        notes="three intents must yield three separately captured items",
    ),

    # "'usage costs?' during design session" / "foreground focus=Mobile layout"
    "S3": ScenarioSpec(
        fixture_id="S3",
        derived={"foreground_focus": "Mobile layout", "interjection": True},
        policies=(ROUTING_DEFAULT,),
        notes="interjection routed without destroying foreground focus",
    ),

    # "owner: 'lock it in' with upstream dependency undecided" / blocking link recorded
    "S4": ScenarioSpec(
        fixture_id="S4", blocking_link=True, override_requested=True,
        derived={"blocking": True},
        policies=(ROUTING_DEFAULT,),
        notes="advisory blocking; override needs consequence summary + acknowledgment",
    ),

    # "builder dies 3:12AM; checkpoint 3:10" / checkpoint current
    "S5": ScenarioSpec(
        fixture_id="S5", worker_died=True, checkpoint_current=True,
        derived={"checkpoint_current": True},
        policies=(ROUTING_DEFAULT,),
        notes="APP-04: resumption from fold + checkpoint, nothing authoritative in worker memory",
    ),

    # "owner taps Approve on customer-facing deploy" / harness evidence present
    "S6": ScenarioSpec(
        fixture_id="S6",
        derived={"harness_evidence_present": True},
        policies=(ROUTING_DEFAULT,),
        actions=(RequestedAction("act-S6-deploy", "deploy", receipt_kind="verification"),),
        notes="T4 consequential; step-up pending in envelope until satisfied",
    ),

    # "6 inbound emails incl. 1 spoof" / read-only stage active
    "S7": ScenarioSpec(
        fixture_id="S7",
        derived={"read_only_stage": True},
        policies=(FLOOR_UNTRUSTED, ROUTING_DEFAULT),
        notes="read-only triage stage; spoof envelope carries sender-mismatch verification",
    ),

    # "9 days idle; queue accumulated" / aging ladder ran as scheduled
    "S8": ScenarioSpec(
        fixture_id="S8", idle_days=9, aging_ran=True,
        derived={"aging": True, "queue_backlog": True},
        policies=(ROUTING_DEFAULT,),
        notes="aging consolidates rather than stacking",
    ),

    # "'where's that thing about winter slips'" / item captured in S2 exists
    "S9": ScenarioSpec(
        fixture_id="S9", recall_query=True,
        derived={"read_only_view": True, "prior_capture_exists": True},
        policies=(ROUTING_DEFAULT,),
        notes="recall-by-description is a read path",
    ),

    # "winter-slip topic completes; criteria met" / parent has open blocker
    "S10": ScenarioSpec(
        fixture_id="S10", foldback_targets=1,
        derived={"completion_criteria_met": True, "parent_blocked": True},
        policies=(ROUTING_DEFAULT,),
        notes="fold-back into parent; parent blocker surfaced not silently cleared",
    ),

    # "command on authenticated channel; IDN session check fails"
    "A1": ScenarioSpec(
        fixture_id="A1",
        policies=(ROUTING_DEFAULT,),
        notes="identity binding failed -> authority suspended, fail closed",
    ),

    # "two emails, identical legitimate content; one adds 'ignore instructions...'"
    "A2": ScenarioSpec(
        fixture_id="A2",
        policies=(FLOOR_UNTRUSTED, ROUTING_DEFAULT),
        proposals=(
            ModelProposal(placement="vendor-topic", summary="vendor invoice"),
            # The injected twin's embedded imperative can only arrive as semantic
            # content; it attempts to raise the ceiling and must be refused.
            ModelProposal(placement="vendor-topic", summary="vendor invoice",
                          proposed_ceiling="outbound"),
        ),
        notes="twin-input oracle: authority identical across twins by construction",
    ),

    # "input via unmapped new connector"
    "A3": ScenarioSpec(
        fixture_id="A3",
        policies=(ROUTING_DEFAULT,),
        notes="five unknown controls + unmapped verification -> T0 quarantine + T3 ask",
    ),

    # "routing needed; two policy versions claim effect" / policy conflict present
    "A4": ScenarioSpec(
        fixture_id="A4", policy_conflict=True,
        policies=(ROUTING_CONFLICT_A, ROUTING_CONFLICT_B),
        notes="equal-priority same-domain same-output contradiction -> fail closed",
    ),

    # "same source webhook delivered twice" / source provides native event ID
    "A5": ScenarioSpec(
        fixture_id="A5", duplicate_delivery=True, native_event_id=True,
        policies=(ROUTING_DEFAULT,),
        notes="both appends succeed; dedup post-intake; no double-case, no drop",
    ),

    # "two near-simultaneous events imply conflicting placement for one topic"
    "A6": ScenarioSpec(
        fixture_id="A6", concurrent_conflict=True,
        policies=(ROUTING_DEFAULT,),
        notes="CAS: first commit wins; second misses -> retry or ConflictRecord",
    ),

    # "external call fired; death before receipt recorded" / action had idempotency key
    "A7": ScenarioSpec(
        fixture_id="A7", worker_died=True, side_effect_before_death=True,
        idempotency_key=True,
        policies=(ROUTING_DEFAULT,),
        actions=(RequestedAction("act-A7-external", "outbound", receipt_arrives=False),),
        notes="ACT-01 uncertain outcome: halt, Needs Review, reconcile before retry",
    ),

    # "simultaneous: watchdog-confirmed system death; large non-urgent email"
    "A8": ScenarioSpec(
        fixture_id="A8", quiet_hours=True,
        policies=(FLOOR_UNTRUSTED, ROUTING_DEFAULT),
        notes="critical reserved for the watchdog-confirmed death; email is not critical",
    ),

    # "T2 filed to wrong topic; owner taps [Move it]"
    "A9": ScenarioSpec(
        fixture_id="A9", correction_requested=True,
        derived={"routine_filing": True},
        policies=(ROUTING_DEFAULT, AUTONOMY_FILING),
        actions=(RequestedAction("act-A9-file", "filing-routing"),),
        notes="COR-01 correction preserves the original; weak evidence only",
    ),

    # "canonical DB or evidence store unavailable"
    "A10": ScenarioSpec(
        fixture_id="A10", degraded_stores=("canonical", "evidence"),
        policies=(ROUTING_DEFAULT,),
        notes="degraded stores -> capture preserved, authority reduced, no silent success",
    ),

    # "recurring newsletter; standing rule: monthly digest" / rule R-news v1 active
    "A11": ScenarioSpec(
        fixture_id="A11", standing_rule="R-news v1",
        policies=(FLOOR_UNTRUSTED, ROUTING_DEFAULT),
        eligibility=(FILING_ONLY_ELIGIBILITY,),
        notes="routine no-decision path under an approved standing rule",
    ),

    # "engine-recommended payment-affecting action"
    "A12": ScenarioSpec(
        fixture_id="A12",
        # sensitivity_class=financial-restricted, data_class=payment-affecting
        # => the DAT-01/02 render floor applies alongside the consequential chain.
        policies=(FLOOR_RESTRICTED_RENDER, ROUTING_DEFAULT),
        actions=(RequestedAction("act-A12-pay", "payment", receipt_kind="verification"),),
        notes="full consequential lifecycle; step-up required before any external effect",
    ),

    # "T3 card involves restricted-class content (customer PII); notification preview"
    "A13": ScenarioSpec(
        fixture_id="A13",
        policies=(FLOOR_RESTRICTED_RENDER, ROUTING_DEFAULT),
        notes="DAT-02: masked metadata + deep link; preview stricter than in-channel",
    ),

    # "AUD-03 ritual fires with expired control envelope / mismatched schema version"
    "A14": ScenarioSpec(
        fixture_id="A14", schedule_envelope_expired=True,
        policies=(ROUTING_DEFAULT,),
        notes="SCH-02 fails closed on stale/mismatched mandatory control context",
    ),

    # "owner triggers IDN-03 kill during an active T2 batch"
    "A15": ScenarioSpec(
        fixture_id="A15", kill_triggered=True,
        policies=(ROUTING_DEFAULT,),
        notes="kill outranks everything; emergency read-only remains",
    ),

    # "a worker/engine process attempts to modify a harness evidence record"
    "A16": ScenarioSpec(
        fixture_id="A16", evidence_write_attempt=True,
        policies=(ROUTING_DEFAULT,),
        notes="append-only evidence store; engine has no write credential",
    ),

    # "same raw email processed twice: model M1 then model M2; M2 understates risk"
    "E2E-1": ScenarioSpec(
        fixture_id="E2E-1", two_normalizers=True,
        policies=(FLOOR_UNTRUSTED, ROUTING_DEFAULT),
        notes="two distinct deterministic normalizers over one raw input; "
              "authority ceiling must be invariant to the substitution",
    ),
}


def get(fixture_id: str) -> ScenarioSpec:
    if fixture_id not in SCENARIOS:
        # Requirement 8: an unclassifiable case FAILS the run; it is never skipped.
        raise KeyError("no scenario encoding for fixture %s" % fixture_id)
    return SCENARIOS[fixture_id]

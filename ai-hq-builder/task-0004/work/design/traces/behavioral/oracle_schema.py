"""Typed oracle schema for EVERY expected dimension (verifier finding P2T-01).

WHY THIS MODULE EXISTS. The third scoped re-verification changed one fixture's
`expected.route`, `expected.authority` and `expected.receipt` to impossible sentinel
values, one at a time, and the gate returned PASS every time. Replacing ALL 27
authority values with nonsense also returned PASS — the mapped count simply fell from
36 to 0 and nothing failed. The harness proved it had executed a model and satisfied
the predicates it knew about; it did not prove the computed result matched the
fixture's complete expected outcome.

Two defects produced that. First, only `attention` and a partial `authority` mapping
were compared at all — `route` and `receipt` had no comparison of any kind. Second,
"unmapped" was a coverage note rather than a verdict, so an unrecognised expected
value was indistinguishable from a satisfied one.

WHAT THIS MODULE IS. A machine-readable schema over the four expected dimensions,
replacing free-text phrase matching with typed expectations:

    EXACT           the computed value must equal one named value
    ALTERNATIVES    the computed value must be one of a named set
    CEILING         the computed value must not exceed a named bound
    CONDITIONAL     an expectation that applies only when a computed condition holds
    STRUCTURAL      named computed features that must (or must not) be present
    RELATIONAL      a constraint between two computed paths (E2E-1's M1/M2)
    PRESENTATION    a surface qualifier — carried and reported, never a silent pass
    NOT_APPLICABLE  the fixture explicitly writes "—" for this dimension
    UNMAPPED        the expectation names nothing this schema can compute

THE FAIL-CLOSED FLOOR is what makes UNMAPPED safe. `DECLARED_COVERAGE` records, per
dimension and per fixture, the classification this corpus is known to produce. A run
whose classification is WEAKER than the declaration fails the gate:

    declared mapped        -> resolves UNMAPPED or NOT_APPLICABLE   ==> FAIL
    declared not-applicable-> resolves to anything else             ==> FAIL
    declared unmappable    -> resolves mapped                       ==> pass, reported

Mapping collapse is therefore impossible: the verifier's single-fixture sentinel
probes make a declared-mapped fixture unmappable (FAIL), and the corpus-scale probe
makes all 27 unmappable (FAIL). Improvement is still allowed — the floor is monotone,
not frozen.

`03F_Replay_Fixtures.json` is FROZEN. This schema is Builder-authored parsing over the
corpus as it stands; it does not edit, reinterpret, or extend a single fixture value.
Where the corpus states an expectation this schema cannot compute, that is recorded
with its rationale and bounded by the floor above — never silently dropped.

ORACLE-SIDE MODULE. Registered in `check_anticircularity.ORACLE_MODULES`; no engine
or scenario module may import it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import engine_core as core

DIMENSIONS: Tuple[str, ...] = ("route", "attention", "authority", "receipt")

KIND_EXACT = "EXACT"
KIND_ALTERNATIVES = "ALTERNATIVES"
KIND_CEILING = "CEILING"
KIND_CONDITIONAL = "CONDITIONAL"
KIND_STRUCTURAL = "STRUCTURAL"
KIND_RELATIONAL = "RELATIONAL"
KIND_PRESENTATION = "PRESENTATION"
KIND_NOT_APPLICABLE = "NOT_APPLICABLE"
KIND_UNMAPPED = "UNMAPPED"

MAPPED_KINDS = (KIND_EXACT, KIND_ALTERNATIVES, KIND_CEILING, KIND_CONDITIONAL,
                KIND_STRUCTURAL, KIND_RELATIONAL, KIND_PRESENTATION)

# The corpus writes an em dash where a dimension does not apply to a fixture.
NOT_APPLICABLE_MARKERS = ("—", "-", "n/a", "none stated", "")


@dataclass(frozen=True)
class Expectation:
    """One fixture's expectation for one dimension, in computable form."""

    dimension: str
    fixture: str
    raw: str
    kind: str
    values: Tuple[str, ...] = ()          # EXACT / ALTERNATIVES / CEILING bound
    requires: Tuple[str, ...] = ()        # feature keys the result MUST show
    forbids: Tuple[str, ...] = ()         # feature keys the result must NOT show
    condition: Optional[str] = None       # feature key gating a CONDITIONAL
    surface: Optional[str] = None         # presentation qualifier, carried
    rationale: str = ""

    @property
    def mapped(self) -> bool:
        return self.kind in MAPPED_KINDS

    @property
    def classification(self) -> str:
        if self.kind == KIND_NOT_APPLICABLE:
            return "not-applicable"
        return "mapped" if self.mapped else "unmappable"

    def to_dict(self) -> Dict[str, object]:
        return {
            "dimension": self.dimension, "raw": self.raw, "kind": self.kind,
            "classification": self.classification,
            "values": list(self.values), "requires": list(self.requires),
            "forbids": list(self.forbids), "condition": self.condition,
            "surface": self.surface, "rationale": self.rationale,
        }


# --------------------------------------------------------------------------
# Computed features — the vocabulary STRUCTURAL expectations are written in.
#
# Every entry reads COMPUTED engine output. None reads a fixture oracle field, and
# none is satisfied merely by "some event exists": each names the specific computed
# artefact the expectation is about. A feature no defect can turn off is a vacuous
# check, so `run_oracle_mutations.py` reports, per feature, the witness that turns
# it off.
# --------------------------------------------------------------------------

def _events(r, etype: str):
    return [e for e in r.events if e.event_type == etype]


def _has(r, etype: str) -> bool:
    return bool(_events(r, etype))


FEATURES: Dict[str, Callable[[object], bool]] = {
    # --- action / receipt chain -------------------------------------------
    "external-receipt": lambda r: any(
        e.externally_authored for e in _events(r, "EvidenceIngestionEvent")),
    "verification-record": lambda r: any(
        e.payload.get("evidence_kind") == "verification"
        for e in _events(r, "EvidenceIngestionEvent")),
    "action-request": lambda r: _has(r, "ActionRequest"),
    "no-engine-authored-receipt": lambda r: not any(
        not e.externally_authored for e in _events(r, "EvidenceIngestionEvent")),
    "receipt-ownership-clean": lambda r: not r.receipt_violations,

    # --- refusal / fail-closed --------------------------------------------
    "refusal-record": lambda r: _has(r, "RefusalEvent"),
    "fail-closed": lambda r: r.ceiling == core.CEILING_NONE,
    # The definition already accepted in `judge.expected_quarantine`: the input is
    # held with no authority. A1 fails closed to ceiling `none` without setting the
    # quarantine flag (which D-B6 §2.2 scopes to an unclassifiable SOURCE, per the
    # RW-10 operationalization); A3 sets the flag. Both are quarantined in the sense
    # the corpus's routes mean. Reusing the accepted disjunction keeps one meaning of
    # the word in the harness instead of two.
    "quarantine": lambda r: bool(r.quarantined) or r.ceiling == core.CEILING_NONE,

    # --- capture / placement ----------------------------------------------
    "placement-record": lambda r: _has(r, "PlacementEvent"),

    # --- named computed mechanisms ----------------------------------------
    "dedup-record": lambda r: _has(r, "DuplicateDeliveryEvent"),
    "conflict-record": lambda r: _has(r, "ConflictRecord"),
    "reconciliation-record": lambda r: _has(r, "ReconciliationEvent"),
    "correction-record": lambda r: _has(r, "CorrectionEvent"),
    "foldback-record": lambda r: _has(r, "FoldBackEvent"),
    "degradation-record": lambda r: _has(r, "DegradationEvent"),
    "checkpoint-record": lambda r: _has(r, "CheckpointEvent"),
    "aging-record": lambda r: _has(r, "AgingEvent"),
    "kill-command": lambda r: _has(r, "KillCommandEvent"),
    "halted-items-listed": lambda r: bool(r.halted_actions),
    "override-consequence-summary": lambda r: any(
        e.payload.get("consequence_summary_shown") and e.payload.get("acknowledged")
        for e in _events(r, "OverrideEvent")),
    "suppression-record": lambda r: any(
        e.payload.get("record") == "suppression" and e.payload.get("suppressed_until")
        for e in r.events),
    "recall-hit": lambda r: any(
        e.payload.get("hit") for e in _events(r, "RecallResultEvent")),
    "provenance-record": lambda r: _has(r, "ProvenanceRecord"),
    "watchdog-fresh": lambda r: any(
        e.payload.get("fresh") for e in _events(r, "WatchdogHeartbeatEvent")),
    "focus-preserved": lambda r: any(
        e.payload.get("preserved") for e in _events(r, "FocusPointerEvent")),

    # --- render / disclosure ----------------------------------------------
    "masked-render": lambda r: (
        any(e.payload.get("record") == "render-policy-application"
            and str(e.payload.get("render_class")) != "full-content" for e in r.events)
        and r.notify_render_class != "full-content"),

    # --- authority surfaces ------------------------------------------------
    "no-outbound-authority": lambda r: not r.outbound_authorized,
    "no-state-written-on-read": lambda r: not r.state_written_on_read,
    "step-up-required": lambda r: bool(r.step_up_required),
    "step-up-satisfied": lambda r: bool(r.step_up_satisfied),
    "read-only-authority": lambda r: (
        core.CEILING_ORDER[r.ceiling] <= core.CEILING_ORDER[core.CEILING_RECORD_ONLY]),
    "internal-write-authority": lambda r: (
        core.CEILING_ORDER[r.ceiling] >= core.CEILING_ORDER[core.CEILING_INTERNAL_WRITE]),
    "receipt-bearing-authority": lambda r: (
        core.CEILING_ORDER[r.ceiling] >= core.CEILING_ORDER[core.CEILING_ACT_WITH_RECEIPT]),
    "no-consequential-execution": lambda r: not (
        r.folded.executed_actions if r.folded else []),
    "policy-version-cited": lambda r: any(
        e.payload.get("basis_policy_version") for e in _events(r, "DecisionEvent")),
    "interrupt-policy-cited": lambda r: any(
        e.payload.get("interrupt_policy") and e.payload.get("interrupt_policy_status")
        for e in _events(r, "DecisionEvent")),
    "no-proposal-without-policy": lambda r: not r.proposals_emitted or bool(
        r.eligible_proposal_classes),
    "hub-visibility": lambda r: bool(r.hub_visibility),
}


def feature(name: str, result) -> bool:
    """Evaluate one named computed feature. Unknown name is a programming error."""
    if name not in FEATURES:
        raise KeyError("unknown computed feature %r" % name)
    return bool(FEATURES[name](result))


# --------------------------------------------------------------------------
# Dimension parsers
# --------------------------------------------------------------------------

def _is_not_applicable(raw: str) -> bool:
    return raw.strip().lower() in NOT_APPLICABLE_MARKERS


def _route_head(raw: str) -> str:
    """The route's leading segment — where the tier designator lives, if any.

    A15's route reads "immediate: all action authority revoked; in-flight T2 halted
    and listed". The `T2` there is the tier of PRE-EXISTING work the kill halts, not
    the route's own tier, and a naive scan of the whole string reads it as one. The
    tier designator is taken only from the text before the first `;`.
    """
    return raw.split(";", 1)[0]


_TIER_RE = re.compile(r"\bT([0-4])\b")


def parse_route(fixture: str, raw: str) -> Expectation:
    text = (raw or "").strip()
    low = text.lower()
    if _is_not_applicable(text):
        return Expectation("route", fixture, text, KIND_NOT_APPLICABLE)

    tiers = tuple("T" + t for t in sorted(set(_TIER_RE.findall(_route_head(text)))))
    requires: List[str] = []
    forbids: List[str] = []

    # Structural markers, each naming a COMPUTED feature.
    if "fail closed" in low or "fail-closed" in low or "refuses to start" in low:
        requires.append("fail-closed")
    if "quarantine" in low:
        requires.append("quarantine")
    if "with-receipt" in low or "with receipt" in low or "+ receipt" in low:
        requires.append("external-receipt")
    if "full chain" in low:
        requires += ["external-receipt", "verification-record"]
    # A11's "NO case record" is deliberately NOT encoded as a forbidden
    # `placement-record`. The corpus's "case record" is a case/topic object; the
    # engine models placements, and no document in the Builder snapshot establishes
    # that one PlacementEvent IS a case record. Asserting the equivalence would be
    # schema over-reach — the clause is carried by A11's tier equality and by its
    # own `case per newsletter` forbidden predicate, both of which are load-bearing.
    if "fold-back" in low or "foldback" in low:
        requires.append("foldback-record")
    if "correction" in low or "cor-01" in low:
        requires.append("correction-record")
    if "degraded ladder" in low or "capture-only" in low:
        requires.append("degradation-record")
    if "reconciliation" in low or "act-01 halt" in low:
        requires.append("reconciliation-record")
    if "revoked" in low and "authority" in low:
        requires.append("kill-command")
    if "serialized" in low:
        requires.append("conflict-record")
    if "second delivery recognized" in low or "single case" in low:
        requires.append("dedup-record")
    if "description match" in low or "ex-11" in low:
        requires.append("recall-hit")
    if "render derived views" in low or "render consolidated state" in low:
        requires.append("no-state-written-on-read")
    if "masked" in low:
        requires.append("masked-render")
    if "write rejected" in low or "tamper attempt logged" in low:
        requires.append("refusal-record")
    if "auto-resume" in low:
        requires.append("checkpoint-record")
    if "ceiling identical across" in low:
        return Expectation("route", fixture, text, KIND_RELATIONAL,
                           rationale="E2E-1: the two normalizer paths must agree on "
                                     "the authorized ceiling")

    if tiers:
        kind = KIND_EXACT if len(tiers) == 1 else KIND_ALTERNATIVES
        return Expectation("route", fixture, text, kind, values=tiers,
                           requires=tuple(requires), forbids=tuple(forbids))
    if requires or forbids:
        return Expectation("route", fixture, text, KIND_STRUCTURAL,
                           requires=tuple(requires), forbids=tuple(forbids))
    return Expectation("route", fixture, text, KIND_UNMAPPED,
                       rationale="route names neither a tier nor a computed mechanism")


# Authority classes, ordered from least to most authority exercised. The corpus's
# authority column states what authority the case may EXERCISE, not the ceiling the
# envelope could support (D-B2 §2.4: `authority` is a policy-function OUTPUT).
AUTH_NONE = "none"
AUTH_READ = "read"
AUTH_INTERNAL = "internal"
AUTH_RECEIPT_BEARING = "receipt-bearing"
AUTH_STEP_UP = "step-up"


def parse_authority(fixture: str, raw: str) -> Expectation:
    """Parse the authority column into a class bound plus computed requirements.

    The column mixes two axes and the schema keeps them apart:
      HOW MUCH — none / read / internal / receipt-bearing / step-up
      WHERE    — "internal" is a DOMAIN claim (nothing outbound, nothing external),
                 not a rung. S2's "internal filing only" exercises act-with-receipt
                 authority and is still internal, so `internal` reads as a ceiling at
                 receipt-bearing plus a no-outbound requirement, never as equality
                 against a lower rung.

    "none exercised" and "read" collapse to the same computable content — nothing
    executed, no outbound. The corpus distinguishes them in prose; this engine models
    no difference between them, and the schema says so rather than inventing one.
    """
    text = (raw or "").strip()
    low = text.lower()
    if _is_not_applicable(text):
        return Expectation("authority", fixture, text, KIND_NOT_APPLICABLE)

    if "lower/escalate" in low or "never raise" in low:
        return Expectation("authority", fixture, text, KIND_RELATIONAL,
                           rationale="model-proposed fields may lower or escalate, "
                                     "never raise (D-B2 §2.4 lower/escalate-only)")

    # Reduction language first: "T2+ suspended; T4 refused" names a REDUCTION, and it
    # contains the word "receipt"-adjacent vocabulary that the rungs below would
    # otherwise capture.
    if "suspend" in low or "refused" in low:
        return Expectation("authority", fixture, text, KIND_CEILING,
                           values=(AUTH_NONE,),
                           requires=("no-consequential-execution",
                                     "no-outbound-authority"),
                           rationale="authority asserted reduced: nothing consequential "
                                     "may execute")

    if "step-up" in low:
        requires = ["step-up-required", "step-up-satisfied"]
        if "executor external" in low:
            requires.append("no-engine-authored-receipt")
        return Expectation("authority", fixture, text, KIND_EXACT,
                           values=(AUTH_STEP_UP,), requires=tuple(requires))

    if "read-only" in low or low.startswith("read"):
        return Expectation("authority", fixture, text, KIND_CEILING,
                           values=(AUTH_NONE,),
                           requires=("read-only-authority", "no-outbound-authority",
                                     "no-consequential-execution"),
                           rationale="a read exercises no action authority; the "
                                     "ceiling must stay at or below record-only")

    if "zero from embedded" in low:
        return Expectation("authority", fixture, text, KIND_STRUCTURAL,
                           requires=("no-outbound-authority", "refusal-record"),
                           rationale="embedded commands carry zero authority, and the "
                                     "rejected raise leaves a flag record (D-B2 §2.4)")
    if "no auto-retry" in low:
        return Expectation("authority", fixture, text, KIND_STRUCTURAL,
                           requires=("reconciliation-record",),
                           rationale="ACT-01: no retry before reconciliation")
    if "interrupt per policy" in low:
        return Expectation("authority", fixture, text, KIND_STRUCTURAL,
                           requires=("interrupt-policy-cited",))
    if "proposes" in low:
        return Expectation("authority", fixture, text, KIND_STRUCTURAL,
                           requires=("no-proposal-without-policy",
                                     "no-outbound-authority"),
                           rationale="the coordinator proposes; acceptance is a "
                                     "separate authority this case never exercises")
    if "standing rule" in low or "rule-scoped" in low:
        return Expectation("authority", fixture, text, KIND_STRUCTURAL,
                           requires=("no-outbound-authority", "policy-version-cited"),
                           rationale="autonomous within a standing rule: internal only, "
                                     "and the governing policy version is cited")

    if "owner-only" in low or "owner only" in low:
        return Expectation("authority", fixture, text, KIND_CEILING,
                           values=(AUTH_NONE,),
                           requires=("no-consequential-execution",
                                     "no-outbound-authority"),
                           rationale="owner decision required; nothing executes alone")

    if "none" in low or "zero" in low:
        requires = ["no-outbound-authority", "no-consequential-execution"]
        if "no send/browse tools" in low:
            requires.append("read-only-authority")
        return Expectation("authority", fixture, text, KIND_EXACT,
                           values=(AUTH_NONE,), requires=tuple(requires))

    if "internal" in low:
        return Expectation("authority", fixture, text, KIND_CEILING,
                           values=(AUTH_RECEIPT_BEARING,),
                           requires=("no-outbound-authority",),
                           rationale="internal domain: filing may bear a receipt, but "
                                     "nothing outbound or consequential-external")

    return Expectation("authority", fixture, text, KIND_UNMAPPED,
                       rationale="authority names no class this schema computes")


def computed_authority_class(result) -> str:
    """The authority the engine actually EXERCISED, computed from what it did.

    The corpus's authority column says "none exercised", not "ceiling none" — D-B2
    §2.4 makes `authority` a policy-function OUTPUT, and what a case exercised is
    what it did, not what its envelope would have permitted. Measuring the ceiling
    instead made S1 ("none exercised", a Desk render) read as `read`, and A15
    ("read-only" after a kill) read as `step-up` because the security-critical class
    sets the step-up flag while the post-kill ceiling is record-only.

    The ladder is therefore action-centric:

        step-up          an action executed under a satisfied step-up gate
        receipt-bearing  an action executed against an external receipt
        internal         no action executed, but no outbound authority either
        none             nothing executed and no outbound authority

    Internal write EVENTS do not raise the class. S8's aging record and S10's
    fold-back are recorded facts the fixtures' own `required_evidence` demands while
    their authority columns read "none" and "coordinator proposes" — so a written
    record is plainly not, in this corpus's vocabulary, authority exercised.
    """
    executed = list(result.folded.executed_actions) if result.folded else []
    if executed and result.step_up_required and result.step_up_satisfied:
        return AUTH_STEP_UP
    if executed:
        return AUTH_RECEIPT_BEARING
    if result.outbound_authorized:
        return AUTH_RECEIPT_BEARING
    return AUTH_NONE


AUTH_ORDER = {AUTH_NONE: 0, AUTH_READ: 1, AUTH_INTERNAL: 2,
              AUTH_RECEIPT_BEARING: 3, AUTH_STEP_UP: 4}


def parse_receipt(fixture: str, raw: str) -> Expectation:
    """Parse the receipt column into the named computed ARTEFACT it requires.

    The word "receipt" alone does not imply an execution receipt: A6's "ordered
    receipts" is a claim about ordering, not about an external executor. Whether an
    execution receipt is expected is a property of what the ROUTE says the engine
    does ("file-with-receipt", "full chain"), so that requirement lives on the route
    dimension and this one checks the artefact the column actually names.
    """
    text = (raw or "").strip()
    low = text.lower()
    if _is_not_applicable(text):
        return Expectation("receipt", fixture, text, KIND_NOT_APPLICABLE)

    requires: List[str] = []
    if "typed-record chain" in low or "external receipt" in low:
        requires += ["external-receipt", "verification-record"]
    elif "combined receipt" in low:
        requires.append("external-receipt")
    if "ordered receipts" in low:
        requires.append("conflict-record")
    if "kill receipt" in low:
        requires.append("kill-command")
    if "halted-item" in low:
        requires.append("halted-items-listed")
    if "consequence summary" in low:
        requires.append("override-consequence-summary")
    if "quarantine" in low:
        requires.append("quarantine")
    if "security log" in low or "tamper event" in low or "refusal record" in low:
        requires.append("refusal-record")
    if "injection flagged" in low:
        requires.append("refusal-record")
    if "suppressed-until-morning" in low or "suppressed until morning" in low:
        requires.append("suppression-record")
    if "interrupt event" in low:
        requires.append("interrupt-policy-cited")
    if "corrected placement" in low:
        requires.append("correction-record")
    if "degraded-mode" in low:
        requires.append("degradation-record")
    if "uncertainty record" in low:
        requires.append("reconciliation-record")
    if "folded-back" in low:
        requires.append("foldback-record")
    if "citing both versions" in low or "citing rule version" in low:
        requires.append("policy-version-cited")
    if "masked" in low:
        requires.append("masked-render")
    if "restore focus" in low:
        requires.append("focus-preserved")
    if "match + status" in low:
        requires.append("recall-hit")

    if requires:
        return Expectation("receipt", fixture, text, KIND_STRUCTURAL,
                           requires=tuple(dict.fromkeys(requires)))

    if any(w in low for w in ("view", "brief", "digest", "banner", "summary", "card")):
        return Expectation("receipt", fixture, text, KIND_PRESENTATION, surface=text,
                           rationale="names a presentation surface, not an evidence "
                                     "artefact; carried and reported, never counted "
                                     "as a receipt-chain comparison it is not")
    return Expectation("receipt", fixture, text, KIND_UNMAPPED,
                       rationale="receipt names no computed artefact or surface")


PARSERS: Dict[str, Callable[[str, str], Expectation]] = {
    "route": parse_route,
    "authority": parse_authority,
    "receipt": parse_receipt,
}


def parse_dimension(dimension: str, fixture: str, expected: dict) -> Expectation:
    raw = str((expected or {}).get(dimension) or "")
    return PARSERS[dimension](fixture, raw)


# --------------------------------------------------------------------------
# The fail-closed coverage floor (P2T-01)
#
# Per dimension: the classification each fixture is DECLARED to produce. Generated
# by reading the frozen corpus once and recorded here so that a later run cannot
# quietly do worse. `classification_regression()` is the gate's fail-closed rule.
#
# `not-applicable` entries are the fixtures whose corpus value is the em dash. The
# corpus is frozen, so any change in those is either a corpus edit or a parser
# regression — both fail.
# --------------------------------------------------------------------------

DECLARED_COVERAGE: Dict[str, Dict[str, str]] = {
    "route": {
        "S1": "mapped", "S2": "mapped", "S3": "mapped", "S4": "mapped",
        "S5": "mapped", "S6": "mapped", "S7": "mapped", "S8": "mapped",
        "S9": "mapped", "S10": "mapped", "A1": "mapped", "A2": "mapped",
        "A3": "mapped", "A4": "mapped", "A5": "mapped", "A6": "mapped",
        "A7": "mapped", "A8": "unmappable", "A9": "mapped", "A10": "mapped",
        "A11": "mapped", "A12": "mapped", "A13": "mapped", "A14": "mapped",
        "A15": "mapped", "A16": "mapped", "E2E-1": "mapped",
    },
    "attention": {
        "S1": "mapped", "S2": "mapped", "S3": "mapped", "S4": "mapped",
        "S5": "mapped", "S6": "mapped", "S7": "mapped", "S8": "mapped",
        "S9": "mapped", "S10": "unmappable", "A1": "unmappable", "A2": "mapped",
        "A3": "mapped", "A4": "mapped", "A5": "mapped", "A6": "unmappable",
        "A7": "mapped", "A8": "mapped", "A9": "mapped", "A10": "unmappable",
        "A11": "mapped", "A12": "mapped", "A13": "mapped", "A14": "mapped",
        "A15": "mapped", "A16": "unmappable", "E2E-1": "mapped",
    },
    "authority": {
        "S1": "mapped", "S2": "mapped", "S3": "mapped", "S4": "mapped",
        "S5": "mapped", "S6": "mapped", "S7": "mapped", "S8": "mapped",
        "S9": "mapped", "S10": "mapped", "A1": "mapped", "A2": "mapped",
        "A3": "mapped", "A4": "mapped", "A5": "not-applicable",
        "A6": "not-applicable", "A7": "mapped", "A8": "mapped", "A9": "mapped",
        "A10": "mapped", "A11": "mapped", "A12": "mapped",
        "A13": "not-applicable", "A14": "mapped", "A15": "mapped",
        "A16": "mapped", "E2E-1": "mapped",
    },
    "receipt": {
        "S1": "mapped", "S2": "mapped", "S3": "mapped", "S4": "mapped",
        "S5": "mapped", "S6": "mapped", "S7": "mapped", "S8": "mapped",
        "S9": "mapped", "S10": "mapped", "A1": "mapped", "A2": "mapped",
        "A3": "mapped", "A4": "mapped", "A5": "not-applicable", "A6": "mapped",
        "A7": "mapped", "A8": "mapped", "A9": "mapped", "A10": "mapped",
        "A11": "mapped", "A12": "mapped", "A13": "mapped", "A14": "mapped",
        "A15": "mapped", "A16": "mapped", "E2E-1": "not-applicable",
    },
}

# Rationale for every declared-unmappable entry. An unmappable expectation without a
# recorded reason is indistinguishable from an oversight, so the gate requires one.
UNMAPPABLE_RATIONALE: Dict[Tuple[str, str], str] = {
    ("route", "A8"):
        "route is a two-input conditional ('watchdog death -> Critical interrupt IF "
        "within owner-ratified ATT-01 operating policy; email -> Briefing') whose "
        "band half is compared under the attention dimension; the route dimension "
        "adds no separately computable claim.",
    ("attention", "S10"): "'per class' defers to a class rule the fixture does not state.",
    ("attention", "A1"): "'security event' names an event class, not a D-B7 §2.1 band.",
    ("attention", "A6"): "'per outcome' defers to an outcome rule the fixture does not state.",
    ("attention", "A10"): "'RES alarm' names an alarm surface, not a D-B7 §2.1 band.",
    ("attention", "A16"):
        "'per ATT-01 security assessment' defers to the ATT-01 assessment rather than "
        "naming a band.",
}


def declared(dimension: str, fixture: str) -> str:
    return DECLARED_COVERAGE.get(dimension, {}).get(fixture, "mapped")


def classification_regression(dimension: str, fixture: str, actual: str) -> Optional[str]:
    """The fail-closed floor. Returns a failure message, or None if acceptable.

    Weakening is a gate failure; strengthening (unmappable -> mapped) is allowed and
    reported, so the floor cannot freeze the harness at today's coverage.
    """
    want = declared(dimension, fixture)
    if want == actual:
        return None
    if want == "unmappable" and actual == "mapped":
        return None                                  # improvement
    return ("%s/%s: declared %s, resolved %s — the coverage floor forbids this "
            "(P2T-01 fail-closed floor)" % (fixture, dimension, want, actual))


def floor_counts() -> Dict[str, int]:
    """Per-dimension count of fixtures that MUST resolve mapped."""
    return {dim: sum(1 for v in DECLARED_COVERAGE[dim].values() if v == "mapped")
            for dim in DIMENSIONS}

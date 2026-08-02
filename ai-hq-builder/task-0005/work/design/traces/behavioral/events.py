"""Event taxonomy, store-ownership matrix, and the three candidate record shapes.

Sources:
  D-B9 §2         event/record taxonomy (16 transition classes)
  D-B9 §3         transactional outbox; partial failure exposed
  D-B9 P2G-11     store-ownership matrix; expanded replay basis
  D-B9 P2S-06     ordering-key declaration, fold phases, deterministic tie-break
  D-B4 §3         ingest_seq / source_ts / caused_by recorded separately
  Plan §B1 (l.91) S1 aggregate root · S2 Decision Case linking separately-owned
                  typed records · S3 independent records/events + projections

Shape neutrality: policy/authority semantics are identical across shapes
(D-B6 §2.1 purity; plan §309 neutrality preconditions). Shapes differ in STORAGE
layout and PROJECTION mechanics only — which is where genuine candidate-specific
divergences arise (P2S-01 requirement 9).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------
# D-B9 P2S-06 — fold phases and store priority
# --------------------------------------------------------------------------

PHASE_CONTROL = 1
PHASE_FACTS = 2
PHASE_DERIVATIONS = 3

STORE_PRIORITY: Dict[str, int] = {
    # D-B9 P2S-06 store-priority list (as amended to declare `control-journal`
    # first, ahead of policy; recorded at D-SM row 13). Ownership of kill-plane
    # commands by the external control-service journal is D-B9 P2G-11 row 9.
    "control-journal": -1,
    "policy": 0,
    "identity": 1,
    "schedule": 2,
    "registry": 3,
    "intake": 4,
    "evidence": 5,
    "model-output": 6,
    "canonical": 7,
}

# event type -> (store, fold phase)
# P2T-02 — event families whose `caused_by` may legitimately be empty. D-B9's
# ordering-key table names IngestionEvent as "None (roots)"; the control-plane
# families name a PRIOR state that does not exist for the first event of a case.
# Everything else must name its complete basis, and every ref must resolve.
GENESIS_EVENT_TYPES: Tuple[str, ...] = (
    "IngestionEvent", "PolicyVersionEvent", "IdentityEvent", "ScheduleEvent",
    "RegistryEvent", "LeaseEvent", "KillCommandEvent",
)

# Stores an `external_basis` entry may name (D-B9 P2G-11 store-ownership matrix).
EXTERNAL_BASIS_STORES: Tuple[str, ...] = (
    "control-journal", "evidence", "provider", "schedule",
)

EVENT_STORE_PHASE: Dict[str, Tuple[str, int]] = {
    # phase 1 — control plane
    "PolicyVersionEvent": ("policy", PHASE_CONTROL),
    "LeaseEvent": ("policy", PHASE_CONTROL),
    "IdentityEvent": ("identity", PHASE_CONTROL),
    "ScheduleEvent": ("schedule", PHASE_CONTROL),
    "RegistryEvent": ("registry", PHASE_CONTROL),
    # phase 2 — facts
    "IngestionEvent": ("intake", PHASE_FACTS),
    "DuplicateDeliveryEvent": ("intake", PHASE_FACTS),
    "EvidenceIngestionEvent": ("evidence", PHASE_FACTS),
    "RecordedModelOutput": ("model-output", PHASE_FACTS),
    # phase 3 — derivations (canonical)
    # D-B9 P2S-06: recorded model outputs are phase-2 facts (RecordedModelOutput
    # family), never regenerated and never phase-3 derivations.
    "NormalizationRecord": ("model-output", PHASE_FACTS),
    "RecommendationRecord": ("model-output", PHASE_FACTS),
    "PolicyEvaluationRecord": ("canonical", PHASE_DERIVATIONS),
    "DecisionEvent": ("canonical", PHASE_DERIVATIONS),
    "OverrideEvent": ("canonical", PHASE_DERIVATIONS),
    "AttentionChangeEvent": ("canonical", PHASE_DERIVATIONS),
    "ActionRequest": ("canonical", PHASE_DERIVATIONS),
    "ReconciliationEvent": ("canonical", PHASE_DERIVATIONS),
    "PlacementEvent": ("canonical", PHASE_DERIVATIONS),
    "ReclassificationEvent": ("canonical", PHASE_DERIVATIONS),
    "FoldBackEvent": ("canonical", PHASE_DERIVATIONS),
    "IntentEvent": ("canonical", PHASE_DERIVATIONS),
    "ConflictRecord": ("canonical", PHASE_DERIVATIONS),
    "AgingEvent": ("canonical", PHASE_DERIVATIONS),
    "CorrectionEvent": ("canonical", PHASE_DERIVATIONS),
    "LearningEvent": ("canonical", PHASE_DERIVATIONS),
    "ObservationEvent": ("canonical", PHASE_DERIVATIONS),
    "DegradationEvent": ("canonical", PHASE_DERIVATIONS),
    "RefusalEvent": ("canonical", PHASE_DERIVATIONS),
    "RecoveryEvent": ("canonical", PHASE_DERIVATIONS),
    "CheckpointEvent": ("canonical", PHASE_DERIVATIONS),
    "QueueAdmissionEvent": ("canonical", PHASE_DERIVATIONS),
    # RW-11 — mechanisms the engine now genuinely computes, so real defects (not
    # mutation-written flags) can perturb them.
    "FocusPointerEvent": ("canonical", PHASE_DERIVATIONS),
    "RecallResultEvent": ("canonical", PHASE_DERIVATIONS),
    "ProvenanceRecord": ("canonical", PHASE_DERIVATIONS),
    "CostEvidenceRecord": ("canonical", PHASE_DERIVATIONS),
    "EconomicReviewEvent": ("canonical", PHASE_DERIVATIONS),
    "WatchdogHeartbeatEvent": ("control-journal", PHASE_CONTROL),
    "KillCommandEvent": ("control-journal", PHASE_CONTROL),
    "KillReceiptEvent": ("control-journal", PHASE_CONTROL),
}

# D-B9 P2G-11: the evidence store is ingestion-only, never engine-authored.
EXTERNALLY_OWNED_EVENTS: Tuple[str, ...] = ("EvidenceIngestionEvent",)


@dataclass(frozen=True)
class Event:
    """One authoritative event. `caused_by` is the only causal authority (D-B4 §3)."""

    event_id: str
    event_type: str
    partition: str = "business"
    object_key: str = "-"
    store_seq: int = 0
    ingest_seq: Optional[int] = None
    caused_by: Tuple[str, ...] = ()
    payload: Dict[str, object] = field(default_factory=dict)
    externally_authored: bool = False
    # P2T-02 — DECLARED out-of-basis dependencies. `caused_by` refs must all resolve
    # inside the replay basis; a dependency on something outside it (a control-service
    # journal entry mirrored on reconnect, an external executor's record) is a
    # different KIND of dependency and is declared here rather than inferred from a
    # `caused_by` ref that happens to be absent. That inference was the defect: the
    # fold treated an unresolvable reference as already satisfied, so an incomplete
    # basis folded silently. Each entry must name a store in `EXTERNAL_BASIS_STORES`.
    external_basis: Tuple[str, ...] = ()
    # P2X-02 — the CONSUMING evidence contract. An event that depends on an external
    # basis must state what the attestation has to be FOR. The receipt check used to
    # require only that a purpose was nonempty, so a `display-monthly-digest` receipt
    # grounded a `delete-production-data` ActionRequest and the basis validated
    # clean. Declared here rather than inferred from the event type, because the
    # requirement is a property of what this event is doing, not of its family; an
    # event with an external basis and an empty tuple fails closed.
    required_receipt_purposes: Tuple[str, ...] = ()

    @property
    def store(self) -> str:
        return EVENT_STORE_PHASE[self.event_type][0]

    @property
    def phase(self) -> int:
        return EVENT_STORE_PHASE[self.event_type][1]

    def sort_key(self) -> Tuple[int, int, str, str, int]:
        """D-B9 P2S-06 total deterministic tie-break.

        fold phase -> store priority -> partition/object key (lexicographic) -> sequence.
        Every component is recorded data: no wall-clock, no arrival nondeterminism.

        For intake events the declared ordering key is `(intake_partition, ingest_seq)`
        (D-B9 P2S-06 table), so `ingest_seq` is the sequence component there; every
        other family uses its store sequence.
        """
        sequence = self.ingest_seq if (self.store == "intake" and self.ingest_seq is not None) \
            else self.store_seq
        return (
            self.phase,
            STORE_PRIORITY[self.store],
            self.partition,
            self.object_key,
            sequence,
        )


# --------------------------------------------------------------------------
# Candidate record shapes — plan §B1
# --------------------------------------------------------------------------

SHAPES: Tuple[str, ...] = ("S1", "S2", "S3")

SHAPE_DESCRIPTION: Dict[str, str] = {
    "S1": "aggregate root: append-only children under one root per case",
    "S2": "Decision Case linking separately-owned typed records",
    "S3": "independent records/events + separately materialized projections",
}


@dataclass
class ShapeStorage:
    """How a shape lays out folded records and assembles read projections.

    Authority/policy outputs are identical across shapes by construction — this
    class only models storage layout and projection mechanics.
    """

    shape: str
    records: Dict[str, List[str]] = field(default_factory=dict)
    projection_materialized: bool = True
    projection_generation: int = 0
    last_event_generation: int = 0

    def store_record(self, case_id: str, event: Event) -> None:
        if self.shape == "S1":
            # One aggregate root; every record is an append-only child of it.
            bucket = "root:%s" % case_id
        elif self.shape == "S2":
            # A Decision Case links separately-owned typed records, one bucket per type.
            bucket = "case:%s/%s" % (case_id, event.event_type)
        else:
            # S3: records/events are independent; identity is the store, not the case.
            bucket = "store:%s" % event.store
        self.records.setdefault(bucket, []).append(event.event_id)
        self.last_event_generation += 1
        if self.shape in ("S1", "S2"):
            # Reads walk live records: projections cannot lag by construction.
            self.projection_generation = self.last_event_generation

    def rebuild_projections(self) -> None:
        self.projection_generation = self.last_event_generation
        self.projection_materialized = True

    @property
    def projection_stale(self) -> bool:
        """Only S3 can carry a freshness gap — the divergence the shape genuinely has."""
        return self.projection_generation < self.last_event_generation

    def storage_summary(self) -> Dict[str, object]:
        return {
            "shape": self.shape,
            "layout": SHAPE_DESCRIPTION[self.shape],
            "bucket_count": len(self.records),
            "buckets": sorted(self.records.keys()),
            "record_count": sum(len(v) for v in self.records.values()),
            "projection_materialized": self.projection_materialized,
            "projection_stale": self.projection_stale,
        }


def shape_divergences(summaries: Dict[str, Dict[str, object]]) -> List[Dict[str, object]]:
    """Compute candidate-specific divergences from the shapes' own computed storage.

    Requirement 9: divergences are produced, not excluded by blanket assumption.
    Nothing here reads a fixture `delta_S1`/`delta_S3`/`trace_S2` field.
    """
    out: List[Dict[str, object]] = []
    ref = summaries.get("S2")
    if ref is None:
        return out
    for shape in ("S1", "S3"):
        cur = summaries.get(shape)
        if cur is None:
            continue
        if cur["bucket_count"] != ref["bucket_count"]:
            out.append(
                {
                    "shape": shape,
                    "kind": "storage-layout",
                    "detail": "%s groups records into %d bucket(s) vs S2's %d"
                    % (shape, cur["bucket_count"], ref["bucket_count"]),
                }
            )
    s3 = summaries.get("S3")
    if s3 is not None:
        out.append(
            {
                "shape": "S3",
                "kind": "projection-dependency",
                "detail": "read path depends on separately materialized projections; "
                          "freshness must be proven (stale=%s)" % s3["projection_stale"],
            }
        )
    return out

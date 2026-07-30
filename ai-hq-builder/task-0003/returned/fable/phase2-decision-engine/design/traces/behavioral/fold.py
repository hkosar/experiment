"""Deterministic cross-store replay fold (D-B9 §4 + P2S-06).

`state = fold(events, recorded_model_outputs)` — no model re-invocation anywhere.

The fold is a causal topological sort with a total deterministic tie-break:
an event is eligible when every `caused_by[]` ref is folded; among eligible events,
order = fold phase -> store priority -> partition/object key -> store sequence
(D-B9 P2S-06 "Deterministic fold"). Every component is recorded data, so the fold
is order-independent over any delivery permutation that preserves causal edges.

Reproduces (DE-R7 verbatim list, D-B9 §4): canonical state, authority ceilings,
decisions, emitted ActionRequests, queue/attention projections, all UI-observable
state. Any divergence is a gate failure, not a warning.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from events import Event, EXTERNALLY_OWNED_EVENTS, ShapeStorage


class FoldError(Exception):
    """Raised when the event set cannot be folded (unresolvable causal basis)."""


@dataclass
class FoldedState:
    shape: str
    order: List[str] = field(default_factory=list)
    canonical: Dict[str, Dict[str, object]] = field(default_factory=dict)
    action_requests: List[str] = field(default_factory=list)
    receipts_by_action: Dict[str, str] = field(default_factory=dict)
    executed_actions: List[str] = field(default_factory=list)
    verified_actions: List[str] = field(default_factory=list)
    queue: List[str] = field(default_factory=list)
    attention: Dict[str, str] = field(default_factory=dict)
    ceilings: Dict[str, str] = field(default_factory=dict)
    conflicts: List[str] = field(default_factory=list)
    reconciliation_items: List[str] = field(default_factory=list)
    outbox_residue: List[str] = field(default_factory=list)
    causal_violations: List[str] = field(default_factory=list)
    storage: Optional[ShapeStorage] = None

    def digest(self) -> str:
        """Stable digest over every authoritative surface the fold reproduces."""
        payload = {
            "shape": self.shape,
            "order": self.order,
            "canonical": self.canonical,
            "action_requests": self.action_requests,
            "receipts_by_action": self.receipts_by_action,
            "executed_actions": sorted(self.executed_actions),
            "verified_actions": sorted(self.verified_actions),
            "queue": self.queue,
            "attention": self.attention,
            "ceilings": self.ceilings,
            "conflicts": sorted(self.conflicts),
            "reconciliation_items": sorted(self.reconciliation_items),
            "outbox_residue": sorted(self.outbox_residue),
            "causal_violations": sorted(self.causal_violations),
            "storage": self.storage.storage_summary() if self.storage else None,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def surfaces(self) -> Dict[str, object]:
        return {
            "canonical": self.canonical,
            "action_requests": self.action_requests,
            "executed_actions": sorted(self.executed_actions),
            "verified_actions": sorted(self.verified_actions),
            "queue": self.queue,
            "attention": self.attention,
            "ceilings": self.ceilings,
            "storage": self.storage.storage_summary() if self.storage else None,
        }


def topological_order(events: Sequence[Event], enforce_causality: bool = True) -> List[Event]:
    """Causal topological sort with the P2S-06 total tie-break.

    `enforce_causality=False` is used ONLY by the seeded-defect suite to prove the
    harness detects a causal reorder; production paths always enforce.
    """
    by_id = {e.event_id: e for e in events}
    if len(by_id) != len(events):
        raise FoldError("duplicate event IDs in fold input")

    if not enforce_causality:
        return list(events)

    folded: List[Event] = []
    done: set = set()
    remaining = list(events)

    while remaining:
        eligible = [
            e for e in remaining
            if all((ref in done) or (ref not in by_id) for ref in e.caused_by)
        ]
        if not eligible:
            unresolved = sorted(e.event_id for e in remaining)
            raise FoldError("causal cycle or missing basis among: %s" % ", ".join(unresolved))
        eligible.sort(key=lambda e: e.sort_key())
        nxt = eligible[0]
        folded.append(nxt)
        done.add(nxt.event_id)
        remaining.remove(nxt)

    return folded


def fold(events: Sequence[Event], shape: str, case_id: str,
         enforce_causality: bool = True,
         enforce_receipt_ownership: bool = True,
         rebuild_projections: bool = True) -> FoldedState:
    """Replay the full multi-store basis into folded state for one candidate shape.

    The `enforce_*` / `rebuild_projections` switches exist so the seeded-defect
    suite can breach an invariant and prove the harness fails. Production paths
    use the defaults.
    """
    ordered = topological_order(events, enforce_causality=enforce_causality)
    storage = ShapeStorage(shape=shape)
    st = FoldedState(shape=shape, storage=storage)

    present = {e.event_id for e in events}
    folded_ids: set = set()

    for ev in ordered:
        # Causal-integrity witness: an event folded before a basis event that IS in
        # the set is a causal-order violation. Detected even when the topological
        # sort is disabled, so a seeded reorder cannot pass silently.
        for ref in ev.caused_by:
            if ref in present and ref not in folded_ids:
                st.causal_violations.append(
                    "%s folded before its basis %s" % (ev.event_id, ref))
        folded_ids.add(ev.event_id)
        st.order.append(ev.event_id)
        storage.store_record(case_id, ev)
        t = ev.event_type

        if t == "ActionRequest":
            st.action_requests.append(ev.event_id)
            forced = bool(ev.payload.get("defect_force_executed"))
            st.canonical[ev.event_id] = {
                "type": t,
                "action_class": ev.payload.get("action_class"),
                "state": "executed" if forced else "requested",
                "aik": ev.payload.get("aik"),
            }
            if forced:
                # Seeded defect: the candidate advances to executed with no receipt.
                st.executed_actions.append(ev.event_id)

        elif t == "EvidenceIngestionEvent":
            # D-B9 P2G-11: receipts enter by ingestion only; never engine-authored.
            if enforce_receipt_ownership and not ev.externally_authored:
                raise FoldError(
                    "engine-authored evidence event %s — receipts are externally owned"
                    % ev.event_id
                )
            target = str(ev.payload.get("answers_action") or "")
            kind = str(ev.payload.get("evidence_kind") or "receipt")
            if target:
                st.receipts_by_action[target] = ev.event_id
                if target in st.canonical:
                    st.canonical[target]["state"] = (
                        "verified" if kind == "verification" else "executed"
                    )
                if kind == "verification":
                    st.verified_actions.append(target)
                else:
                    st.executed_actions.append(target)

        elif t == "ConflictRecord":
            st.conflicts.append(ev.event_id)

        elif t == "ReconciliationEvent":
            st.reconciliation_items.append(ev.event_id)
            residue = ev.payload.get("outbox_residue")
            if residue:
                st.outbox_residue.append(str(residue))

        elif t == "QueueAdmissionEvent":
            st.queue.append(str(ev.payload.get("item") or ev.event_id))

        elif t == "AttentionChangeEvent":
            st.attention[str(ev.payload.get("object") or case_id)] = str(
                ev.payload.get("band") or "none"
            )

        elif t == "DecisionEvent":
            st.canonical[ev.event_id] = {
                "type": t,
                "disposition": ev.payload.get("disposition"),
                "basis_policy_version": ev.payload.get("basis_policy_version"),
                "falsifier_status": ev.payload.get("falsifier_status"),
            }
            if ev.payload.get("ceiling") is not None:
                st.ceilings[case_id] = str(ev.payload.get("ceiling"))

        else:
            st.canonical[ev.event_id] = {"type": t, **{
                k: v for k, v in ev.payload.items() if isinstance(v, (str, int, float, bool))
            }}

    if rebuild_projections:
        storage.rebuild_projections()

    return st


def receipt_ownership_violations(state: FoldedState, events: Sequence[Event]) -> List[str]:
    """Requirement 6: executed/verified state only where an external receipt exists."""
    problems: List[str] = []
    for action_id in set(state.executed_actions) | set(state.verified_actions):
        receipt = state.receipts_by_action.get(action_id)
        if not receipt:
            problems.append("action %s reached executed/verified with no receipt" % action_id)
            continue
        ev = next((e for e in events if e.event_id == receipt), None)
        if ev is None:
            problems.append("receipt %s referenced but absent from the basis" % receipt)
        elif not ev.externally_authored:
            problems.append("receipt %s is engine-authored" % receipt)
    for cid, rec in state.canonical.items():
        if rec.get("state") in ("executed", "verified") and cid not in state.receipts_by_action:
            problems.append("record %s shows %s without a receipt" % (cid, rec.get("state")))
    return problems


def permute(events: Sequence[Event], seed: int) -> List[Event]:
    """Deterministic causal-edge-preserving delivery permutation (P2S-06).

    Uses a fixed-seed linear congruential shuffle — deterministic and reproducible,
    no `random` module, no wall-clock. Causal edges are preserved because the fold
    re-derives order from `caused_by` + the tie-break; the permutation only changes
    *delivery* order into the fold.
    """
    items = list(events)
    state = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
    for i in range(len(items) - 1, 0, -1):
        state = (state * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        j = (state >> 33) % (i + 1)
        items[i], items[j] = items[j], items[i]
    return items

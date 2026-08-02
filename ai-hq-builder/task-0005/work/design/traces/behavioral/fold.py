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
from typing import Dict, List, Optional, Sequence, Tuple

import external_basis
from events import (Event, EXTERNAL_BASIS_STORES, GENESIS_EVENT_TYPES,
                    ShapeStorage)


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


# --------------------------------------------------------------------------
# P2T-02 — preflight basis validation (runs BEFORE any state is emitted)
# --------------------------------------------------------------------------

class BasisError(FoldError):
    """The replay basis is incomplete or malformed. Raised before any fold work."""


def validate_basis(events: Sequence[Event],
                   external_manifest: Optional["external_basis.ExternalManifest"] = None,
                   receipt_registry: Optional["external_basis.ReceiptRegistry"] = None,
                   evidence_policy: Optional["external_basis.EvidencePolicy"] = None
                   ) -> List[str]:
    """Check the replay basis is complete and well-formed. Returns problem strings.

    The defect this closes: `topological_order` treated a `caused_by` reference that
    was ABSENT from the event set as already satisfied —

        all((ref in done) or (ref not in by_id) for ref in e.caused_by)

    — so a DecisionEvent naming a policy event nobody delivered folded cleanly, and
    the causal-violation check missed it too because that check only looked at
    references it could already see. An incomplete basis therefore produced
    authoritative state in silence. Shuffle invariance over a truncated basis proves
    nothing about replay correctness.

    Checks (D-B9 P2S-06 ordering-key table + P2G-11 store matrix):
      1  event IDs unique
      2  every `caused_by` ref resolves inside the basis
      3  no causal cycle
      4  a non-genesis event names at least one basis ref (or a declared external one)
      5  every `external_basis` entry RESOLVES against the supplied external manifest
      6  EvidenceIngestionEvent answers an ActionRequest that is in the basis
      7  RecordedModelOutput names its input event
      8  store sequences unique within a store
      9  every event type is registered with a store and fold phase

    P2U-02 rewrote check 5. It used to read the text before the first colon and accept
    the entry if that prefix was one of four store names, so
    `control-journal:definitely-missing` passed and a DecisionEvent with no `caused_by`
    and that single reference folded to authoritative state. Resolution is now
    delegated to `external_basis.resolve`, which requires the reference to parse as
    `store:object-id@version#content-hash` and to match a record in a hash-bound
    manifest supplied WITH the fold input. No manifest and an external basis in use is
    a failure, not a default: see `external_basis` for the six distinct problems.
    """
    problems: List[str] = []
    ids = [e.event_id for e in events]
    by_id = {e.event_id: e for e in events}

    if len(by_id) != len(ids):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        problems.append("duplicate event IDs: %s" % ", ".join(dupes))

    for e in events:
        try:
            e.store, e.phase
        except KeyError:
            problems.append("event %s has unregistered type %r"
                            % (e.event_id, e.event_type))

        for ref in e.caused_by:
            if ref not in by_id:
                problems.append(
                    "event %s names causal basis %s, which is absent from the replay "
                    "basis (P2T-02: an unresolvable reference is incompleteness, not "
                    "satisfaction)" % (e.event_id, ref))

        if e.external_basis:
            # P2Y-01 — the purposes come from the POLICY PLANE, keyed by what the
            # event declares about itself. The event's own opinion of what evidence
            # it needs is not consulted, because that opinion was the finding.
            allowed, policy_problems = external_basis.governed_purposes(
                e.action_context, evidence_policy, external_manifest)
            for problem in policy_problems:
                problems.append("event %s: %s" % (e.event_id, problem))
        else:
            allowed = ()
        for ext in e.external_basis:
            for problem in external_basis.resolve(
                    ext, external_manifest, EXTERNAL_BASIS_STORES,
                    receipt_registry=receipt_registry,
                    required_purposes=allowed):
                problems.append("event %s: %s" % (e.event_id, problem))

        if (not e.caused_by and not e.external_basis
                and e.event_type not in GENESIS_EVENT_TYPES):
            problems.append(
                "event %s (%s) declares no causal basis and its family is not a "
                "declared genesis root" % (e.event_id, e.event_type))

        if e.event_type == "EvidenceIngestionEvent":
            target = str(e.payload.get("answers_action") or "")
            if target and target not in by_id:
                problems.append(
                    "evidence %s answers action %s, which is absent from the basis"
                    % (e.event_id, target))
        if e.event_type == "RecordedModelOutput" and not e.caused_by:
            problems.append("recorded model output %s names no input event"
                            % e.event_id)

    seen_seq: Dict[Tuple[str, int], str] = {}
    for e in events:
        try:
            key = (e.store, e.store_seq)
        except KeyError:
            continue
        if key in seen_seq and seen_seq[key] != e.event_id:
            problems.append("store %s sequence %d used by both %s and %s"
                            % (e.store, e.store_seq, seen_seq[key], e.event_id))
        seen_seq.setdefault(key, e.event_id)

    # Cycle detection over the resolvable edges.
    colour: Dict[str, int] = {}

    def visit(node: str, trail: List[str]) -> None:
        state = colour.get(node, 0)
        if state == 1:
            cycle = trail[trail.index(node):] + [node] if node in trail else [node]
            problems.append("causal cycle: %s" % " -> ".join(cycle))
            return
        if state == 2:
            return
        colour[node] = 1
        for ref in by_id[node].caused_by:
            if ref in by_id:
                visit(ref, trail + [node])
        colour[node] = 2

    for e in events:
        if colour.get(e.event_id, 0) == 0:
            visit(e.event_id, [])

    return problems


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
        # P2T-02: eligibility requires every named basis event to be FOLDED. The
        # `or (ref not in by_id)` escape that used to live here is what let an
        # absent reference count as satisfied.
        eligible = [
            e for e in remaining
            if all(ref in done for ref in e.caused_by)
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
         rebuild_projections: bool = True,
         enforce_basis: bool = True,
         external_manifest: Optional["external_basis.ExternalManifest"] = None,
         receipt_registry: Optional["external_basis.ReceiptRegistry"] = None,
         evidence_policy: Optional["external_basis.EvidencePolicy"] = None
         ) -> FoldedState:
    """Replay the full multi-store basis into folded state for one candidate shape.

    The `enforce_*` / `rebuild_projections` switches exist so the seeded-defect
    suite can breach an invariant and prove the harness fails. Production paths
    use the defaults.

    P2T-02: the basis is validated FIRST and the fold refuses to start on an
    incomplete one — no ordering, no state, no projection is produced from a basis
    that does not resolve. `enforce_basis=False` exists only so the missing-basis
    suite can demonstrate what the old behavior did.

    P2U-02: `external_manifest` is the enumerable registry of externally-owned
    records this replay may depend on. It defaults to None, and None is not
    permissive — an event declaring an `external_basis` with no manifest supplied
    fails closed. No corpus fixture declares one, so the default is also the
    production path.

    P2W-02: `receipt_registry` is the SEPARATELY controlled, separately bound source
    of attestations. It is a distinct argument, not a section of the manifest,
    because the independence the contract rests on is structural: the manifest's
    author cannot supply both. It defaults to None, and None is not permissive
    either — a record citing a receipt with no registry supplied fails closed.
    """
    if enforce_basis:
        problems = validate_basis(events, external_manifest=external_manifest,
                                  receipt_registry=receipt_registry,
                                  evidence_policy=evidence_policy)
        if problems:
            raise BasisError("incomplete replay basis (%d problem(s)): %s"
                             % (len(problems), "; ".join(problems[:4])))
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
    """Requirement 6: executed/verified state only where an external receipt exists.

    EVERY evidence event answering an action is checked, not just the last one
    recorded. `receipts_by_action` keeps a single reference per action, so an
    engine-authored execution receipt would otherwise be masked by a later
    legitimate VerificationRecord for the same action — a masking gap the
    per-predicate reachability search surfaced.
    """
    problems: List[str] = []
    evidence_by_action: Dict[str, List[Event]] = {}
    for e in events:
        if e.event_type == "EvidenceIngestionEvent":
            target = str(e.payload.get("answers_action") or "")
            if target:
                evidence_by_action.setdefault(target, []).append(e)

    for action_id in set(state.executed_actions) | set(state.verified_actions):
        evidence = evidence_by_action.get(action_id, [])
        if not evidence and not state.receipts_by_action.get(action_id):
            problems.append("action %s reached executed/verified with no receipt" % action_id)
            continue
        for ev in evidence:
            if not ev.externally_authored:
                problems.append("receipt %s is engine-authored" % ev.event_id)

    for cid, rec in state.canonical.items():
        if rec.get("state") in ("executed", "verified") and cid not in state.receipts_by_action:
            problems.append("record %s shows %s without a receipt" % (cid, rec.get("state")))

    # RW-24 — restored: a receipt REFERENCED by folded state but absent from the
    # basis is unevidenced state just as surely as a missing reference is. The R1
    # version of this function carried this branch; the R2 per-evidence rewrite
    # dropped it, so a dangling reference passed.
    present_ids = {e.event_id for e in events}
    for action_id, receipt_id in sorted(state.receipts_by_action.items()):
        if receipt_id not in present_ids:
            problems.append(
                "action %s cites receipt %s, which is absent from the folded basis"
                % (action_id, receipt_id))
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

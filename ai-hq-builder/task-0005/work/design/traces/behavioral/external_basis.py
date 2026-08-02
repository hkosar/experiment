"""External-basis resolver contract (verifier finding P2U-02).

WHY THIS MODULE EXISTS. TASK-0004 closed the missing-`caused_by` hole and left a
second door open. `validate_basis` checked one thing about an `external_basis` entry:
that the text before the first colon was one of four allowed store names. The verifier
walked through it with

    control-journal:definitely-missing
    evidence:definitely-missing
    provider:definitely-missing
    schedule:definitely-missing

each on a non-genesis `DecisionEvent` with no `caused_by` at all. Every one produced
`validate_basis problems: []`, `fold accepted: true`, `causal violations: []`. A
prefix is not a resolution, and "declared" had been allowed to stand in for
"resolvable" — the same substitution, in a different field, as the defect the previous
cycle fixed.

WHAT A REFERENCE MUST NOW CARRY. The verifier named the minimum: store, object/event
ID, version or content hash, verification receipt. The grammar is

    store:object-id@version#content-hash

and anything that does not parse is a problem, not a reference. The four probe strings
above fail here — they carry no version and no hash — and that is the first of five
independent reasons any one of them cannot fold.

WHAT IT MUST RESOLVE AGAINST. An `ExternalManifest`: an enumerable registry of the
externally-owned records the replay basis is entitled to depend on, supplied WITH the
fold input rather than looked up from anywhere. It is hash-bound — the manifest
carries the digest it was frozen at, and a manifest whose contents no longer produce
that digest is refused before any record in it is consulted. There is no ambient
resolver, no network, and no default: `fold()` with events that declare an external
basis and NO manifest fails closed, which is the verifier's own fallback ("If no
external resolver belongs in this design-gate harness, fail closed on every
`external_basis` use").

THE FIVE FAILURE MODES the verifier asked for tests for, each a distinct problem
string, because collapsing them would hide which one fired:

    nonexistent object      the manifest has no record under that store and id
    wrong version           the record exists; the reference names another version
    wrong content hash      the record exists at that version; the hash disagrees
    omitted from the frozen manifest
                            the RESOLVER knows the object, but the frozen snapshot
                            this replay is bound to does not list it. Distinct from
                            "nonexistent": the object is real and the basis is still
                            incomplete, which is the harder case to notice.
    unavailable / degraded resolver
                            the manifest declares its resolver could not be reached,
                            or answered from a degraded path. Unverified answers are
                            not evidence, so every reference fails.

and one more the verifier's list implies rather than states:

    unverified              the record carries no verification receipt.

ENGINE-SIDE MODULE. Registered in `check_anticircularity.ENGINE_MODULES`; reads no
oracle data and imports nothing oracle-side.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

# Resolver states a manifest may declare. Only `available` permits a reference to
# resolve; the other two fail closed, which is the point of naming them at all.
RESOLVER_AVAILABLE = "available"
RESOLVER_DEGRADED = "degraded"
RESOLVER_UNAVAILABLE = "unavailable"
RESOLVER_STATES: Tuple[str, ...] = (RESOLVER_AVAILABLE, RESOLVER_DEGRADED,
                                    RESOLVER_UNAVAILABLE)

REFERENCE_GRAMMAR = "store:object-id@version#content-hash"

# store:object@version#hash — every part required, none empty. Deliberately strict:
# a permissive grammar here would re-create the defect one layer down, because a
# reference missing its hash would parse and then have nothing to check.
_REF_RE = re.compile(
    r"^(?P<store>[a-z][a-z0-9-]*)"
    r":(?P<object_id>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"@(?P<version>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"#(?P<content_hash>[0-9a-f]{8,64})$")


@dataclass(frozen=True)
class ExternalRef:
    """One parsed `external_basis` entry."""

    store: str
    object_id: str
    version: str
    content_hash: str

    @property
    def key(self) -> str:
        return "%s:%s" % (self.store, self.object_id)

    def __str__(self) -> str:
        return "%s:%s@%s#%s" % (self.store, self.object_id, self.version,
                                self.content_hash)


@dataclass(frozen=True)
class ExternalRecord:
    """One externally-owned record the frozen snapshot is entitled to depend on."""

    store: str
    object_id: str
    version: str
    content_hash: str
    verification_receipt: Optional[str] = None

    @property
    def key(self) -> str:
        return "%s:%s" % (self.store, self.object_id)

    def as_row(self) -> Dict[str, object]:
        return {"store": self.store, "object_id": self.object_id,
                "version": self.version, "content_hash": self.content_hash,
                "verification_receipt": self.verification_receipt}


@dataclass(frozen=True)
class ExternalManifest:
    """The enumerable registry an external basis resolves against.

    `records`             the frozen snapshot: what this replay may depend on.
    `resolver_known_ids`  keys the resolver can see but the frozen snapshot does not
                          list. Present so "omitted from the frozen manifest" is a
                          state the harness can actually reach and test; without it
                          that failure mode is indistinguishable from "nonexistent".
    `resolver_state`      available / degraded / unavailable.
    `declared_digest`     the digest the manifest was frozen at. `None` means the
                          manifest declares no binding, which is itself refused —
                          an unbound manifest is a list, not a frozen snapshot.
    """

    records: Tuple[ExternalRecord, ...] = ()
    resolver_known_ids: Tuple[str, ...] = ()
    resolver_state: str = RESOLVER_AVAILABLE
    declared_digest: Optional[str] = None

    def computed_digest(self) -> str:
        blob = json.dumps([r.as_row() for r in
                           sorted(self.records, key=lambda r: (r.store, r.object_id))],
                          sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def bound(self) -> "ExternalManifest":
        """This manifest with `declared_digest` set to its own contents' digest."""
        return ExternalManifest(records=self.records,
                                resolver_known_ids=self.resolver_known_ids,
                                resolver_state=self.resolver_state,
                                declared_digest=self.computed_digest())

    def lookup(self, ref: ExternalRef) -> Optional[ExternalRecord]:
        for rec in self.records:
            if rec.store == ref.store and rec.object_id == ref.object_id:
                return rec
        return None

    def keys(self) -> List[str]:
        return sorted(r.key for r in self.records)

    def integrity_problems(self) -> List[str]:
        """Problems with the manifest ITSELF, checked before any reference uses it."""
        problems: List[str] = []
        if self.resolver_state not in RESOLVER_STATES:
            problems.append(
                "external manifest declares unknown resolver state %r; the declared "
                "states are %s" % (self.resolver_state, list(RESOLVER_STATES)))
        if self.declared_digest is None:
            problems.append(
                "external manifest declares no digest — an unbound manifest cannot be "
                "the frozen snapshot a replay is bound to (P2U-02: hash-bound)")
        else:
            # Named `computed`, not `actual`: `actual` is one of the fixture oracle
            # field names, and `check_anticircularity.check_textual()` bans that
            # vocabulary from engine code by word-boundary match. The check is
            # deliberately blunt, so the engine avoids the word rather than the check
            # learning exceptions — a whitelist there is how it would stop working.
            computed = self.computed_digest()
            if computed != self.declared_digest:
                problems.append(
                    "external manifest digest mismatch: declared %s, contents hash to "
                    "%s — the frozen snapshot has been altered"
                    % (self.declared_digest[:16], computed[:16]))
        if self.resolver_state != RESOLVER_AVAILABLE:
            problems.append(
                "external resolver is %s; no reference can be resolved and every "
                "external basis fails closed (P2U-02: an unverified answer is not "
                "evidence)" % self.resolver_state)
        return problems


def parse_reference(raw: str) -> Tuple[Optional[ExternalRef], Optional[str]]:
    """Parse one `external_basis` entry. Returns (ref, problem); exactly one is None."""
    text = str(raw)
    m = _REF_RE.match(text)
    if not m:
        return None, ("external basis %r does not parse as %r — a store prefix is not "
                      "a resolvable reference (P2U-02)" % (text, REFERENCE_GRAMMAR))
    return ExternalRef(store=m.group("store"), object_id=m.group("object_id"),
                       version=m.group("version"),
                       content_hash=m.group("content_hash")), None


def resolve(raw: str, manifest: Optional[ExternalManifest],
            declared_stores: Sequence[str]) -> List[str]:
    """Resolve ONE reference. Returns the problems; empty means it resolved.

    Order matters and is fail-closed at every step: nothing about a reference is
    accepted on the strength of a check that has not run yet.
    """
    ref, problem = parse_reference(raw)
    if problem:
        return [problem]

    problems: List[str] = []
    if ref.store not in declared_stores:
        problems.append(
            "external basis %s names store %r, which is not a declared external "
            "store %s" % (ref, ref.store, list(declared_stores)))
        return problems

    if manifest is None:
        return ["external basis %s cannot be resolved: no external manifest was "
                "supplied with the fold input (P2U-02: declared is not resolvable)"
                % ref]

    integrity = manifest.integrity_problems()
    if integrity:
        return ["external basis %s not resolvable — %s" % (ref, p) for p in integrity]

    record = manifest.lookup(ref)
    if record is None:
        if ref.key in manifest.resolver_known_ids:
            return ["external basis %s is known to the resolver but is OMITTED from "
                    "the frozen external manifest (%d record(s): %s) — the replay is "
                    "not entitled to depend on it"
                    % (ref, len(manifest.records), ", ".join(manifest.keys()) or "none")]
        return ["external basis %s names no record in the external manifest "
                "(%d record(s): %s)"
                % (ref, len(manifest.records), ", ".join(manifest.keys()) or "none")]

    if record.version != ref.version:
        problems.append("external basis %s names version %r; the manifest records %r"
                        % (ref, ref.version, record.version))
    if record.content_hash != ref.content_hash:
        problems.append("external basis %s names content hash %r; the manifest records "
                        "%r" % (ref, ref.content_hash, record.content_hash))
    if not record.verification_receipt:
        problems.append("external basis %s resolves to a record with no verification "
                        "receipt — an unverified external record is not evidence"
                        % ref)
    return problems


def reference_for(record: ExternalRecord) -> str:
    """The reference string that resolves to `record`. Used to build positive cases."""
    return "%s:%s@%s#%s" % (record.store, record.object_id, record.version,
                            record.content_hash)

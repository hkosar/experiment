"""External-basis resolver contract (verifier findings P2U-02, P2V-02/03, P2W-02/03).

WHY THIS MODULE EXISTS, AND WHAT EACH CYCLE GOT WRONG. The history matters because
every correction so far has been the previous correction one layer short, and the
shape repeats: a control that NAMES a thing without ESTABLISHING it.

  P2U-02  `validate_basis` checked that an `external_basis` string began with one of
          four store names. `control-journal:definitely-missing` on a DecisionEvent
          with no `caused_by` folded to authoritative state. A prefix is not a
          resolution.
  P2V-02  the fix made the reference resolve and left its ATTESTATION a free-text
          string: `verification_receipt="verified"` satisfied it.
  P2V-03  the manifest digest covered `records` only, so `resolver_state` — the
          control that fails every reference closed when the resolver is unreachable
          — could be edited under a still-valid binding.
  P2W-02  the receipt then had to resolve to a registered record, but IN THE SAME
          MANIFEST. The chain terminated at the first record with no receipt of its
          own, and that record was trusted because the same author had listed it. The
          verifier put an unrelated root in one manifest and had it certify a target:
          `integrity_problems: []`, `fold accepted: true`. The reference grammar also
          accepted 8-hex "content hashes" — `deadbeef`, `cafebabe`.
  P2W-03  the manifest could not REPRESENT, and so could not bind, schema version,
          snapshot identity, source, creation context, receipt-authority identity, or
          a trust-root contract. Two semantically different authority/snapshot
          contexts with the same rows produced the same digest, necessarily.

WHAT THE CONTRACT IS NOW. Fable's RW-33 ruling selects the verifier's first option:
**the independence source is structural — a separate registry and a separate actor —
not positional.** So there are TWO independently bound artifacts:

    ExternalManifest    the frozen snapshot of externally-owned records this replay
                        may depend on. Authored by `source_id`.
    ReceiptRegistry     the attestations. Authored by `authority_id`, which MUST
                        differ from the manifest's `source_id`, and which the
                        manifest names in advance as `receipt_authority_id`.

A record's `verification_receipt` is a `receipt:` reference that can only resolve in
the registry — it is not expressible as a manifest reference, so a same-manifest chain
is not merely refused, it is unconstructible. Every receipt carries:

    subject_ref     the FULL reference of the record it attests to. A receipt that
                    names another record cannot certify this one, which is the
                    verifier's unrelated-root probe.
    purpose         the action class the attestation covers.
    authority_version / content_hash   matched against the reference.

and the registry carries a revocation set the manifest is bound to by
`revocation_snapshot_id`, so a stale revocation list cannot be swapped in.

CONTENT IDENTITY is a full-length lowercase %s digest. Abbreviated values are
refused: a 32-bit prefix is not a content identity, and accepting one made the
verifier's `deadbeef` probe resolve.

WHAT IS NOT CLAIMED. This is structural independence, not cryptographic attestation.
There is no signature, no key, and no trust root: `trust_root_id` is declared as an
explicit not-applicable sentinel rather than left absent, so the absence is a recorded
decision instead of a gap. An actor who controls BOTH artifacts can still author a
consistent pair. What the contract buys is that the manifest author alone cannot —
the two artifacts must be bound separately, by different declared authorities, and the
manifest must have named its receipt authority before the registry is consulted. If
the design later adopts cryptographic attestation (the verifier's second option), the
envelope already carries the fields for it.

ENGINE-SIDE MODULE. Registered in `check_anticircularity.ENGINE_MODULES`; reads no
oracle data and imports nothing oracle-side.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Approved algorithms, schemas and grammars (P2W-03)
# --------------------------------------------------------------------------

DIGEST_ALGORITHM = "sha256"
APPROVED_DIGEST_ALGORITHMS: Tuple[str, ...] = ("sha256",)
DIGEST_HEX_LENGTH = 64

MANIFEST_SCHEMA = "external-basis-manifest/2"
APPROVED_MANIFEST_SCHEMAS: Tuple[str, ...] = (MANIFEST_SCHEMA,)
CANONICALIZATION_VERSION = "json-sorted-keys/1"
APPROVED_CANONICALIZATIONS: Tuple[str, ...] = (CANONICALIZATION_VERSION,)

REGISTRY_SCHEMA = "receipt-registry/1"
APPROVED_REGISTRY_SCHEMAS: Tuple[str, ...] = (REGISTRY_SCHEMA,)

EVIDENCE_POLICY_SCHEMA = "action-evidence-policy/1"
APPROVED_EVIDENCE_POLICY_SCHEMAS: Tuple[str, ...] = (EVIDENCE_POLICY_SCHEMA,)

RECORD_IDENTITY_RULE = "store:object_id unique within the manifest"
APPROVED_RECORD_IDENTITY_RULES: Tuple[str, ...] = (RECORD_IDENTITY_RULE,)

# Declared when no cryptographic attestation contract is in force. Declaring the
# absence keeps it a recorded decision; leaving the field empty would make it a gap.
TRUST_ROOT_NOT_APPLICABLE = "not-applicable:structural-separation-only"

# Resolver states a manifest may declare. Only `available` permits a reference to
# resolve; the other two fail closed, which is the point of naming them at all.
RESOLVER_AVAILABLE = "available"
RESOLVER_DEGRADED = "degraded"
RESOLVER_UNAVAILABLE = "unavailable"
RESOLVER_STATES: Tuple[str, ...] = (RESOLVER_AVAILABLE, RESOLVER_DEGRADED,
                                    RESOLVER_UNAVAILABLE)

REFERENCE_GRAMMAR = "store:object-id@version#<%d-hex-%s>" % (DIGEST_HEX_LENGTH,
                                                             DIGEST_ALGORITHM)
RECEIPT_GRAMMAR = "receipt:receipt-id@authority-version#<%d-hex-%s>" % (
    DIGEST_HEX_LENGTH, DIGEST_ALGORITHM)

_HEX = r"[0-9a-f]{%d}" % DIGEST_HEX_LENGTH

# Deliberately strict at both ends: a permissive grammar re-creates the defect one
# layer down, and an abbreviated hash is not a content identity.
_REF_RE = re.compile(
    r"^(?P<store>[a-z][a-z0-9-]*)"
    r":(?P<object_id>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"@(?P<version>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"#(?P<content_hash>" + _HEX + r")$")

# A receipt reference names the registry, never a manifest store. That is what makes
# a same-manifest chain unconstructible rather than merely refused.
_RECEIPT_RE = re.compile(
    r"^receipt:(?P<receipt_id>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"@(?P<authority_version>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"#(?P<content_hash>" + _HEX + r")$")


# --------------------------------------------------------------------------
# References
# --------------------------------------------------------------------------

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
class ReceiptRef:
    """One parsed `verification_receipt` entry."""

    receipt_id: str
    authority_version: str
    content_hash: str

    def __str__(self) -> str:
        return "receipt:%s@%s#%s" % (self.receipt_id, self.authority_version,
                                     self.content_hash)


def parse_reference(raw: str) -> Tuple[Optional[ExternalRef], Optional[str]]:
    """Parse one `external_basis` entry. Returns (ref, problem); exactly one is None."""
    text = str(raw)
    m = _REF_RE.match(text)
    if not m:
        return None, ("external basis %r does not parse as %r — a store prefix is not "
                      "a resolvable reference, and an abbreviated hash is not a "
                      "content identity (P2U-02, P2W-02)" % (text, REFERENCE_GRAMMAR))
    return ExternalRef(store=m.group("store"), object_id=m.group("object_id"),
                       version=m.group("version"),
                       content_hash=m.group("content_hash")), None


def parse_receipt_reference(raw: str) -> Tuple[Optional[ReceiptRef], Optional[str]]:
    text = str(raw)
    m = _RECEIPT_RE.match(text)
    if not m:
        return None, ("verification receipt %r does not parse as %r — an attestation "
                      "is an object in the receipt registry, not a string and not a "
                      "record in the manifest being attested (P2W-02)"
                      % (text, RECEIPT_GRAMMAR))
    return ReceiptRef(receipt_id=m.group("receipt_id"),
                      authority_version=m.group("authority_version"),
                      content_hash=m.group("content_hash")), None


# --------------------------------------------------------------------------
# Records and receipts
# --------------------------------------------------------------------------

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
class Receipt:
    """One attestation, held by an authority that is not the manifest's author.

    `subject_ref` is the whole point: the receipt names the record it attests to, at
    a version and content hash. Without it, any registered receipt certifies any
    record — which is what the verifier's unrelated-root probe demonstrated.

    P2X-02: `content_hash` used to be self-declared — a field the receipt's author
    filled in with anything, compared only against the reference that cited it. Two
    self-declared values agreeing with each other is not integrity. It is now the
    CANONICAL DIGEST of the receipt's own content, computed by `row_digest()`, and a
    receipt whose declared hash does not equal its computed one is refused before it
    can attest to anything.
    """

    receipt_id: str
    subject_ref: str
    purpose: str
    authority_version: str
    content_hash: str

    def content_row(self) -> Dict[str, object]:
        """Everything the content hash covers — the row minus the hash itself."""
        return {"receipt_id": self.receipt_id, "subject_ref": self.subject_ref,
                "purpose": self.purpose, "authority_version": self.authority_version}

    def row_digest(self) -> str:
        return _digest(self.content_row())

    def as_row(self) -> Dict[str, object]:
        return dict(self.content_row(), content_hash=self.content_hash)

    def bound(self) -> "Receipt":
        """This receipt with `content_hash` set to its own canonical row digest."""
        return Receipt(receipt_id=self.receipt_id, subject_ref=self.subject_ref,
                       purpose=self.purpose,
                       authority_version=self.authority_version,
                       content_hash=self.row_digest())


# --------------------------------------------------------------------------
# The action-evidence contract (P2Y-01)
#
# R3 let the CONSUMING EVENT declare `required_receipt_purposes`, and the verifier
# pointed out what that means: the comparison worked, and the action chose the value
# it was compared against. A `delete-production-data` ActionRequest declaring
# `display-monthly-digest` as its requirement was satisfied by a display receipt with
# `basis problems: []`. Two self-consistent declarations by one producer are not a
# governed contract — which is the same substitution as every finding before it, one
# more layer up: the event named its requirement instead of being subject to one.
#
# `46_` §3, ratified by Fable as a design ruling, states the contract: valid evidence
# purposes are determined by an independently governed mapping keyed by action class,
# scope, policy version and risk/data class. The event declares FACTS ABOUT ITSELF —
# what class of action it is, in what scope, under which policy version, at what risk
# class — and the policy plane decides what evidence that combination requires. The
# event may carry the resolved contract id, and if it does it must match the one the
# lookup finds; it cannot select a different contract and it cannot invent purposes.
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ActionEvidenceContract:
    """One governed row: which evidence purposes an action class may be grounded by."""

    contract_id: str
    action_class: str
    scope: str
    policy_version: str
    risk_class: str
    allowed_purposes: Tuple[str, ...] = ()

    @property
    def key(self) -> Tuple[str, str, str, str]:
        return (self.action_class, self.scope, self.policy_version, self.risk_class)

    def as_row(self) -> Dict[str, object]:
        return {"contract_id": self.contract_id, "action_class": self.action_class,
                "scope": self.scope, "policy_version": self.policy_version,
                "risk_class": self.risk_class,
                "allowed_purposes": sorted(self.allowed_purposes)}


@dataclass(frozen=True)
class EvidencePolicy:
    """The policy-plane artifact holding the contracts. Independently bound.

    Authored by `authority_id`, which must differ from the manifest's `source_id` AND
    from the receipt registry's `authority_id` (`48_` §4.1). R4 checked only the first
    half, so the party that ISSUES receipts could also decide which receipt purposes
    authorize an action — one actor holding both ends of the comparison, which is the
    same substitution P2Y-01 was raised about, moved one artifact along.

    `policy_version` is the artifact's own version and it is load-bearing: every
    contract row it carries must declare that same version (`48_` §4.2). A policy that
    announces P999 while applying P1 rows has an ambiguous identity, and a version
    nothing is checked against is a label, not a version.
    """

    schema_version: str = EVIDENCE_POLICY_SCHEMA
    authority_id: str = ""
    policy_version: str = ""
    contracts: Tuple[ActionEvidenceContract, ...] = ()
    declared_digest: Optional[str] = None

    def computed_digest(self) -> str:
        return _digest({
            "schema_version": self.schema_version,
            "authority_id": self.authority_id,
            "policy_version": self.policy_version,
            "contracts": [c.as_row() for c in
                          sorted(self.contracts, key=lambda c: c.contract_id)],
        })

    def bound(self) -> "EvidencePolicy":
        return EvidencePolicy(schema_version=self.schema_version,
                              authority_id=self.authority_id,
                              policy_version=self.policy_version,
                              contracts=self.contracts,
                              declared_digest=self.computed_digest())

    def lookup(self, action_class: str, scope: str, policy_version: str,
               risk_class: str) -> Optional[ActionEvidenceContract]:
        want = (action_class, scope, policy_version, risk_class)
        for contract in self.contracts:
            if contract.key == want:
                return contract
        return None

    def duplicate_keys(self) -> List[str]:
        seen: Dict[Tuple[str, str, str, str], int] = {}
        for c in self.contracts:
            seen[c.key] = seen.get(c.key, 0) + 1
        return sorted("/".join(k) for k, n in seen.items() if n > 1)

    def integrity_problems(self) -> List[str]:
        problems: List[str] = []
        if self.schema_version not in APPROVED_EVIDENCE_POLICY_SCHEMAS:
            problems.append(
                "evidence policy declares schema %r; approved schemas are %s"
                % (self.schema_version, list(APPROVED_EVIDENCE_POLICY_SCHEMAS)))
        for name in ("authority_id", "policy_version"):
            if not str(getattr(self, name) or "").strip():
                problems.append("evidence policy declares no %s" % name)
        for key in self.duplicate_keys():
            problems.append(
                "evidence policy carries more than one contract for %s — which one "
                "governs would depend on tuple order (P2Y-01)" % key)
        for c in self.contracts:
            if not str(c.contract_id or "").strip():
                problems.append("evidence policy holds a contract with no contract_id")
        # `48_` §4.2 — ONE coherent version per artifact. A multi-version policy set is
        # separately bound versioned artifacts or an explicitly versioned policy-set
        # schema; it is never versions silently mixed inside one artifact, because then
        # the artifact's declared version stops being load-bearing.
        for c in sorted(self.contracts, key=lambda c: c.contract_id):
            if c.policy_version != self.policy_version:
                problems.append(
                    "evidence policy declares version %r but carries contract %r at "
                    "version %r — one artifact, one version: a policy that applies rows "
                    "from a version it does not claim has no determinate identity "
                    "(P2Y-01, 48_ §4.2)"
                    % (self.policy_version, c.contract_id, c.policy_version))
        if self.declared_digest is None:
            problems.append(
                "evidence policy declares no digest — an unbound policy is a "
                "suggestion, not an authority")
        elif self.computed_digest() != self.declared_digest:
            problems.append(
                "evidence policy digest mismatch: declared %s, contents hash to %s"
                % (self.declared_digest[:16], self.computed_digest()[:16]))
        return problems


@dataclass(frozen=True)
class ActionContext:
    """What the consuming event declares ABOUT ITSELF (P2Y-01).

    Facts, not requirements. `declared_contract_id` is the resolved contract the
    producer believes governs it — optional, and checked against the lookup rather
    than trusted, so naming a permissive contract does not select one.
    """

    action_class: str = ""
    scope: str = ""
    policy_version: str = ""
    risk_class: str = ""
    declared_contract_id: str = ""


def reference_for(record: ExternalRecord) -> str:
    """The reference string that resolves to `record`."""
    return "%s:%s@%s#%s" % (record.store, record.object_id, record.version,
                            record.content_hash)


def receipt_reference_for(receipt: Receipt) -> str:
    return "receipt:%s@%s#%s" % (receipt.receipt_id, receipt.authority_version,
                                 receipt.content_hash)


# --------------------------------------------------------------------------
# The receipt registry — separately controlled, separately bound (P2W-02)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ReceiptRegistry:
    """Attestations, bound independently of the manifest they attest to."""

    schema_version: str = REGISTRY_SCHEMA
    authority_id: str = ""
    authority_version: str = ""
    snapshot_id: str = ""
    digest_algorithm: str = DIGEST_ALGORITHM
    receipts: Tuple[Receipt, ...] = ()
    revoked_receipt_ids: Tuple[str, ...] = ()
    declared_digest: Optional[str] = None

    def computed_digest(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "authority_id": self.authority_id,
            "authority_version": self.authority_version,
            "snapshot_id": self.snapshot_id,
            "digest_algorithm": self.digest_algorithm,
            "receipts": [r.as_row() for r in
                         sorted(self.receipts, key=lambda r: r.receipt_id)],
            "revoked_receipt_ids": sorted(self.revoked_receipt_ids),
        }
        missing = sorted(set(REGISTRY_DIGEST_BOUND_FIELDS) - set(payload))
        if missing:
            raise AssertionError(
                "registry digest-bound field(s) %s are declared but not hashed — the "
                "enumeration and the hash have drifted (P2W-03)" % missing)
        return _digest(payload)

    def bound(self) -> "ReceiptRegistry":
        return ReceiptRegistry(
            schema_version=self.schema_version, authority_id=self.authority_id,
            authority_version=self.authority_version, snapshot_id=self.snapshot_id,
            digest_algorithm=self.digest_algorithm, receipts=self.receipts,
            revoked_receipt_ids=self.revoked_receipt_ids,
            declared_digest=self.computed_digest())

    def lookup(self, ref: ReceiptRef) -> Optional[Receipt]:
        for receipt in self.receipts:
            if receipt.receipt_id == ref.receipt_id:
                return receipt
        return None

    def duplicate_receipt_ids(self) -> List[str]:
        seen: Dict[str, int] = {}
        for r in self.receipts:
            seen[r.receipt_id] = seen.get(r.receipt_id, 0) + 1
        return sorted(k for k, n in seen.items() if n > 1)

    def integrity_problems(self) -> List[str]:
        problems: List[str] = list(_check_registry_field_coverage())
        if self.schema_version not in APPROVED_REGISTRY_SCHEMAS:
            problems.append(
                "receipt registry declares schema %r; approved schemas are %s"
                % (self.schema_version, list(APPROVED_REGISTRY_SCHEMAS)))
        if self.digest_algorithm not in APPROVED_DIGEST_ALGORITHMS:
            problems.append(
                "receipt registry declares digest algorithm %r; approved algorithms "
                "are %s" % (self.digest_algorithm, list(APPROVED_DIGEST_ALGORITHMS)))
        for name in ("authority_id", "authority_version", "snapshot_id"):
            if not str(getattr(self, name) or "").strip():
                problems.append(
                    "receipt registry declares no %s — an unidentified attestation "
                    "authority cannot be independent of anything (P2W-02)" % name)
        for rid in self.duplicate_receipt_ids():
            problems.append(
                "receipt registry carries more than one receipt with id %r — which "
                "one answers would depend on tuple order (P2W-03 ambiguous identity)"
                % rid)
        if self.declared_digest is None:
            problems.append(
                "receipt registry declares no digest — an unbound registry is a list, "
                "not an independently bound artifact")
        elif self.computed_digest() != self.declared_digest:
            problems.append(
                "receipt registry digest mismatch: declared %s, contents hash to %s "
                "— the registry has been altered after binding"
                % (self.declared_digest[:16], self.computed_digest()[:16]))
        return problems


# --------------------------------------------------------------------------
# The manifest envelope (P2W-03)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ExternalManifest:
    """The canonical versioned envelope an external basis resolves against.

    Every field below except `declared_digest` is bound by the digest. The set was
    not chosen by me: it is the enumeration in the P2W-03 required correction, and
    `REQUIRED_CONTRACT_CONTROLS` maps each item of that list to the field that
    carries it, so "the manifest declares all fields the accepted contract requires"
    is checked rather than believed.
    """

    # schema and canonicalization
    schema_version: str = MANIFEST_SCHEMA
    canonicalization_version: str = CANONICALIZATION_VERSION
    # snapshot identity and provenance
    snapshot_id: str = ""
    snapshot_epoch: str = ""
    source_id: str = ""
    creation_context: str = ""
    # record identity
    record_identity_rule: str = RECORD_IDENTITY_RULE
    # digest contract
    digest_algorithm: str = DIGEST_ALGORITHM
    digest_hex_length: int = DIGEST_HEX_LENGTH
    # resolver
    resolver_id: str = ""
    resolver_version: str = ""
    resolver_state: str = RESOLVER_AVAILABLE
    # receipt / evidence authority
    receipt_authority_id: str = ""
    receipt_authority_version: str = ""
    receipt_verification_config: str = ""
    # P2X-01 — the registry's CONTENT digest, not its label. The manifest bound
    # `receipt_authority_id`, `receipt_authority_version` and `revocation_snapshot_id`
    # and nothing about what the registry actually contained, so two separately valid
    # registries could carry the same three labels and different receipts. The
    # verifier supplied one without `r-late` (unresolved) and one with it (resolved)
    # while the manifest stayed byte-identical: the replay was deterministic over the
    # pair of runtime arguments, not over its own declared evidence basis.
    receipt_registry_digest: str = ""
    trust_root_id: str = TRUST_ROOT_NOT_APPLICABLE
    trust_root_key_version: str = TRUST_ROOT_NOT_APPLICABLE
    revocation_snapshot_id: str = ""
    # payload
    records: Tuple[ExternalRecord, ...] = ()
    resolver_known_ids: Tuple[str, ...] = ()
    # the binding
    declared_digest: Optional[str] = None

    def _payload(self) -> Dict[str, object]:
        payload: Dict[str, object] = {}
        for name in DIGEST_BOUND_FIELDS:
            if not hasattr(self, name):
                raise AssertionError(
                    "external manifest declares field %r in the digest enumeration, "
                    "but the manifest has no such field — the enumeration is stale "
                    "and no digest can be produced (P2V-03)" % name)
            value = getattr(self, name)
            if name == "records":
                value = [r.as_row() for r in
                         sorted(value, key=lambda r: (r.store, r.object_id))]
            elif name == "resolver_known_ids":
                value = sorted(value)
            payload[name] = value
        return payload

    def computed_digest(self) -> str:
        """Hash over EVERY digest-bound field, in a declared canonical order.

        Built by walking `DIGEST_BOUND_FIELDS` rather than by listing fields here a
        second time. The R1 version listed them, which is a place for the hash and
        the enumeration to drift; now a field can only be hashed if it is enumerated,
        and `_check_digest_field_coverage()` fails if any dataclass field is not.
        """
        return _digest(self._payload())

    def bound(self) -> "ExternalManifest":
        """This manifest with `declared_digest` set to its own contents' digest."""
        values = {name: getattr(self, name)
                  for name in ExternalManifest.__dataclass_fields__}
        values["declared_digest"] = self.computed_digest()
        return ExternalManifest(**values)

    def lookup(self, ref: ExternalRef) -> Optional[ExternalRecord]:
        for rec in self.records:
            if rec.store == ref.store and rec.object_id == ref.object_id:
                return rec
        return None

    def keys(self) -> List[str]:
        return sorted(r.key for r in self.records)

    def duplicate_identities(self) -> List[str]:
        seen: Dict[str, List[str]] = {}
        for rec in self.records:
            seen.setdefault(rec.key, []).append(rec.version)
        return sorted(k for k, versions in seen.items() if len(versions) > 1)

    def integrity_problems(self) -> List[str]:
        """Problems with the ENVELOPE itself, checked before any reference uses it."""
        problems: List[str] = list(_check_digest_field_coverage())
        problems.extend(_check_record_row_coverage())

        if self.schema_version not in APPROVED_MANIFEST_SCHEMAS:
            problems.append(
                "external manifest declares schema %r; approved schemas are %s "
                "(P2W-03: unknown schema versions are refused)"
                % (self.schema_version, list(APPROVED_MANIFEST_SCHEMAS)))
        if self.canonicalization_version not in APPROVED_CANONICALIZATIONS:
            problems.append(
                "external manifest declares canonicalization %r; approved are %s"
                % (self.canonicalization_version, list(APPROVED_CANONICALIZATIONS)))
        if self.digest_algorithm not in APPROVED_DIGEST_ALGORITHMS:
            problems.append(
                "external manifest declares digest algorithm %r; approved algorithms "
                "are %s (P2W-02: no abbreviated or unapproved content identity)"
                % (self.digest_algorithm, list(APPROVED_DIGEST_ALGORITHMS)))
        if self.digest_hex_length != DIGEST_HEX_LENGTH:
            problems.append(
                "external manifest declares digest length %r; the approved length is "
                "%d hex characters" % (self.digest_hex_length, DIGEST_HEX_LENGTH))
        if self.record_identity_rule not in APPROVED_RECORD_IDENTITY_RULES:
            problems.append(
                "external manifest declares record-identity rule %r; approved rules "
                "are %s" % (self.record_identity_rule,
                            list(APPROVED_RECORD_IDENTITY_RULES)))

        for control, field_name in sorted(REQUIRED_CONTRACT_CONTROLS.items()):
            if not str(getattr(self, field_name, "") or "").strip():
                problems.append(
                    "external manifest declares no %s (control %r) — a required "
                    "control the contract names is missing, so the envelope is "
                    "incomplete (P2W-03)" % (field_name, control))

        if self.receipt_authority_id and self.source_id \
                and self.receipt_authority_id == self.source_id:
            problems.append(
                "external manifest names itself (%s) as its own receipt authority — "
                "attestations from the record author are not independent evidence "
                "(P2W-02)" % self.source_id)

        for key in self.duplicate_identities():
            versions = sorted(r.version for r in self.records if r.key == key)
            problems.append(
                "external manifest carries %d records for identity %s (versions %s) — "
                "which one answers for that identity would depend on tuple order, so "
                "the manifest is refused (P2V-03)"
                % (len(versions), key, ", ".join(versions)))

        if self.resolver_state not in RESOLVER_STATES:
            problems.append(
                "external manifest declares unknown resolver state %r; the declared "
                "states are %s" % (self.resolver_state, list(RESOLVER_STATES)))
        if self.declared_digest is None:
            problems.append(
                "external manifest declares no digest — an unbound manifest cannot be "
                "the frozen snapshot a replay is bound to (P2V-03: hash-bound)")
        else:
            # `computed`, not `actual` — `actual` is a fixture oracle field name and
            # `check_anticircularity.check_textual()` bans that vocabulary from engine
            # code. This file has tripped that check on that identifier twice; the
            # check caught it both times, which is the argument for keeping it blunt.
            computed = self.computed_digest()
            if computed != self.declared_digest:
                problems.append(
                    "external manifest digest mismatch: declared %s, contents hash to "
                    "%s — the frozen snapshot has been altered after binding"
                    % (self.declared_digest[:16], computed[:16]))
        if self.resolver_state != RESOLVER_AVAILABLE:
            problems.append(
                "external resolver is %s; no reference can be resolved and every "
                "external basis fails closed (P2U-02: an unverified answer is not "
                "evidence)" % self.resolver_state)
        return problems


# --------------------------------------------------------------------------
# The digest-binding enumeration and its guards (P2V-03, extended for P2W-03)
# --------------------------------------------------------------------------

DIGEST_BOUND_FIELDS: Tuple[str, ...] = (
    "schema_version", "canonicalization_version",
    "snapshot_id", "snapshot_epoch", "source_id", "creation_context",
    "record_identity_rule",
    "digest_algorithm", "digest_hex_length",
    "resolver_id", "resolver_version", "resolver_state",
    "receipt_authority_id", "receipt_authority_version",
    "receipt_verification_config", "receipt_registry_digest",
    "trust_root_id", "trust_root_key_version",
    "revocation_snapshot_id",
    "records", "resolver_known_ids",
)
DIGEST_EXEMPT_FIELDS: Dict[str, str] = {
    "declared_digest": "the digest itself — hashing it would be circular, and it is "
                       "the value the other fields are checked against",
}

REGISTRY_DIGEST_BOUND_FIELDS: Tuple[str, ...] = (
    "schema_version", "authority_id", "authority_version", "snapshot_id",
    "digest_algorithm", "receipts", "revoked_receipt_ids",
)
REGISTRY_DIGEST_EXEMPT_FIELDS: Dict[str, str] = {
    "declared_digest": "the digest itself",
}

# The P2W-03 required-correction list, item by item, mapped to the field that carries
# it. The field-coverage guard proves every field is classified; THIS proves the
# contract's required controls are present at all — the gap the verifier named:
# "it does not prove that the manifest declares all fields the accepted contract
# requires".
REQUIRED_CONTRACT_CONTROLS: Dict[str, str] = {
    "manifest schema version": "schema_version",
    "canonicalization version": "canonicalization_version",
    "snapshot id / epoch": "snapshot_id",
    "snapshot epoch": "snapshot_epoch",
    "source identity": "source_id",
    "creation or capture context": "creation_context",
    "record-identity tuple and uniqueness rule": "record_identity_rule",
    "approved digest algorithm": "digest_algorithm",
    "resolver identity": "resolver_id",
    "resolver version": "resolver_version",
    "resolver state": "resolver_state",
    "receipt/evidence authority identity": "receipt_authority_id",
    "receipt authority version/configuration": "receipt_authority_version",
    "receipt verification configuration": "receipt_verification_config",
    "exact receipt-registry content identity": "receipt_registry_digest",
    "trust-root or key version": "trust_root_id",
    "trust-root key version": "trust_root_key_version",
    "revocation/status snapshot": "revocation_snapshot_id",
}

# Receipt chains are followed to prove the attestation is registered, not to build a
# trust hierarchy. Retained from R1 for the registry-side walk.
MAX_RECEIPT_CHAIN = 8


def _digest(payload: Dict[str, object]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.new(DIGEST_ALGORITHM, blob.encode("utf-8")).hexdigest()


def _coverage_problems(cls, bound, exempt, label) -> List[str]:
    declared = set(bound) | set(exempt)
    present = set(cls.__dataclass_fields__)
    problems = []
    for name in sorted(present - declared):
        problems.append(
            "%s field %r is neither digest-bound nor declared exempt — it could be "
            "edited without invalidating the declared digest (P2V-03)" % (label, name))
    for name in sorted(declared - present):
        problems.append(
            "%s declares field %r in the digest enumeration, but the class has no "
            "such field — the enumeration is stale (P2V-03)" % (label, name))
    return problems


def _check_digest_field_coverage() -> List[str]:
    """Every manifest field must be digest-bound or declared exempt (P2V-03)."""
    return _coverage_problems(ExternalManifest, DIGEST_BOUND_FIELDS,
                              DIGEST_EXEMPT_FIELDS, "external manifest")


def _check_registry_field_coverage() -> List[str]:
    return _coverage_problems(ReceiptRegistry, REGISTRY_DIGEST_BOUND_FIELDS,
                              REGISTRY_DIGEST_EXEMPT_FIELDS, "receipt registry")


def _check_record_row_coverage() -> List[str]:
    """Every ExternalRecord / Receipt field must appear in its `as_row()` (P2W-03).

    The verifier's exact gap: the field-coverage guard "does not cover future fields
    added to `ExternalRecord.as_row()` incorrectly". A field on the record that
    `as_row()` omits is outside the manifest digest just as surely as an unenumerated
    manifest field — the row is what gets hashed.
    """
    problems = []
    probes = (
        (ExternalRecord, ExternalRecord(store="s", object_id="o", version="v",
                                        content_hash="0" * DIGEST_HEX_LENGTH),
         "external record"),
        (Receipt, Receipt(receipt_id="r", subject_ref="x", purpose="p",
                          authority_version="v",
                          content_hash="0" * DIGEST_HEX_LENGTH), "receipt"),
    )
    for cls, probe, label in probes:
        row_keys = set(probe.as_row())
        fields = set(cls.__dataclass_fields__)
        for name in sorted(fields - row_keys):
            problems.append(
                "%s field %r is not present in as_row(), so it is outside the digest "
                "even though the class carries it (P2W-03)" % (label, name))
        for name in sorted(row_keys - fields):
            problems.append(
                "%s as_row() emits %r, which is not a field of the class — the row "
                "and the class have drifted (P2W-03)" % (label, name))
    return problems


def required_control_coverage() -> List[str]:
    """Every control the contract names must map to a real manifest field."""
    fields = set(ExternalManifest.__dataclass_fields__)
    return ["required control %r maps to field %r, which the manifest does not have"
            % (control, name)
            for control, name in sorted(REQUIRED_CONTRACT_CONTROLS.items())
            if name not in fields]


# --------------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------------

def governed_purposes(context: Optional[ActionContext],
                      policy: Optional[EvidencePolicy],
                      manifest: Optional[ExternalManifest],
                      registry: Optional[ReceiptRegistry]
                      ) -> Tuple[Tuple[str, ...], List[str]]:
    """Resolve the purposes the POLICY PLANE allows for this action (P2Y-01).

    Returns (allowed_purposes, problems). The event supplies only the four keys; the
    values come from the governed mapping. Every step fails closed, because the
    finding is precisely that a permissive default lets the action pick its own rule.

    `48_` §4.1 adds the receipt-registry authority context to this boundary. R4 could
    only see one of the two actors it had to separate the policy from, so a policy
    authored by the receipt authority resolved with `problems: []`. The authority
    context is now REQUIRED whenever external evidence is used: an absent manifest or
    an absent registry is not a reason to skip the separation check, it is a reason to
    refuse, because a check that cannot see its own inputs has not been performed.
    """
    if policy is None:
        return (), ["no action-evidence policy was supplied with the fold input — "
                    "the purposes an action may be grounded by are policy-plane data, "
                    "and their absence is not permission (P2Y-01)"]
    problems = policy.integrity_problems()
    if problems:
        return (), ["action-evidence policy unusable — %s" % p for p in problems]
    # The authority context, both halves of it, before any separation is claimed.
    # Also over-determined on the present corpus and said so out loud: this boundary is
    # only reached when the event HAS an external basis, and every such reference is
    # separately refused downstream when its manifest or its registry is missing. The
    # clause is here because `48_` §4.1 requires the separation check to fail closed
    # rather than be skipped, not because it is the only thing standing between a
    # missing registry and a fold.
    if manifest is None or registry is None:
        missing = [name for name, obj in (("external manifest", manifest),
                                          ("receipt registry", registry))
                   if obj is None]
        return (), ["external evidence is in use but the policy boundary was given no "
                    "%s, so the evidence policy cannot be shown independent of the "
                    "parties it governs — an unperformed separation check is not a "
                    "passed one (P2Y-01, 48_ §4.1)" % " and no ".join(missing)]
    if policy.authority_id == manifest.source_id:
        return (), ["the action-evidence policy is authored by %r, which is also the "
                    "manifest source — an evidence rule written by the party whose "
                    "evidence it governs is not governed (P2Y-01)" % policy.authority_id]
    if policy.authority_id == registry.authority_id:
        return (), ["the action-evidence policy is authored by %r, which is also the "
                    "receipt-registry authority — the same actor would decide which "
                    "receipt purposes authorize an action AND issue the receipts, so "
                    "the purpose comparison has one party on both sides of it "
                    "(P2Y-01, 48_ §4.1)" % policy.authority_id]
    if context is None or not str(context.action_class or "").strip():
        return (), ["the consuming event declares no action class — the governed "
                    "mapping is keyed by action class, scope, policy version and risk "
                    "class, and an event that names none cannot be governed (P2Y-01)"]
    # `48_` §4.2, the consuming half. Checked BEFORE the lookup and reported on its own
    # terms: a mismatched version would otherwise surface as "no contract for these
    # keys", which is the message for an ungoverned action class and says nothing about
    # which policy artifact the caller thought it was being judged under.
    #
    # Stated plainly, because it would otherwise read as a control doing more than it
    # does: with the first half of §4.2 enforced above, every contract in the artifact
    # carries the artifact's version, so a context asking for any other version can
    # never match a row and the lookup would refuse it anyway. This check changes the
    # REASON given, never whether it refuses. Section C3 of `run_basis.py` ships that
    # fact rather than asserting it — the R4 reconstruction, which has no such check,
    # refuses the same fixture saying "the policy holds no contract for those keys".
    if context.policy_version != policy.policy_version:
        return (), ["the consuming event asks to be governed under policy version %r; "
                    "the supplied policy artifact is version %r — the artifact in hand "
                    "is not the one the action claims governs it, and resolving it "
                    "anyway would let either side name a version nothing checks "
                    "(P2Y-01, 48_ §4.2)"
                    % (context.policy_version, policy.policy_version)]
    contract = policy.lookup(context.action_class, context.scope,
                             context.policy_version, context.risk_class)
    if contract is None:
        return (), ["the action-evidence policy holds no contract for "
                    "(action_class=%r, scope=%r, policy_version=%r, risk_class=%r) — "
                    "an ungoverned action class cannot be grounded by any evidence "
                    "(P2Y-01)" % (context.action_class, context.scope,
                                  context.policy_version, context.risk_class)]
    declared = str(context.declared_contract_id or "").strip()
    if declared and declared != contract.contract_id:
        return (), ["the consuming event names contract %r; the governed mapping for "
                    "its own keys is %r — an action cannot select the contract that "
                    "governs it (P2Y-01)" % (declared, contract.contract_id)]
    if not contract.allowed_purposes:
        return (), ["contract %r allows no evidence purpose for this action class — "
                    "nothing can ground it (P2Y-01)" % contract.contract_id]
    return tuple(contract.allowed_purposes), []


def _resolve_receipt(record: ExternalRecord, manifest: ExternalManifest,
                     registry: Optional[ReceiptRegistry],
                     required_purposes: Sequence[str] = ()) -> List[str]:
    """P2W-02 — the attestation must come from a separately controlled authority.

    Every step is a refusal the previous contract did not make:
      * the receipt is a `receipt:` reference, so it cannot name a manifest record;
      * the registry must exist, be schema-valid, and be independently bound;
      * its `authority_id` must match what the manifest declared IN ADVANCE and must
        differ from the manifest's own `source_id`;
      * the receipt must name THIS record as its subject, at this version and hash;
      * the receipt must not be revoked, and the revocation snapshot the manifest is
        bound to must be the one the registry carries.
    """
    raw = record.verification_receipt
    ref, problem = parse_receipt_reference(raw)
    if problem:
        return [problem]

    if registry is None:
        return ["record %s cites receipt %s but no receipt registry was supplied with "
                "the fold input — a same-manifest attestation is not independent "
                "evidence and there is no other source (P2W-02)" % (record.key, ref)]

    integrity = registry.integrity_problems()
    if integrity:
        return ["record %s: receipt registry unusable — %s" % (record.key, p)
                for p in integrity]

    if registry.authority_id != manifest.receipt_authority_id:
        return ["record %s: the manifest names receipt authority %r; the supplied "
                "registry is authored by %r — the authority must be the one the "
                "manifest declared before the registry was consulted (P2W-02)"
                % (record.key, manifest.receipt_authority_id, registry.authority_id)]
    if registry.authority_id == manifest.source_id:
        return ["record %s: the receipt registry and the manifest share authority %r "
                "— an attestation by the record's own author is not independent "
                "evidence (P2W-02)" % (record.key, registry.authority_id)]
    if registry.authority_version != manifest.receipt_authority_version:
        return ["record %s: the manifest binds receipt-authority version %r; the "
                "registry declares %r"
                % (record.key, manifest.receipt_authority_version,
                   registry.authority_version)]
    if registry.snapshot_id != manifest.revocation_snapshot_id:
        return ["record %s: the manifest is bound to revocation snapshot %r; the "
                "supplied registry is snapshot %r — a stale revocation list cannot "
                "answer for this manifest (P2W-03)"
                % (record.key, manifest.revocation_snapshot_id, registry.snapshot_id)]
    # P2X-01 — the CONTENT, not the label. The three identity fields above are
    # labels an author chooses; two registries can carry the same three and
    # different receipts, which is exactly what the verifier substituted.
    if registry.declared_digest != manifest.receipt_registry_digest:
        return ["record %s: the manifest is bound to receipt-registry content %s; "
                "the supplied registry's declared digest is %s — same authority, "
                "same version, same snapshot label, DIFFERENT content, so the "
                "replay is not bound to its own declared evidence basis (P2X-01)"
                % (record.key, (manifest.receipt_registry_digest or "-")[:16],
                   (registry.declared_digest or "-")[:16])]

    receipt = registry.lookup(ref)
    if receipt is None:
        return ["record %s cites receipt %s, which names no attestation in the "
                "registry (%d receipt(s))"
                % (record.key, ref, len(registry.receipts))]
    if receipt.authority_version != ref.authority_version:
        return ["record %s cites receipt %s at authority version %r; the registry "
                "records %r" % (record.key, ref.receipt_id, ref.authority_version,
                                receipt.authority_version)]
    # P2X-02 — the receipt's own authority identity must agree with the registry that
    # owns it. The reference and the receipt agreeing with each other says nothing
    # about which authority issued it: the verifier put `receipt-object-v999` on a
    # receipt inside an `ra-v1` registry and it resolved.
    if receipt.authority_version != registry.authority_version:
        return ["receipt %s declares authority version %r; the registry that holds "
                "it is %s@%r — a receipt cannot carry an authority identity its own "
                "registry does not (P2X-02)"
                % (receipt.receipt_id, receipt.authority_version,
                   registry.authority_id, registry.authority_version)]
    # P2X-02 — `content_hash` is the receipt's canonical row digest, not a value its
    # author asserts. Comparing a self-declared field against the reference that
    # cites it is two assertions agreeing, which is not integrity.
    if receipt.content_hash != receipt.row_digest():
        return ["receipt %s declares content hash %s; its canonical row hashes to "
                "%s — a self-declared content identity is not an identity (P2X-02)"
                % (receipt.receipt_id, receipt.content_hash[:16],
                   receipt.row_digest()[:16])]
    if receipt.content_hash != ref.content_hash:
        return ["record %s cites receipt %s with content hash %r; the registry "
                "records %r" % (record.key, ref.receipt_id, ref.content_hash,
                                receipt.content_hash)]
    if receipt.receipt_id in registry.revoked_receipt_ids:
        return ["record %s is attested by receipt %s, which the registry lists as "
                "REVOKED" % (record.key, receipt.receipt_id)]
    if not str(receipt.purpose or "").strip():
        return ["receipt %s declares no purpose — an attestation with no action class "
                "attests to nothing in particular (P2W-02)" % receipt.receipt_id]

    subject = reference_for(record)
    if receipt.subject_ref != subject:
        return ["receipt %s attests to %s, not to %s — a registered attestation for "
                "another record cannot certify this one (P2W-02)"
                % (receipt.receipt_id, receipt.subject_ref, subject)]

    # P2X-02 — the purpose must match the CONSUMING contract. "Nonempty" was the
    # whole check, so a `display-monthly-digest` receipt grounded a
    # `delete-production-data` action and `basis_problems` came back empty. The
    # consumer declares what evidence it needs; an undeclared consumer fails closed,
    # because a consequential action with no stated evidence requirement is the
    # case this check exists for.
    wanted = [str(p) for p in required_purposes if str(p).strip()]
    if not wanted:
        return ["record %s resolves an attestation but no governed evidence purpose "
                "applies to the consuming action — evidence cannot be matched to a "
                "use the policy plane does not describe (P2X-02, P2Y-01)" % record.key]
    if receipt.purpose not in wanted:
        return ["receipt %s attests purpose %r; the governed contract for this "
                "action permits %s — a receipt for one purpose is not evidence for a "
                "materially different one (P2X-02, P2Y-01)"
                % (receipt.receipt_id, receipt.purpose, wanted)]
    return []


def resolve(raw: str, manifest: Optional[ExternalManifest],
            declared_stores: Sequence[str],
            receipt_registry: Optional[ReceiptRegistry] = None,
            required_purposes: Sequence[str] = ()) -> List[str]:
    """Resolve ONE reference. Returns the problems; empty means it resolved.

    Order matters and is fail-closed at every step: nothing about a reference is
    accepted on the strength of a check that has not run yet.
    """
    ref, problem = parse_reference(raw)
    if problem:
        return [problem]

    problems: List[str] = []
    if ref.store not in declared_stores:
        return ["external basis %s names store %r, which is not a declared external "
                "store %s" % (ref, ref.store, list(declared_stores))]

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
    if problems:
        return problems

    if not record.verification_receipt:
        problems.append("external basis %s resolves to a record with no verification "
                        "receipt — an unverified external record is not evidence"
                        % ref)
    else:
        problems.extend("external basis %s: %s" % (ref, p)
                        for p in _resolve_receipt(record, manifest, receipt_registry,
                                                  required_purposes))
    return problems

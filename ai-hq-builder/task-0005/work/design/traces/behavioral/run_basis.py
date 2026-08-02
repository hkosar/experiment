"""Missing-basis suite — the fold must fail closed on an incomplete causal basis.

Verifier finding P2T-02. The fold's eligibility rule was

    all((ref in done) or (ref not in by_id) for ref in e.caused_by)

so a `caused_by` reference absent from the supplied event set counted as already
satisfied, and the later causal-violation check only inspected references it could
already see. The verifier's probe — a DecisionEvent naming `missing-policy-event` —
was accepted by `topological_order`, accepted by `fold`, and produced an empty
`causal_violations` list. An incomplete replay basis therefore produced authoritative
state in silence.

This suite is the shipped proof that it no longer can. Every case below is a
synthetic basis (never a corpus fixture), driven through the REAL `validate_basis`
and `fold`:

  1  the verifier's exact probe — missing direct cause
  2  missing transitive cause (the grandparent is absent)
  3  missing external receipt basis — evidence answering an action nobody delivered
  4  unknown external/genesis reference type — an `external_basis` naming no
     declared store, and a non-genesis event declaring no basis at all
  5  causal cycle
  6  duplicate event IDs
  7  store-sequence collision

Each case ships with its DEFECT WITNESS: the same basis folded with
`enforce_basis=False` reproduces the old accepting behavior. A check that cannot be
turned off has not been shown to be doing anything, so each case reports both sides.

SECTION B — EXTERNAL-BASIS RESOLUTION (verifier finding P2U-02). Section A left a
second door open, and the verifier walked through it: `validate_basis` accepted any
`external_basis` string whose prefix was one of four store names, so a non-genesis
`DecisionEvent` with no `caused_by` and `control-journal:definitely-missing` as its
sole basis folded to authoritative state with `causal_violations: []`.

Section B is the resolver contract's evidence. It ships the verifier's four exact
probe strings as failing cases, the five tests named in the required correction
(nonexistent object · wrong version · wrong content hash · omitted from the frozen
manifest · unavailable and degraded resolver), the two the contract implies
(unverified record · tampered manifest digest), and the POSITIVE case — a reference
that resolves, folds, and produces state — because a validator that refuses
everything is not a validator.

Each section-B case names the problem substring it expects, so a case that starts
failing for a DIFFERENT reason than the one it was written for is visible rather than
silently still-green.

SECTION B, ROWS ADDED IN R1 (verifier findings P2V-02 and P2V-03). The contract above
had three holes of its own, and each has its cases here: a `verification_receipt` that
was any nonempty string (six rows — arbitrary string, unregistered attestation, wrong
version, wrong content hash, self-reference, mutual cycle); a manifest digest that
covered `records` only, so `resolver_state` could be edited from `unavailable` to
`available` under a still-valid binding; and duplicate `store:object_id` identities,
where `lookup()` silently answered with whichever record came first.

Every row carries TWO counterfactuals, because there are now two previous contracts to
be measured against: `PREFIX` is the TASK-0004 store-prefix check, and `P2U CONTRACT`
re-implements the TASK-0005 rules — records-only digest, nonempty-string receipt, no
duplicate check — so each row says which cycle's defect it witnesses. The eight rows
marked `*** ACCEPTED ***` under `P2U CONTRACT` are this rework's evidence.

`digest_enumeration_guard()` is the negative control for the enumeration itself: the
list of digest-bound fields is checked mechanically against the dataclass, and the
check is shown FAILING under a dropped field and under a stale name before it is
counted as a guard.

The suite also confirms the 81 production combinations validate cleanly, so the new
gate is not passing by refusing everything.

Usage:  python3 run_basis.py [--fixtures PATH] [--out DIR]
"""

from __future__ import annotations

import argparse
import hashlib
import re
import json
import os
import sys
from typing import Dict, List, Tuple

import external_basis as extb
from events import EXTERNAL_BASIS_STORES, Event
from fixture_io import load_stimuli
from fold import BasisError, FoldError, fold, validate_basis
from simulate import Defects, simulate


def _ev(eid: str, etype: str, caused_by: Tuple[str, ...] = (),
        external_basis: Tuple[str, ...] = (), seq: int = 0,
        payload: Dict[str, object] = None, external: bool = False,
        object_key: str = "case") -> Event:
    return Event(event_id=eid, event_type=etype, partition="business",
                 object_key=object_key, store_seq=seq, caused_by=caused_by,
                 external_basis=external_basis, payload=payload or {},
                 externally_authored=external)


def _root(seq: int = 1) -> Event:
    return _ev("policy-1", "PolicyVersionEvent", seq=seq,
               payload={"version": "P1"}, object_key="policy")


# name -> (description, event list, the exact problem substring expected)
CASES: List[Tuple[str, str, List[Event], str]] = [
    (
        "missing-direct-cause",
        "the verifier's exact probe: DecisionEvent caused_by=[missing-policy-event]",
        [_ev("decision-1", "DecisionEvent", caused_by=("missing-policy-event",), seq=1)],
        "absent from the replay basis",
    ),
    (
        "missing-transitive-cause",
        "the decision's parent is present; the parent's own basis is not",
        [_root(),
         _ev("eval-1", "PolicyEvaluationRecord", caused_by=("policy-1", "ingest-missing"),
             seq=2),
         _ev("decision-1", "DecisionEvent", caused_by=("eval-1",), seq=3)],
        "ingest-missing",
    ),
    (
        "missing-external-receipt-basis",
        "an evidence record answers an ActionRequest nobody delivered",
        [_root(),
         _ev("evidence-1", "EvidenceIngestionEvent", caused_by=("policy-1",), seq=2,
             payload={"answers_action": "action-missing", "evidence_kind": "receipt"},
             external=True, object_key="evidence")],
        "answers action action-missing",
    ),
    (
        # P2U-02 changed what this case detects, and the change is recorded rather
        # than absorbed. `hearsay:some-id` used to fail the store whitelist, which was
        # the only check there was. It now fails the GRAMMAR first — it carries no
        # version and no content hash — so the store check never runs on it. The
        # store rule itself is still exercised, on a well-formed reference, by
        # section B's `undeclared-store` case. Both orderings are therefore covered:
        # malformed-and-undeclared here, well-formed-but-undeclared there.
        "unknown-external-reference-type",
        "an external_basis entry that is neither well-formed nor a declared store",
        [_root(),
         _ev("decision-1", "DecisionEvent", caused_by=("policy-1",),
             external_basis=("hearsay:some-id",), seq=2)],
        "does not parse",
    ),
    (
        "no-declared-basis-non-genesis",
        "a non-genesis event declaring no causal basis at all",
        [_root(), _ev("decision-1", "DecisionEvent", seq=2)],
        "not a declared genesis root",
    ),
    (
        "causal-cycle",
        "two canonical events naming each other",
        [_root(),
         _ev("decision-1", "DecisionEvent", caused_by=("policy-1", "decision-2"), seq=2),
         _ev("decision-2", "DecisionEvent", caused_by=("decision-1",), seq=3)],
        "causal cycle",
    ),
    (
        "duplicate-event-ids",
        "the same event ID delivered twice",
        [_root(),
         _ev("decision-1", "DecisionEvent", caused_by=("policy-1",), seq=2),
         _ev("decision-1", "DecisionEvent", caused_by=("policy-1",), seq=3)],
        "duplicate event IDs",
    ),
    (
        "store-sequence-collision",
        "two events claiming the same sequence in one store",
        [_root(),
         _ev("decision-1", "DecisionEvent", caused_by=("policy-1",), seq=7),
         _ev("decision-2", "DecisionEvent", caused_by=("policy-1",), seq=7)],
        "sequence 7 used by both",
    ),
]

# --------------------------------------------------------------------------
# Section B — external-basis resolution (P2U-02, P2V-02/03, P2W-02/03)
# --------------------------------------------------------------------------

def _h(label: str) -> str:
    """A full-length content hash for a fixture, derived from a fixed label.

    P2W-02 required a full approved digest; the previous fixtures used 8- and
    16-hex literals and the verifier resolved `deadbeef` and `cafebabe` through the
    parser. These are real 64-hex sha256 values, and each is derived from the LABEL
    of the thing it identifies, never from the record that carries it — a hash
    computed from the record would make every comparison a comparison with itself.
    """
    return hashlib.sha256(("ai-hq/fixture/" + label).encode("utf-8")).hexdigest()


# ---- the two authorities. Their separation is the contract (P2W-02) ----------
MANIFEST_SOURCE = "provider-snapshot-service"
RECEIPT_AUTHORITY = "control-plane-attestation-service"
AUTHORITY_VERSION = "auth-v4"
REVOCATION_SNAPSHOT = "rev-2026-07-31"

# The basis record the frozen manifest lists.
GOOD_RECORD = extb.ExternalRecord(
    store="control-journal", object_id="kill-cmd-77", version="v3",
    content_hash=_h("kill-cmd-77"),
    verification_receipt="receipt:att-77@%s#%s" % (AUTHORITY_VERSION, _h("att-77")))

# Its attestation, held by the OTHER authority, naming this record as its subject.
GOOD_RECEIPT = extb.Receipt(
    receipt_id="att-77", subject_ref=extb.reference_for(GOOD_RECORD),
    purpose="kill-command-delivery", authority_version=AUTHORITY_VERSION,
    content_hash=_h("att-77"))

# The verifier's P2W-02 probe, in its exact shape: an attestation that is real,
# registered and bound, but names a DIFFERENT subject.
UNRELATED_RECEIPT = extb.Receipt(
    receipt_id="att-unrelated", subject_ref="provider:something-else@v1#" + _h("else"),
    purpose="unrelated", authority_version=AUTHORITY_VERSION,
    content_hash=_h("att-unrelated"))
UNRELATED_TARGET = extb.ExternalRecord(
    store="provider", object_id="action-42", version="v7",
    content_hash=_h("action-42"),
    verification_receipt="receipt:att-unrelated@%s#%s"
                         % (AUTHORITY_VERSION, _h("att-unrelated")))

REVOKED_RECEIPT = extb.Receipt(
    receipt_id="att-revoked", subject_ref="provider:revoked-target@v1#" + _h("revoked"),
    purpose="filing", authority_version=AUTHORITY_VERSION,
    content_hash=_h("att-revoked"))
REVOKED_TARGET = extb.ExternalRecord(
    store="provider", object_id="revoked-target", version="v1",
    content_hash=_h("revoked"),
    verification_receipt="receipt:att-revoked@%s#%s"
                         % (AUTHORITY_VERSION, _h("att-revoked")))

NO_PURPOSE_RECEIPT = extb.Receipt(
    receipt_id="att-nopurpose",
    subject_ref="provider:nopurpose-target@v1#" + _h("nopurpose"),
    purpose="   ", authority_version=AUTHORITY_VERSION,
    content_hash=_h("att-nopurpose"))
NO_PURPOSE_TARGET = extb.ExternalRecord(
    store="provider", object_id="nopurpose-target", version="v1",
    content_hash=_h("nopurpose"),
    verification_receipt="receipt:att-nopurpose@%s#%s"
                         % (AUTHORITY_VERSION, _h("att-nopurpose")))

STRING_RECEIPT_RECORD = extb.ExternalRecord(
    store="control-journal", object_id="obj-str", version="v1",
    content_hash=_h("obj-str"), verification_receipt="verified-trust-me")
UNREGISTERED_RECEIPT_RECORD = extb.ExternalRecord(
    store="control-journal", object_id="obj-unreg", version="v1",
    content_hash=_h("obj-unreg"),
    verification_receipt="receipt:att-nonexistent@%s#%s"
                         % (AUTHORITY_VERSION, _h("att-nonexistent")))
WRONG_AUTHVER_RECORD = extb.ExternalRecord(
    store="control-journal", object_id="obj-ver", version="v1",
    content_hash=_h("obj-ver"),
    verification_receipt="receipt:att-77@auth-v9#%s" % _h("att-77"))
WRONG_RECEIPT_HASH_RECORD = extb.ExternalRecord(
    store="control-journal", object_id="obj-hash", version="v1",
    content_hash=_h("obj-hash"),
    verification_receipt="receipt:att-77@%s#%s" % (AUTHORITY_VERSION, "0" * 64))
# The verifier's short-hash probe: `deadbeef` as a content identity.
SHORT_HASH_RECORD = extb.ExternalRecord(
    store="provider", object_id="short-target", version="1",
    content_hash="cafebabe",
    verification_receipt="receipt:short-root@1#deadbeef")
# A receipt reference that names a MANIFEST record instead of a registry entry —
# the R1 same-manifest chain, now unconstructible by grammar.
SAME_MANIFEST_CHAIN_RECORD = extb.ExternalRecord(
    store="control-journal", object_id="obj-chain", version="v1",
    content_hash=_h("obj-chain"),
    verification_receipt="evidence:some-root@v1#" + _h("some-root"))

RECORDS = (GOOD_RECORD, UNRELATED_TARGET, REVOKED_TARGET, NO_PURPOSE_TARGET,
           STRING_RECEIPT_RECORD, UNREGISTERED_RECEIPT_RECORD, WRONG_AUTHVER_RECORD,
           WRONG_RECEIPT_HASH_RECORD, SHORT_HASH_RECORD, SAME_MANIFEST_CHAIN_RECORD)

# Known to the resolver, deliberately NOT in the frozen snapshot. This is what makes
# "omitted from the frozen manifest" a reachable state distinct from "nonexistent".
OMITTED_KEY = "evidence:exec-receipt-91"


def _manifest(**overrides):
    """A well-formed envelope with every control the P2W-03 contract requires."""
    base = dict(
        schema_version=extb.MANIFEST_SCHEMA,
        canonicalization_version=extb.CANONICALIZATION_VERSION,
        snapshot_id="snap-2026-07-31T00:00Z", snapshot_epoch="epoch-118",
        source_id=MANIFEST_SOURCE,
        creation_context="nightly external-record capture, business partition",
        record_identity_rule=extb.RECORD_IDENTITY_RULE,
        digest_algorithm=extb.DIGEST_ALGORITHM,
        digest_hex_length=extb.DIGEST_HEX_LENGTH,
        resolver_id="resolver-primary", resolver_version="r-2.1",
        resolver_state=extb.RESOLVER_AVAILABLE,
        receipt_authority_id=RECEIPT_AUTHORITY,
        receipt_authority_version=AUTHORITY_VERSION,
        receipt_verification_config="subject-bound-registry/1",
        trust_root_id=extb.TRUST_ROOT_NOT_APPLICABLE,
        trust_root_key_version=extb.TRUST_ROOT_NOT_APPLICABLE,
        revocation_snapshot_id=REVOCATION_SNAPSHOT,
        records=RECORDS, resolver_known_ids=(OMITTED_KEY,))
    base.update(overrides)
    return extb.ExternalManifest(**base)


def _registry(**overrides):
    base = dict(
        schema_version=extb.REGISTRY_SCHEMA,
        authority_id=RECEIPT_AUTHORITY, authority_version=AUTHORITY_VERSION,
        snapshot_id=REVOCATION_SNAPSHOT, digest_algorithm=extb.DIGEST_ALGORITHM,
        receipts=(GOOD_RECEIPT, UNRELATED_RECEIPT, REVOKED_RECEIPT,
                  NO_PURPOSE_RECEIPT),
        revoked_receipt_ids=("att-revoked",))
    base.update(overrides)
    return extb.ReceiptRegistry(**base)


MANIFEST = _manifest().bound()
REGISTRY = _registry().bound()

DEGRADED_MANIFEST = _manifest(resolver_state=extb.RESOLVER_DEGRADED).bound()
UNAVAILABLE_MANIFEST = _manifest(resolver_state=extb.RESOLVER_UNAVAILABLE).bound()

# A manifest whose declared digest no longer matches its contents.
TAMPERED_MANIFEST = extb.ExternalManifest(
    **dict({name: getattr(MANIFEST, name)
            for name in extb.ExternalManifest.__dataclass_fields__},
           records=RECORDS + (extb.ExternalRecord(
               store="evidence", object_id="smuggled", version="v1",
               content_hash=_h("smuggled"), verification_receipt=None),)))
# P2V-03 — the SAME records, with only the resolver state edited.
RESOLVER_TAMPERED_MANIFEST = extb.ExternalManifest(
    **dict({name: getattr(UNAVAILABLE_MANIFEST, name)
            for name in extb.ExternalManifest.__dataclass_fields__},
           resolver_state=extb.RESOLVER_AVAILABLE))
# P2W-03 — the same records and resolver state under a DIFFERENT snapshot identity.
# Under the R1 envelope this was not expressible, so the two contexts hashed alike.
SNAPSHOT_TAMPERED_MANIFEST = extb.ExternalManifest(
    **dict({name: getattr(MANIFEST, name)
            for name in extb.ExternalManifest.__dataclass_fields__},
           snapshot_id="snap-2026-01-01T00:00Z"))
# P2V-03 — one identity, two records.
DUPLICATE_IDENTITY_MANIFEST = _manifest(
    records=RECORDS + (extb.ExternalRecord(
        store="control-journal", object_id="kill-cmd-77", version="v4",
        content_hash=_h("kill-cmd-77-v4"),
        verification_receipt=GOOD_RECORD.verification_receipt),)).bound()
UNVERIFIED_MANIFEST = _manifest(
    records=(extb.ExternalRecord(store="provider", object_id="obj-5", version="v1",
                                 content_hash=_h("obj-5"),
                                 verification_receipt=None),)).bound()
# P2W-03 — envelope controls left undeclared, one at a time.
NO_SNAPSHOT_MANIFEST = _manifest(snapshot_id="").bound()
NO_AUTHORITY_MANIFEST = _manifest(receipt_authority_id="").bound()
BAD_SCHEMA_MANIFEST = _manifest(schema_version="external-basis-manifest/1").bound()
BAD_ALGORITHM_MANIFEST = _manifest(digest_algorithm="md5").bound()
# P2W-02 — the manifest naming ITSELF as its own receipt authority.
SELF_AUTHORITY_MANIFEST = _manifest(receipt_authority_id=MANIFEST_SOURCE).bound()

# ---- registries that break the independence contract -------------------------
FOREIGN_REGISTRY = _registry(authority_id="some-other-service").bound()
SAME_ACTOR_REGISTRY = _registry(authority_id=MANIFEST_SOURCE).bound()
STALE_REVOCATION_REGISTRY = _registry(snapshot_id="rev-2020-01-01").bound()
UNBOUND_REGISTRY = _registry()                       # declared_digest is None
DUPLICATE_RECEIPT_REGISTRY = _registry(
    receipts=(GOOD_RECEIPT, UNRELATED_RECEIPT, REVOKED_RECEIPT, NO_PURPOSE_RECEIPT,
              extb.Receipt(receipt_id="att-77", subject_ref="x:y@v1#" + _h("x"),
                           purpose="p", authority_version=AUTHORITY_VERSION,
                           content_hash=_h("dup")))).bound()

GOOD_REF = extb.reference_for(GOOD_RECORD)

# name -> (description, external_basis refs, manifest, registry, expected substring)
EXTERNAL_CASES: List[Tuple[str, str, Tuple[str, ...], object, object, str]] = [
    (
        "probe-control-journal",
        "the verifier's P2U-02 probe string, verbatim",
        ("control-journal:definitely-missing",), MANIFEST, REGISTRY,
        "does not parse",
    ),
    (
        "probe-evidence",
        "the verifier's P2U-02 probe string, verbatim",
        ("evidence:definitely-missing",), MANIFEST, REGISTRY,
        "does not parse",
    ),
    (
        "probe-provider",
        "the verifier's P2U-02 probe string, verbatim",
        ("provider:definitely-missing",), MANIFEST, REGISTRY,
        "does not parse",
    ),
    (
        "probe-schedule",
        "the verifier's P2U-02 probe string, verbatim",
        ("schedule:definitely-missing",), MANIFEST, REGISTRY,
        "does not parse",
    ),
    (
        "nonexistent-object",
        "well-formed reference to an object no manifest record names",
        ("control-journal:no-such-object@v1#" + _h("nope"),), MANIFEST, REGISTRY,
        "names no record in the external manifest",
    ),
    (
        "wrong-version",
        "the record exists; the reference names a different version",
        ("control-journal:kill-cmd-77@v2#" + _h("kill-cmd-77"),), MANIFEST, REGISTRY,
        "names version 'v2'; the manifest records 'v3'",
    ),
    (
        "wrong-content-hash",
        "the record exists at that version; the content hash disagrees",
        ("control-journal:kill-cmd-77@v3#" + "0" * 64,), MANIFEST, REGISTRY,
        "names content hash",
    ),
    (
        "omitted-from-frozen-manifest",
        "the resolver knows the object; the frozen snapshot does not list it",
        ("evidence:exec-receipt-91@v1#" + _h("exec-91"),), MANIFEST, REGISTRY,
        "OMITTED from the frozen external manifest",
    ),
    (
        "no-manifest-supplied",
        "an external basis with no manifest in the fold input at all",
        (GOOD_REF,), None, REGISTRY,
        "no external manifest was supplied",
    ),
    (
        "resolver-degraded",
        "the manifest declares its resolver answered from a degraded path",
        (GOOD_REF,), DEGRADED_MANIFEST, REGISTRY,
        "external resolver is degraded",
    ),
    (
        "resolver-unavailable",
        "the manifest declares its resolver could not be reached",
        (GOOD_REF,), UNAVAILABLE_MANIFEST, REGISTRY,
        "external resolver is unavailable",
    ),
    (
        "tampered-manifest",
        "a record added to the frozen snapshot after it was hash-bound",
        (GOOD_REF,), TAMPERED_MANIFEST, REGISTRY,
        "external manifest digest mismatch",
    ),
    (
        "unverified-record",
        "the reference resolves to a record carrying no verification receipt",
        ("provider:obj-5@v1#" + _h("obj-5"),), UNVERIFIED_MANIFEST, REGISTRY,
        "no verification receipt",
    ),
    (
        "undeclared-store",
        "a well-formed reference naming a store outside the P2G-11 matrix",
        ("hearsay:obj-1@v1#" + _h("obj-1"),), MANIFEST, REGISTRY,
        "not a declared external store",
    ),
    # ---- P2V-02 / P2W-02: the attestation ------------------------------------
    (
        "receipt-is-an-arbitrary-string",
        "the record attests to itself with a bare word — the P2V-02 probe",
        (extb.reference_for(STRING_RECEIPT_RECORD),), MANIFEST, REGISTRY,
        "does not parse as",
    ),
    (
        "receipt-names-a-manifest-record",
        "the R1 same-manifest chain: a receipt pointing back into the manifest. The "
        "receipt grammar names the registry, so this is unconstructible, not merely "
        "refused",
        (extb.reference_for(SAME_MANIFEST_CHAIN_RECORD),), MANIFEST, REGISTRY,
        "not a string and not a record in the manifest being attested",
    ),
    (
        "receipt-names-no-registered-attestation",
        "a well-formed receipt reference resolving to nothing in the registry",
        (extb.reference_for(UNREGISTERED_RECEIPT_RECORD),), MANIFEST, REGISTRY,
        "names no attestation in the registry",
    ),
    (
        "receipt-wrong-authority-version",
        "the attestation exists; the receipt cites another authority version",
        (extb.reference_for(WRONG_AUTHVER_RECORD),), MANIFEST, REGISTRY,
        "at authority version 'auth-v9'",
    ),
    (
        "receipt-wrong-content-hash",
        "the attestation exists; the receipt's content hash disagrees",
        (extb.reference_for(WRONG_RECEIPT_HASH_RECORD),), MANIFEST, REGISTRY,
        "with content hash",
    ),
    (
        "receipt-attests-to-another-subject",
        "the verifier's P2W-02 probe: a real, registered, bound attestation that "
        "names a DIFFERENT record as its subject",
        (extb.reference_for(UNRELATED_TARGET),), MANIFEST, REGISTRY,
        "cannot certify this one",
    ),
    (
        "receipt-revoked",
        "the attestation is registered and subject-bound, and revoked",
        (extb.reference_for(REVOKED_TARGET),), MANIFEST, REGISTRY,
        "which the registry lists as REVOKED",
    ),
    (
        "receipt-declares-no-purpose",
        "an attestation with no action class attests to nothing in particular",
        (extb.reference_for(NO_PURPOSE_TARGET),), MANIFEST, REGISTRY,
        "declares no purpose",
    ),
    (
        "abbreviated-content-hash",
        "the verifier's short-hash probe: `cafebabe` / `deadbeef` as content identity",
        ("provider:short-target@1#cafebabe",), MANIFEST, REGISTRY,
        "does not parse",
    ),
    (
        "no-receipt-registry-supplied",
        "a record citing a receipt with no registry in the fold input",
        (GOOD_REF,), MANIFEST, None,
        "no receipt registry was supplied",
    ),
    (
        "registry-from-the-wrong-authority",
        "a bound registry authored by someone the manifest did not name",
        (GOOD_REF,), MANIFEST, FOREIGN_REGISTRY,
        "must be the one the manifest declared",
    ),
    (
        "registry-authored-by-the-manifest-source",
        "the same actor authored both artifacts — structurally not independent",
        (GOOD_REF,), MANIFEST, SAME_ACTOR_REGISTRY,
        "must be the one the manifest declared",
    ),
    (
        "manifest-names-itself-as-receipt-authority",
        "the manifest declares its own source as the attestation authority",
        (GOOD_REF,), SELF_AUTHORITY_MANIFEST, SAME_ACTOR_REGISTRY,
        "names itself",
    ),
    (
        "registry-stale-revocation-snapshot",
        "a registry whose revocation snapshot is not the one the manifest is bound to",
        (GOOD_REF,), MANIFEST, STALE_REVOCATION_REGISTRY,
        "a stale revocation list cannot answer",
    ),
    (
        "registry-unbound",
        "a registry with no declared digest — a list, not a bound artifact",
        (GOOD_REF,), MANIFEST, UNBOUND_REGISTRY,
        "receipt registry declares no digest",
    ),
    (
        "registry-duplicate-receipt-ids",
        "two attestations sharing one receipt id",
        (GOOD_REF,), MANIFEST, DUPLICATE_RECEIPT_REGISTRY,
        "more than one receipt with id",
    ),
    # ---- P2W-03: the envelope -------------------------------------------------
    (
        "resolver-state-edited-under-a-valid-digest",
        "the P2V-03 probe: the same records with resolver_state edited",
        (GOOD_REF,), RESOLVER_TAMPERED_MANIFEST, REGISTRY,
        "external manifest digest mismatch",
    ),
    (
        "snapshot-identity-edited-under-a-valid-digest",
        "the P2W-03 probe: the same records and resolver state under a different "
        "snapshot identity — a context the R1 envelope could not even represent",
        (GOOD_REF,), SNAPSHOT_TAMPERED_MANIFEST, REGISTRY,
        "external manifest digest mismatch",
    ),
    (
        "duplicate-external-record-identity",
        "one store:object_id carried by two records at different versions",
        (GOOD_REF,), DUPLICATE_IDENTITY_MANIFEST, REGISTRY,
        "records for identity control-journal:kill-cmd-77",
    ),
    (
        "envelope-missing-snapshot-id",
        "a required control the contract names is left undeclared",
        (GOOD_REF,), NO_SNAPSHOT_MANIFEST, REGISTRY,
        "declares no snapshot_id",
    ),
    (
        "envelope-missing-receipt-authority",
        "the manifest declares no receipt authority at all",
        (GOOD_REF,), NO_AUTHORITY_MANIFEST, REGISTRY,
        "declares no receipt_authority_id",
    ),
    (
        "envelope-unknown-schema-version",
        "a manifest declaring a schema this validator does not approve",
        (GOOD_REF,), BAD_SCHEMA_MANIFEST, REGISTRY,
        "approved schemas are",
    ),
    (
        "envelope-unapproved-digest-algorithm",
        "a manifest declaring an algorithm outside the approved set",
        (GOOD_REF,), BAD_ALGORITHM_MANIFEST, REGISTRY,
        "approved algorithms are",
    ),
]
def _p2v_era_accepts(raw: str, manifest, registry) -> bool:
    """Would the contract THIS REWORK replaces (R1 / P2V) have accepted this?

    A faithful re-implementation of the R1 rules, so each row says which cycle's
    defect it witnesses. The R1 differences are exactly the findings: content hashes
    of any length >= 8, a receipt that resolved INSIDE the manifest, a digest over
    records + resolver state + known ids only, and no envelope controls at all.

    `registry` is accepted and ignored — R1 had no registry, and taking the argument
    keeps the call sites identical rather than special-casing them.
    """
    del registry
    m = re.match(r"^([a-z][a-z0-9-]*):([A-Za-z0-9][A-Za-z0-9._-]*)"
                 r"@([A-Za-z0-9][A-Za-z0-9._-]*)#([0-9a-f]{8,64})$", str(raw))
    if not m or manifest is None:
        return False
    store, object_id, version, content_hash = m.groups()
    if store not in EXTERNAL_BASIS_STORES:
        return False
    if manifest.resolver_state not in extb.RESOLVER_STATES:
        return False
    if manifest.declared_digest is None:
        return False
    if _p2v_digest(manifest) != _p2v_declared_digest(manifest):
        return False
    if manifest.resolver_state != extb.RESOLVER_AVAILABLE:
        return False
    # R1 had no duplicate-identity check: lookup answered with the first match.
    record = next((r for r in manifest.records
                   if r.store == store and r.object_id == object_id), None)
    if record is None or record.version != version \
            or record.content_hash != content_hash:
        return False
    # R1's receipt rule: parse as a MANIFEST reference and resolve in the manifest,
    # matching version and hash. No subject binding, no authority, no revocation.
    if not record.verification_receipt:
        return False
    rm = re.match(r"^([a-z][a-z0-9-]*):([A-Za-z0-9][A-Za-z0-9._-]*)"
                  r"@([A-Za-z0-9][A-Za-z0-9._-]*)#([0-9a-f]{8,64})$",
                  str(record.verification_receipt))
    if not rm:
        return False
    rstore, rid, rver, rhash = rm.groups()
    att = next((r for r in manifest.records
                if r.store == rstore and r.object_id == rid), None)
    return bool(att and att.version == rver and att.content_hash == rhash
                and att.key != record.key)


def _p2v_digest(manifest) -> str:
    """The R1 digest: records + resolver_known_ids + resolver_state."""
    payload = {
        "records": [r.as_row() for r in
                    sorted(manifest.records, key=lambda r: (r.store, r.object_id))],
        "resolver_known_ids": sorted(manifest.resolver_known_ids),
        "resolver_state": manifest.resolver_state,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _p2v_declared_digest(manifest) -> str:
    """What each manifest's `declared_digest` WOULD have been in the R1 world.

    The deliberately-stale manifests carry a digest minted from a DIFFERENT manifest,
    and the counterfactual has to mint theirs from the same origin or it is not the
    same experiment — the mistake this function's R1 ancestor made on its first draft.
    """
    if manifest is TAMPERED_MANIFEST:
        return _p2v_digest(MANIFEST)
    if manifest is RESOLVER_TAMPERED_MANIFEST:
        return _p2v_digest(UNAVAILABLE_MANIFEST)
    if manifest is SNAPSHOT_TAMPERED_MANIFEST:
        # R1 could not represent a snapshot id, so editing it changed nothing the
        # digest saw: the R1 binding stays valid. That IS the P2W-03 finding.
        return _p2v_digest(MANIFEST)
    return _p2v_digest(manifest)


def _external_events(refs: Tuple[str, ...]) -> List[Event]:
    """The verifier's exact shape: one non-genesis DecisionEvent, no `caused_by`."""
    return [_ev("decision-ext", "DecisionEvent", external_basis=refs, seq=1)]


def external_basis_cases() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for name, description, refs, manifest, registry, expect in EXTERNAL_CASES:
        events = _external_events(refs)
        problems = validate_basis(events, external_manifest=manifest,
                                  receipt_registry=registry)
        detected = any(expect in p for p in problems)

        refused = False
        try:
            fold(events, shape="S1", case_id="extb-" + name,
                 external_manifest=manifest, receipt_registry=registry)
        except FoldError:
            refused = True

        # The defect witness for this section is the PREVIOUS contract, not a switch:
        # the old check accepted any entry whose colon-prefix was a declared store.
        # Reproduced here so each row shows what used to happen to it.
        prefix = str(refs[0]).split(":", 1)[0]
        old_accepted = prefix in ("control-journal", "evidence", "provider", "schedule")

        rows.append({
            "case": name, "description": description,
            "references": list(refs),
            "manifest": "none" if manifest is None else (
                "%s resolver, %d record(s), snapshot %s, digest %s"
                % (manifest.resolver_state, len(manifest.records),
                   manifest.snapshot_id or "-",
                   (manifest.declared_digest or "-")[:12])),
            "registry": "none" if registry is None else (
                "authority %s@%s, %d receipt(s), revocation snapshot %s"
                % (registry.authority_id, registry.authority_version,
                   len(registry.receipts), registry.snapshot_id)),
            "expected_problem": expect,
            "problems": problems,
            "detected": detected,
            "fold_refused": refused,
            "accepted_by_the_prefix_check_this_replaces": old_accepted,
            "closed": detected and refused,
        })
    return rows


def r1_contract_witnesses() -> Dict[str, object]:
    """Section C — `38A_`'s probes in the shape the verifier BUILT them, run under
    both contracts.

    The per-row "would R1 have accepted this?" column that R1 itself introduced does
    not work here, and the reason is worth stating rather than quietly dropping: the
    R2 fixtures are not expressible in the R1 contract. A receipt is now a
    `receipt:` reference into a separate registry, and R1 had no registry — so every
    new row comes back "R1 rejected", which is true and completely uninformative.

    So the witnesses are the verifier's own probes, reconstructed in their original
    R1 shape, each run through the R1 rule (which must ACCEPT) and through the
    shipped contract (which must REFUSE). That is the comparison the finding is
    about.
    """
    aaaa = "a" * 64
    bbbb = "b" * 64

    # 38A_/P2W-02: an unrelated root, in the same manifest, certifying the target.
    target = extb.ExternalRecord(store="provider", object_id="action-42", version="7",
                                 content_hash=aaaa,
                                 verification_receipt="evidence:unrelated-root@1#" + bbbb)
    root = extb.ExternalRecord(store="evidence", object_id="unrelated-root",
                               version="1", content_hash=bbbb,
                               verification_receipt=None)
    same_manifest = _manifest(records=(target, root)).bound()

    # 38A_/P2W-02: `cafebabe` / `deadbeef` as content identity.
    short_target = extb.ExternalRecord(store="provider", object_id="short-target",
                                       version="1", content_hash="cafebabe",
                                       verification_receipt="evidence:short-root@1#deadbeef")
    short_root = extb.ExternalRecord(store="evidence", object_id="short-root",
                                     version="1", content_hash="deadbeef",
                                     verification_receipt=None)
    short_manifest = _manifest(records=(short_target, short_root)).bound()

    rows: List[Dict[str, object]] = []
    for name, ref, manifest, description in (
            ("unrelated-root-certifies-target", extb.reference_for(target),
             same_manifest,
             "38A_/P2W-02: `integrity_problems: []`, `fold accepted: true`"),
            ("abbreviated-content-hash", "provider:short-target@1#cafebabe",
             short_manifest,
             "38A_/P2W-02 short-hash probe: 8-hex values resolved"),
    ):
        r1 = _p2v_era_accepts(ref, manifest, None)
        now = validate_basis(_external_events((ref,)), external_manifest=manifest,
                             receipt_registry=REGISTRY)
        rows.append({"probe": name, "description": description, "reference": ref,
                     "r1_contract_accepted": r1, "problems_now": now,
                     "refused_now": bool(now),
                     "witnesses_the_finding": bool(r1) and bool(now)})

    # 38A_/P2W-03: two semantically different snapshot contexts, same rows.
    ctx_a = _manifest(snapshot_id="snap-A", snapshot_epoch="epoch-1").bound()
    ctx_b = _manifest(snapshot_id="snap-B", snapshot_epoch="epoch-2").bound()
    rows.append({
        "probe": "same-rows-different-snapshot-context",
        "description": "38A_/P2W-03: `same_records_same_digest: true` — the R1 "
                       "envelope could not represent a snapshot identity, so two "
                       "contexts hashed alike NECESSARILY",
        "reference": "-",
        "r1_contract_accepted": _p2v_digest(ctx_a) == _p2v_digest(ctx_b),
        "problems_now": ["digests differ: %s vs %s"
                         % (ctx_a.declared_digest[:16], ctx_b.declared_digest[:16])],
        "refused_now": ctx_a.declared_digest != ctx_b.declared_digest,
        "witnesses_the_finding":
            _p2v_digest(ctx_a) == _p2v_digest(ctx_b)
            and ctx_a.declared_digest != ctx_b.declared_digest,
    })

    return {"probes": rows,
            "all_witness": all(r["witnesses_the_finding"] for r in rows),
            "not_witnessing": [r["probe"] for r in rows
                               if not r["witnesses_the_finding"]]}


def digest_enumeration_guard() -> Dict[str, object]:
    """P2V-03 / P2W-03 — the enumerations that decide what is bound are themselves
    checked, and the checks are OBSERVED failing before they count as guards.

    Four witnesses, each a temporary edit restored in `finally`:
      manifest-undeclared   a real manifest field removed from both lists — it could
                            then be edited without invalidating the digest;
      manifest-stale        a name in the enumeration that is not a field — the
                            enumeration and the hash have drifted, and
                            `computed_digest()` refuses to produce a value;
      registry-undeclared   the same, for the receipt registry, which is a second
                            independently bound artifact with its own enumeration;
      contract-control      a REQUIRED CONTRACT CONTROL pointed at a field the
                            manifest does not have. This is the verifier's exact
                            P2W-03 gap: the field-coverage guard "does not prove that
                            the manifest declares all fields the accepted contract
                            requires".

    Plus a static check with no edit: every field of `ExternalRecord` and `Receipt`
    must appear in its `as_row()`, since the row is what gets hashed — the other half
    of the same gap.
    """
    rows: List[Dict[str, object]] = []

    def record(case, problems, expect_problem, extra=None):
        row = {"case": case, "problems": problems, "expect_problem": expect_problem}
        if extra is not None:
            row["computed_digest_refused"] = extra
        rows.append(row)

    record("live manifest enumeration", extb._check_digest_field_coverage(), False)
    record("live registry enumeration", extb._check_registry_field_coverage(), False)
    record("live required-control map", extb.required_control_coverage(), False)
    record("live record/receipt as_row coverage", extb._check_record_row_coverage(),
           False)

    saved = extb.DIGEST_BOUND_FIELDS
    try:
        extb.DIGEST_BOUND_FIELDS = tuple(f for f in saved if f != "resolver_state")
        record("manifest control dropped from the enumeration",
               extb._check_digest_field_coverage(), True)
        extb.DIGEST_BOUND_FIELDS = saved + ("not_a_manifest_field",)
        problems = extb._check_digest_field_coverage()
        try:
            _manifest().computed_digest()
            refused = None
        except AssertionError as exc:
            refused = str(exc)
        record("manifest enumeration names a field that does not exist",
               problems, True, refused)
    finally:
        extb.DIGEST_BOUND_FIELDS = saved

    saved_reg = extb.REGISTRY_DIGEST_BOUND_FIELDS
    try:
        extb.REGISTRY_DIGEST_BOUND_FIELDS = tuple(
            f for f in saved_reg if f != "revoked_receipt_ids")
        record("registry control dropped from the enumeration",
               extb._check_registry_field_coverage(), True)
    finally:
        extb.REGISTRY_DIGEST_BOUND_FIELDS = saved_reg

    saved_controls = dict(extb.REQUIRED_CONTRACT_CONTROLS)
    try:
        extb.REQUIRED_CONTRACT_CONTROLS["a control nobody implemented"] = "absent_field"
        record("required contract control maps to no manifest field",
               extb.required_control_coverage(), True)
    finally:
        extb.REQUIRED_CONTRACT_CONTROLS.clear()
        extb.REQUIRED_CONTRACT_CONTROLS.update(saved_controls)

    ok = all(bool(r["problems"]) == r["expect_problem"] for r in rows)
    digest_refused = any(r.get("computed_digest_refused") for r in rows)
    return {
        "manifest_bound_fields": list(saved),
        "manifest_exempt_fields": dict(extb.DIGEST_EXEMPT_FIELDS),
        "manifest_fields": sorted(extb.ExternalManifest.__dataclass_fields__),
        "registry_bound_fields": list(saved_reg),
        "registry_fields": sorted(extb.ReceiptRegistry.__dataclass_fields__),
        "required_contract_controls": dict(saved_controls),
        "rows": rows,
        "guard_discriminates": ok and digest_refused,
    }


def external_basis_positive() -> Dict[str, object]:
    """A reference that RESOLVES must fold and produce state.

    Without this the section proves only that the validator can say no. The event set
    is the same shape as every failing case above — one non-genesis DecisionEvent
    whose entire basis is external — so the single difference between folding and
    refusing is whether the reference resolves.
    """
    events = _external_events((GOOD_REF,))
    problems = validate_basis(events, external_manifest=MANIFEST,
                              receipt_registry=REGISTRY)
    folded = None
    error = None
    try:
        st = fold(events, shape="S1", case_id="extb-positive",
                  external_manifest=MANIFEST, receipt_registry=REGISTRY)
        folded = {"order": list(st.order),
                  "causal_violations": list(st.causal_violations),
                  "canonical_records": len(st.canonical)}
    except FoldError as exc:
        error = str(exc)
    return {
        "reference": GOOD_REF,
        "manifest_digest": MANIFEST.declared_digest,
        "manifest_source_id": MANIFEST.source_id,
        "manifest_records": MANIFEST.keys(),
        "registry_authority_id": REGISTRY.authority_id,
        "registry_digest": REGISTRY.declared_digest,
        "attestation": {"receipt_id": GOOD_RECEIPT.receipt_id,
                        "subject_ref": GOOD_RECEIPT.subject_ref,
                        "purpose": GOOD_RECEIPT.purpose},
        "authorities_are_distinct": MANIFEST.source_id != REGISTRY.authority_id,
        "problems": problems,
        "folded": folded,
        "error": error,
        "resolved_and_folded": not problems and folded is not None
        and not folded["causal_violations"]
        and MANIFEST.source_id != REGISTRY.authority_id,
    }


def run(fixtures_path: str, out_dir: str) -> Dict[str, object]:
    rows: List[Dict[str, object]] = []
    for name, description, events, expect in CASES:
        problems = validate_basis(events)
        detected = any(expect in p for p in problems)

        refused = False
        try:
            fold(events, shape="S1", case_id="basis-" + name)
        except BasisError:
            refused = True
        except FoldError:
            refused = True

        # The defect witness. Two independent layers now reject an incomplete basis:
        # the preflight validator, and `topological_order`'s eligibility rule (which
        # no longer treats an unresolvable reference as satisfied). Turning BOTH off
        # reproduces the behavior the verifier recorded — accepted, folded, and
        # `causal_violations = []` — which is what makes the fix falsifiable rather
        # than asserted. The middle row reports whether the second layer alone still
        # catches it, so the depth of the defense is visible instead of claimed.
        try:
            fold(events, shape="S1", case_id="basis-" + name + "-w1",
                 enforce_basis=False, enforce_receipt_ownership=False)
            second_layer = "accepted"
        except FoldError:
            second_layer = "rejected by the topological sort"

        try:
            st = fold(events, shape="S1", case_id="basis-" + name + "-w2",
                      enforce_basis=False, enforce_causality=False,
                      enforce_receipt_ownership=False)
            witness = ("old behavior reproduced: folded, causal_violations=%d"
                       % len(st.causal_violations))
            witness_ok = True
        except FoldError as exc:
            witness = "not reproducible with both checks off: %s" % str(exc)[:60]
            witness_ok = False

        rows.append({
            "case": name, "description": description,
            "expected_problem": expect,
            "problems": problems,
            "detected": detected,
            "fold_refused": refused,
            "defect_witness": witness,
            "second_layer_alone": second_layer,
            "witness_reproduces_old_behavior": witness_ok,
            "closed": detected and refused,
        })

    stimuli = load_stimuli(fixtures_path)
    production_problems: Dict[str, List[str]] = {}
    for stim in stimuli:
        for shape in ("S1", "S2", "S3"):
            res = simulate(stim, shape, Defects())
            probs = validate_basis(res.events)
            if probs:
                production_problems["%s/%s" % (stim.id, shape)] = probs

    ext_rows = external_basis_cases()
    ext_positive = external_basis_positive()
    ext_guard = digest_enumeration_guard()
    ext_r1 = r1_contract_witnesses()

    payload = {
        "summary": {
            "cases": len(rows),
            "closed": sum(1 for r in rows if r["closed"]),
            "open": [r["case"] for r in rows if not r["closed"]],
            "witnesses_reproducing_old_behavior":
                sum(1 for r in rows if r["witness_reproduces_old_behavior"]),
            "external_cases": len(ext_rows),
            "external_closed": sum(1 for r in ext_rows if r["closed"]),
            "external_open": [r["case"] for r in ext_rows if not r["closed"]],
            "external_accepted_by_the_prefix_check_this_replaces":
                sum(1 for r in ext_rows
                    if r["accepted_by_the_prefix_check_this_replaces"]),
            "external_positive_resolves": ext_positive["resolved_and_folded"],
            "digest_enumeration_guard_discriminates":
                ext_guard["guard_discriminates"],
            "r1_contract_witnesses_all_witness": ext_r1["all_witness"],
            "r1_contract_witnesses_not_witnessing": ext_r1["not_witnessing"],
            "production_combinations_validated": len(stimuli) * 3,
            "production_basis_problems": production_problems,
        },
        "cases": rows,
        "external_basis_cases": ext_rows,
        "external_basis_positive": ext_positive,
        "digest_enumeration_guard": ext_guard,
        "r1_contract_witnesses": ext_r1,
        "external_reference_grammar": extb.REFERENCE_GRAMMAR,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "basis_validation.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return payload


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures",
                    default=os.path.join("..", "..", "..", "03F_Replay_Fixtures.json"))
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)

    payload = run(args.fixtures, args.out)
    s = payload["summary"]

    print("TASK-0004 missing-basis suite (P2T-02)")
    print("  %-32s %-8s %-8s %-30s %s"
          % ("CASE", "DETECT", "REFUSE", "SECOND LAYER ALONE", "BOTH CHECKS OFF"))
    for r in payload["cases"]:
        print("  %-32s %-8s %-8s %-30s %s" % (
            r["case"], r["detected"], r["fold_refused"],
            r["second_layer_alone"], r["defect_witness"][:44]))
    print("  closed: %d / %d" % (s["closed"], s["cases"]))
    if s["open"]:
        print("  *** OPEN: %s ***" % ", ".join(s["open"]))

    print()
    print("TASK-0005 external-basis resolution (P2U-02)")
    print("  reference grammar: %s" % payload["external_reference_grammar"])
    print("  %-46s %-7s %-7s %s"
          % ("CASE", "DETECT", "REFUSE", "PREFIX CHECK"))
    for r in payload["external_basis_cases"]:
        print("  %-46s %-7s %-7s %s"
              % (r["case"], r["detected"], r["fold_refused"],
                 "accepted" if r["accepted_by_the_prefix_check_this_replaces"]
                 else "rejected"))
    print("  closed: %d / %d" % (s["external_closed"], s["external_cases"]))
    if s["external_open"]:
        print("  *** OPEN: %s ***" % ", ".join(s["external_open"]))
    print("  %d of these %d references were ACCEPTED by the prefix check TASK-0005 "
          "replaced" % (s["external_accepted_by_the_prefix_check_this_replaces"],
                        s["external_cases"]))
    print()
    print("C. R1-CONTRACT WITNESSES — 38A_'s probes in the shape the verifier built")
    print("   them, under both contracts. R1 must ACCEPT and the shipped contract")
    print("   must REFUSE, or the row witnesses nothing.")
    print("   %-38s %-12s %s" % ("PROBE", "R1 ACCEPTS", "REFUSED NOW"))
    for r in payload["r1_contract_witnesses"]["probes"]:
        print("   %-38s %-12s %s%s"
              % (r["probe"], r["r1_contract_accepted"], r["refused_now"],
                 "" if r["witnesses_the_finding"] else "   *** NOT A WITNESS ***"))
        print("      %s" % r["description"])

    print()
    g = payload["digest_enumeration_guard"]
    print("  manifest digest binds %d field(s); registry binds %d; the contract names "
          "%d required controls"
          % (len(g["manifest_bound_fields"]), len(g["registry_bound_fields"]),
             len(g["required_contract_controls"])))
    for r in g["rows"]:
        print("    %-46s %s"
              % (r["case"], (r["problems"][0][:58] if r["problems"] else "clean")))
    print("    enumeration guard discriminates: %s%s"
          % (g["guard_discriminates"],
             "" if g["guard_discriminates"] else "   *** NO ***"))
    p = payload["external_basis_positive"]
    print("  positive case  : %s" % p["reference"])
    print("    manifest     : %d record(s) %s, digest %s"
          % (len(p["manifest_records"]), p["manifest_records"],
             (p["manifest_digest"] or "-")[:16]))
    print("    resolves and folds: %s%s"
          % (p["resolved_and_folded"],
             "" if p["resolved_and_folded"]
             else "   *** the validator refuses everything: %s ***"
             % (p["problems"] or p["error"])))

    print()
    print("  production combinations validated : %d" % s["production_combinations_validated"])
    if s["production_basis_problems"]:
        print("  *** production basis problems: %s ***"
              % json.dumps(s["production_basis_problems"])[:300])
    else:
        print("  production basis problems         : none — the check is fail-closed, "
              "not refuse-everything")

    ok = (not s["open"] and not s["production_basis_problems"]
          and not s["external_open"] and bool(s["external_positive_resolves"])
          and bool(s["digest_enumeration_guard_discriminates"])
          and bool(s["r1_contract_witnesses_all_witness"]))
    print()
    print("MISSING-BASIS SUITE %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

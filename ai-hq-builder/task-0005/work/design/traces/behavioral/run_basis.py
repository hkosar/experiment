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
# Section B — external-basis resolution (P2U-02)
# --------------------------------------------------------------------------

# The attestation the frozen manifest holds. It carries no receipt of its own: it is
# the root of the chain, and requiring IT to be attested would not terminate.
ATTESTATION = extb.ExternalRecord(
    store="evidence", object_id="ctrl-receipt-77", version="v1",
    content_hash="cafebabe1234", verification_receipt=None)

# The one basis record the frozen manifest lists. Hashes are fixed literals, not
# digests of anything computed here: a self-consistent fixture would let a
# hash-comparison bug pass by comparing a value to itself.
#
# P2V-02 — `verification_receipt` used to read "ctrl-receipt-77", a bare string that
# named nothing and was accepted because it was nonempty. It is now a REFERENCE that
# resolves to ATTESTATION above, in the same manifest, at a matching version and hash.
GOOD_RECORD = extb.ExternalRecord(
    store="control-journal", object_id="kill-cmd-77", version="v3",
    content_hash="4f1c2ab9de3057c6",
    verification_receipt=extb.reference_for(ATTESTATION))

# Known to the resolver, deliberately NOT in the frozen snapshot. This is what makes
# "omitted from the frozen manifest" a reachable state distinct from "nonexistent".
OMITTED_KEY = "evidence:exec-receipt-91"

BASE_RECORDS = (GOOD_RECORD, ATTESTATION)

MANIFEST = extb.ExternalManifest(
    records=BASE_RECORDS,
    resolver_known_ids=(OMITTED_KEY,),
    resolver_state=extb.RESOLVER_AVAILABLE).bound()

DEGRADED_MANIFEST = extb.ExternalManifest(
    records=BASE_RECORDS, resolver_state=extb.RESOLVER_DEGRADED).bound()
UNAVAILABLE_MANIFEST = extb.ExternalManifest(
    records=BASE_RECORDS, resolver_state=extb.RESOLVER_UNAVAILABLE).bound()
# A manifest whose declared digest no longer matches its contents: the frozen
# snapshot was altered after it was bound.
TAMPERED_MANIFEST = extb.ExternalManifest(
    records=BASE_RECORDS + (
        extb.ExternalRecord(store="evidence", object_id="smuggled", version="v1",
                            content_hash="00000000", verification_receipt=None),),
    resolver_state=extb.RESOLVER_AVAILABLE,
    declared_digest=MANIFEST.declared_digest)
# P2V-03 — the SAME records, with only the resolver state edited. Under the previous
# digest (records only) this verified: the fail-closed control could be turned off
# without invalidating the binding. It is inside the digest now.
RESOLVER_TAMPERED_MANIFEST = extb.ExternalManifest(
    records=UNAVAILABLE_MANIFEST.records,
    resolver_known_ids=UNAVAILABLE_MANIFEST.resolver_known_ids,
    resolver_state=extb.RESOLVER_AVAILABLE,
    declared_digest=UNAVAILABLE_MANIFEST.declared_digest)
# P2V-03 — one identity, two records. `lookup()` returned whichever came first.
DUPLICATE_IDENTITY_MANIFEST = extb.ExternalManifest(
    records=BASE_RECORDS + (
        extb.ExternalRecord(store="control-journal", object_id="kill-cmd-77",
                            version="v4", content_hash="9999999999999999",
                            verification_receipt=extb.reference_for(ATTESTATION)),),
    resolver_state=extb.RESOLVER_AVAILABLE).bound()
UNVERIFIED_MANIFEST = extb.ExternalManifest(
    records=(extb.ExternalRecord(store="provider", object_id="obj-5", version="v1",
                                 content_hash="aa11bb22", verification_receipt=None),),
    resolver_state=extb.RESOLVER_AVAILABLE).bound()

# ---- P2V-02 receipt manifests -------------------------------------------------
def _rec(object_id, content_hash, receipt, store="evidence", version="v1"):
    return extb.ExternalRecord(store=store, object_id=object_id, version=version,
                               content_hash=content_hash,
                               verification_receipt=receipt)

STRING_RECEIPT = _rec("obj-str", "1111111111111111", "verified-trust-me",
                      store="control-journal")
UNREGISTERED_RECEIPT = _rec("obj-unreg", "2222222222222222",
                            "evidence:no-such-attestation@v1#3333333333333333",
                            store="control-journal")
WRONG_VERSION_RECEIPT = _rec("obj-ver", "4444444444444444",
                             "evidence:ctrl-receipt-77@v9#cafebabe1234",
                             store="control-journal")
WRONG_HASH_RECEIPT = _rec("obj-hash", "5555555555555555",
                          "evidence:ctrl-receipt-77@v1#0000000000000000",
                          store="control-journal")
SELF_RECEIPT = _rec("obj-self", "6666666666666666",
                    "evidence:obj-self@v1#6666666666666666")
CYCLE_A = _rec("cyc-a", "7777777777777777", "evidence:cyc-b@v1#8888888888888888")
CYCLE_B = _rec("cyc-b", "8888888888888888", "evidence:cyc-a@v1#7777777777777777")

RECEIPT_MANIFEST = extb.ExternalManifest(
    records=(ATTESTATION, STRING_RECEIPT, UNREGISTERED_RECEIPT,
             WRONG_VERSION_RECEIPT, WRONG_HASH_RECEIPT, SELF_RECEIPT,
             CYCLE_A, CYCLE_B),
    resolver_state=extb.RESOLVER_AVAILABLE).bound()

GOOD_REF = extb.reference_for(GOOD_RECORD)

# name -> (description, external_basis refs, manifest, expected problem substring)
# `manifest is None` means the fold input carried no manifest at all.
EXTERNAL_CASES: List[Tuple[str, str, Tuple[str, ...], object, str]] = [
    (
        "probe-control-journal",
        "the verifier's probe string, verbatim",
        ("control-journal:definitely-missing",), MANIFEST,
        "does not parse",
    ),
    (
        "probe-evidence",
        "the verifier's probe string, verbatim",
        ("evidence:definitely-missing",), MANIFEST,
        "does not parse",
    ),
    (
        "probe-provider",
        "the verifier's probe string, verbatim",
        ("provider:definitely-missing",), MANIFEST,
        "does not parse",
    ),
    (
        "probe-schedule",
        "the verifier's probe string, verbatim",
        ("schedule:definitely-missing",), MANIFEST,
        "does not parse",
    ),
    (
        "nonexistent-object",
        "well-formed reference to an object no manifest record names",
        ("control-journal:no-such-object@v1#deadbeef01",), MANIFEST,
        "names no record in the external manifest",
    ),
    (
        "wrong-version",
        "the record exists; the reference names a different version",
        ("control-journal:kill-cmd-77@v2#4f1c2ab9de3057c6",), MANIFEST,
        "names version 'v2'; the manifest records 'v3'",
    ),
    (
        "wrong-content-hash",
        "the record exists at that version; the content hash disagrees",
        ("control-journal:kill-cmd-77@v3#0000000000000000",), MANIFEST,
        "names content hash '0000000000000000'",
    ),
    (
        "omitted-from-frozen-manifest",
        "the resolver knows the object; the frozen snapshot does not list it",
        ("evidence:exec-receipt-91@v1#123456789abc",), MANIFEST,
        "OMITTED from the frozen external manifest",
    ),
    (
        "no-manifest-supplied",
        "an external basis with no manifest in the fold input at all",
        (GOOD_REF,), None,
        "no external manifest was supplied",
    ),
    (
        "resolver-degraded",
        "the manifest declares its resolver answered from a degraded path",
        (GOOD_REF,), DEGRADED_MANIFEST,
        "external resolver is degraded",
    ),
    (
        "resolver-unavailable",
        "the manifest declares its resolver could not be reached",
        (GOOD_REF,), UNAVAILABLE_MANIFEST,
        "external resolver is unavailable",
    ),
    (
        "tampered-manifest",
        "a record added to the frozen snapshot after it was hash-bound",
        (GOOD_REF,), TAMPERED_MANIFEST,
        "external manifest digest mismatch",
    ),
    (
        "unverified-record",
        "the reference resolves to a record carrying no verification receipt",
        ("provider:obj-5@v1#aa11bb22",), UNVERIFIED_MANIFEST,
        "no verification receipt",
    ),
    (
        "undeclared-store",
        "a well-formed reference naming a store outside the P2G-11 matrix",
        ("hearsay:obj-1@v1#aabbccdd",), MANIFEST,
        "not a declared external store",
    ),
    # ---- P2V-02: the verification receipt is itself a resolved reference ------
    (
        "receipt-is-an-arbitrary-string",
        "the record attests to itself with a bare word — the verifier's P2V-02 probe",
        (extb.reference_for(STRING_RECEIPT),), RECEIPT_MANIFEST,
        "is not a reference in the form",
    ),
    (
        "receipt-names-no-registered-record",
        "a well-formed receipt reference resolving to nothing in the manifest",
        (extb.reference_for(UNREGISTERED_RECEIPT),), RECEIPT_MANIFEST,
        "names no record in the external manifest",
    ),
    (
        "receipt-wrong-version",
        "the attestation exists; the receipt cites another version of it",
        (extb.reference_for(WRONG_VERSION_RECEIPT),), RECEIPT_MANIFEST,
        "cites verification receipt evidence:ctrl-receipt-77 at version 'v9'",
    ),
    (
        "receipt-wrong-content-hash",
        "the attestation exists at that version; the receipt's hash disagrees",
        (extb.reference_for(WRONG_HASH_RECEIPT),), RECEIPT_MANIFEST,
        "with content hash '0000000000000000'",
    ),
    (
        "receipt-self-referential",
        "a record naming itself as its own attestation",
        (extb.reference_for(SELF_RECEIPT),), RECEIPT_MANIFEST,
        "verification receipt cycle",
    ),
    (
        "receipt-mutual-cycle",
        "two records vouching for each other",
        (extb.reference_for(CYCLE_A),), RECEIPT_MANIFEST,
        "verification receipt cycle",
    ),
    # ---- P2V-03: the digest binds the controls; identities are unique ---------
    (
        "resolver-state-edited-under-a-valid-digest",
        "the same records with resolver_state edited unavailable -> available; the "
        "verifier's P2V-03 probe, and the previous digest verified it",
        (GOOD_REF,), RESOLVER_TAMPERED_MANIFEST,
        "external manifest digest mismatch",
    ),
    (
        "duplicate-external-record-identity",
        "one store:object_id carried by two records at different versions",
        (GOOD_REF,), DUPLICATE_IDENTITY_MANIFEST,
        "records for identity control-journal:kill-cmd-77",
    ),
]


def _p2u_records_digest(records) -> str:
    """The TASK-0005 digest: `records` and nothing else."""
    blob = json.dumps(
        [r.as_row() for r in sorted(records, key=lambda r: (r.store, r.object_id))],
        sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _p2u_declared_digest(manifest) -> str:
    """What each manifest's `declared_digest` WOULD have been in the P2U world.

    This matters and the first version of this function got it wrong. Every manifest
    above is bound with the CURRENT digest, so comparing a records-only digest against
    it reports a mismatch for every case — including the two that are supposed to
    witness the finding, which then read as "the old contract caught this too". They
    did not.

    In the P2U world `bound()` set `declared_digest` to the records-only digest, so a
    legitimately bound manifest carried that. The two deliberately-stale manifests
    carried a digest minted from a DIFFERENT manifest, and the counterfactual has to
    mint theirs from the same origin, or it is not the same experiment.
    """
    if manifest is TAMPERED_MANIFEST:
        return _p2u_records_digest(BASE_RECORDS)          # minted before the extra record
    if manifest is RESOLVER_TAMPERED_MANIFEST:
        return _p2u_records_digest(UNAVAILABLE_MANIFEST.records)
    return _p2u_records_digest(manifest.records)          # legitimately bound


def _p2u_era_accepts(raw: str, manifest) -> bool:
    """Would the contract THIS REWORK replaces have accepted this reference?

    A faithful re-implementation of the TASK-0005 checks, in one place, so each
    section-B row can say which cycle's defect it witnesses. The three differences
    are exactly the three findings: the digest covered `records` only, a
    `verification_receipt` was any nonempty string, and duplicate record identities
    were not looked for.

    Reproducing the old rule here rather than keeping a switch inside
    `external_basis` is deliberate — P2V-01 was a disable path shipped in production
    code, and the lesson generalises past the file it was found in.
    """
    ref, problem = extb.parse_reference(raw)
    if problem or ref.store not in EXTERNAL_BASIS_STORES or manifest is None:
        return False
    if manifest.resolver_state not in extb.RESOLVER_STATES:
        return False
    if manifest.declared_digest is None:
        return False
    if _p2u_records_digest(manifest.records) != _p2u_declared_digest(manifest):
        return False
    if manifest.resolver_state != extb.RESOLVER_AVAILABLE:
        return False
    record = manifest.lookup(ref)
    if record is None or record.version != ref.version \
            or record.content_hash != ref.content_hash:
        return False
    return bool(record.verification_receipt)


def _external_events(refs: Tuple[str, ...]) -> List[Event]:
    """The verifier's exact shape: one non-genesis DecisionEvent, no `caused_by`."""
    return [_ev("decision-ext", "DecisionEvent", external_basis=refs, seq=1)]


def external_basis_cases() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for name, description, refs, manifest, expect in EXTERNAL_CASES:
        events = _external_events(refs)
        problems = validate_basis(events, external_manifest=manifest)
        detected = any(expect in p for p in problems)

        refused = False
        try:
            fold(events, shape="S1", case_id="extb-" + name,
                 external_manifest=manifest)
        except FoldError:
            refused = True

        # The defect witness for this section is the PREVIOUS contract, not a switch:
        # the old check accepted any entry whose colon-prefix was a declared store.
        # Reproduced here so each row shows what used to happen to it.
        prefix = str(refs[0]).split(":", 1)[0]
        old_accepted = prefix in ("control-journal", "evidence", "provider", "schedule")
        p2u_accepted = all(_p2u_era_accepts(r, manifest) for r in refs)

        rows.append({
            "case": name, "description": description,
            "references": list(refs),
            "manifest": "none" if manifest is None else (
                "%s resolver, %d record(s), digest %s"
                % (manifest.resolver_state, len(manifest.records),
                   (manifest.declared_digest or "-")[:12])),
            "expected_problem": expect,
            "problems": problems,
            "detected": detected,
            "fold_refused": refused,
            "accepted_by_the_prefix_check_this_replaces": old_accepted,
            "accepted_by_the_p2u_contract_this_rework_replaces": p2u_accepted,
            "closed": detected and refused,
        })
    return rows


def digest_enumeration_guard() -> Dict[str, object]:
    """P2V-03 — the enumeration of digest-bound fields is itself checked.

    `DIGEST_BOUND_FIELDS` is the correction: it says which control fields the manifest
    digest covers. A list is only worth what its maintenance is worth, and this one is
    maintained by the same memory that left `resolver_state` outside the digest in the
    first place. So the guard is mechanical — and, like every other guard in this
    harness, it has to be OBSERVED failing before it counts as evidence.

    Two witnesses, each a temporary edit to the enumeration, restored in `finally`:
      undeclared  a real manifest field removed from both lists — it could then be
                  edited without invalidating the digest, which is the finding;
      stale       a name in the enumeration that is not a field — the digest and the
                  enumeration have drifted, and `computed_digest()` refuses to
                  produce a value rather than hash a payload missing a bound field.
    """
    saved = extb.DIGEST_BOUND_FIELDS
    rows: List[Dict[str, object]] = []

    rows.append({"case": "live enumeration", "problems": extb._check_digest_field_coverage(),
                 "expect_problem": False})
    try:
        extb.DIGEST_BOUND_FIELDS = tuple(f for f in saved if f != "resolver_state")
        rows.append({"case": "control field dropped from the enumeration",
                     "problems": extb._check_digest_field_coverage(),
                     "expect_problem": True})
        extb.DIGEST_BOUND_FIELDS = saved + ("not_a_manifest_field",)
        problems = extb._check_digest_field_coverage()
        try:
            extb.ExternalManifest().computed_digest()
            digest_refused = None
        except AssertionError as exc:
            digest_refused = str(exc)
        rows.append({"case": "enumeration names a field that does not exist",
                     "problems": problems, "expect_problem": True,
                     "computed_digest_refused": digest_refused})
    finally:
        extb.DIGEST_BOUND_FIELDS = saved

    ok = all(bool(r["problems"]) == r["expect_problem"] for r in rows)
    return {
        "bound_fields": list(saved),
        "exempt_fields": dict(extb.DIGEST_EXEMPT_FIELDS),
        "manifest_fields": sorted(extb.ExternalManifest.__dataclass_fields__),
        "rows": rows,
        "guard_discriminates": ok and bool(rows[2].get("computed_digest_refused")),
    }


def external_basis_positive() -> Dict[str, object]:
    """A reference that RESOLVES must fold and produce state.

    Without this the section proves only that the validator can say no. The event set
    is the same shape as every failing case above — one non-genesis DecisionEvent
    whose entire basis is external — so the single difference between folding and
    refusing is whether the reference resolves.
    """
    events = _external_events((GOOD_REF,))
    problems = validate_basis(events, external_manifest=MANIFEST)
    folded = None
    error = None
    try:
        st = fold(events, shape="S1", case_id="extb-positive",
                  external_manifest=MANIFEST)
        folded = {"order": list(st.order),
                  "causal_violations": list(st.causal_violations),
                  "canonical_records": len(st.canonical)}
    except FoldError as exc:
        error = str(exc)
    return {
        "reference": GOOD_REF,
        "manifest_digest": MANIFEST.declared_digest,
        "manifest_records": MANIFEST.keys(),
        "problems": problems,
        "folded": folded,
        "error": error,
        "resolved_and_folded": not problems and folded is not None
        and not folded["causal_violations"],
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
            "external_accepted_by_the_p2u_contract_this_rework_replaces":
                sorted(r["case"] for r in ext_rows
                       if r["accepted_by_the_p2u_contract_this_rework_replaces"]),
            "external_positive_resolves": ext_positive["resolved_and_folded"],
            "digest_enumeration_guard_discriminates":
                ext_guard["guard_discriminates"],
            "production_combinations_validated": len(stimuli) * 3,
            "production_basis_problems": production_problems,
        },
        "cases": rows,
        "external_basis_cases": ext_rows,
        "external_basis_positive": ext_positive,
        "digest_enumeration_guard": ext_guard,
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
    print("  %-42s %-7s %-7s %-9s %s"
          % ("CASE", "DETECT", "REFUSE", "PREFIX", "P2U CONTRACT"))
    for r in payload["external_basis_cases"]:
        print("  %-42s %-7s %-7s %-9s %s"
              % (r["case"], r["detected"], r["fold_refused"],
                 "accepted" if r["accepted_by_the_prefix_check_this_replaces"]
                 else "rejected",
                 "*** ACCEPTED ***"
                 if r["accepted_by_the_p2u_contract_this_rework_replaces"]
                 else "rejected"))
    print("  closed: %d / %d" % (s["external_closed"], s["external_cases"]))
    if s["external_open"]:
        print("  *** OPEN: %s ***" % ", ".join(s["external_open"]))
    print("  %d of these %d references were ACCEPTED by the prefix check TASK-0005 "
          "replaced" % (s["external_accepted_by_the_prefix_check_this_replaces"],
                        s["external_cases"]))
    p2u = s["external_accepted_by_the_p2u_contract_this_rework_replaces"]
    print("  %d were ACCEPTED by the TASK-0005 contract THIS REWORK replaces — the"
          % len(p2u))
    print("  P2V defect witnesses: %s" % (", ".join(p2u) or "none"))
    g = payload["digest_enumeration_guard"]
    print("  digest-bound fields: %s | exempt: %s | manifest fields: %s"
          % (g["bound_fields"], sorted(g["exempt_fields"]), g["manifest_fields"]))
    for r in g["rows"]:
        print("    %-46s %s"
              % (r["case"], (r["problems"][0][:60] if r["problems"] else "clean")))
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
          and bool(s["digest_enumeration_guard_discriminates"]))
    print()
    print("MISSING-BASIS SUITE %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

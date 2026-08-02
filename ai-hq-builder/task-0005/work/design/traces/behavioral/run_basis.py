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

The suite also confirms the 81 production combinations validate cleanly, so the new
gate is not passing by refusing everything.

Usage:  python3 run_basis.py [--fixtures PATH] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Tuple

import external_basis as extb
from events import Event
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

# The one record the frozen manifest lists. Its hash is a fixed literal, not a digest
# of anything computed here: a self-consistent fixture would let a hash-comparison bug
# pass by comparing a value to itself.
GOOD_RECORD = extb.ExternalRecord(
    store="control-journal", object_id="kill-cmd-77", version="v3",
    content_hash="4f1c2ab9de3057c6", verification_receipt="ctrl-receipt-77")

# Known to the resolver, deliberately NOT in the frozen snapshot. This is what makes
# "omitted from the frozen manifest" a reachable state distinct from "nonexistent".
OMITTED_KEY = "evidence:exec-receipt-91"

MANIFEST = extb.ExternalManifest(
    records=(GOOD_RECORD,),
    resolver_known_ids=(OMITTED_KEY,),
    resolver_state=extb.RESOLVER_AVAILABLE).bound()

DEGRADED_MANIFEST = extb.ExternalManifest(
    records=(GOOD_RECORD,), resolver_state=extb.RESOLVER_DEGRADED).bound()
UNAVAILABLE_MANIFEST = extb.ExternalManifest(
    records=(GOOD_RECORD,), resolver_state=extb.RESOLVER_UNAVAILABLE).bound()
# A manifest whose declared digest no longer matches its contents: the frozen
# snapshot was altered after it was bound.
TAMPERED_MANIFEST = extb.ExternalManifest(
    records=(GOOD_RECORD,
             extb.ExternalRecord(store="evidence", object_id="smuggled",
                                 version="v1", content_hash="00000000",
                                 verification_receipt="r")),
    resolver_state=extb.RESOLVER_AVAILABLE,
    declared_digest=MANIFEST.declared_digest)
UNVERIFIED_MANIFEST = extb.ExternalManifest(
    records=(extb.ExternalRecord(store="provider", object_id="obj-5", version="v1",
                                 content_hash="aa11bb22", verification_receipt=None),),
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
]


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
            "closed": detected and refused,
        })
    return rows


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
            "production_combinations_validated": len(stimuli) * 3,
            "production_basis_problems": production_problems,
        },
        "cases": rows,
        "external_basis_cases": ext_rows,
        "external_basis_positive": ext_positive,
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
    print("  %-32s %-8s %-8s %-9s %s"
          % ("CASE", "DETECT", "REFUSE", "OLD CHECK", "PROBLEM"))
    for r in payload["external_basis_cases"]:
        print("  %-32s %-8s %-8s %-9s %s"
              % (r["case"], r["detected"], r["fold_refused"],
                 "accepted" if r["accepted_by_the_prefix_check_this_replaces"]
                 else "rejected",
                 (r["problems"][0] if r["problems"] else "*** NONE ***")[:70]))
    print("  closed: %d / %d" % (s["external_closed"], s["external_cases"]))
    if s["external_open"]:
        print("  *** OPEN: %s ***" % ", ".join(s["external_open"]))
    print("  %d of these %d references were ACCEPTED by the prefix check this "
          "replaces" % (s["external_accepted_by_the_prefix_check_this_replaces"],
                        s["external_cases"]))
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
          and not s["external_open"] and bool(s["external_positive_resolves"]))
    print()
    print("MISSING-BASIS SUITE %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

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
        "unknown-external-reference-type",
        "an external_basis entry naming a store outside the declared set",
        [_root(),
         _ev("decision-1", "DecisionEvent", caused_by=("policy-1",),
             external_basis=("hearsay:some-id",), seq=2)],
        "not a declared external store",
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

    payload = {
        "summary": {
            "cases": len(rows),
            "closed": sum(1 for r in rows if r["closed"]),
            "open": [r["case"] for r in rows if not r["closed"]],
            "witnesses_reproducing_old_behavior":
                sum(1 for r in rows if r["witness_reproduces_old_behavior"]),
            "production_combinations_validated": len(stimuli) * 3,
            "production_basis_problems": production_problems,
        },
        "cases": rows,
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
    print("  production combinations validated : %d" % s["production_combinations_validated"])
    if s["production_basis_problems"]:
        print("  *** production basis problems: %s ***"
              % json.dumps(s["production_basis_problems"])[:300])
    else:
        print("  production basis problems         : none — the check is fail-closed, "
              "not refuse-everything")

    ok = not s["open"] and not s["production_basis_problems"]
    print()
    print("MISSING-BASIS SUITE %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

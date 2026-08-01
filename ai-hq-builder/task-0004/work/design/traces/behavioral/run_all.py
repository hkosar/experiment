"""Main runner: all 27 fixtures x 3 candidate shapes = 81 combinations.

Every combination must produce a computed result and a judged pass/fail. A fixture
the harness cannot classify FAILS the run (P2S-01 requirement 8) — never skipped.

Deterministic: no wall-clock, no unseeded randomness. Two consecutive runs on the
same code produce byte-identical outputs.

Usage:  python3 run_all.py [--fixtures PATH] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

import oracle
import oracle_schema
import scenarios as scen
from events import SHAPES
from fixture_io import load_oracle, load_stimuli
from judge import judge
from simulate import Defects, divergences_for, simulate

DEFAULT_FIXTURES = os.path.join("..", "..", "..", "03F_Replay_Fixtures.json")


def run(fixtures_path: str, out_dir: str, defects: Defects | None = None) -> Dict[str, object]:
    stimuli = load_stimuli(fixtures_path)          # INPUT-SIDE only
    oracle_cases = load_oracle(fixtures_path)      # ORACLE side, judge only

    results: List[Dict[str, object]] = []
    judgements: List[Dict[str, object]] = []
    divergence_report: List[Dict[str, object]] = []
    per_fixture_computed = {}

    combos = 0
    passes = 0
    failures = 0
    unclassifiable = 0

    for stim in stimuli:
        shape_results = {}
        for shape in SHAPES:
            combos += 1
            try:
                res = simulate(stim, shape, defects)
            except KeyError as exc:
                # Requirement 8: unclassifiable case FAILS the run.
                unclassifiable += 1
                failures += 1
                judgements.append({
                    "fixture": stim.id, "shape": shape, "passed": False,
                    "failures": ["unclassifiable: %s" % exc],
                    "forbidden_evaluated": 0,
                })
                continue
            shape_results[shape] = res
            j = judge(res, oracle_cases[stim.id], stim, scen.get(stim.id))
            judgements.append(j.to_dict())
            if j.passed:
                passes += 1
            else:
                failures += 1
            if j.unclassifiable:
                unclassifiable += 1

            results.append({
                "fixture": stim.id,
                "shape": shape,
                # RW-27: the same honest-coverage shape for the attention dimension.
                "attention_mapping": oracle.expected_attention(
                    oracle_cases[stim.id].expected, stim.id).to_dict(),
                "tier": res.tier,
                "ceiling": res.ceiling,
                "attention": res.attention,
                "quarantined": res.quarantined,
                "step_up_required": res.step_up_required,
                "step_up_satisfied": res.step_up_satisfied,
                "event_count": len(res.events),
                "event_types": sorted({e.event_type for e in res.events}),
                "action_requests": [e.event_id for e in res.events
                                    if e.event_type == "ActionRequest"],
                "executed": sorted(res.folded.executed_actions) if res.folded else [],
                "verified": sorted(res.folded.verified_actions) if res.folded else [],
                "receipt_violations": res.receipt_violations,
                "eligible_proposal_classes": res.eligible_proposal_classes,
                "proposals_emitted": res.proposals_emitted,
                "storage": res.storage_summary,
                "fold_digest": res.digest(),
                "reasons": res.reasons,
                "proposal_notes": res.proposal_notes,
                "extras": res.extras,
            })

        if len(shape_results) == len(SHAPES):
            per_fixture_computed[stim.id] = shape_results
            for d in divergences_for(shape_results):
                divergence_report.append({"fixture": stim.id, **d})

    summary = {
        "fixtures": len(stimuli),
        "shapes": len(SHAPES),
        "combinations_expected": len(stimuli) * len(SHAPES),
        "combinations_computed": combos,
        "passes": passes,
        "failures": failures,
        "unclassifiable": unclassifiable,
        "forbidden_predicates_evaluated": sum(
            int(j.get("forbidden_evaluated") or 0) for j in judgements),
        "divergences": len(divergence_report),
        # P2T-01 — per-dimension accounting over all four expected dimensions.
        # Reported per dimension, never averaged: an average would let one
        # dimension's collapse hide behind another's coverage.
        "dimension_coverage": {
            dim: {
                "compared": sum(1 for j in judgements
                                if j.get("dimensions", {}).get(dim) == "mapped"),
                "unmappable": sum(1 for j in judgements
                                  if j.get("dimensions", {}).get(dim) == "unmappable"),
                "not_applicable": sum(1 for j in judgements
                                      if j.get("dimensions", {}).get(dim)
                                      == "not-applicable"),
            } for dim in oracle_schema.DIMENSIONS},
        "dimension_floor_fixtures": oracle_schema.floor_counts(),
        # RW-27 — compared / unmapped / unresolved, never conflated. "Unresolved"
        # means the fixture and the engine name different bands and the rule that
        # would settle it is in a document the Builder does not hold: those are
        # change requests, and they are NOT counted as compared.
        "attention_compared": sum(
            1 for r in results if r["attention_mapping"]["mapped"]),
        "attention_unmapped": sum(
            1 for r in results
            if not r["attention_mapping"]["mapped"]
            and not r["attention_mapping"]["unresolved"]),
        "attention_unresolved": sum(
            1 for r in results if r["attention_mapping"]["unresolved"]),
        "attention_unresolved_fixtures": sorted(oracle.ATTENTION_UNRESOLVED),
    }

    os.makedirs(out_dir, exist_ok=True)
    _write(os.path.join(out_dir, "results.json"),
           {"summary": summary, "results": results})
    _write(os.path.join(out_dir, "judgements.json"),
           {"summary": summary, "judgements": judgements})
    _write(os.path.join(out_dir, "divergences.json"),
           {"summary": {"count": len(divergence_report)}, "divergences": divergence_report})

    return {"summary": summary, "judgements": judgements,
            "divergences": divergence_report, "results": results}


def _write(path: str, payload: object) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", default=DEFAULT_FIXTURES)
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)

    report = run(args.fixtures, args.out)
    s = report["summary"]

    print("TASK-0003 behavioral simulator — base run")
    print("  fixtures                : %d" % s["fixtures"])
    print("  shapes                  : %d  %s" % (s["shapes"], ", ".join(SHAPES)))
    print("  combinations computed   : %d / %d" % (s["combinations_computed"],
                                                   s["combinations_expected"]))
    print("  judged PASS             : %d" % s["passes"])
    print("  judged FAIL             : %d" % s["failures"])
    print("  unclassifiable          : %d" % s["unclassifiable"])
    print("  forbidden predicates run: %d" % s["forbidden_predicates_evaluated"])
    print("  divergences computed    : %d" % s["divergences"])
    print("  --- P2T-01 expected-result coverage, per dimension (of %d combinations) ---"
          % s["combinations_computed"])
    for dim in oracle_schema.DIMENSIONS:
        d = s["dimension_coverage"][dim]
        print("    %-10s compared %3d | unmappable %3d | not-applicable %3d | "
              "floor %d fixtures"
              % (dim, d["compared"], d["unmappable"], d["not_applicable"],
                 s["dimension_floor_fixtures"][dim]))
    if s["attention_unresolved_fixtures"]:
        print("     UNRESOLVED — change request to Fable: %s"
              % ", ".join(s["attention_unresolved_fixtures"]))
        for fid in s["attention_unresolved_fixtures"]:
            print("       %s: %s" % (fid, oracle.ATTENTION_UNRESOLVED[fid]))

    if s["failures"]:
        print("\nFAILING COMBINATIONS:")
        for j in report["judgements"]:
            if not j["passed"]:
                detail = j.get("forbidden_violated") or j.get("failures")
                print("  %-7s %-3s  %s" % (j["fixture"], j["shape"], detail))

    ok = (s["combinations_computed"] == s["combinations_expected"]
          and s["unclassifiable"] == 0)
    print("\nRUN %s" % ("COMPLETE (all combinations executed)" if ok
                        else "INCOMPLETE — requirement 8 breach"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

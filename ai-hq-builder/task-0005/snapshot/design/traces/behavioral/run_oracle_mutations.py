"""Oracle-mutation suite — proof that every expected dimension is load-bearing.

Verifier finding P2T-01 was demonstrated with four probes: change one fixture's
`expected.route`, `expected.authority` or `expected.receipt` to an impossible
sentinel, or replace all 27 authority values at once, and the gate still returned
PASS. This runner reproduces those probes and every generalisation of them, and
requires each to FAIL.

Three sections:

  A  VERIFIER PROBES — the exact four probes from `28A_Verifier_Probe_Evidence`,
     re-run against the corrected harness. Each must now produce a gate failure.
     A probe that still passes fails this runner.

  B  SENTINEL CORRUPTION — for every fixture and every one of the four dimensions
     (108 pairs), replace the expected value with an unrecognised sentinel. The
     fail-closed coverage floor must reject it: a declared-mapped pair becoming
     unmappable, or a declared not-applicable pair becoming anything else, is a gate
     failure. This is what makes "unmapped" safe rather than a free pass.

  C  CONTRADICTORY-BUT-VALID CORRUPTION — the verifier's closure falsifier: "replacing
     the expected value with a contradictory but schema-valid value must cause that
     fixture/shape to fail." Rather than inventing values, this section SWAPS IN
     ANOTHER FIXTURE'S REAL VALUE for the same dimension — schema-valid by
     construction, since it is a value the frozen corpus already contains. For each
     declared-mapped pair it reports the swapped value that flips the case. A pair no
     corpus value can flip is reported as NOT LOAD-BEARING and fails this runner,
     because a dimension that cannot disagree is not evidence.

Exit code 0 only if every probe is defeated, every sentinel is rejected, and every
governed fixture-dimension pair has a named contradictory witness.

Usage:  python3 run_oracle_mutations.py [--fixtures PATH] [--out DIR]
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from dataclasses import replace
from typing import Dict, List, Optional

import oracle_schema
import scenarios as scen
from events import SHAPES
from fixture_io import load_oracle, load_stimuli
from judge import judge
from simulate import Defects, simulate

SENTINELS = {
    "route": "__IMPOSSIBLE_ROUTE__",
    "attention": "__IMPOSSIBLE_ATTENTION__",
    "authority": "__IMPOSSIBLE_AUTHORITY__",
    "receipt": "__IMPOSSIBLE_RECEIPT__",
}


def _corrupt(oc, dimension: str, value: str):
    """Return a copy of one OracleCase with a single expected dimension replaced."""
    expected = copy.deepcopy(oc.expected) if isinstance(oc.expected, dict) else {}
    expected[dimension] = value
    return replace(oc, expected=expected)


def _case_passes(stim, oracle_case, shape: str) -> bool:
    res = simulate(stim, shape, Defects())
    return judge(res, oracle_case, stim, scen.get(stim.id)).passed


def _corpus_passes(stimuli, cases) -> bool:
    """True only if EVERY combination passes — the gate's own pass condition."""
    for stim in stimuli:
        for shape in SHAPES:
            if not _case_passes(stim, cases[stim.id], shape):
                return False
    return True


# --------------------------------------------------------------------------
# A — the verifier's own probes
# --------------------------------------------------------------------------

def verifier_probes(stimuli, cases) -> List[Dict[str, object]]:
    by_id = {s.id: s for s in stimuli}
    out: List[Dict[str, object]] = []

    for dim in ("route", "authority", "receipt"):
        mutated = dict(cases)
        mutated["S1"] = _corrupt(cases["S1"], dim, SENTINELS[dim])
        passed = _corpus_passes(stimuli, mutated)
        out.append({
            "probe": "28A_/oracle_mutation_probes/%s" % dim,
            "mutation": "S1 expected.%s=%s" % (dim, SENTINELS[dim]),
            "verifier_observed": "gate PASS",
            "now": "gate PASS" if passed else "gate FAIL",
            "defeated": not passed,
        })

    mutated = {fid: _corrupt(oc, "authority", SENTINELS["authority"])
               for fid, oc in cases.items()}
    passed = _corpus_passes(stimuli, mutated)
    out.append({
        "probe": "28A_/oracle_mutation_probes/all_authority_values",
        "mutation": "all 27 expected.authority values replaced by an unrecognised sentinel",
        "verifier_observed": "gate PASS, 0 mapped / 81 unmapped",
        "now": "gate PASS" if passed else "gate FAIL",
        "defeated": not passed,
    })
    del by_id
    return out


# --------------------------------------------------------------------------
# B — sentinel corruption over all 108 fixture-dimension pairs
# --------------------------------------------------------------------------

def sentinel_matrix(stimuli, cases) -> Dict[str, object]:
    """Corrupt every fixture-dimension pair with an unrecognised value.

    Three outcomes, kept apart because conflating them is how "unmapped" became a
    free pass in the first place:

      rejected        the corruption fails the case — what a governed pair must do,
                      and what a declared not-applicable pair must do too (the corpus
                      is frozen, so a dimension that stops being "—" is a corpus edit
                      or a parser regression).
      not-rejectable  the pair is DECLARED unmappable: it carries no comparable claim,
                      so replacing one uncomparable value with another changes
                      nothing. This is the honest limit of a sentinel probe, not a
                      hole — and each such pair must carry a recorded rationale, or
                      it is indistinguishable from an oversight and fails here.
      survived        a governed pair whose corruption still passed. A real hole.
    """
    by_id = {s.id: s for s in stimuli}
    rows: List[Dict[str, object]] = []
    survived: List[str] = []
    not_rejectable: List[str] = []
    missing_rationale: List[str] = []
    for stim in stimuli:
        for dim in oracle_schema.DIMENSIONS:
            decl = oracle_schema.declared(dim, stim.id)
            mutated = _corrupt(cases[stim.id], dim, SENTINELS[dim])
            fails = [sh for sh in SHAPES if not _case_passes(by_id[stim.id], mutated, sh)]
            rejected = len(fails) == len(SHAPES)
            key = "%s/%s" % (stim.id, dim)
            if decl == "unmappable":
                outcome = "rejected" if rejected else "not-rejectable"
                if not rejected:
                    not_rejectable.append(key)
                    if (dim, stim.id) not in oracle_schema.UNMAPPABLE_RATIONALE:
                        missing_rationale.append(key)
            else:
                outcome = "rejected" if rejected else "survived"
                if not rejected:
                    survived.append(key)
            rows.append({
                "fixture": stim.id, "dimension": dim, "declared": decl,
                "shapes_failed": len(fails), "outcome": outcome,
            })
    return {"pairs": len(rows),
            "rejected": sum(1 for r in rows if r["outcome"] == "rejected"),
            "not_rejectable": not_rejectable,
            "missing_rationale": missing_rationale,
            "survived": survived, "rows": rows}


# --------------------------------------------------------------------------
# C — contradictory-but-schema-valid corruption (the closure falsifier)
# --------------------------------------------------------------------------

def contradiction_matrix(stimuli, cases) -> Dict[str, object]:
    by_id = {s.id: s for s in stimuli}
    ids = [s.id for s in stimuli]
    rows: List[Dict[str, object]] = []
    not_load_bearing: List[str] = []

    for stim in stimuli:
        for dim in oracle_schema.DIMENSIONS:
            if oracle_schema.declared(dim, stim.id) != "mapped":
                continue                      # not a governed pair; section B covers it
            own = str((cases[stim.id].expected or {}).get(dim) or "")
            witness: Optional[str] = None
            witness_from: Optional[str] = None
            for other in ids:
                if other == stim.id:
                    continue
                alt = str((cases[other].expected or {}).get(dim) or "")
                if not alt or alt == own:
                    continue
                mutated = _corrupt(cases[stim.id], dim, alt)
                if all(not _case_passes(by_id[stim.id], mutated, sh) for sh in SHAPES):
                    witness, witness_from = alt, other
                    break
            rows.append({
                "fixture": stim.id, "dimension": dim, "own_value": own,
                "contradictory_value": witness, "borrowed_from": witness_from,
                "load_bearing": witness is not None,
            })
            if witness is None:
                not_load_bearing.append("%s/%s" % (stim.id, dim))

    return {"governed_pairs": len(rows),
            "load_bearing": sum(1 for r in rows if r["load_bearing"]),
            "not_load_bearing": not_load_bearing, "rows": rows}


def run(fixtures_path: str, out_dir: str) -> Dict[str, object]:
    stimuli = load_stimuli(fixtures_path)
    cases = load_oracle(fixtures_path)

    clean = _corpus_passes(stimuli, cases)
    probes = verifier_probes(stimuli, cases)
    sentinel = sentinel_matrix(stimuli, cases)
    contradiction = contradiction_matrix(stimuli, cases)

    payload = {
        "summary": {
            "clean_corpus_passes": clean,
            "verifier_probes": len(probes),
            "verifier_probes_defeated": sum(1 for p in probes if p["defeated"]),
            "sentinel_pairs": sentinel["pairs"],
            "sentinel_rejected": sentinel["rejected"],
            "sentinel_not_rejectable": sentinel["not_rejectable"],
            "sentinel_missing_rationale": sentinel["missing_rationale"],
            "sentinel_survived": sentinel["survived"],
            "governed_pairs": contradiction["governed_pairs"],
            "contradiction_load_bearing": contradiction["load_bearing"],
            "not_load_bearing": contradiction["not_load_bearing"],
            "coverage_floor": oracle_schema.floor_counts(),
        },
        "verifier_probes": probes,
        "sentinel_corruption": sentinel,
        "contradictory_corruption": contradiction,
        "declared_coverage": oracle_schema.DECLARED_COVERAGE,
        "unmappable_rationale": {"%s/%s" % k: v
                                 for k, v in oracle_schema.UNMAPPABLE_RATIONALE.items()},
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "oracle_mutations.json"), "w",
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

    print("TASK-0004 oracle-mutation suite (P2T-01)")
    print("  clean corpus passes: %s" % s["clean_corpus_passes"])
    print()
    print("A. VERIFIER PROBES from 28A_ — each must now FAIL the gate")
    print("   %-56s %-12s %s" % ("MUTATION", "VERIFIER", "NOW"))
    for p in payload["verifier_probes"]:
        print("   %-56s %-12s %s%s" % (p["mutation"][:56], "PASS", p["now"],
                                       "" if p["defeated"] else "   *** NOT DEFEATED ***"))
    print("   defeated: %d / %d" % (s["verifier_probes_defeated"], s["verifier_probes"]))

    print()
    print("B. SENTINEL CORRUPTION — every fixture x dimension, unrecognised value")
    print("   pairs corrupted : %d" % s["sentinel_pairs"])
    print("   rejected        : %d" % s["sentinel_rejected"])
    print("   not rejectable  : %d — declared UNMAPPABLE, so there is no claim for a"
          % len(s["sentinel_not_rejectable"]))
    print("                     sentinel to contradict; each carries a recorded reason:")
    for key in s["sentinel_not_rejectable"]:
        fid, dim = key.split("/")
        print("       %-18s %s" % (key,
              oracle_schema.UNMAPPABLE_RATIONALE.get((dim, fid), "*** NO RATIONALE ***")))
    if s["sentinel_missing_rationale"]:
        print("   *** UNMAPPABLE WITHOUT A RECORDED REASON: %s ***"
              % ", ".join(s["sentinel_missing_rationale"]))
    if s["sentinel_survived"]:
        print("   *** SURVIVED (a governed pair passed while corrupted): %s ***"
              % ", ".join(s["sentinel_survived"]))
    else:
        print("   survived        : none — no governed pair passes while corrupted")

    print()
    print("C. CONTRADICTORY-BUT-VALID CORRUPTION — another fixture's real value")
    print("   governed pairs  : %d" % s["governed_pairs"])
    print("   load-bearing    : %d" % s["contradiction_load_bearing"])
    if s["not_load_bearing"]:
        print("   *** NOT LOAD-BEARING (no corpus value contradicts them): %s ***"
              % ", ".join(s["not_load_bearing"]))
    else:
        print("   not load-bearing: none — every governed pair has a named "
              "contradictory witness")

    print()
    print("   declared coverage floor (fixtures that MUST map, per dimension): %s"
          % s["coverage_floor"])

    ok = (bool(s["clean_corpus_passes"])
          and s["verifier_probes_defeated"] == s["verifier_probes"]
          and not s["sentinel_survived"]
          and not s["sentinel_missing_rationale"]
          and not s["not_load_bearing"])
    print()
    print("ORACLE-MUTATION SUITE %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

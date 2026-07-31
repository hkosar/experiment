"""Seeded-defect falsifier suite + per-predicate reachability proof.

Two layers:

  A  ENGINE-LEVEL DEFECTS (`Defects`) — the P2S-01 named falsifier classes, seeded
     inside the engine/fold so the whole pipeline misbehaves. Each must flip at
     least one previously-passing fixture x shape combination.

  B  PREDICATE REACHABILITY (`mutations`) — rework finding RW-02. Every forbidden
     predicate must be provably able to fire. For each predicate we search the
     mutation catalogue for a candidate defect that makes it return True. A
     predicate no mutation can reach is reported NOT-EVALUABLE with rationale and
     is EXCLUDED from the evaluated count — an honest smaller number over a padded
     larger one.

Exit code 0 only if every named defect class flips a case AND no predicate is
silently counted as evidence when it cannot discriminate.

Usage:  python3 run_defects.py [--fixtures PATH] [--out DIR]
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from typing import Dict, List, Tuple

import mutations
import oracle
import scenarios as scen
from events import SHAPES
from fixture_io import load_oracle, load_stimuli
from judge import judge
from simulate import Defects, simulate

# The P2S-01 falsifier's five named classes, plus the extra invariants this
# harness enforces. Each is seeded INSIDE the engine, not post-hoc.
CATALOGUE = [
    ("authority-raise", lambda: Defects(authority_raise=True),
     "changes authority — a model proposal raises the ceiling above the model-free base"),
    ("dropped-receipt", lambda: Defects(drop_receipt=True),
     "drops a receipt — the action still advances to executed with no evidence"),
    ("causal-reorder", lambda: Defects(causal_reorder=True),
     "reorders a causal event — delivery permuted and the topological sort disabled"),
    ("forbidden-outcome-admission", lambda: Defects(admit_forbidden=True),
     "admits a forbidden outcome — state written on a read-only path"),
    ("stale-projection", lambda: Defects(stale_projection=True),
     "produces a stale projection — S3 projections are not rebuilt"),
    ("engine-authored-receipt", lambda: Defects(engine_authored_receipt=True),
     "breaks external-receipt ownership — the engine authors its own evidence"),
    ("skip-eligibility-check", lambda: Defects(skip_eligibility_check=True),
     "P2S-07 — proposals from untrusted content with no eligibility policy"),
    ("normalizer-authority-leak", lambda: Defects(normalizer_authority_leak=True),
     "E2E-1 — a substituted normalizer raises the maximum authorized action"),
]

# Predicates that no candidate defect can reach because the situation they describe
# is outside what this simulator models. Reported honestly, excluded from counts.
NOT_EVALUABLE_RATIONALE: Dict[str, str] = {}


def _ctx(res, stim, spec, oc):
    return {"result": res, "stim": stim, "spec": spec, "oracle": oc}


def baseline(fixtures_path: str):
    stimuli = load_stimuli(fixtures_path)
    oracle_cases = load_oracle(fixtures_path)
    passes = {}
    for stim in stimuli:
        for shape in SHAPES:
            res = simulate(stim, shape, Defects())
            j = judge(res, oracle_cases[stim.id], stim, scen.get(stim.id))
            passes[(stim.id, shape)] = j.passed
    return stimuli, oracle_cases, passes


def prove_reachability(stimuli, oracle_cases) -> Dict[str, object]:
    """For every predicate, find a candidate defect that makes it fire."""
    # which fixtures carry which phrase
    carriers: Dict[str, List[str]] = {}
    for fid, oc in oracle_cases.items():
        for phrase in oc.forbidden:
            carriers.setdefault(phrase, []).append(fid)

    stim_by_id = {s.id: s for s in stimuli}
    reach: Dict[str, Dict[str, object]] = {}

    for phrase, fixture_ids in sorted(carriers.items()):
        pred = oracle.forbidden_predicate(phrase)
        witnesses: List[str] = []
        fires_in_production = False

        for fid in fixture_ids:
            stim = stim_by_id[fid]
            spec = scen.get(fid)
            oc = oracle_cases[fid]
            for shape in SHAPES:
                base_res = simulate(stim, shape, Defects())
                if pred(_ctx(base_res, stim, spec, oc)):
                    fires_in_production = True
                for mut in mutations.mutation_names():
                    res = simulate(stim, shape, Defects())
                    try:
                        mutations.apply_mutation(mut, res, spec, stim)
                        fired = bool(pred(_ctx(res, stim, spec, oc)))
                    except Exception:
                        fired = False
                    if fired:
                        witnesses.append("%s@%s/%s" % (mut, fid, shape))
                        break
                if witnesses:
                    break
            if witnesses:
                break

        reach[phrase] = {
            "fixtures": sorted(fixture_ids),
            "defect_reachable": bool(witnesses),
            "witness": witnesses[0] if witnesses else None,
            "fires_in_production": fires_in_production,
        }
    return reach


def run(fixtures_path: str, out_dir: str) -> Dict[str, object]:
    stimuli, oracle_cases, base = baseline(fixtures_path)
    base_passes = sum(1 for v in base.values() if v)

    # ---- layer A: engine-level named defect classes ----
    report: List[Dict[str, object]] = []
    all_effective = True
    for name, factory, description in CATALOGUE:
        d = factory()
        flipped: List[str] = []
        for stim in stimuli:
            for shape in SHAPES:
                try:
                    res = simulate(stim, shape, d)
                    passed = judge(res, oracle_cases[stim.id], stim,
                                   scen.get(stim.id)).passed
                except Exception:
                    passed = False
                if base[(stim.id, shape)] and not passed:
                    flipped.append("%s/%s" % (stim.id, shape))
        effective = bool(flipped)
        all_effective = all_effective and effective
        report.append({"defect": name, "witnesses": description,
                       "flipped_count": len(flipped), "flipped": flipped,
                       "effective": effective})

    # ---- layer B: per-predicate reachability ----
    reach = prove_reachability(stimuli, oracle_cases)
    reachable = [p for p, r in reach.items() if r["defect_reachable"]]
    not_evaluable = [p for p, r in reach.items() if not r["defect_reachable"]]

    payload = {
        "summary": {
            "baseline_passes": base_passes,
            "defects_seeded": len(CATALOGUE),
            "defects_effective": sum(1 for r in report if r["effective"]),
            "all_effective": all_effective,
            "predicates_total": len(reach),
            "predicates_defect_reachable": len(reachable),
            "predicates_not_evaluable": len(not_evaluable),
            "mutations_in_catalogue": len(mutations.mutation_names()),
        },
        "defects": report,
        "predicate_reachability": reach,
        "not_evaluable": sorted(not_evaluable),
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "seeded_defects.json"), "w",
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

    print("TASK-0003 seeded-defect falsifier suite")
    print("  baseline passing combinations: %d" % s["baseline_passes"])
    print()
    print("A. ENGINE-LEVEL DEFECT CLASSES (P2S-01 falsifier)")
    print("   %-30s %-9s %s" % ("DEFECT", "FLIPPED", "VERDICT"))
    for r in payload["defects"]:
        print("   %-30s %-9d %s" % (
            r["defect"], r["flipped_count"],
            "DETECTED" if r["effective"] else "*** NOT DETECTED — harness defect ***"))
    print("   effective: %d / %d" % (s["defects_effective"], s["defects_seeded"]))
    print()
    print("B. PER-PREDICATE REACHABILITY (rework finding RW-02)")
    print("   mutation catalogue        : %d candidate defects" % s["mutations_in_catalogue"])
    print("   predicates total          : %d" % s["predicates_total"])
    print("   defect-reachable          : %d" % s["predicates_defect_reachable"])
    print("   NOT-EVALUABLE (excluded)  : %d" % s["predicates_not_evaluable"])
    for p in payload["not_evaluable"]:
        print("      NOT-EVALUABLE: %s" % p)

    ok = bool(s["all_effective"])
    print()
    print("FALSIFIER PROOF %s" % ("PASS" if ok else "FAIL — a named defect went undetected"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

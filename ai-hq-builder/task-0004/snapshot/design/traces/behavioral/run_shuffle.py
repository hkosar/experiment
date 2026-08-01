"""P2S-06 shuffle-invariance runner (D-B9 P2S-06 section).

  "The behavioral fold must produce byte-identical final state, projections, and
   divergence lists when fed the same event set under multiple seeded delivery-order
   permutations that preserve causal edges. Any difference is a gate failure."

For every fixture x shape, the computed event set is delivered under a fixed list of
seeded permutations. The fold re-derives order from `caused_by` plus the P2S-06
tie-break, so every permutation must yield the same digest.

Usage:  python3 run_shuffle.py [--fixtures PATH] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

from events import SHAPES
from fixture_io import load_stimuli
from fold import fold, permute
from simulate import Defects, simulate

SEEDS = (20260730, 11, 4242, 987654321, 31337)      # fixed: deterministic reproducibility


def run(fixtures_path: str, out_dir: str) -> Dict[str, object]:
    stimuli = load_stimuli(fixtures_path)
    rows: List[Dict[str, object]] = []
    mismatches: List[Dict[str, object]] = []

    for stim in stimuli:
        for shape in SHAPES:
            res = simulate(stim, shape, Defects())
            if res.folded is None:
                mismatches.append({"fixture": stim.id, "shape": shape,
                                   "error": "no folded state"})
                continue
            baseline = res.folded.digest()
            digests = {"natural": baseline}
            for seed in SEEDS:
                shuffled = permute(res.events, seed)
                f = fold(shuffled, shape=shape, case_id=stim.id)
                digests["seed:%d" % seed] = f.digest()
            distinct = sorted(set(digests.values()))
            invariant = len(distinct) == 1
            rows.append({
                "fixture": stim.id, "shape": shape,
                "permutations": len(SEEDS) + 1,
                "distinct_digests": len(distinct),
                "invariant": invariant,
                "digest": baseline,
            })
            if not invariant:
                mismatches.append({"fixture": stim.id, "shape": shape,
                                   "digests": digests})

    payload = {
        "summary": {
            "seeds": list(SEEDS),
            "permutations_per_combination": len(SEEDS) + 1,
            "combinations": len(rows),
            "invariant": sum(1 for r in rows if r["invariant"]),
            "violations": len(mismatches),
        },
        "rows": rows,
        "mismatches": mismatches,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "p2s06_shuffle_invariance.json"), "w",
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
    print("P2S-06 — shuffle invariance under causal-preserving delivery permutations")
    print("  seeds                      : %s" % ", ".join(str(x) for x in s["seeds"]))
    print("  permutations per combination: %d (natural + %d seeded)"
          % (s["permutations_per_combination"], len(s["seeds"])))
    print("  combinations checked       : %d" % s["combinations"])
    print("  byte-identical digests     : %d" % s["invariant"])
    print("  violations                 : %d" % s["violations"])
    for m in payload["mismatches"][:10]:
        print("    MISMATCH %s/%s" % (m["fixture"], m.get("shape")))
    ok = s["violations"] == 0
    print("\nP2S-06 %s" % ("PASS — fold is order-independent" if ok
                           else "FAIL — delivery order changed the result"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

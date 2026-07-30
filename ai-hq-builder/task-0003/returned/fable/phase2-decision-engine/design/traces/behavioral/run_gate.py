"""Master runner — executes every suite and reports the acceptance-criteria table.

  python3 run_gate.py [--fixtures PATH] [--out DIR]

Exit code 0 only if every suite passes. Deterministic end to end: no wall-clock,
no unseeded randomness, so two consecutive runs produce byte-identical outputs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

import check_anticircularity
import run_all
import run_defects
import run_p2s05
import run_p2s07
import run_shuffle
from events import SHAPES

DEFAULT_FIXTURES = os.path.join("..", "..", "..", "03F_Replay_Fixtures.json")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", default=DEFAULT_FIXTURES)
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)

    base = run_all.run(args.fixtures, args.out)
    defects = run_defects.run(args.fixtures, args.out)
    shuffle = run_shuffle.run(args.fixtures, args.out)
    p2s05 = run_p2s05.run(args.out)
    p2s07 = run_p2s07.run(args.out)
    anti = [check_anticircularity.check_textual(),
            check_anticircularity.check_imports(),
            check_anticircularity.check_structural()]
    anti_ok = all(a["passed"] for a in anti)

    s = base["summary"]
    e2e = next((r for r in base["results"] if r["fixture"] == "E2E-1"), {})
    e2e_extras = e2e.get("extras", {}) if isinstance(e2e, dict) else {}
    e2e_defect = next((d for d in defects["defects"]
                       if d["defect"] == "normalizer-authority-leak"), {})

    criteria = [
        ("1  anti-circularity: no oracle read in engine/scenario code",
         anti_ok, "textual+import+structural all pass"),
        ("2  all 27 x 3 = 81 combinations computed, none skipped",
         s["combinations_computed"] == 81 and s["unclassifiable"] == 0,
         "%d/81 computed, %d unclassifiable" % (s["combinations_computed"],
                                                s["unclassifiable"])),
        ("3  computed-vs-expected compared; every forbidden list evaluated",
         s["forbidden_predicates_evaluated"] == 171 and s["failures"] == 0,
         "%d forbidden predicates evaluated, %d judged failures"
         % (s["forbidden_predicates_evaluated"], s["failures"])),
        ("4  executed/verified only with an external receipt reference",
         all(not r["receipt_violations"] for r in base["results"]),
         "0 receipt-ownership violations across 81"),
        ("5  fold replays the multi-store basis with P2S-06 ordering",
         shuffle["summary"]["violations"] == 0,
         "%d combinations, %d order-invariant"
         % (shuffle["summary"]["combinations"], shuffle["summary"]["invariant"])),
        ("6  candidate-specific divergences produced, not assumed away",
         s["divergences"] > 0, "%d divergences computed" % s["divergences"]),
        ("7  E2E-1 executed as a real two-normalizer computation",
         bool(e2e_extras.get("authority_invariant")) and
         bool(e2e_extras.get("risk_suggestions_differ")) and
         bool(e2e_defect.get("effective")),
         "M1/M2 risk differ=%s, authority invariant=%s, seeded leak detected=%s"
         % (e2e_extras.get("risk_suggestions_differ"),
            e2e_extras.get("authority_invariant"), e2e_defect.get("effective"))),
        ("8  every seeded defect flips its target from pass to fail",
         bool(defects["summary"]["all_effective"]),
         "%d/%d defects effective" % (defects["summary"]["defects_effective"],
                                      defects["summary"]["defects_seeded"])),
        ("9  shuffle-invariance across >=3 seeded permutations",
         shuffle["summary"]["permutations_per_combination"] >= 4
         and shuffle["summary"]["violations"] == 0,
         "%d permutations per combination, 0 violations"
         % shuffle["summary"]["permutations_per_combination"]),
        ("10 P2S-05 five traces present and separately reported",
         p2s05["summary"]["traces"] == 5 and p2s05["summary"]["failed"] == 0,
         "%d/5 traces pass" % p2s05["summary"]["passed"]),
        ("11 P2S-07 negative and positive tests present and reported",
         p2s07["summary"]["tests"] == 2 and p2s07["summary"]["failed"] == 0,
         "%d/2 tests pass" % p2s07["summary"]["passed"]),
    ]

    print("=" * 86)
    print("TASK-0003 — P2S-01 Behavioral Candidate-Transition/Fold Simulator")
    print("=" * 86)
    print("fixtures %d x shapes %d (%s) = %d combinations"
          % (s["fixtures"], s["shapes"], ", ".join(SHAPES), s["combinations_expected"]))
    print()
    print("ACCEPTANCE CRITERIA")
    for label, ok, detail in criteria:
        print("  [%s] %-58s %s" % ("PASS" if ok else "FAIL", label, detail))

    all_ok = all(ok for _, ok, _ in criteria)
    payload = {
        "criteria": [{"criterion": c, "passed": bool(ok), "detail": d}
                     for c, ok, d in criteria],
        "all_passed": all_ok,
        "base_summary": s,
        "defects_summary": defects["summary"],
        "shuffle_summary": shuffle["summary"],
        "p2s05_summary": p2s05["summary"],
        "p2s07_summary": p2s07["summary"],
        "anticircularity_passed": anti_ok,
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "gate_report.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")

    print()
    print("GATE %s" % ("PASS — all acceptance criteria met" if all_ok
                       else "FAIL — see criteria above"))
    print("outputs written to %s/" % args.out)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

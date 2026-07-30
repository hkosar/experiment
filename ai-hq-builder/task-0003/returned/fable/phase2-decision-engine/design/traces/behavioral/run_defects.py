"""Seeded-defect falsifier suite (P2S-01 closure condition).

  "The corrected harness must fail when a seeded candidate defect changes authority,
   drops a receipt, reorders a causal event, admits a forbidden outcome, or produces
   a stale projection."

Each named defect must flip at least one fixture x shape combination from PASS to
FAIL. If any seeded defect still passes everywhere, THE HARNESS ITSELF FAILS
ACCEPTANCE (Task Packet acceptance criterion 8) and this runner exits non-zero.

Usage:  python3 run_defects.py [--fixtures PATH] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

import scenarios as scen
from events import SHAPES
from fixture_io import load_oracle, load_stimuli
from judge import judge
from simulate import Defects, simulate

# name -> (Defects factory, the P2S-01 defect class it witnesses)
CATALOGUE = [
    ("authority-raise", lambda: Defects(authority_raise=True),
     "changes authority — a model proposal raises the ceiling above the model-free base"),
    ("dropped-receipt", lambda: Defects(drop_receipt=True),
     "drops a receipt — an action's external ExecutionReceipt never arrives"),
    ("causal-reorder", lambda: Defects(causal_reorder=True),
     "reorders a causal event — the fold stops enforcing caused_by topology"),
    ("forbidden-outcome-admission", lambda: Defects(admit_forbidden=True),
     "admits a forbidden outcome — state written on a read-only path"),
    ("stale-projection", lambda: Defects(stale_projection=True),
     "produces a stale projection — S3 projections are not rebuilt after events"),
    ("engine-authored-receipt", lambda: Defects(engine_authored_receipt=True),
     "breaks external-receipt ownership — the engine authors its own evidence"),
    ("skip-eligibility-check", lambda: Defects(skip_eligibility_check=True),
     "P2S-07 — proposals emitted from untrusted content with no eligibility policy"),
    ("normalizer-authority-leak", lambda: Defects(normalizer_authority_leak=True),
     "E2E-1 — a substituted normalizer raises the maximum authorized action"),
]


def baseline_pass_set(fixtures_path: str):
    stimuli = load_stimuli(fixtures_path)
    oracle_cases = load_oracle(fixtures_path)
    out = {}
    for stim in stimuli:
        for shape in SHAPES:
            res = simulate(stim, shape, Defects())
            j = judge(res, oracle_cases[stim.id], stim, scen.get(stim.id))
            out[(stim.id, shape)] = j.passed
    return stimuli, oracle_cases, out


def run(fixtures_path: str, out_dir: str) -> Dict[str, object]:
    stimuli, oracle_cases, base = baseline_pass_set(fixtures_path)
    base_passes = sum(1 for v in base.values() if v)

    report: List[Dict[str, object]] = []
    all_effective = True

    for name, factory, description in CATALOGUE:
        d = factory()
        flipped: List[str] = []
        errored: List[str] = []
        for stim in stimuli:
            for shape in SHAPES:
                try:
                    res = simulate(stim, shape, d)
                    j = judge(res, oracle_cases[stim.id], stim, scen.get(stim.id))
                    passed = j.passed
                except Exception as exc:            # a defect that crashes the fold also fails
                    passed = False
                    errored.append("%s/%s: %s" % (stim.id, shape, exc))
                if base[(stim.id, shape)] and not passed:
                    flipped.append("%s/%s" % (stim.id, shape))

        effective = len(flipped) > 0
        all_effective = all_effective and effective
        report.append({
            "defect": name,
            "witnesses": description,
            "flipped_count": len(flipped),
            "flipped": flipped,
            "errors": errored,
            "effective": effective,
        })

    os.makedirs(out_dir, exist_ok=True)
    payload = {
        "summary": {
            "baseline_passes": base_passes,
            "defects_seeded": len(CATALOGUE),
            "defects_effective": sum(1 for r in report if r["effective"]),
            "all_effective": all_effective,
        },
        "defects": report,
    }
    with open(os.path.join(out_dir, "seeded_defects.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return payload


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", default=os.path.join("..", "..", "..", "03F_Replay_Fixtures.json"))
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)

    payload = run(args.fixtures, args.out)
    s = payload["summary"]

    print("TASK-0003 seeded-defect falsifier suite")
    print("  baseline passing combinations: %d" % s["baseline_passes"])
    print()
    print("  %-30s %-9s %s" % ("DEFECT", "FLIPPED", "VERDICT"))
    print("  " + "-" * 74)
    for r in payload["defects"]:
        print("  %-30s %-9d %s" % (
            r["defect"], r["flipped_count"],
            "DETECTED (harness fails as required)" if r["effective"]
            else "*** NOT DETECTED — harness defect ***"))
        if r["flipped"]:
            print("      e.g. %s" % ", ".join(r["flipped"][:6])
                  + (" ..." if len(r["flipped"]) > 6 else ""))
    print()
    print("  defects effective: %d / %d" % (s["defects_effective"], s["defects_seeded"]))
    ok = bool(s["all_effective"])
    print("\nFALSIFIER PROOF %s" % ("PASS — every seeded defect flips at least one case"
                                    if ok else
                                    "FAIL — a seeded defect went undetected"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""P2S-02 supersession check — patterns DERIVED FROM D-SM, not hand-listed.

Verifier finding P2T-04: the previous version of this file searched nine exact
literal patterns, hand-copied from the supersession map. It could not detect the
active old script names, the active per-occurrence ExpectedRun mechanism, or the old
evidence classifications, so its PASS did not prove the design was contradiction-free
— it proved nine specific sentences were absent.

WHAT CHANGED. The phrase set is now read out of `design/D-SM_Supersession_Map.md` at
RUNTIME. Every row's "Superseded statement" cell is parsed into patterns, so a row
Fable adds to the map is enforced on the next run with no edit here. The map is the
authority; this file is only its executor.

FOUR STRUCTURAL FAMILIES are checked in addition, because a superseded MECHANISM can
survive without any of its old sentences surviving (P2T-04 required correction 6):

    retired artifact paths        a withdrawn script named as something to run
    retired parameter values      an old numeric parameter still stated as current
    retired evidence labels       an old evidence class still claimed
    retired mechanism identifiers a superseded mechanism still described as primary

These four tables are Builder-declared and documented as such: they encode the
mechanisms the verifier named, and they are the part of this checker that a future
supersession will NOT automatically extend. That limit is stated rather than papered
over — the D-SM-derived half grows by itself; this half does not.

WHAT A PASS MEANS. No pattern derived from the current map, and no declared retired
mechanism, appears outside a line carrying a `SUPERSEDED` marker or an explicit
retirement word. It does not mean the design carries no contradiction of a kind
nobody has written a row for.

Usage:
    python3 check_supersessions.py [--design DIR] [--json PATH]
    python3 check_supersessions.py --self-test     # seeds violations, expects FAIL
Exit 1 on any hit.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from typing import Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DESIGN = os.path.join(HERE, "..")
MAP_NAME = "D-SM_Supersession_Map.md"

# A line carrying any of these is history, not an active instruction.
RETIREMENT_MARKERS = ("SUPERSEDED", "superseded", "withdrawn", "retired", "replaced by",
                      "no longer", "former ", "formerly", "historical", "errata")

# Fragments shorter than this are too generic to evidence a live contradiction.
MIN_PATTERN_LEN = 12

# --- Builder-declared structural families (P2T-04 correction 6) -------------
# Each entry: (pattern, what the authoritative replacement is). Mechanisms, not
# sentences — a superseded mechanism can survive with all-new wording.

RETIRED_ARTIFACTS: Tuple[Tuple[str, str], ...] = (
    (r"gen_shape_traces\.py", "withdrawn circular trace generator"),
    (r"run_fold_comparison\.py", "withdrawn circular fold comparator"),
)

RETIRED_PARAMETERS: Tuple[Tuple[str, str], ...] = (
    (r"n_min\s*(?:=|\s)\s*100\b", "D-B6 minimum verified sample 100 (now 149)"),
    (r"[Rr]olling 14[- ]day", "D-B6 rolling 14-day window (now a 28-day mature window)"),
    (r"18/17/13", "D-B1 scored comparison 18/17/13 (the rebuild superseded it)"),
    (r"\bJSONB\b", "D-B14 product notation (now a conceptual `document` type)"),
)

RETIRED_LABELS: Tuple[Tuple[str, str], ...] = (
    (r"machine-verified", "evidence label resting on the withdrawn circular comparator"),
    (r"machine-executed \(corpus\)", "evidence label resting on the withdrawn comparator"),
    (r"100% coverage", "D-B14 coverage claim (now a row-audited table)"),
)

RETIRED_MECHANISMS: Tuple[Tuple[str, str], ...] = (
    (r"ExpectedRun (?:record )?at scheduling time",
     "per-occurrence ExpectedRun as the PRIMARY missed-run model (D-KR P2S-04: the "
     "watchdog computes deadlines from the specs it holds; ExpectedRun corroborates)"),
    (r"writes each ExpectedRun",
     "scheduler-written ExpectedRun as the primary liveness mechanism"),
    (r"surfaced at next owner contact",
     "watchdog-outage residual acceptance (D-KR P2S-03 two-leg dead-man replaces it)"),
    # Deliberately narrow: D-B9's commutativity statement legitimately says phase-2
    # facts are "mutually independent by construction", which is a different claim
    # about a different subject. A pattern loose enough to catch both would report a
    # correct sentence as a contradiction, and a checker that cries wolf gets
    # switched off. This matches the retired KILL claim only.
    (r"independent control path by construction",
     "kill independence asserted by construction (D-KR §1 designs the mechanism)"),
)

STRUCTURAL_FAMILIES = (
    ("retired artifact path", RETIRED_ARTIFACTS),
    ("retired parameter value", RETIRED_PARAMETERS),
    ("retired evidence label", RETIRED_LABELS),
    ("retired mechanism identifier", RETIRED_MECHANISMS),
)


def _quoted(cell: str) -> List[str]:
    """Quoted or backticked fragments — a row's exact superseded wording."""
    out: List[str] = []
    for m in re.finditer(r"[\"“]([^\"”]{%d,})[\"”]" % MIN_PATTERN_LEN, cell):
        out.append(m.group(1).strip())
    for m in re.finditer(r"`([^`]{%d,})`" % MIN_PATTERN_LEN, cell):
        out.append(m.group(1).strip())
    return out


def derive_patterns(design_dir: str) -> Tuple[List[Dict[str, str]], List[str]]:
    """Parse D-SM at RUNTIME into patterns. A new row needs no code change here."""
    path = os.path.join(design_dir, MAP_NAME)
    notes: List[str] = []
    if not os.path.exists(path):
        return [], ["%s not found — no map-derived patterns available" % MAP_NAME]

    patterns: List[Dict[str, str]] = []
    rows = 0
    unquoted: List[str] = []
    unscoped: List[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 4 or not cells[0].isdigit():
                continue
            rows += 1
            row_id, where, superseded, replacement = cells[0], cells[1], cells[2], cells[3]
            frags = _quoted(superseded)
            if not frags:
                unquoted.append("row %s (%s)" % (row_id, where))
                continue
            # Each row names the artifact it is about ("D-B5 §2 invariants"), so its
            # patterns are SCOPED to that artifact. Applied globally, row 3's
            # "independent by construction" flagged D-B9's commutativity statement —
            # a correct sentence about a different subject. The map's own structure
            # supplies the scope; using it is more faithful, not merely quieter.
            m = re.match(r"([A-Z]+-[A-Za-z0-9]+)", where)
            scope = m.group(1) if m else None
            if scope is None:
                unscoped.append("row %s (%s)" % (row_id, where))
            for frag in frags:
                patterns.append({
                    "pattern": re.escape(frag), "source": "D-SM row %s" % row_id,
                    "location": where, "replacement": replacement, "literal": frag,
                    "scope": scope,
                })
    notes.append("parsed %d D-SM rows -> %d map-derived patterns" % (rows, len(patterns)))
    if unquoted:
        notes.append("D-SM rows stating no quoted phrase (only the structural families "
                     "can enforce these): %s" % "; ".join(unquoted))
    if unscoped:
        notes.append("D-SM rows naming no parseable artifact, so their patterns are "
                     "checked across every file: %s" % "; ".join(unscoped))
    return patterns, notes


def structural_patterns() -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for family, table in STRUCTURAL_FAMILIES:
        for pat, description in table:
            out.append({"pattern": pat, "source": family,
                        "location": "structural (Builder-declared)",
                        "replacement": description, "literal": pat, "scope": None})
    return out


def scan(design_dir: str) -> Dict[str, object]:
    map_patterns, notes = derive_patterns(design_dir)
    all_patterns = map_patterns + structural_patterns()
    compiled = [(p, re.compile(p["pattern"])) for p in all_patterns]

    hits: List[Dict[str, object]] = []
    files_scanned = 0
    for dirpath, dirs, files in os.walk(design_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in sorted(files):
            if not fn.endswith(".md") or fn == MAP_NAME:
                continue
            files_scanned += 1
            path = os.path.join(dirpath, fn)
            with open(path, "r", encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if any(mark in line for mark in RETIREMENT_MARKERS):
                        continue
                    for p, rx in compiled:
                        if p.get("scope") and not fn.startswith(p["scope"]):
                            continue          # this row is about a different artifact
                        if rx.search(line):
                            hits.append({
                                "file": os.path.relpath(path, design_dir).replace(
                                    os.sep, "/"),
                                "line": i, "matched": p["literal"],
                                "source": p["source"], "location": p["location"],
                                "authoritative_replacement": p["replacement"],
                            })
    return {
        "files_scanned": files_scanned,
        "map_derived_patterns": len(map_patterns),
        "structural_patterns": len(all_patterns) - len(map_patterns),
        "patterns_total": len(all_patterns),
        "notes": notes,
        "hits": hits,
        "passed": not hits,
    }


def self_test() -> Dict[str, object]:
    """Seed retired text outside a SUPERSEDED block; the check MUST fail.

    Runs against a scratch COPY — the real design tree is never written to. Both
    halves of the checker are exercised (a map-derived phrase and two structural
    mechanisms), plus the negative case: the same phrase inside a marked block must
    still pass, or the check would forbid the design from recording its own history.
    """
    results: List[Dict[str, object]] = []
    src = os.path.abspath(DEFAULT_DESIGN)
    with tempfile.TemporaryDirectory() as tmp:
        scratch = os.path.join(tmp, "design")
        shutil.copytree(src, scratch,
                        ignore=shutil.ignore_patterns("__pycache__", "out"))
        baseline = scan(scratch)
        results.append({"case": "clean scratch copy", "expect": "PASS",
                        "got": "PASS" if baseline["passed"] else "FAIL",
                        "hits": len(baseline["hits"]), "ok": baseline["passed"],
                        "detail": [h["file"] + ":" + str(h["line"])
                                   for h in baseline["hits"][:5]]})

        seeds = [
            ("map-derived phrase",
             "The stale-policy race is closed by flag-for-later-review.\n"),
            ("structural: retired artifact as an instruction",
             "Reproduction record: run gen_shape_traces.py then "
             "run_fold_comparison.py to reproduce.\n"),
            ("structural: retired mechanism",
             "The scheduler writes each ExpectedRun at scheduling time.\n"),
            ("structural: retired parameter",
             "Minimum verified sample n_min = 100 over a rolling 14-day window.\n"),
        ]
        # The seed file is named for the artifact D-SM row 1 is about, because
        # map-derived patterns are SCOPED to their row's artifact. Seeding the phrase
        # into an unrelated file would (correctly) not fire, and a self-test that
        # tested the unscoped path would be testing something the checker no longer
        # does.
        target = os.path.join(scratch, "D-B4_selftest_scratch.md")
        for label, text in seeds:
            with open(target, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("# scratch\n\n" + text)
            got = scan(scratch)
            results.append({"case": "seeded: " + label, "expect": "FAIL",
                            "got": "PASS" if got["passed"] else "FAIL",
                            "hits": len(got["hits"]), "ok": not got["passed"],
                            "detail": [h["matched"] for h in got["hits"][:3]]})

        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# scratch\n\n*(SUPERSEDED per P2S-02: closed by "
                     "flag-for-later-review; run gen_shape_traces.py.)*\n")
        marked = scan(scratch)
        results.append({"case": "same text inside a SUPERSEDED block", "expect": "PASS",
                        "got": "PASS" if marked["passed"] else "FAIL",
                        "hits": len(marked["hits"]), "ok": marked["passed"],
                        "detail": [h["matched"] for h in marked["hits"][:3]]})

    return {"cases": results, "passed": all(r["ok"] for r in results)}


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default=DEFAULT_DESIGN)
    ap.add_argument("--json", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        st = self_test()
        print("check_supersessions self-test (P2T-04)")
        for r in st["cases"]:
            print("  %-46s expect %-4s got %-4s hits=%-3d %s"
                  % (r["case"], r["expect"], r["got"], r["hits"],
                     "ok" if r["ok"] else "*** WRONG ***"))
            if not r["ok"] and r["detail"]:
                print("        %s" % r["detail"])
        print("SELF-TEST %s" % ("PASS" if st["passed"] else "FAIL"))
        return 0 if st["passed"] else 1

    report = scan(args.design)
    if args.json:
        parent = os.path.dirname(os.path.abspath(args.json))
        os.makedirs(parent, exist_ok=True)
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")

    for note in report["notes"]:
        print("  note: %s" % note)
    if report["hits"]:
        print("FAIL — %d unmarked superseded statement(s):" % len(report["hits"]))
        for h in report["hits"][:40]:
            print("  - %s:%d matches %r (%s -> %s)"
                  % (h["file"], h["line"], h["matched"], h["source"],
                     h["authoritative_replacement"][:70]))
        return 1
    print("PASS — %d files scanned against %d patterns (%d derived from D-SM at "
          "runtime, %d structural); no unmarked superseded statement."
          % (report["files_scanned"], report["patterns_total"],
             report["map_derived_patterns"], report["structural_patterns"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

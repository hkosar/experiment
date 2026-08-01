#!/usr/bin/env python3
"""P2S-02 machine check: superseded phrases/parameters must not appear outside
a line/block carrying a SUPERSEDED marker (or the map itself). Exit 1 on hit."""
import os, sys, re

PATTERNS = [
    r"flag-not-reexecute",
    r"independent control path by construction",
    r"accepts weaker authentication",
    r"\| Minimum verified sample \| 100 ",
    r"\| Observation window \| Rolling 14 days \|",
    r"emits its own failure notice",
    r"surfaced at next owner contact",
    r"100% coverage of the designed",
    r"eligible for filing/summary/placement proposals, ineligible",
]
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
hits = []
for dirpath, _dirs, files in os.walk(ROOT):
    for fn in files:
        if not fn.endswith(".md") or fn == "D-SM_Supersession_Map.md":
            continue
        path = os.path.join(dirpath, fn)
        for i, line in enumerate(open(path), 1):
            for pat in PATTERNS:
                if re.search(pat, line) and "SUPERSEDED" not in line:
                    hits.append(f"{fn}:{i}: unmarked superseded text matches /{pat}/")
if hits:
    print("FAIL:")
    [print(" -", h) for h in hits]
    sys.exit(1)
print(f"PASS — no unmarked superseded phrase in design/ ({len(PATTERNS)} patterns scanned)")

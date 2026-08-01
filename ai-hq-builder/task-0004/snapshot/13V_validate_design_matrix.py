#!/usr/bin/env python3
"""Structural validator for the rebuilt 13M_/13G_ matrices (P2G-01 format).

WHAT THIS VALIDATOR IS: a fail-closed STRUCTURAL check. It verifies IDs,
order, text-hash binding to the accepted register, enums, cross-file
consistency, and referential integrity of evidence pointers.

WHAT IT IS NOT: a semantic judge. Whether a cited artifact actually
satisfies the accepted requirement is determined by the human verifier's
requirement-by-requirement audit — a PASS here is never proof of
requirement completion (P2G-01).

Checks:
  1. 13M and 13G both contain exactly the register's 125 accepted IDs, once
     each, in register order, then exactly DE-R1..DE-R8.
  2. Every accepted row's text hash (both files) equals the first 12 hex of
     SHA-256 of the register's exact Requirement text; DE-R hashes match
     the plan's DE-R blockquote lines.
  3. 13M treatments in {Binding, Design subject, Deferred, N/A,
     Design subject (proposed)}; 13G statuses in the declared enum.
  4. Referential integrity: every `D-B<n>`/`design/` mention in 13M
     artifact cells and 13G result cells resolves to an existing file.
  5. Consistency: Deferred/N-A treatments pair with Deliberately deferred/
     N-A statuses; Incomplete rows carry a non-empty remaining dependency.
  6. --final-gate: every required row (treatment Binding/Design subject/
     proposed) must be Complete, Binding invariant, Build-gate deferred,
     or Deliberately deferred; Not started/Incomplete/Blocked fail.
Exit 0 only if all checks pass. Run from this directory.
"""
import csv
import hashlib
import os
import re
import sys

REGISTER = "../phase1-audit-v1.0/05_Requirements_Register_v1.1.csv"
MATRIX = "13M_Design_Requirements_Applicability_Matrix.md"
OVERLAY = "13G_Design_Gate_Status_and_Evidence_Matrix.md"
PLAN = "13_CP-P2-A_Design_Phase_Change_Plan.md"
TREATMENTS = {"Binding", "Design subject", "Deferred", "N/A", "Design subject (proposed)"}
STATUSES = {"Not started", "Complete", "Binding invariant", "Incomplete", "Blocked",
            "Build-gate deferred", "Deliberately deferred", "N/A"}
GATE_OK = {"Complete", "Binding invariant", "Build-gate deferred", "Deliberately deferred"}

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


with open(REGISTER, newline="") as f:
    reg = list(csv.DictReader(f))
check(len(reg) == 125, f"register rows: {len(reg)} != 125")
order = [r["ID"] for r in reg]
texthash = {r["ID"]: hashlib.sha256(r["Requirement"].encode()).hexdigest()[:12] for r in reg}

plan_text = open(PLAN).read()
for n in range(1, 9):
    rid = f"DE-R{n}"
    lines = [l for l in plan_text.splitlines() if l.startswith(f"> **{rid} (")]
    check(len(lines) == 1, f"plan: {rid} blockquote count {len(lines)} != 1")
    if lines:
        texthash[rid] = hashlib.sha256(lines[0].encode()).hexdigest()[:12]
all_ids = order + [f"DE-R{n}" for n in range(1, 9)]

ROW = re.compile(r"^\| ((?:[A-Z]+-\d+)|(?:DE-R\d+)) \| `([0-9a-f]{12})` \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|(?: ([^|]*?) \|)?$", re.M)

def parse(path, ncols):
    rows = []
    for line in open(path).read().splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or line.startswith("| ID |"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == ncols and re.fullmatch(r"(?:[A-Z]+-\d+)|(?:DE-R\d+)", cells[0]):
            rows.append(cells)
    return rows

mrows = parse(MATRIX, 6)   # ID, hash, treatment, mechanism, artifact, test
grows = parse(OVERLAY, 5)  # ID, hash, status, actual, dependency

check([r[0] for r in mrows] == all_ids, f"13M IDs/order mismatch ({len(mrows)} rows, expected 133)")
check([r[0] for r in grows] == all_ids, f"13G IDs/order mismatch ({len(grows)} rows, expected 133)")

design_files = set(os.listdir("design")) if os.path.isdir("design") else set()

def refcheck(rid, cell, where):
    for m in re.finditer(r"D-(?:B\d+|GS|ODP|AM)[A-Za-z0-9_]*", cell):
        stem = m.group(0)
        hits = [f for f in design_files if f.startswith(stem + "_") or f.startswith(stem + ".")]
        check(bool(hits), f"{where} {rid}: artifact reference '{stem}' resolves to no file in design/")

status_by_id, treatment_by_id = {}, {}
for cells in mrows:
    rid, h, treatment, mech, art, test = cells
    h = h.strip("`")
    check(h == texthash.get(rid), f"13M {rid}: text hash {h} != register/plan {texthash.get(rid)}")
    check(treatment in TREATMENTS, f"13M {rid}: treatment '{treatment}' not allowed")
    treatment_by_id[rid] = treatment
    if treatment in ("Binding", "Design subject", "Design subject (proposed)"):
        check(mech not in ("", "—"), f"13M {rid}: required row missing mechanism")
    refcheck(rid, art, "13M")

for cells in grows:
    rid, h, status, actual, dep = cells
    h = h.strip("`")
    check(h == texthash.get(rid), f"13G {rid}: text hash {h} != register/plan {texthash.get(rid)}")
    check(status in STATUSES, f"13G {rid}: status '{status}' not in enum")
    status_by_id[rid] = status
    if status == "Incomplete":
        check(dep not in ("", "—"), f"13G {rid}: Incomplete without remaining dependency")
    if status in ("Complete", "Binding invariant"):
        check(actual not in ("", "—"), f"13G {rid}: {status} without actual result")
    refcheck(rid, actual, "13G")

for rid in order:
    t, s = treatment_by_id.get(rid), status_by_id.get(rid)
    if t == "N/A":
        check(s == "N/A", f"{rid}: treatment N/A but status {s}")
    if t == "Deferred":
        check(s == "Deliberately deferred", f"{rid}: treatment Deferred but status {s}")

# --- 13D deliberate-deferral register (P2S-08) ---
DEFREG = "13D_Deliberate_Deferral_Register.md"
if os.path.exists(DEFREG):
    dref = {}
    for line in open(DEFREG):
        m = re.match(r"^\| ([A-Z]+-\d+) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$", line)
        if m:
            dref[m.group(1)] = [g.strip() for g in m.groups()[1:]]
    deferred = [r for r in all_ids if status_by_id.get(r) == "Deliberately deferred"]
    for rid in deferred:
        if rid not in dref:
            check(False, f"13D: deferred row {rid} has no register entry")
        else:
            check(all(f not in ("", "—") for f in dref[rid]),
                  f"13D {rid}: entry missing one of authority/rationale/destination/dependency/trigger")
    for rid in dref:
        check(rid in deferred, f"13D: entry {rid} is not a Deliberately deferred row in 13G")
else:
    check(False, "13D_Deliberate_Deferral_Register.md missing (P2S-08)")

if "--final-gate" in sys.argv[1:]:
    for rid in all_ids:
        if treatment_by_id.get(rid) in ("Binding", "Design subject", "Design subject (proposed)"):
            s = status_by_id.get(rid, "")
            if s not in GATE_OK:
                check(False, f"FINAL GATE {rid}: status '{s}' blocks the design gate")

if failures:
    print(f"FAIL — {len(failures)} check(s):")
    for msg in failures[:40]:
        print(f"  - {msg}")
    if len(failures) > 40:
        print(f"  ... and {len(failures)-40} more")
    sys.exit(1)

mode = "final-gate" if "--final-gate" in sys.argv[1:] else "structural"
from collections import Counter
cnt = Counter(status_by_id[r] for r in order)
print(f"PASS ({mode}) — 133 rows in both matrices, text hashes bound to the exact register/plan texts, "
      f"references resolve; accepted statuses: {dict(sorted(cnt.items()))}. "
      f"NOTE: structural validation only — semantic sufficiency is the human verifier's judgment (P2G-01).")

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

  7. (P2T-05) SUMMARY CONSISTENCY: any declared status-count block in 13G is
     parsed and must agree with the actual rows. The verifier found 13G
     asserting "Complete: 33 / Incomplete: 57" in its closing block while its
     rows said 90 Complete — and both validators returned PASS, because they
     validated the table and never read the document's own summary of it.
     A ledger cannot be the gate's evidence surface while presenting two
     incompatible snapshots of itself.

  8. (P2T-05) FINDING DEPENDENCIES: a Remaining-dependency cell may name a
     controlling finding as `P2T-02: ...`. Under --final-gate a row whose
     dependency names an OPEN finding fails, whatever its status — so a
     requirement cannot sit Complete while a Critical/High finding against its
     evidence is open. Open findings are read from `13F_Open_Findings.json`
     (format below, Fable-maintained). If a row names a finding and that file is
     absent, --final-gate FAILS: an unreadable list means the finding's state is
     unknown, and unknown is not closed.

`13F_Open_Findings.json` format (Builder-designed, documented here so the file
and its reader cannot drift apart):

    {
      "schema": "open-findings/1",
      "generated_by": "Fable (control plane)",
      "open": [
        {"id": "P2T-01", "severity": "Critical",
         "title": "gate does not enforce the complete expected result",
         "blocks_gate": true}
      ]
    }

  * `open` lists findings that are NOT yet closed. A closed finding is removed
    from the list (or given `"blocks_gate": false` if it is open but agreed
    non-blocking).
  * `id` must match the token before the colon in a dependency cell.
  * Any other key is ignored, so the file can carry notes without breaking.

Exit 0 only if all checks pass. Run from this directory.
Also: `--self-test` builds synthetic matrices in a temp directory and proves the
two new checks fail when they should; it touches no repository file.
"""
import csv
import hashlib
import json
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

OPEN_FINDINGS = "13F_Open_Findings.json"
# A dependency cell may open with a controlling finding id, e.g.
# "P2T-02: fold must fail closed on a missing causal basis".
DEP_FINDING = re.compile(r"^\s*([A-Z][A-Z0-9]*-\d+)\s*:")
# Closure finding L-7: a cell that plainly INTENDS a finding reference but is
# mistyped ("P2T2:", "p2t-02:") silently became a non-reference, so the row stopped
# being gated and nothing said so. This matches the intent; anything it catches that
# DEP_FINDING does not is reported as malformed.
DEP_LOOKS_LIKE_FINDING = re.compile(r"^\s*([A-Za-z][A-Za-z0-9-]{1,11})\s*:")


def parse_declared_summary(text):
    """Parse 13G's own declared status-count block(s).

    Returns (accepted, proposed, found) where the first two are {status: count}
    and `found` says whether any declared block existed at all. A document that
    declares no summary cannot contradict itself, which is reported rather than
    silently treated as agreement.
    """
    accepted, proposed = {}, {}
    found = False
    for line in text.splitlines():
        if "status counts" not in line.lower():
            continue
        found = True
        head, _, tail = line.partition("Proposed DE-R rows:")
        for target, chunk in ((accepted, head), (proposed, tail)):
            for m in re.finditer(r"([A-Za-z][A-Za-z/ -]*?):\s*(\d+)", chunk):
                label = m.group(1).strip()
                if label.lower().startswith(("accepted-row", "proposed")):
                    continue
                target[label] = int(m.group(2))
    return accepted, proposed, found


def summary_problems(overlay_text, accepted_counts, proposed_counts):
    """Declared counts must equal the counts derived from the rows."""
    problems = []
    declared_a, declared_p, found = parse_declared_summary(overlay_text)
    if not found:
        return ["13G declares no status-count summary block (P2T-05 requires the "
                "counts be stated and derived, so a stale block cannot reappear)"]
    for label, declared, actual, which in (
            (declared_a, declared_a, accepted_counts, "accepted"),
            (declared_p, declared_p, proposed_counts, "proposed DE-R"),
    ):
        for status, count in sorted(declared.items()):
            if status == "total":
                continue
            if actual.get(status, 0) != count:
                problems.append("13G %s summary says %s: %d, rows say %d"
                                % (which, status, count, actual.get(status, 0)))
        for status, count in sorted(actual.items()):
            if status not in declared:
                problems.append("13G %s summary omits %s (%d row(s) have it)"
                                % (which, status, count))
        if "total" in declared and declared["total"] != sum(actual.values()):
            problems.append("13G %s summary total %d != %d rows"
                            % (which, declared["total"], sum(actual.values())))
    return problems


def load_open_findings(path=OPEN_FINDINGS):
    """(open_ids, note). Absent file => None, so callers can fail closed."""
    if not os.path.exists(path):
        return None, "%s absent" % path
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, "%s unreadable: %s" % (path, exc)
    ids = {str(e.get("id")) for e in doc.get("open", [])
           if isinstance(e, dict) and e.get("blocks_gate", True)}
    return ids, "%s: %d gate-blocking open finding(s)" % (path, len(ids))


def finding_dependency_problems(dep_by_id, status_by_id, open_ids, note):
    """Under --final-gate, an open controlling finding blocks its rows."""
    problems = []
    referencing = {rid: DEP_FINDING.match(dep).group(1)
                   for rid, dep in dep_by_id.items() if DEP_FINDING.match(dep or "")}
    for rid, dep in sorted(dep_by_id.items()):
        if DEP_FINDING.match(dep or ""):
            continue
        m = DEP_LOOKS_LIKE_FINDING.match(dep or "")
        token = m.group(1) if m else ""
        if token and any(c.isdigit() for c in token) and any(c.isalpha() for c in token):
            problems.append("13G %s: dependency %r looks like a finding reference but "
                            "does not parse as one — it would silently stop gating "
                            "this row" % (rid, token))
    if not referencing:
        return problems
    if open_ids is None:
        problems.append("FINAL GATE: %d row(s) name a controlling finding but the "
                        "open-findings list is unavailable (%s) — unknown is not "
                        "closed" % (len(referencing), note))
        return problems
    for rid, finding in sorted(referencing.items()):
        if finding in open_ids:
            problems.append("FINAL GATE %s: status '%s' but controlling finding %s is "
                            "open" % (rid, status_by_id.get(rid, "?"), finding))
    return problems


def _self_test():
    """Prove the two new checks fail when they should. Touches no repo file."""
    cases = []

    rows = {"Complete": 90, "Incomplete": 3}
    good = ("**Accepted-row status counts:** Complete: 90; Incomplete: 3 — total 93.")
    stale = ("**Accepted-row status counts:** Complete: 33; Incomplete: 57 — total 90.")
    missing_status = ("**Accepted-row status counts:** Complete: 90 — total 90.")

    cases.append(("summary agrees with rows", "PASS",
                  not summary_problems(good, rows, {})))
    cases.append(("summary contradicts rows (the exact 13G defect)", "FAIL",
                  bool(summary_problems(stale, rows, {}))))
    cases.append(("summary omits a status the rows carry", "FAIL",
                  bool(summary_problems(missing_status, rows, {}))))
    cases.append(("document declares no summary block at all", "FAIL",
                  bool(summary_problems("no counts here", rows, {}))))

    deps = {"APP-04": "P2T-02: fold must fail closed", "ACT-01": "—"}
    stat = {"APP-04": "Complete", "ACT-01": "Complete"}
    cases.append(("row depends on an OPEN finding", "FAIL",
                  bool(finding_dependency_problems(deps, stat, {"P2T-02"}, "test"))))
    cases.append(("row depends on a CLOSED finding", "PASS",
                  not finding_dependency_problems(deps, stat, set(), "test")))
    cases.append(("open-findings list unavailable while a row names one", "FAIL",
                  bool(finding_dependency_problems(deps, stat, None, "absent"))))
    cases.append(("no row names a finding, list unavailable", "PASS",
                  not finding_dependency_problems({"ACT-01": "—"}, stat, None, "absent")))
    for bad in ("P2T2: fold must fail closed", "p2t-02: fold must fail closed"):
        cases.append(("malformed finding token %r is reported" % bad.split(":")[0], "FAIL",
                      bool(finding_dependency_problems({"APP-04": bad}, stat, set(), "t"))))
    cases.append(("ordinary prose dependency is not mistaken for a finding", "PASS",
                  not finding_dependency_problems(
                      {"APP-04": "Build gate: live drill at activation"}, stat, set(), "t")))

    print("13V_ self-test (P2T-05 extensions)")
    ok_all = True
    for name, expect, ok in cases:
        ok = bool(ok)
        ok_all = ok_all and ok
        print("  %-56s expect %-4s %s" % (name, expect, "ok" if ok else "*** WRONG ***"))
    print("SELF-TEST %s" % ("PASS" if ok_all else "FAIL"))
    return 0 if ok_all else 1


if "--self-test" in sys.argv[1:]:
    sys.exit(_self_test())

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

dep_by_id = {}
for cells in grows:
    rid, h, status, actual, dep = cells
    dep_by_id[rid] = dep
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

# --- P2T-05 check 7: the document's own summary must match its own rows ---
from collections import Counter as _Counter
_accepted_counts = _Counter(status_by_id[r] for r in order if r in status_by_id)
_proposed_counts = _Counter(status_by_id[f"DE-R{n}"] for n in range(1, 9)
                            if f"DE-R{n}" in status_by_id)
for _msg in summary_problems(open(OVERLAY, encoding="utf-8").read(),
                             dict(_accepted_counts), dict(_proposed_counts)):
    check(False, _msg)

# --- P2T-05 check 8: an open controlling finding blocks its rows ---
_open_ids, _open_note = load_open_findings()

if "--final-gate" in sys.argv[1:]:
    for _msg in finding_dependency_problems(dep_by_id, status_by_id,
                                            _open_ids, _open_note):
        check(False, _msg)
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
      f"Declared summary agrees with the rows (P2T-05 check 7); open findings: {_open_note}. "
      f"NOTE: structural validation only — semantic sufficiency is the human verifier's judgment (P2G-01).")

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

  8. (P2T-05) FINDING DEPENDENCIES — TRACEABILITY. A Remaining-dependency cell
     may name a controlling finding as `P2T-02: ...`. Under --final-gate a row
     whose dependency names an OPEN gate-blocking finding fails, whatever its
     status; a cell that looks like a finding reference but does not parse as one
     is reported; and a cell naming an id the findings authority does not know at
     all is reported as unresolvable.

  9. (P2U-05) GLOBAL OPEN-FINDING GATE. Check 8 is traceability and was mistaken
     for enforcement. The verifier set the four finding-dependent rows to
     Complete, cleared their dependency cells, regenerated the count summary, and
     `--final-gate` returned exit code 0 and PASS with six `blocks_gate: true`
     findings still open. Deleting `13F_Open_Findings.json` outright also
     returned 0 — and this module's own self-test declared that correct ("no row
     names a finding, list unavailable" => PASS), so it was designed behavior,
     not an oversight.

     Under --final-gate, INDEPENDENTLY OF EVERY ROW:
       * a missing, unreadable, or schema-invalid `13F_Open_Findings.json` fails;
       * any finding with `blocks_gate: true` in `open` fails.
     Rows can no longer switch the gate off by not mentioning anything.

`13F_Open_Findings.json` format (Builder-designed, documented here so the file
and its reader cannot drift apart):

    {
      "schema": "open-findings/1",
      "generated_by": "Fable (control plane)",
      "open": [
        {"id": "P2T-01", "severity": "Critical",
         "title": "gate does not enforce the complete expected result",
         "blocks_gate": true}
      ],
      "closed": [{"id": "P2T-06"}]
    }

  * `schema` must be exactly "open-findings/1". A file that does not declare it
    is not this format and is refused rather than read hopefully.
  * `open` lists findings that are NOT yet closed. Each entry must be an object
    with a non-empty string `id`; `blocks_gate` defaults to true and must be a
    boolean when present. An open finding with `blocks_gate: false` is open but
    agreed non-blocking: it is reported and does not fail the gate.
  * `closed` (OPTIONAL, added for P2U-05) enumerates findings that have been
    closed. It exists so that a dependency cell naming `P2T-99` can be told apart
    from one naming a genuinely closed finding — without it, every id not in
    `open` looks closed, which is how a typo'd or fabricated reference passes.
    While `closed` is absent, --final-gate reports each row-named id it cannot
    resolve and fails: "I cannot tell whether this is closed" is the same state
    as "the list is unavailable", and this module already fails on that.
  * `id` must match the token before the colon in a dependency cell.
  * Any other key is ignored, so the file can carry notes without breaking.

Exit 0 only if all checks pass. Run from this directory.

`--self-test` runs two suites and touches no repository file:
  * the check-level cases, including file-level ones against real files written
    into a temp directory;
  * an END-TO-END probe that builds a complete synthetic matrix set (register,
    plan, 13M, 13G, 13D, 13F) in a temp directory and invokes THIS FILE as a
    subprocess with `--final-gate`, so the verifier's `32A_` evidence — an exit
    code from the real command — is reproduced in the same terms. Each probe runs
    twice: once against this file, once against a temp COPY with check 9 elided
    from its source, and the copy must still produce the exit code the verifier
    recorded. NOTHING in the shipped file can skip check 9 — see P2V-01 below.

**No argv disables any check (P2V-01).** An earlier version of this file accepted
`--p2u05-defect-witness`, which turned check 9 off so the probe could show the
counterfactual. That put a documented, public waiver on the gate command itself:
`--final-gate --p2u05-defect-witness` returned 0 with six blocking findings open.
The flag is deleted, the counterfactual is built by eliding the check from a
throwaway copy, and `--self-test` runs the real command with that flag and three
other plausible disable spellings and requires exit 1 for each.
"""
import csv
import hashlib
import json
import os
import re
import sys
import tempfile

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


FINDINGS_SCHEMA = "open-findings/1"

# P2V-01. There was a `--p2u05-defect-witness` flag here that disabled check 9, so
# that the end-to-end probe could show the same input still returning exit 0 with the
# check off. The reasoning was `fold(enforce_basis=False)`; the mistake was the
# delivery mechanism. `enforce_basis` is a keyword argument on a library function that
# no command line reaches. This was an argv flag on the gate command itself, which
# means the correction for P2U-05 shipped with a documented, public way to turn it
# back off — `13V_ --final-gate --p2u05-defect-witness` and six open blocking findings
# returned 0. A control that can be waived from the command line is a suggestion.
#
# The flag is gone. No argv, no environment variable, and no attribute of this module
# can skip check 9. Two self-tests hold that line:
#   * `_witness_source` builds the counterfactual by ELIDING the check from a COPY of
#     this file in a temp directory, so the defect is still observed rather than
#     asserted, and the thing that can be turned off is a throwaway copy;
#   * `--self-test` runs the real command with the deleted flag (and other plausible
#     disable spellings) and requires exit 1 — the P2V-01 probe as a failing case.
DISABLE_SPELLINGS_THAT_MUST_NOT_WORK = (
    "--p2u05-defect-witness",          # the flag this return deleted
    "--no-final-gate-findings",
    "--skip-open-findings",
    "--disable-check-9",
)


def load_findings(path=OPEN_FINDINGS):
    """Read the open-findings authority. Returns a state dict; never raises.

    P2U-05 replaced the previous `(open_ids, note)` return. That shape had exactly
    one failure signal — `None` for "absent or unreadable" — and a file that parsed
    as JSON but was not this format produced an empty id set indistinguishable from
    "no findings are open". `{"open": "P2T-01"}` is a string, not a list of entries;
    the old reader iterated its characters, found no dicts, and reported zero
    gate-blocking findings.

    Keys:
      available            the file exists, parses, and is schema-valid
      unavailable_reason   why not, when it is not
      blocking_ids         open findings with blocks_gate true
      nonblocking_ids      open findings explicitly agreed non-blocking
      closed_ids           the `closed` enumeration, or None if the file omits it
      note                 one line for the PASS/FAIL banner
    """
    def unusable(reason):
        return {"path": path, "available": False, "unavailable_reason": reason,
                "blocking_ids": set(), "nonblocking_ids": set(), "closed_ids": None,
                "note": "%s: %s" % (path, reason)}

    if not os.path.exists(path):
        return unusable("absent")
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        return unusable("unreadable: %s" % exc)

    if not isinstance(doc, dict):
        return unusable("malformed: top level is %s, not an object"
                        % type(doc).__name__)
    if doc.get("schema") != FINDINGS_SCHEMA:
        return unusable("malformed: schema is %r, not %r"
                        % (doc.get("schema"), FINDINGS_SCHEMA))
    if not isinstance(doc.get("open"), list):
        return unusable("malformed: 'open' is %s, not a list"
                        % type(doc.get("open")).__name__)
    if "closed" in doc and not isinstance(doc["closed"], list):
        return unusable("malformed: 'closed' is %s, not a list"
                        % type(doc["closed"]).__name__)

    blocking, nonblocking = set(), set()
    for i, entry in enumerate(doc["open"]):
        if not isinstance(entry, dict):
            return unusable("malformed: open[%d] is %s, not an object"
                            % (i, type(entry).__name__))
        fid = entry.get("id")
        if not isinstance(fid, str) or not fid.strip():
            return unusable("malformed: open[%d] has no usable 'id'" % i)
        blocks = entry.get("blocks_gate", True)
        if not isinstance(blocks, bool):
            return unusable("malformed: open[%d] ('%s') has non-boolean "
                            "blocks_gate %r" % (i, fid, blocks))
        (blocking if blocks else nonblocking).add(fid.strip())

    closed_ids = None
    if "closed" in doc:
        closed_ids = set()
        for i, entry in enumerate(doc["closed"]):
            fid = entry.get("id") if isinstance(entry, dict) else entry
            if not isinstance(fid, str) or not fid.strip():
                return unusable("malformed: closed[%d] has no usable 'id'" % i)
            closed_ids.add(fid.strip())

    return {
        "path": path, "available": True, "unavailable_reason": None,
        "blocking_ids": blocking, "nonblocking_ids": nonblocking,
        "closed_ids": closed_ids,
        "note": "%s: %d gate-blocking, %d open non-blocking, %s closed"
                % (path, len(blocking), len(nonblocking),
                   len(closed_ids) if closed_ids is not None else "no"),
    }


def global_finding_problems(state):
    """P2U-05 check 9 — the gate reads the findings authority, not the rows.

    No argument here is derived from the matrix. That is the correction: the
    previous mechanism could only fire through a row, so clearing four dependency
    cells switched it off while six gate-blocking findings stayed open.
    """
    if not state["available"]:
        return ["FINAL GATE: the open-findings authority is unusable (%s) — the "
                "state of every finding is therefore unknown, and unknown is not "
                "closed (P2U-05)" % state["note"]]
    problems = []
    if state["blocking_ids"]:
        problems.append(
            "FINAL GATE: %d finding(s) marked blocks_gate are open and block the "
            "design gate globally, whether or not any row names them: %s (P2U-05)"
            % (len(state["blocking_ids"]), ", ".join(sorted(state["blocking_ids"]))))
    return problems


def finding_dependency_problems(dep_by_id, status_by_id, state):
    """Under --final-gate, rows carry TRACEABILITY — no longer the gate itself.

    Three row-level problems, kept distinct because they mean different things:
      * a cell that looks like a finding reference and does not parse as one;
      * a row whose controlling finding is open and gate-blocking;
      * a row naming an id the authority cannot resolve — neither open nor listed
        as closed. Without a `closed` enumeration in `13F_` every unknown id looks
        closed, so a typo or an invented reference reads as a satisfied dependency.
    """
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
    if not state["available"]:
        problems.append("FINAL GATE: %d row(s) name a controlling finding but the "
                        "open-findings list is unavailable (%s) — unknown is not "
                        "closed" % (len(referencing), state["note"]))
        return problems
    known = set(state["blocking_ids"]) | set(state["nonblocking_ids"])
    closed = state["closed_ids"]
    for rid, finding in sorted(referencing.items()):
        if finding in state["blocking_ids"]:
            problems.append("FINAL GATE %s: status '%s' but controlling finding %s is "
                            "open" % (rid, status_by_id.get(rid, "?"), finding))
        elif finding not in known and (closed is None or finding not in closed):
            problems.append(
                "FINAL GATE %s: dependency names finding %s, which the authority "
                "neither lists as open nor %s — the reference is unresolvable and "
                "cannot be read as satisfied (P2U-05)"
                % (rid, finding,
                   "as closed" if closed is not None
                   else "enumerates as closed (%s declares no `closed` list)"
                        % state["path"]))
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

    def state(blocking=(), nonblocking=(), closed=None, available=True, reason=None):
        return {"path": "13F_(test)", "available": available,
                "unavailable_reason": reason, "blocking_ids": set(blocking),
                "nonblocking_ids": set(nonblocking),
                "closed_ids": None if closed is None else set(closed),
                "note": reason or "test"}

    deps = {"APP-04": "P2T-02: fold must fail closed", "ACT-01": "—"}
    stat = {"APP-04": "Complete", "ACT-01": "Complete"}
    closed_only = state(closed=["P2T-02"])
    cases.append(("row depends on an OPEN finding", "FAIL",
                  bool(finding_dependency_problems(deps, stat, state(["P2T-02"])))))
    cases.append(("row depends on a CLOSED finding", "PASS",
                  not finding_dependency_problems(deps, stat, closed_only)))
    cases.append(("open-findings list unavailable while a row names one", "FAIL",
                  bool(finding_dependency_problems(
                      deps, stat, state(available=False, reason="absent")))))
    for bad in ("P2T2: fold must fail closed", "p2t-02: fold must fail closed"):
        cases.append(("malformed finding token %r is reported" % bad.split(":")[0], "FAIL",
                      bool(finding_dependency_problems({"APP-04": bad}, stat,
                                                       closed_only))))
    cases.append(("ordinary prose dependency is not mistaken for a finding", "PASS",
                  not finding_dependency_problems(
                      {"APP-04": "Build gate: live drill at activation"}, stat,
                      closed_only)))

    # ---- P2U-05: the five cases the verifier named -----------------------
    # 1 and 2 are the two probes from `32A_`. Both used to be PASS, and case 2 was
    # this module's own self-test asserting that PASS was correct — the line
    # "no row names a finding, list unavailable => PASS" is deleted, not amended,
    # because the behavior it protected is the finding.
    norows = {"ACT-01": "—"}
    cases.append(("P2U-05 probe 1: gate-blocking finding open, NO row names it",
                  "FAIL",
                  bool(global_finding_problems(state(["P2T-01", "P2T-02"])))
                  and not finding_dependency_problems(norows, stat,
                                                      state(["P2T-01", "P2T-02"]))))
    cases.append(("P2U-05: closed / non-blocking findings only, no row names one",
                  "PASS",
                  not global_finding_problems(state(nonblocking=["P2T-06"],
                                                    closed=["P2T-01"]))
                  and not finding_dependency_problems(norows, stat,
                                                      state(closed=["P2T-01"]))))
    cases.append(("P2U-05: row names a finding id the authority cannot resolve",
                  "FAIL",
                  bool(finding_dependency_problems(
                      {"APP-04": "P2T-99: invented reference"}, stat, closed_only))))
    cases.append(("P2U-05: unresolvable id is reported even with no `closed` list",
                  "FAIL",
                  bool(finding_dependency_problems(
                      {"APP-04": "P2T-99: invented reference"}, stat,
                      state(["P2T-01"])))))

    # File-level cases: these are about a FILE, so they run against real files.
    with tempfile.TemporaryDirectory() as tmp:
        def write(name, text):
            p = os.path.join(tmp, name)
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            return p

        absent = os.path.join(tmp, "does-not-exist.json")
        cases.append(("P2U-05 probe 2: findings file MISSING, no row names one",
                      "FAIL",
                      bool(global_finding_problems(load_findings(absent)))
                      and not finding_dependency_problems(
                          norows, stat, load_findings(absent))))

        malformed = (
            ('not-json-at-all', "{{{"),
            ('top level is a list', "[]"),
            ('wrong schema', '{"schema": "something-else", "open": []}'),
            ("'open' is a string", '{"schema": "open-findings/1", "open": "P2T-01"}'),
            ('entry is not an object',
             '{"schema": "open-findings/1", "open": ["P2T-01"]}'),
            ('entry has no id',
             '{"schema": "open-findings/1", "open": [{"severity": "High"}]}'),
            ('blocks_gate is not a boolean',
             '{"schema": "open-findings/1", '
             '"open": [{"id": "P2T-01", "blocks_gate": "yes"}]}'),
            ("'closed' is not a list",
             '{"schema": "open-findings/1", "open": [], "closed": 3}'),
        )
        for i, (label, body) in enumerate(malformed):
            path = write("malformed-%d.json" % i, body)
            st = load_findings(path)
            cases.append(("P2U-05: malformed findings file — %s" % label, "FAIL",
                          not st["available"]
                          and bool(global_finding_problems(st))))

        good = write("good.json", json.dumps({
            "schema": FINDINGS_SCHEMA,
            "open": [{"id": "P2T-06", "severity": "Medium", "blocks_gate": False}],
            "closed": [{"id": "P2T-01"}, {"id": "P2T-02"}],
        }, indent=2) + "\n")
        gst = load_findings(good)
        cases.append(("P2U-05: well-formed file, nothing blocking -> gate is clear",
                      "PASS",
                      gst["available"] and not global_finding_problems(gst)
                      and gst["closed_ids"] == {"P2T-01", "P2T-02"}
                      and gst["nonblocking_ids"] == {"P2T-06"}))

        blocking = write("blocking.json", json.dumps({
            "schema": FINDINGS_SCHEMA,
            "open": [{"id": "P2T-01", "blocks_gate": True}],
        }, indent=2) + "\n")
        bst = load_findings(blocking)
        cases.append(("P2U-05: well-formed file with one blocking finding",
                      "FAIL",
                      bst["available"] and bool(global_finding_problems(bst))))

    print("13V_ self-test (P2T-05 + P2U-05 extensions)")
    ok_all = True
    for name, expect, ok in cases:
        ok = bool(ok)
        ok_all = ok_all and ok
        print("  %-56s expect %-4s %s" % (name, expect, "ok" if ok else "*** WRONG ***"))
    print("SELF-TEST %s — %d cases" % ("PASS" if ok_all else "FAIL", len(cases)))
    return 0 if ok_all else 1


def _build_synthetic_repo(root, findings_doc, clear_dependencies):
    """Write a complete, VALID synthetic matrix set under `root`.

    Everything the validator reads is generated here: the requirements register,
    the plan's DE-R blockquotes, 13M, 13G with a self-consistent count summary, the
    13D deferral register, and (optionally) 13F. No repository file is read or
    written. Artifact cells deliberately mention no `D-B<n>` stem, so the
    referential-integrity check has nothing to resolve and cannot fail for reasons
    unrelated to the probe.
    """
    ids = ["SYN-%d" % n for n in range(1, 126)]
    os.makedirs(os.path.join(root, "..", "phase1-audit-v1.0"), exist_ok=True)
    reg_path = os.path.join(root, "..", "phase1-audit-v1.0",
                            "05_Requirements_Register_v1.1.csv")
    texts = {rid: "synthetic requirement %s" % rid for rid in ids}
    with open(reg_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ID", "Requirement"])
        for rid in ids:
            w.writerow([rid, texts[rid]])

    plan_lines, der_hash = [], {}
    for n in range(1, 9):
        line = "> **DE-R%d (synthetic):** synthetic design requirement %d." % (n, n)
        plan_lines.append(line)
        der_hash["DE-R%d" % n] = hashlib.sha256(line.encode()).hexdigest()[:12]
    with open(os.path.join(root, PLAN), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(plan_lines) + "\n")

    def h(rid):
        return (der_hash[rid] if rid.startswith("DE-R")
                else hashlib.sha256(texts[rid].encode()).hexdigest()[:12])

    all_syn = ids + ["DE-R%d" % n for n in range(1, 9)]
    dep = "—" if clear_dependencies else "P2T-02: fold must fail closed"

    with open(os.path.join(root, MATRIX), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("| ID | Hash | Treatment | Mechanism | Artifact | Test |\n")
        fh.write("| --- | --- | --- | --- | --- | --- |\n")
        for rid in all_syn:
            fh.write("| %s | `%s` | Binding | synthetic mechanism | synthetic note | "
                     "synthetic test |\n" % (rid, h(rid)))

    with open(os.path.join(root, OVERLAY), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("| ID | Hash | Status | Actual result | Remaining dependency |\n")
        fh.write("| --- | --- | --- | --- | --- |\n")
        for rid in all_syn:
            cell = dep if rid == "SYN-1" else "—"
            fh.write("| %s | `%s` | Complete | synthetic result | %s |\n"
                     % (rid, h(rid), cell))
        fh.write("\n**Accepted-row status counts:** Complete: 125 — total 125. "
                 "Proposed DE-R rows: Complete: 8 — total 8.\n")

    with open(os.path.join(root, "13D_Deliberate_Deferral_Register.md"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("| ID | Authority | Rationale | Destination | Dependency | Trigger |\n")
        fh.write("| --- | --- | --- | --- | --- | --- |\n")

    findings_path = os.path.join(root, OPEN_FINDINGS)
    if findings_doc is None:
        if os.path.exists(findings_path):
            os.remove(findings_path)
    else:
        with open(findings_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(findings_doc if isinstance(findings_doc, str)
                     else json.dumps(findings_doc, indent=2) + "\n")


# The check-9 call site, anchored on the comment above it so the constant does not
# match itself. A bare `for _msg in global_finding_problems(_findings):` appeared
# twice — here and at the call site — and the elision guard below caught it on the
# first run rather than producing a "witness" copy identical to the shipped file.
CHECK9_CALL = ("    # which is the whole of the P2U-05 correction.\n"
               "    for _msg in global_finding_problems(_findings):\n"
               "        check(False, _msg)\n")
CHECK9_ELIDED = ("    # P2V-01 WITNESS COPY: check 9 elided by _witness_source().\n"
                 "    for _msg in []:\n"
                 "        check(False, _msg)\n")


def _witness_source(destination):
    """Write a COPY of this file with check 9 elided, and return its path.

    P2V-01. The counterfactual still has to exist — a check nobody has watched fail
    is a claim — but it must not be reachable from the shipped command. So the
    disable lives in a throwaway copy built by the test, not in a flag the gate
    accepts. The elision is asserted, not assumed: if the anchor line stops matching
    (because the call moved or was renamed) this raises instead of silently producing
    an identical copy that would "prove" the check is load-bearing by passing.
    """
    source = open(os.path.abspath(__file__), encoding="utf-8").read()
    if source.count(CHECK9_CALL) != 1:
        raise AssertionError(
            "witness elision anchor matched %d times, not once — the counterfactual "
            "would not remove check 9 and the witness would be meaningless"
            % source.count(CHECK9_CALL))
    elided = source.replace(CHECK9_CALL, CHECK9_ELIDED, 1)
    if elided == source:
        raise AssertionError("witness copy is identical to the shipped file")
    with open(destination, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(elided)
    return destination


def _probe_e2e():
    """Run the verifier's `32A_` P2U-05 probes against the REAL command.

    `--self-test` proves the checks behave; it does not prove the COMMAND does,
    and the verifier's evidence is an exit code from the command. This builds a
    complete synthetic matrix set in a temp directory and invokes this file as a
    subprocess, exactly as the verifier invoked it — same argv, same exit-code
    reading.

    Both probes set every row Complete and clear the dependency cells, which is
    what made the old row-only mechanism silent. Probe 1 leaves gate-blocking
    findings open; probe 2 deletes the findings file. The verifier recorded exit
    code 0 and PASS for both.

    A third case is the control: identical rows, a well-formed findings file with
    nothing blocking, and the gate must return 0. Without it these probes would be
    satisfied by a validator that had simply learned to always fail.
    """
    import subprocess
    me = os.path.abspath(__file__)
    blocking = {"schema": FINDINGS_SCHEMA,
                "open": [{"id": "P2T-0%d" % n, "severity": "High",
                          "title": "synthetic", "blocks_gate": True}
                         for n in range(1, 7)]}
    clear = {"schema": FINDINGS_SCHEMA, "open": [],
             "closed": [{"id": "P2T-0%d" % n} for n in range(1, 7)]}
    # `witness` is the exit code the SAME synthetic repo must produce with check 9
    # disabled — the verifier's recorded observation. Where it is 0, this run
    # reproduces the defect rather than describing it; a check that cannot be turned
    # off has not been shown to be doing anything. `None` means the case is not about
    # check 9 and the witness would prove nothing.
    probes = [
        ("32A_ probe 1: rows Complete, dependencies cleared, 6 findings open",
         blocking, True, 1, "block the design gate globally", 0),
        ("32A_ probe 2: same rows, findings file deleted",
         None, True, 1, "unusable", 0),
        ("control: same rows, findings file clear -> the gate must PASS",
         clear, True, 0, "PASS", None),
        ("malformed findings file, no row names a finding",
         '{"schema": "open-findings/1", "open": "P2T-01"}', True, 1, "malformed", 0),
        ("row names an open finding (traceability leg still live)",
         blocking, False, 1, "controlling finding", 1),
    ]
    print("13V_ end-to-end probe (P2U-05) — the real command, real exit codes")
    print("  WITNESS column: the exit code the same repo gives with check 9 disabled")
    print("  — 0 there is the verifier's recorded observation, reproduced.")
    ok_all = True
    for label, doc, cleared, want_code, want_text, want_witness in probes:
        with tempfile.TemporaryDirectory() as tmp:
            work = os.path.join(tmp, "repo")
            os.makedirs(work)
            _build_synthetic_repo(work, doc, cleared)
            proc = subprocess.run([sys.executable, me, "--final-gate"], cwd=work,
                                  capture_output=True, text=True)
            out = (proc.stdout + proc.stderr).strip()
            ok = proc.returncode == want_code and want_text in out
            witness_code = None
            if want_witness is not None:
                # P2V-01: the counterfactual runs a COPY with check 9 elided. The
                # shipped file has no flag that would do this.
                copy = _witness_source(os.path.join(tmp, "witness_copy.py"))
                wproc = subprocess.run([sys.executable, copy, "--final-gate"],
                                       cwd=work, capture_output=True, text=True)
                witness_code = wproc.returncode
                ok = ok and witness_code == want_witness
            ok_all = ok_all and ok
            print("  %-58s exit %d (want %d)  witness %s (want %s)  %s"
                  % (label[:58], proc.returncode, want_code,
                     "-" if witness_code is None else witness_code,
                     "-" if want_witness is None else want_witness,
                     "ok" if ok else "*** WRONG ***"))
            print("      %s" % (out.splitlines()[0] if out else "(no output)")[:104])
            if len(out.splitlines()) > 1:
                print("      %s" % out.splitlines()[1][:104])
    # ---- P2V-01: no argv may switch check 9 off ------------------------------
    print()
    print("  P2V-01 — the deleted disable flag, and other plausible spellings, must")
    print("  NOT switch check 9 off. Each is run against a repository with six open")
    print("  gate-blocking findings and must still exit 1.")
    with tempfile.TemporaryDirectory() as tmp:
        work = os.path.join(tmp, "repo")
        os.makedirs(work)
        _build_synthetic_repo(work, blocking, True)
        for flag in DISABLE_SPELLINGS_THAT_MUST_NOT_WORK:
            proc = subprocess.run([sys.executable, me, "--final-gate", flag],
                                  cwd=work, capture_output=True, text=True)
            out = (proc.stdout + proc.stderr).strip()
            ok = proc.returncode == 1 and "block the design gate globally" in out
            ok_all = ok_all and ok
            print("    %-34s exit %d (want 1)  %s"
                  % (flag, proc.returncode, "ok" if ok else "*** DISABLED THE CHECK ***"))
        # And the flag is not merely ignored — the constant is gone from the source.
        # The token is assembled at runtime: written as a literal it would appear in
        # this line and the check would report itself. That is the third self-match
        # in this file today (the elision anchor matched its own constant, twice), so
        # it is worth naming: a source check whose own text satisfies the pattern it
        # searches for is not a check.
        removed_constant = "P2U05_" + "WITNESS_FLAG"
        src = open(me, encoding="utf-8").read()
        gone = removed_constant not in src
        ok_all = ok_all and gone
        print("    %-34s %s" % ("flag constant gone from the source",
                                "ok" if gone else "*** STILL PRESENT ***"))

    print("END-TO-END PROBE %s — %d gate cases + %d disable-spelling cases"
          % ("PASS" if ok_all else "FAIL", len(probes),
             len(DISABLE_SPELLINGS_THAT_MUST_NOT_WORK)))
    return 0 if ok_all else 1


if "--self-test" in sys.argv[1:]:
    rc = _self_test()
    print()
    sys.exit(rc or _probe_e2e())

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

# --- P2T-05 check 8 (row traceability) + P2U-05 check 9 (global gate) ---
_findings = load_findings()

if "--final-gate" in sys.argv[1:]:
    # Check 9 FIRST and with no matrix input at all: the rows cannot influence it,
    # which is the whole of the P2U-05 correction.
    for _msg in global_finding_problems(_findings):
        check(False, _msg)
    for _msg in finding_dependency_problems(dep_by_id, status_by_id, _findings):
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
      f"Declared summary agrees with the rows (P2T-05 check 7); open findings: {_findings['note']}. "
      f"NOTE: structural validation only — semantic sufficiency is the human verifier's judgment (P2G-01).")

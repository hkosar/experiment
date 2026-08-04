#!/usr/bin/env python3
# THROWAWAY POC EVIDENCE APPARATUS — see ../stub/stub_server.py header.
"""Completeness and provenance validator for the POC measurement record (`25_` §D).

Rev 4 treated an `evidence_ref` as resolvable merely because the named file
existed, so one unrelated file could be cited for every result. This validator
implements the correction: **evidence is a record, bound to the exact
measurement tuple.**

What it enforces, and nothing else:

    MEASURED     value REQUIRED (non-null); evidence_ref REQUIRED, resolvable,
                 AND the evidence record's candidate / poc / measure_id /
                 observed_value MUST MATCH the measurement
    NOT_TESTED   reason REQUIRED (non-empty)
    UNSUPPORTED  reason REQUIRED AND capability_gap_evidence REQUIRED, naming
                 the SAME candidate, poc, and capability/measure

It also enumerates the full expected (candidate x POC x measure) matrix and
fails on any missing combination, so nothing disappears by omission. Path
existence is a preliminary integrity check only, never the provenance rule.

**It judges completeness and provenance, never values.** Whether a measured
number is plausible, favourable or correct is not this program's business; it
checks that a number claiming to be measured is accompanied by a record that
says it was measured, of this thing, by someone, from something hashable.

Usage:
    python3 validate_measurements.py [path ...]      (default: the template)
Exit:
    0  no violations
    1  one or more violations (each printed, with its tuple)
    2  the file could not be read or parsed
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.join(HERE, "measurements.template.json")

VALID_STATUSES = ("MEASURED", "NOT_TESTED", "UNSUPPORTED")

# --------------------------------------------------------------------------
# The expected matrix. `25_` §D requires it to be enumerated here rather than
# inferred from the document, because a matrix read out of the file being
# checked cannot detect the thing it exists to detect: an omission.
# --------------------------------------------------------------------------
CANDIDATES = ("zapier", "n8n")
POCS = ("POC1", "POC2", "POC3")

# `25_` §D's required measure family, mapped to the measure_id that carries it.
# The left column is what the validator requires to be present for EVERY
# candidate x POC; the right column is the §D phrase it answers to, so the
# mapping can be checked against the packet without reading the code.
REQUIRED_MEASURE_FAMILY = {
    "artifact_bytes": "artifact bytes",
    "artifact_file_count": "file count",
    "artifact_source_digest": "source digest",
    "destination_digest_claimed": "destination digest CLAIMED (non-authoritative, §C)",
    "original_vs_reconstituted": "original-vs-reconstituted (UNSUPPORTED by default)",
    "provider_task_count": "provider task count",
    "provider_step_count": "provider step count",
    "provider_execution_count": "provider execution count",
    "owner_friction_step_count": "owner-attention steps",
    "owner_friction_total_minutes": "owner-attention minutes",
    "approval_latency_seconds": "approval latency",
    "retry_count": "retry count",
    "uncertain_reconciliation_outcome": "uncertain-result reconciliation outcome",
    "capture_receipt_completeness": "capture/receipt completeness",
    "provider_retention_deletion_observation": "provider retention/deletion observation",
    "failure_or_unsupported_capability_reason": "failure/unsupported-capability reason",
}

# The per-POC comparison measures the round set out to collect. These are
# enumerated for the same reason: a measure that quietly stops being reported
# is exactly what §D's matrix rule is for.
POC_MEASURES = {
    "POC1": ("connector_coverage", "setup_wall_clock_minutes", "human_approval_support",
             "response_monitoring", "evidence_quality", "duplicate_send_prevention",
             "monthly_cost_at_expected_volume", "connection_revocation_severs_access",
             "revocation_time_to_effect_seconds", "billing_units_consumed",
             "actual_cost_incurred"),
    "POC2": ("setup_wall_clock_minutes", "classification_handoff", "trust_isolation",
             "queue_update", "mobile_visibility", "data_handling",
             "end_to_end_latency_seconds", "cost_per_1000_messages",
             "billing_units_consumed", "actual_cost_incurred"),
    "POC3": ("setup_wall_clock_minutes", "missed_run_detected",
             "time_to_missed_run_alert_seconds", "watchdog_independence",
             "retry_semantics", "durability_across_induced_kill",
             "checkpoint_integration", "evidence_and_replay",
             "side_effect_uncertainty_handling", "billing_units_consumed",
             "actual_cost_incurred"),
}

EVIDENCE_REQUIRED_FIELDS = ("candidate", "poc", "measure_id", "observed_value",
                            "unit", "observed_at", "collector",
                            "artifact_or_capture_hash")


def expected_matrix():
    """Every (candidate, poc, measure_id) the document must account for."""
    for candidate in CANDIDATES:
        for poc in POCS:
            for measure in sorted(set(POC_MEASURES[poc])
                                  | set(REQUIRED_MEASURE_FAMILY)):
                yield candidate, poc, measure


class Report:
    def __init__(self):
        self.violations = []
        self.checked = 0

    def fail(self, candidate, poc, measure, rule, detail):
        self.violations.append({"candidate": candidate, "poc": poc,
                                "measure_id": measure, "rule": rule,
                                "detail": detail})

    def ok(self):
        return not self.violations


def _nonempty_str(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_document(doc, path, report: Report):
    if not isinstance(doc, dict):
        report.fail("-", "-", "-", "document", "the document is not a JSON object")
        return

    records = doc.get("evidence_records")
    if records is None:
        records = {}
    if not isinstance(records, dict):
        report.fail("-", "-", "-", "evidence_records",
                    "evidence_records must be an object keyed by evidence_ref")
        records = {}

    candidates = doc.get("candidates")
    if not isinstance(candidates, dict):
        report.fail("-", "-", "-", "document",
                    "the document has no `candidates` object")
        candidates = {}

    seen = set()
    for candidate, cbody in sorted(candidates.items()):
        pocs = (cbody or {}).get("pocs")
        if not isinstance(pocs, dict):
            report.fail(candidate, "-", "-", "structure",
                        "candidate has no `pocs` object")
            continue
        for poc, pbody in sorted(pocs.items()):
            measures = (pbody or {}).get("measures")
            if not isinstance(measures, dict):
                report.fail(candidate, poc, "-", "structure",
                            "POC has no `measures` object")
                continue
            for measure, m in sorted(measures.items()):
                seen.add((candidate, poc, measure))
                report.checked += 1
                _validate_measurement(candidate, poc, measure, m, records,
                                      path, report)

    # The matrix rule: nothing disappears by omission.
    for tup in expected_matrix():
        if tup not in seen:
            report.fail(tup[0], tup[1], tup[2], "matrix",
                        "expected (candidate x POC x measure) combination is "
                        "absent from the document")


def _validate_measurement(candidate, poc, measure, m, records, path, report):
    if not isinstance(m, dict):
        report.fail(candidate, poc, measure, "structure",
                    "measurement is not an object")
        return
    status = m.get("status")
    if status not in VALID_STATUSES:
        report.fail(candidate, poc, measure, "status",
                    "status %r is not one of %s" % (status, list(VALID_STATUSES)))
        return

    if status == "NOT_TESTED":
        if not _nonempty_str(m.get("reason")):
            report.fail(candidate, poc, measure, "NOT_TESTED",
                        "NOT_TESTED requires a non-empty `reason`")
        return

    if status == "UNSUPPORTED":
        if not _nonempty_str(m.get("reason")):
            report.fail(candidate, poc, measure, "UNSUPPORTED",
                        "UNSUPPORTED requires a non-empty `reason`")
        gap = m.get("capability_gap_evidence")
        if not isinstance(gap, dict):
            report.fail(candidate, poc, measure, "UNSUPPORTED",
                        "UNSUPPORTED requires a `capability_gap_evidence` object")
            return
        # It must name the SAME candidate, poc and capability/measure. A gap
        # note that names something else is the Rev-4 defect in another form.
        if gap.get("candidate") != candidate:
            report.fail(candidate, poc, measure, "UNSUPPORTED",
                        "capability_gap_evidence names candidate %r, not %r"
                        % (gap.get("candidate"), candidate))
        if gap.get("poc") != poc:
            report.fail(candidate, poc, measure, "UNSUPPORTED",
                        "capability_gap_evidence names poc %r, not %r"
                        % (gap.get("poc"), poc))
        named = gap.get("capability") or gap.get("measure_id")
        if named != measure:
            report.fail(candidate, poc, measure, "UNSUPPORTED",
                        "capability_gap_evidence names capability/measure %r, "
                        "not %r" % (named, measure))
        if not _nonempty_str(gap.get("detail")):
            report.fail(candidate, poc, measure, "UNSUPPORTED",
                        "capability_gap_evidence requires a non-empty `detail`")
        return

    # MEASURED
    if m.get("value") is None:
        report.fail(candidate, poc, measure, "MEASURED",
                    "MEASURED requires a non-null `value`")
    ref = m.get("evidence_ref")
    if not _nonempty_str(ref):
        report.fail(candidate, poc, measure, "MEASURED",
                    "MEASURED requires an `evidence_ref`")
        return
    record = records.get(ref)
    if record is None:
        report.fail(candidate, poc, measure, "MEASURED",
                    "evidence_ref %r does not resolve to a measurement-evidence "
                    "record" % ref)
        return
    if not isinstance(record, dict):
        report.fail(candidate, poc, measure, "MEASURED",
                    "evidence record %r is not an object" % ref)
        return

    missing = [f for f in EVIDENCE_REQUIRED_FIELDS if f not in record]
    if missing:
        report.fail(candidate, poc, measure, "MEASURED",
                    "evidence record %r is missing %s" % (ref, missing))

    # The binding: the record must be about THIS measurement, not merely exist.
    for field, want in (("candidate", candidate), ("poc", poc),
                        ("measure_id", measure)):
        if record.get(field) != want:
            report.fail(candidate, poc, measure, "MEASURED",
                        "evidence record %r declares %s=%r, but the measurement "
                        "is %r" % (ref, field, record.get(field), want))
    if record.get("observed_value") != m.get("value"):
        report.fail(candidate, poc, measure, "MEASURED",
                    "evidence record %r declares observed_value %r, but the "
                    "measurement reports %r"
                    % (ref, record.get("observed_value"), m.get("value")))
    if not _nonempty_str(record.get("collector")):
        report.fail(candidate, poc, measure, "MEASURED",
                    "evidence record %r names no collector" % ref)
    if not _nonempty_str(record.get("artifact_or_capture_hash")):
        report.fail(candidate, poc, measure, "MEASURED",
                    "evidence record %r carries no artifact_or_capture_hash" % ref)

    # Preliminary integrity check ONLY. A resolvable path is not provenance —
    # the tuple match above is. This exists to catch a citation to a file that
    # is simply not there, and it never stands in for the binding.
    src = record.get("source_path")
    if _nonempty_str(src):
        full = src if os.path.isabs(src) else os.path.join(os.path.dirname(path), src)
        if not os.path.exists(full):
            report.fail(candidate, poc, measure, "MEASURED",
                        "evidence record %r cites source_path %r, which does not "
                        "exist (preliminary integrity check)" % (ref, src))


def validate_path(path, report: Report) -> int:
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except OSError as exc:
        sys.stderr.write("cannot read %s: %s\n" % (path, exc))
        return 2
    except ValueError as exc:
        sys.stderr.write("cannot parse %s: %s\n" % (path, exc))
        return 2
    validate_document(doc, path, report)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Validate POC measurement completeness and provenance (25_ §D)")
    ap.add_argument("paths", nargs="*", default=None,
                    help="measurement documents (default: measurements.template.json)")
    ap.add_argument("--json", action="store_true",
                    help="emit the machine-readable report on stdout")
    args = ap.parse_args(argv)
    paths = args.paths or [DEFAULT_PATH]

    report = Report()
    for path in paths:
        rc = validate_path(path, report)
        if rc:
            return rc

    expected = sum(1 for _ in expected_matrix())
    out = {"check": "measurement completeness and provenance (25_ §D)",
           "paths": paths,
           "expected_combinations": expected,
           "measurements_checked": report.checked,
           "violations": report.violations,
           "ok": report.ok()}
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))

    for v in report.violations:
        sys.stderr.write("  [VIOLATION] %-6s %-5s %-42s %-12s %s\n"
                         % (v["candidate"], v["poc"], v["measure_id"],
                            v["rule"], v["detail"]))
    sys.stderr.write(
        "\n%s — %d measurements checked against %d expected combinations, "
        "%d violation(s)\n"
        % ("MEASUREMENT VALIDATION PASS" if report.ok()
           else "MEASUREMENT VALIDATION FAIL",
           report.checked, expected, len(report.violations)))
    return 0 if report.ok() else 1


if __name__ == "__main__":
    sys.exit(main())

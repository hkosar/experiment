#!/usr/bin/env python3
"""D-EC_ receipt-conformance gap analysis for provider results.

Packet `07_` §4 asks for "receipt/evidence quality against the D-EC_ shape (what
fields a provider result actually carries vs what the wrapper must synthesize)".
This computes that gap mechanically: feed it a captured provider result and it
reports, field by field, PRESENT / DERIVABLE / MUST-BE-SYNTHESIZED.

The required shape is taken from `D-EC_Evidence_and_Schedule_Contracts.md` and
the TASK-0005 R5 encoding it anchors — the three-authority separation (§1), the
occurrence window (§4), and the rule that a provider result is corroborating raw
material, never a receipt (`05_` §2 standing rules).

WHAT THIS PROVES: for any supplied provider result, exactly which D-EC_ fields
that provider can and cannot supply.
WHAT THIS DOES NOT PROVE: anything about Zapier or n8n specifically, until real
captured results are fed in. No provider result has been captured — see
data/measurements.template.json, where those captures belong.

Usage:
  receipt_conformance.py <provider_result.json> [...]
  receipt_conformance.py --fields          # the requirement inventory
  receipt_conformance.py --self-test
Exit: 0 ok / 1 self-test failure / 2 usage error
"""
from __future__ import annotations

import json
import sys

# field -> (D-EC_ basis, who can supply it)
#   provider      the executing fabric can carry it
#   wrapper       only the AI OS can mint it; a provider value would be self-attestation
#   authority     a party structurally distinct from the provider must supply it
REQUIRED = {
    "receipt_id":            ("D-EC_ §1 receipt identity", "provider"),
    "subject_ref":           ("D-EC_ §1 the receipt names its subject", "provider"),
    "executed_at":           ("D-EC_ §4 occurrence temporal validity", "provider"),
    "occurrence":            ("D-EC_ §4 receipt satisfies only its own occurrence", "wrapper"),
    "schedule_version":      ("D-EC_ §4 version-bound run receipts", "wrapper"),
    "purpose":               ("D-EC_ §1 evidence purpose", "authority"),
    "authority_id":          ("D-EC_ §1 receipt authority, distinct from evidence source", "authority"),
    "authority_version":     ("D-EC_ §1 bound authority version", "authority"),
    "content_hash":          ("D-EC_ §1 canonical row digest; a self-declared identity is not an identity", "wrapper"),
    "action_request_id":     ("05_ §2 every consequential action crosses as an ActionRequest", "wrapper"),
    "action_class":          ("D-EC_ §1 contract key", "wrapper"),
    "scope":                 ("D-EC_ §1 contract key", "wrapper"),
    "policy_version":        ("D-EC_ §1 contract key; one artifact, one version", "wrapper"),
    "risk_class":            ("D-EC_ §1 contract key", "wrapper"),
    "idempotency_key":       ("ACT-01 / 04_ §2 semantic idempotency stays with the AI OS", "wrapper"),
    "side_effect_status":    ("ACT-01 uncertain outcomes halt automatic retry", "provider"),
}

# Common provider-result spellings that a wrapper can map without inventing data.
ALIASES = {
    "receipt_id": ("id", "execution_id", "executionId", "run_id", "task_id"),
    "executed_at": ("finished_at", "finishedAt", "stoppedAt", "timestamp", "completed_at"),
    "subject_ref": ("resource", "target", "object_id", "url"),
    "side_effect_status": ("status", "state", "result"),
}


def analyse(result: dict, label: str) -> dict:
    flat = {k.lower(): v for k, v in result.items()}
    rows = []
    for field, (basis, who) in REQUIRED.items():
        if field in flat and flat[field] not in (None, ""):
            state = "PRESENT"
            via = field
        else:
            via = next((a for a in ALIASES.get(field, ()) if a.lower() in flat
                        and flat[a.lower()] not in (None, "")), None)
            if via:
                state = "DERIVABLE"
            else:
                state = "MUST-BE-SYNTHESIZED"
                via = None
        # A provider supplying an authority-owned field is not conformance, it is
        # the P2Y-01 defect: the party being attested to writing its own attestation.
        flag = None
        if who == "authority" and state in ("PRESENT", "DERIVABLE"):
            flag = ("provider supplied an AUTHORITY-owned field — under D-EC_ §1 this "
                    "value is NOT usable as supplied; the wrapper must obtain it from "
                    "the receipt authority, not from the executing provider")
        if who == "wrapper" and state in ("PRESENT", "DERIVABLE"):
            flag = ("provider supplied a WRAPPER-owned field — treat as corroborating "
                    "raw material only (05_ §2); the wrapper still mints the value")
        rows.append({"field": field, "d_ec_basis": basis, "owner": who,
                     "state": state, "sourced_from": via, "caution": flag})
    counts = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    return {
        "result_label": label,
        "fields": rows,
        "counts": counts,
        "provider_can_supply": sum(1 for r in rows if r["owner"] == "provider"),
        "wrapper_must_mint": sum(1 for r in rows if r["owner"] == "wrapper"),
        "authority_must_supply": sum(1 for r in rows if r["owner"] == "authority"),
        "cautions": [r["field"] for r in rows if r["caution"]],
    }


def self_test() -> int:
    cases = []
    # A rich provider result: many fields present, but ownership still governs.
    rich = {"id": "exec-1", "finishedAt": "2026-08-03T03:00:00Z", "status": "success",
            "resource": "crm:lead-9", "purpose": "kill-command-delivery",
            "authority_id": "the-provider-itself"}
    a = analyse(rich, "rich")
    cases.append(("rich result still flags authority fields",
                  "purpose" in a["cautions"] and "authority_id" in a["cautions"]))
    cases.append(("aliases resolve to DERIVABLE",
                  next(r for r in a["fields"] if r["field"] == "receipt_id")["state"] == "DERIVABLE"))
    cases.append(("wrapper-owned occurrence is not satisfiable by a bare result",
                  next(r for r in a["fields"] if r["field"] == "occurrence")["state"] == "MUST-BE-SYNTHESIZED"))
    empty = analyse({}, "empty")
    cases.append(("empty result -> every field synthesized",
                  empty["counts"].get("MUST-BE-SYNTHESIZED") == len(REQUIRED)))
    cases.append(("ownership totals sum to the field count",
                  empty["provider_can_supply"] + empty["wrapper_must_mint"]
                  + empty["authority_must_supply"] == len(REQUIRED)))
    blank = analyse({"receipt_id": "", "purpose": None}, "blank")
    cases.append(("empty-string and null count as absent",
                  next(r for r in blank["fields"] if r["field"] == "receipt_id")["state"]
                  == "MUST-BE-SYNTHESIZED"
                  and "purpose" not in blank["cautions"]))
    passed = sum(1 for _, ok in cases if ok)
    for label, ok in cases:
        sys.stderr.write("  [%s] %s\n" % ("ok  " if ok else "FAIL", label))
    print(json.dumps({"check": "receipt-conformance self-test",
                      "cases": [{"case": c, "ok": o} for c, o in cases],
                      "passed": passed, "total": len(cases)}, indent=2))
    sys.stderr.write("RECEIPT CONFORMANCE SELF-TEST %s — %d/%d\n"
                     % ("PASS" if passed == len(cases) else "FAIL", passed, len(cases)))
    return 0 if passed == len(cases) else 1


def main(argv):
    if argv and argv[0] == "--self-test":
        return self_test()
    if argv and argv[0] == "--fields":
        print(json.dumps({"contract": "D-EC_Evidence_and_Schedule_Contracts.md",
                          "required_fields": {k: {"basis": b, "owner": w}
                                              for k, (b, w) in REQUIRED.items()},
                          "aliases": {k: list(v) for k, v in ALIASES.items()}}, indent=2))
        return 0
    if not argv:
        print(json.dumps({
            "check": "D-EC_ receipt conformance",
            "analysed": [],
            "status": "NO PROVIDER RESULTS CAPTURED — the owner session has not run. "
                      "Every provider's receipt quality is NOT TESTED.",
            "required_field_count": len(REQUIRED),
            "ownership": {"provider": sum(1 for _, w in REQUIRED.values() if w == "provider"),
                          "wrapper": sum(1 for _, w in REQUIRED.values() if w == "wrapper"),
                          "authority": sum(1 for _, w in REQUIRED.values() if w == "authority")},
        }, indent=2))
        sys.stderr.write("RECEIPT CONFORMANCE: no captures to analyse — NOT TESTED\n")
        return 0
    out = []
    for path in argv:
        with open(path, encoding="utf-8") as fh:
            out.append(analyse(json.load(fh), path))
    print(json.dumps({"check": "D-EC_ receipt conformance", "analysed": out}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

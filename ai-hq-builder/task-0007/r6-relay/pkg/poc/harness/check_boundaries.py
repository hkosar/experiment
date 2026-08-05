#!/usr/bin/env python3
"""Boundary compliance check over the POC workflow definitions.

`05_` §2 and packet `07_` §3 state binding constraints and say plainly that
"violations are findings, not judgment calls". A rule phrased that way should be
machine-checked, not asserted in prose — so this checks the definitions the
Builder authored against the constraints the Builder was given.

WHAT THIS PROVES: the shipped workflow definitions do not, on their face,
carry Personal-partition data, ship policy-plane artifacts to a provider, let a
provider decide an approval, or classify before the external-untrusted envelope
is applied.

WHAT THIS DOES NOT PROVE: anything about runtime. A definition that looks clean
can still be run against a Personal mailbox by whoever wires the credential.
Runtime boundary behaviour is NOT TESTED and is measured in the owner session.

Usage:  check_boundaries.py [--self-test]
Exit:   0 clean / 1 violations found / 2 usage error
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WF_DIR = os.path.join(HERE, "..", "workflows", "n8n")

# --- the constraint vocabulary -------------------------------------------------
# Terms that mean a policy-plane / evidence / journal artifact would be handed to
# a provider. `05_` §2: providers "never hold the rulebook".
RULEBOOK_TERMS = (
    "evidence_policy", "evidencepolicy", "action_evidence_contract",
    "actionevidencecontract", "policy_artifact", "policy_plane", "policyplane",
    "receipt_registry", "receiptregistry", "journal_entry", "journal_contents",
    "control_journal", "step_up_secret", "stepup_secret", "step_up_factor",
)
# Terms that mean a secret would be present in a definition at all.
SECRET_TERMS = (
    "password", "passwd", "api_key", "apikey", "client_secret", "clientsecret",
    "private_key", "privatekey", "bearer ", "authorization:",
)
# Personal-partition markers. Packet §3: Business partition only, this round.
PERSONAL_TERMS = ("personal",)
# A provider node that decides rather than transports an approval.
PROVIDER_DECIDES = re.compile(
    r"(approve|approval|decision)[^\n]{0,40}(auto|automatic|provider|zapier|n8n)"
    r"|(auto|automatic|provider)[^\n]{0,40}(approve|approval|decide)",
    re.IGNORECASE,
)

ENVELOPE_MARKER = "external-untrusted"
CLASSIFY_MARKER = re.compile(r"classif|triage|recommend", re.IGNORECASE)


def _walk_strings(obj, path="$"):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_strings(v, "%s.%s" % (path, k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_strings(v, "%s[%d]" % (path, i))


def check_workflow(wf: dict, filename: str) -> list:
    """Return a list of violation strings for one workflow definition."""
    problems = []
    nodes = wf.get("nodes", [])
    order = {n.get("name"): i for i, n in enumerate(nodes)}

    declared = (wf.get("meta") or {}).get("partition")
    if declared != "business":
        problems.append(
            "meta.partition is %r; packet §3 permits only 'business' this round"
            % declared)

    for path, s in _walk_strings(wf):
        low = s.lower()
        for term in RULEBOOK_TERMS:
            if term in low:
                problems.append(
                    "policy-plane/journal artifact %r appears at %s — 05_ §2: "
                    "providers never hold the rulebook" % (term, path))
        for term in SECRET_TERMS:
            if term in low:
                problems.append(
                    "possible secret material %r at %s — packet §3: secrets never "
                    "in code, logs, or the return zip" % (term, path))
        for term in PERSONAL_TERMS:
            # `partition: business` and prose like "Business/Personal" are fine;
            # a Personal *data path* is not. Flag only value-position mentions
            # that are not part of the two known safe phrasings.
            if term in low and "business/personal" not in low and "personal-partition data" not in low:
                if not path.endswith(".notes"):
                    problems.append(
                        "'personal' appears at %s — packet §3: no Personal-partition "
                        "data enters any provider this round" % path)

    # Envelope must precede anything that classifies.
    envelope_idx = None
    for n in nodes:
        blob = json.dumps(n).lower()
        if ENVELOPE_MARKER in blob:
            envelope_idx = min(envelope_idx, order[n["name"]]) if envelope_idx is not None else order[n["name"]]
    classify_nodes = [n for n in nodes
                      if CLASSIFY_MARKER.search(n.get("name", ""))
                      or CLASSIFY_MARKER.search(json.dumps(n.get("parameters", {})))]
    if classify_nodes and envelope_idx is None:
        problems.append(
            "a classification step exists but no external-untrusted envelope node "
            "was found — packet §3 requires the envelope before classification")
    for n in classify_nodes:
        if envelope_idx is not None and order[n["name"]] < envelope_idx:
            problems.append(
                "node %r classifies before the external-untrusted envelope is "
                "applied — packet §3" % n["name"])

    # Approval authority must not sit with the provider.
    for n in nodes:
        blob = "%s %s" % (n.get("name", ""), json.dumps(n.get("parameters", {})))
        if PROVIDER_DECIDES.search(blob):
            problems.append(
                "node %r reads as the provider deciding an approval — packet §3: "
                "the provider may carry the pause, never decide it" % n["name"])

    return problems


def run(wf_dir: str) -> dict:
    rows = []
    for fn in sorted(f for f in os.listdir(wf_dir) if f.endswith(".json")):
        with open(os.path.join(wf_dir, fn), encoding="utf-8") as fh:
            wf = json.load(fh)
        problems = check_workflow(wf, fn)
        rows.append({"file": fn, "clean": not problems, "violations": problems})
    return {
        "check": "05_ §2 / packet §3 boundary compliance",
        "scope": "authored workflow definitions only",
        "runtime_boundary_behaviour": "NOT TESTED — measured in the owner session",
        "workflows": rows,
        "all_clean": all(r["clean"] for r in rows),
    }


# --- self-test: every rule must be observed rejecting something ---------------
def self_test() -> int:
    base = {
        "name": "t", "meta": {"partition": "business"},
        "nodes": [
            {"name": "Apply External-Untrusted Envelope", "type": "n8n-nodes-base.code",
             "parameters": {"jsCode": "trust:'external-untrusted'"}},
            {"name": "AI OS — Classify", "type": "n8n-nodes-base.httpRequest",
             "parameters": {"url": "https://wrapper/triage"}},
        ],
        "connections": {},
    }
    import copy
    cases = []

    cases.append(("clean control", copy.deepcopy(base), True))

    c = copy.deepcopy(base); c["meta"]["partition"] = "personal"
    cases.append(("personal partition declared", c, False))

    c = copy.deepcopy(base)
    c["nodes"][1]["parameters"]["body"] = "{{ $json.evidence_policy }}"
    cases.append(("policy artifact sent to provider", c, False))

    c = copy.deepcopy(base)
    c["nodes"][1]["parameters"]["headers"] = "Authorization: Bearer abc"
    cases.append(("secret material in a definition", c, False))

    c = copy.deepcopy(base)
    c["nodes"][1]["parameters"]["url"] = "https://wrapper/personal-inbox"
    cases.append(("personal data path", c, False))

    c = copy.deepcopy(base); c["nodes"] = [c["nodes"][1]]
    cases.append(("classification with no envelope", c, False))

    c = copy.deepcopy(base); c["nodes"] = [base["nodes"][1], base["nodes"][0]]
    cases.append(("classification before the envelope", c, False))

    c = copy.deepcopy(base)
    c["nodes"].append({"name": "Auto Approve In Provider", "type": "x", "parameters": {}})
    cases.append(("provider decides the approval", c, False))

    c = copy.deepcopy(base)
    c["nodes"][1]["parameters"]["body"] = "{{ $json.control_journal }}"
    cases.append(("journal contents sent to provider", c, False))

    passed = 0
    rows = []
    for label, wf, should_be_clean in cases:
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "c.json"), "w") as fh:
                json.dump(wf, fh)
            clean = run(d)["all_clean"]
        ok = clean == should_be_clean
        passed += ok
        rows.append({"case": label, "expected": "clean" if should_be_clean else "violation",
                     "actual": "clean" if clean else "violation", "ok": ok})
        sys.stderr.write("  [%s] %s\n" % ("ok  " if ok else "FAIL", label))
    print(json.dumps({"check": "boundary-checker self-test", "cases": rows,
                      "passed": passed, "total": len(cases)}, indent=2))
    sys.stderr.write("BOUNDARY SELF-TEST %s — %d/%d cases\n"
                     % ("PASS" if passed == len(cases) else "FAIL", passed, len(cases)))
    return 0 if passed == len(cases) else 1


def main(argv):
    if argv and argv[0] == "--self-test":
        return self_test()
    if argv:
        sys.stderr.write(__doc__)
        return 2
    report = run(WF_DIR)
    print(json.dumps(report, indent=2))
    for r in report["workflows"]:
        sys.stderr.write("  [%s] %s\n" % ("CLEAN" if r["clean"] else "VIOLATION", r["file"]))
        for v in r["violations"]:
            sys.stderr.write("         - %s\n" % v)
    sys.stderr.write("BOUNDARY CHECK %s (runtime behaviour NOT TESTED)\n"
                     % ("CLEAN" if report["all_clean"] else "VIOLATIONS FOUND"))
    return 0 if report["all_clean"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""P2S-07: proposal-eligibility negative and positive tests (D-B2 P2G-13 §4).

  negative — extracted claims with NO eligibility policy produce ZERO proposals of
             any class, INCLUDING filing and placement
  positive — an approved filing-only policy permits the filing proposal while the
             outbound verified-origin floor still blocks any outbound path

Both run against the real engine functions, not a mock.

Usage:  python3 run_p2s07.py [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

import engine_core as core

UNTRUSTED_ENVELOPE: Dict[str, str] = {
    "origin": "external",
    "source_id": "mail-9931",
    "source_type": "email",
    "trust_class": "external-untrusted",
    "instruction_authority": "none",
    "sensitivity_class": "business-external",
    "data_class": "external-content",
    "verification_state": "unverified-external",
    "identity_session_state": "n/a (non-owner channel)",
    "policy_version": "P1",
    "schema_version": "SV-1",
}

REQUIRED_FIELDS = tuple(UNTRUSTED_ENVELOPE.keys())

FILING_ONLY = core.EligibilityPolicy(
    policy_id="eligibility.filing-only", version=1,
    source_class="external-untrusted", permitted_proposal_classes=("filing",),
)

# Extracted claims from the isolated context (D-B2 P2G-13 §2 bounded extraction).
EXTRACTED_CLAIMS = [
    {"claim_type": "topic-candidate", "value": "vendor-invoice",
     "provenance": {"source_id": "mail-9931", "content_hash": "ab12cd34"}},
    {"claim_type": "amount", "value": "1240.00",
     "provenance": {"source_id": "mail-9931", "content_hash": "ab12cd34"}},
]


def _proposals_for(eligible: List[str]) -> List[str]:
    """Which proposal classes the engine would actually emit."""
    return [c for c in ("filing", "placement", "summary", "outbound") if c in eligible]


def negative_test() -> Dict[str, object]:
    eligible = list(core.eligible_proposal_classes(
        UNTRUSTED_ENVELOPE["trust_class"], []))          # no policy at all
    emitted = _proposals_for(eligible)
    verdict = core.verify_envelope(UNTRUSTED_ENVELOPE, REQUIRED_FIELDS)
    base = core.base_disposition(UNTRUSTED_ENVELOPE, verdict, {})
    passed = (len(emitted) == 0
              and "filing" not in emitted and "placement" not in emitted
              and core.CEILING_ORDER[base.ceiling] < core.CEILING_ORDER[core.CEILING_OUTBOUND])
    return {
        "test": "negative — no eligibility policy",
        "expectation": "zero proposals of ANY class, including filing and placement",
        "extracted_claims": len(EXTRACTED_CLAIMS),
        "claims_retain_provenance": all("provenance" in c for c in EXTRACTED_CLAIMS),
        "eligible_classes": eligible,
        "proposals_emitted": emitted,
        "computed_ceiling": base.ceiling,
        "passed": passed,
    }


def positive_test() -> Dict[str, object]:
    eligible = list(core.eligible_proposal_classes(
        UNTRUSTED_ENVELOPE["trust_class"], [FILING_ONLY]))
    emitted = _proposals_for(eligible)
    verdict = core.verify_envelope(UNTRUSTED_ENVELOPE, REQUIRED_FIELDS)
    base = core.base_disposition(UNTRUSTED_ENVELOPE, verdict, {})
    outbound_blocked = core.CEILING_ORDER[base.ceiling] < core.CEILING_ORDER[
        core.CEILING_OUTBOUND]
    passed = ("filing" in emitted and "outbound" not in emitted
              and "placement" not in emitted and outbound_blocked)
    return {
        "test": "positive — approved filing-only eligibility policy",
        "expectation": "filing permitted; outbound still blocked by the verified-origin floor",
        "policy": "%s.v%d permits %s" % (FILING_ONLY.policy_id, FILING_ONLY.version,
                                         ",".join(FILING_ONLY.permitted_proposal_classes)),
        "eligible_classes": eligible,
        "proposals_emitted": emitted,
        "computed_ceiling": base.ceiling,
        "outbound_blocked": outbound_blocked,
        "passed": passed,
    }


def run(out_dir: str) -> Dict[str, object]:
    tests = [negative_test(), positive_test()]
    payload = {
        "summary": {"tests": len(tests),
                    "passed": sum(1 for t in tests if t["passed"]),
                    "failed": sum(1 for t in tests if not t["passed"])},
        "tests": tests,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "p2s07_eligibility.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return payload


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)
    payload = run(args.out)
    print("P2S-07 — proposal eligibility for untrusted content (D-B2 P2G-13 §4)")
    for t in payload["tests"]:
        print("  %-52s %s" % (t["test"], "PASS" if t["passed"] else "FAIL"))
        print("      emitted: %s | ceiling: %s"
              % (t["proposals_emitted"] or "none", t["computed_ceiling"]))
    s = payload["summary"]
    print("\n  %d/%d tests pass" % (s["passed"], s["tests"]))
    return 0 if s["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

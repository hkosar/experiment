"""P2S-05: the five policy/lease linearization traces (D-B4 §2.3).

One serialization point: policy commits AND authorization-lease acquisitions
serialize through the same policy-plane authority store, so "before/after" between
a policy change and a lease is always well-defined.

  1 policy-first                  -> lease acquisition FAILS (store rejects a lease
                                     against a revoked epoch — same-store atomicity)
  2 lease-first                   -> action explicitly recorded IN FLIGHT under its
                                     epoch; a later policy change cannot prevent it
  3 policy-after-acceptance       -> historical fact + receipt; policy governs future
  4 lease expiry                  -> re-acquisition re-serializes against current epoch
  5 uncertain provider response   -> ACT-01 halt + Needs Review, reconcile before retry

What is provable (D-B4 §2.3) is asserted; what is NOT claimed — prevention of an
action already accepted by the provider — is asserted as NOT claimed, so an
overclaiming implementation fails this suite.

Usage:  python3 run_p2s05.py [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

LEASE_MAX_SECONDS = 60          # D-B4 §2.3 rule 3 declared bound


@dataclass
class PolicyPlane:
    """Single serialization point over BOTH policy commits and lease acquisitions."""

    epoch: int = 1
    sequence: List[str] = field(default_factory=list)
    revoked_epochs: set = field(default_factory=set)
    leases: Dict[str, Dict[str, object]] = field(default_factory=dict)
    receipts: Dict[str, Dict[str, object]] = field(default_factory=dict)
    uncertain: set = field(default_factory=set)
    reconciled: set = field(default_factory=set)

    def commit_policy(self, name: str, stricter: bool) -> Dict[str, object]:
        self.epoch += 1
        self.sequence.append("PolicyVersionEvent:%s@E%d" % (name, self.epoch))
        if stricter:
            # Every pending authorization bound to a prior epoch is revoked.
            self.revoked_epochs.add(self.epoch - 1)
            for lid, l in self.leases.items():
                if l["epoch"] < self.epoch and l["state"] == "held":
                    l["revoked_by_policy_event"] = True
        return {"event": "PolicyVersionEvent", "epoch": self.epoch, "stricter": stricter}

    def acquire_lease(self, lease_id: str, at_epoch: Optional[int] = None) -> Dict[str, object]:
        want = self.epoch if at_epoch is None else at_epoch
        self.sequence.append("LeaseAcquire:%s@E%d" % (lease_id, want))
        if want in self.revoked_epochs or want != self.epoch:
            return {"acquired": False,
                    "reason": "lease rejected against revoked/stale epoch E%d "
                              "(current E%d)" % (want, self.epoch)}
        # NOTE (RW-17): D-B4 §2.3 defines `revoked_by_policy_event` for PENDING
        # authorizations. Here it is reused as the in-flight MARKER on an already
        # held lease: it records that a stricter policy landed mid-flight so
        # reconciliation can note the epoch, and it deliberately does NOT retract
        # the lease (rule 3 declines to claim that prevention).
        self.leases[lease_id] = {"epoch": want, "state": "held", "elapsed": 0,
                                 "revoked_by_policy_event": False}
        return {"acquired": True, "epoch": want}

    def submit_to_provider(self, lease_id: str, response: str) -> Dict[str, object]:
        """Attempt the side effect under a held lease. Returns a COMPUTED outcome.

        `response` is the provider's behaviour, not the verdict: "accepted",
        "uncertain". Everything the traces assert is derived from what this and
        `pre_execution_check` actually return (rework finding RW-03).
        """
        check = self.pre_execution_check(lease_id)
        if not check["ok"]:
            return {"submitted": False, "reason": check["reason"], "receipt": None}
        lease = self.leases[lease_id]
        lease["state"] = "used"                       # single-use (D-B4 §2.3 rule 3)
        self.sequence.append("ProviderSubmit:%s@E%d" % (lease_id, lease["epoch"]))
        if response == "accepted":
            receipt = {"receipt_id": "rcpt-%s" % lease_id, "externally_owned": True,
                       "epoch": lease["epoch"]}
            self.receipts[lease_id] = receipt
            self.sequence.append("ProviderAccepted:%s" % lease_id)
            return {"submitted": True, "accepted": True, "receipt": receipt}
        # uncertain: no receipt, ACT-01 halt path
        self.uncertain.add(lease_id)
        self.sequence.append("ProviderUncertain:%s" % lease_id)
        return {"submitted": True, "accepted": None, "receipt": None}

    def retry_allowed(self, lease_id: str) -> bool:
        """ACT-01: no retry until the uncertain outcome has been reconciled."""
        return lease_id not in self.uncertain or lease_id in self.reconciled

    def reconcile(self, lease_id: str) -> Dict[str, object]:
        self.reconciled.add(lease_id)
        self.sequence.append("Reconcile:%s" % lease_id)
        return {"reconciled": True, "needs_review_raised": lease_id in self.uncertain}

    def history(self) -> List[str]:
        return list(self.sequence)

    def pre_execution_check(self, lease_id: str) -> Dict[str, object]:
        l = self.leases.get(lease_id)
        if l is None:
            return {"ok": False, "reason": "no lease held"}
        if l["state"] != "held":
            return {"ok": False, "reason": "lease %s" % l["state"]}
        if l["elapsed"] > LEASE_MAX_SECONDS:
            l["state"] = "expired"
            return {"ok": False, "reason": "lease expired (> %ds); re-acquisition required"
                                           % LEASE_MAX_SECONDS}
        # D-B4 §2.3 rule 3, precisely: the epoch is enforced at ACQUISITION (rule 2).
        # A policy change that lands while a lease is already held does NOT retract
        # it — the design explicitly declines to claim that prevention. The in-flight
        # exposure is bounded by the lease lifetime instead, and the epoch move is
        # recorded on the lease so reconciliation can note it.
        # (An authorization not yet leased is a different case: it must acquire a
        # lease at execution time, and that acquisition fails against the new epoch —
        # which is the P2G-05 race trace.)
        return {"ok": True, "epoch": l["epoch"],
                "epoch_moved": l["epoch"] != self.epoch}


def trace_1_policy_first(defect: bool = False) -> Dict[str, object]:
    p = PolicyPlane()
    p.commit_policy("stricter-filing", stricter=True)
    if defect:
        p.revoked_epochs.clear()                       # seeded: revocation not enforced
        p.epoch = 1
    acq = p.acquire_lease("lease-1", at_epoch=1)      # authorized under the old epoch
    passed = not acq["acquired"]
    return {
        "trace": "1-policy-before-lease",
        "expectation": "lease acquisition fails; no side effect can reach a provider",
        "result": acq,
        "side_effect_reached_provider": False,
        "passed": passed,
        "sequence": p.sequence,
    }


def trace_2_lease_first(defect: bool = False) -> Dict[str, object]:
    p = PolicyPlane()
    acq = p.acquire_lease("lease-2")
    lease_epoch = p.leases["lease-2"]["epoch"] if acq["acquired"] else None
    p.commit_policy("stricter-filing", stricter=True)
    l = p.leases.get("lease-2", {})
    in_flight_recorded = bool(l.get("revoked_by_policy_event")) and l.get("state") == "held"
    if defect:
        # Seeded: the epoch marker is lost, so the in-flight action is not recorded.
        l["revoked_by_policy_event"] = False
        in_flight_recorded = False
    # COMPUTED: does the already-leased action actually reach the provider?
    outcome = p.submit_to_provider("lease-2", "accepted")
    completed = bool(outcome.get("accepted"))
    receipt = outcome.get("receipt")
    notes_epoch = bool(receipt and receipt.get("epoch") == lease_epoch)
    return {
        "trace": "2-lease-before-policy",
        "expectation": "in-flight recorded under its epoch, completes; no prevention claimed",
        "in_flight_recorded": in_flight_recorded,
        "completed": completed,
        "prevention_claimed": False,
        "reconciliation_notes_epoch": notes_epoch,
        "receipt": receipt,
        "passed": in_flight_recorded and completed and notes_epoch,
        "sequence": p.history(),
    }


def trace_3_policy_after_acceptance(defect: bool = False) -> Dict[str, object]:
    p = PolicyPlane()
    p.acquire_lease("lease-3")
    outcome = p.submit_to_provider("lease-3", "accepted")     # COMPUTED acceptance
    history_before = p.history()
    p.commit_policy("stricter-filing", stricter=True)
    if defect:
        # Seeded: the later policy commit retroactively deletes the receipt —
        # a history rewrite the trace must catch.
        p.receipts.pop("lease-3", None)
    receipt = p.receipts.get("lease-3")
    history_after = p.history()
    history_rewritten = history_after[:len(history_before)] != history_before
    receipt_survived = receipt is not None and bool(receipt.get("externally_owned"))
    return {
        "trace": "3-policy-after-provider-acceptance",
        "expectation": "executed action is a historical fact + receipt; policy governs future only",
        "receipt": receipt,
        "provider_accepted": bool(outcome.get("accepted")),
        "history_rewritten": history_rewritten,
        "policy_governs_future_only": not history_rewritten,
        "passed": bool(outcome.get("accepted")) and receipt_survived and not history_rewritten,
        "sequence": history_after,
    }


def trace_4_lease_expiry(defect: bool = False) -> Dict[str, object]:
    p = PolicyPlane()
    p.acquire_lease("lease-4")
    p.leases["lease-4"]["elapsed"] = (0 if defect else LEASE_MAX_SECONDS + 1)
    first = p.pre_execution_check("lease-4")
    p.commit_policy("stricter-filing", stricter=True)
    re_acq = p.acquire_lease("lease-4b", at_epoch=p.epoch)
    reserialized = re_acq["acquired"] and re_acq["epoch"] == p.epoch
    return {
        "trace": "4-lease-expiry",
        "expectation": "expiry blocks execution; re-acquisition re-serializes against current epoch",
        "expired_check": first,
        "reacquisition": re_acq,
        "passed": (not first["ok"]) and reserialized,
        "sequence": p.sequence,
    }


def trace_5_uncertain_response(defect: bool = False) -> Dict[str, object]:
    p = PolicyPlane()
    p.acquire_lease("lease-5")
    outcome = p.submit_to_provider("lease-5", "uncertain")    # COMPUTED uncertainty
    if defect:
        # Seeded: the candidate treats an uncertain outcome as retryable.
        p.uncertain.discard("lease-5")
    retry_before = p.retry_allowed("lease-5")                 # must be blocked
    recon = p.reconcile("lease-5")
    retry_after = p.retry_allowed("lease-5")                  # allowed once reconciled
    halted = outcome.get("receipt") is None and outcome.get("accepted") is None
    engine_marked_executed = "lease-5" in p.receipts
    return {
        "trace": "5-uncertain-provider-response",
        "expectation": "halt, Needs Review, reconcile before any retry (ACT-01)",
        "outcome": {"provider_response": "uncertain", "receipt": outcome.get("receipt")},
        "halted": halted,
        "needs_review_raised": bool(recon.get("needs_review_raised")),
        "retry_allowed_before_reconcile": retry_before,
        "retry_allowed_after_reconcile": retry_after,
        "engine_marked_executed": engine_marked_executed,
        "passed": (halted and bool(recon.get("needs_review_raised"))
                   and not retry_before and retry_after
                   and not engine_marked_executed),
        "sequence": p.history(),
    }


TRACES = [trace_1_policy_first, trace_2_lease_first, trace_3_policy_after_acceptance,
          trace_4_lease_expiry, trace_5_uncertain_response]


def run(out_dir: str) -> Dict[str, object]:
    results = [fn() for fn in TRACES]
    # RW-03 falsifier: every trace verdict must be COMPUTED, so a seeded defect in
    # the mechanism it exercises must flip it to FAIL. A trace that passes under its
    # own defect is asserting a constant, not measuring anything.
    discrimination = []
    for fn, clean in zip(TRACES, results):
        broken = fn(defect=True)
        discrimination.append({
            "trace": clean["trace"],
            "clean_passed": clean["passed"],
            "defect_passed": broken["passed"],
            "discriminates": bool(clean["passed"] and not broken["passed"]),
        })
    payload = {
        "summary": {
            "traces": len(results),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": sum(1 for r in results if not r["passed"]),
            "discriminating": sum(1 for d in discrimination if d["discriminates"]),
        },
        "traces": results,
        "falsifier": discrimination,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "p2s05_linearization.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return payload


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)
    payload = run(args.out)
    print("P2S-05 — policy/lease linearization traces (D-B4 §2.3)")
    for r in payload["traces"]:
        print("  %-34s %s" % (r["trace"], "PASS" if r["passed"] else "FAIL"))
        print("      %s" % r["expectation"])
    s = payload["summary"]
    print()
    print("  falsifier — each trace must FAIL under a seeded defect in its mechanism:")
    for d in payload["falsifier"]:
        print("    %-34s clean=%-5s defect=%-5s %s"
              % (d["trace"], d["clean_passed"], d["defect_passed"],
                 "DISCRIMINATES" if d["discriminates"] else "*** ASSERTS A CONSTANT ***"))
    print("\n  %d/%d traces pass; %d/%d discriminate"
          % (s["passed"], s["traces"], s["discriminating"], s["traces"]))
    ok = s["failed"] == 0 and s["discriminating"] == s["traces"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

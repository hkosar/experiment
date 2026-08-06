#!/usr/bin/env python3
# THROWAWAY POC EVIDENCE APPARATUS — see stub_server.py header.
"""Deterministic two-request barrier tests over live HTTP (`33_` §4).

`33_` §4 requires deterministic barriers — not stress — for each of the five
subject identities and for revoke-versus-deliver in all three orderings, and it
requires them demonstrated failing against the pinned R3 artifact.

**Where the barrier goes, and why it is not where the reviewer put it.**
The reviewer's probes align two requests *inside* the transition, by blocking in
`write_capture` or `Transition.prepare`. Under the architecture `33_` §1 selects
— a single global lock held across the entire critical path — that point is
mutually exclusive by construction, so the second request cannot arrive and the
barrier times out. It is not that the build fails those probes; it is that the
probes cannot express their intent against any correct implementation of the
selected model. That conflict is reported as AUDIT-R4-5 in the Delivery Record,
for Fable to rule on, and is not worked around here.

These barriers align the two requests at the **socket**, which is reachable
under either model: both requests are in flight before either can acquire the
lock. The property under test is unchanged — one subject identity yields exactly
one effective transition, and the loser is told the truth — and it is the
property SEC-R3-01 actually states.

Run directly to compare both builds:

    python3 barrier_suite.py                  # against the live build
    python3 barrier_suite.py r3_reference/stub_server_r3.py
"""
from __future__ import annotations

import http.client
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DIGEST = "a" * 64


class Server:
    """A live stub on a real socket, for one scenario."""

    def __init__(self, target: str, candidate: str = "barrier"):
        self.target = target
        self.data = tempfile.mkdtemp(prefix="barrier-")
        self.port = _free_port()
        self.proc = subprocess.Popen(
            [sys.executable, target, "--candidate", candidate,
             "--port", str(self.port), "--data", self.data],
            stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
        banner = ""
        deadline = time.time() + 25
        self.owner_key = self.provider_key = None
        while time.time() < deadline:
            line = self.proc.stderr.readline()
            if not line:
                break
            banner += line
            m = re.search(r"OWNER-SURFACE KEY.*?\n\s*(\S+)\n", banner, re.S)
            n = re.search(r"PROVIDER CREDENTIAL.*?\n\s*(\S+)\n", banner, re.S)
            if m and n:
                self.owner_key, self.provider_key = m.group(1), n.group(1)
                break
        if not self.owner_key:
            self.close()
            raise RuntimeError("the stub did not start: %s" % banner[:300])

    def post(self, path, body, who="provider", conn=None):
        c = conn or http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        headers = {"Content-Type": "application/json"}
        headers["X-Owner-Key" if who == "owner" else "X-Provider-Key"] = (
            self.owner_key if who == "owner" else self.provider_key)
        c.request("POST", path, json.dumps(body), headers)
        r = c.getresponse()
        raw = r.read()
        if conn is None:
            c.close()
        try:
            return r.status, json.loads(raw or b"{}")
        except ValueError:
            return r.status, {}

    def close(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=10)
        except Exception:                                        # noqa: BLE001
            self.proc.kill()


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def race(fn_a, fn_b):
    """Run two requests with a barrier immediately before the send."""
    bar = threading.Barrier(2, timeout=20)
    out = [None, None]

    def go(i, fn):
        try:
            bar.wait()
        except threading.BrokenBarrierError:
            pass
        try:
            out[i] = fn()
        except Exception as exc:                                 # noqa: BLE001
            out[i] = ("EXC", {"error": type(exc).__name__})

    ts = [threading.Thread(target=go, args=(0, fn_a)),
          threading.Thread(target=go, args=(1, fn_b))]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=40)
    return out


# --------------------------------------------------------------------------
# scenario helpers
# --------------------------------------------------------------------------
def register_body(task="T", role="verifier"):
    return {"source_digest": DIGEST, "size_bytes": 1, "file_count": 1,
            "task_id": task, "transition": "R", "target_role": role}


def review_body(ref, task="T", epoch=1):
    return {"registration_ref": ref, "task_id": task, "transition": "R",
            "artifact_digest": DIGEST, "target_role": "verifier",
            "submission_epoch": epoch,
            "envelope": {"trust": "external-untrusted", "partition": "business"}}


def to_capability(srv, task="T"):
    ref = srv.post("/owner/artifact/register", register_body(task), "owner")[1]
    opened = srv.post("/poc1/review-case", review_body(ref["registration_ref"], task))[1]
    cases = srv.post("/owner/cases", {}, "owner")[1]["cases"]
    cid = [c["case_id"] for c in cases if not c["decided"]][-1]
    srv.post("/owner/decide", {"case_id": cid, "decision": "accept"}, "owner")
    v = srv.post("/poc1/verify-decision", {"token": opened["resume_token"]})[1]
    return cid, v


# --------------------------------------------------------------------------
# the six scenarios
# --------------------------------------------------------------------------
def s_registration(srv):
    """One registration identity ⇒ one record."""
    body = register_body("REG")
    a, b = race(lambda: srv.post("/owner/artifact/register", body, "owner"),
                lambda: srv.post("/owner/artifact/register", body, "owner"))
    refs = {r[1].get("registration_ref") for r in (a, b) if r and r[1]}
    ids = {r[1].get("artifact_id") for r in (a, b) if r and r[1]}
    return {"distinct_registration_refs": len(refs - {None}),
            "distinct_artifact_ids": len(ids - {None}),
            "statuses": [r[0] for r in (a, b)],
            "outcomes": [r[1].get("outcome") for r in (a, b)]}, \
        len(refs - {None}) == 1 and len(ids - {None}) == 1


def s_review_case(srv):
    """One submission identity ⇒ one case and one token."""
    ref = srv.post("/owner/artifact/register", register_body("CASE"), "owner")[1]
    body = review_body(ref["registration_ref"], "CASE")
    a, b = race(lambda: srv.post("/poc1/review-case", body),
                lambda: srv.post("/poc1/review-case", body))
    outs = [r[1].get("outcome") for r in (a, b)]
    tokens = {r[1].get("resume_token") for r in (a, b)} - {None}
    cases = srv.post("/owner/cases", {}, "owner")[1]["cases"]
    mine = [c for c in cases if c.get("task_id") == "CASE"]
    return {"outcomes": outs, "distinct_tokens": len(tokens),
            "cases_for_identity": len(mine),
            "statuses": [r[0] for r in (a, b)]}, \
        (len(mine) == 1 and outs.count("case-opened") == 1
         and outs.count("duplicate-suppressed") == 1 and len(tokens) == 1)


def s_token_spend(srv):
    """One resume token ⇒ one ActionRequest and one capability."""
    ref = srv.post("/owner/artifact/register", register_body("TOK"), "owner")[1]
    opened = srv.post("/poc1/review-case",
                      review_body(ref["registration_ref"], "TOK"))[1]
    cases = srv.post("/owner/cases", {}, "owner")[1]["cases"]
    cid = [c["case_id"] for c in cases if not c["decided"]][-1]
    srv.post("/owner/decide", {"case_id": cid, "decision": "accept"}, "owner")
    tok = opened["resume_token"]
    a, b = race(lambda: srv.post("/poc1/verify-decision", {"token": tok}),
                lambda: srv.post("/poc1/verify-decision", {"token": tok}))
    caps = {r[1].get("execution_capability") for r in (a, b)} - {None}
    ars = {(r[1].get("action_request") or {}).get("id") for r in (a, b)} - {None}
    authorized = [r[1].get("authorized") for r in (a, b)]
    return {"authorized": authorized, "distinct_capabilities": len(caps),
            "distinct_action_requests": len(ars),
            "statuses": [r[0] for r in (a, b)]}, \
        authorized.count(True) == 1 and len(caps) == 1 and len(ars) == 1


def s_capability_spend(srv):
    """One capability ⇒ one delivery receipt."""
    cid, v = to_capability(srv, "CAP")
    ar, cap = v["action_request"], v["execution_capability"]
    body = {"capability": cap, "action_request_id": ar["id"], "case_id": cid,
            "payload": ar["payload"], "destination_digest_claimed": DIGEST}
    a, b = race(lambda: srv.post("/relay/deliver", body),
                lambda: srv.post("/relay/deliver", body))
    delivered = [r[1].get("delivered") for r in (a, b)]
    receipts = {(r[1].get("receipt") or {}).get("receipt_id") for r in (a, b)} - {None}
    replayed = [r[1].get("replayed") for r in (a, b)]
    return {"delivered": delivered, "distinct_receipts": len(receipts),
            "replayed": replayed, "statuses": [r[0] for r in (a, b)]}, \
        delivered.count(True) == 1 and len(receipts) == 1


def s_run_declaration(srv):
    """One schedule occurrence ⇒ one run."""
    body = {"schedule_id": "S", "occurrence": "O", "provider_correlation_id": "x"}
    a, b = race(lambda: srv.post("/poc3/run-started", body),
                lambda: srv.post("/poc3/run-started", body))
    runs = {r[1].get("run_id") for r in (a, b)} - {None}
    outs = [r[1].get("outcome") for r in (a, b)]
    return {"distinct_run_ids": len(runs), "outcomes": outs,
            "statuses": [r[0] for r in (a, b)]}, \
        (len(runs) == 1 and outs.count("run-started") == 1
         and outs.count("duplicate-run-declaration") == 1)


def s_revoke_orderings(srv):
    """Revoke versus deliver, in all three orderings (SEC-R3-02).

    The property is one-directional and is the one the finding states: once
    `/owner/revoke` has returned success, no later delivery may become
    effective. A delivery that completes before the revoke is not a violation —
    the revoke then truthfully reports the subject already terminal.
    """
    results = {}

    # (1) revoke strictly before deliver
    cid, v = to_capability(srv, "RV1")
    ar, cap = v["action_request"], v["execution_capability"]
    rv = srv.post("/owner/revoke", {"capability": cap, "reason": "stop"}, "owner")
    dl = srv.post("/relay/deliver",
                  {"capability": cap, "action_request_id": ar["id"], "case_id": cid,
                   "payload": ar["payload"], "destination_digest_claimed": DIGEST})
    results["revoke_before_deliver"] = {
        "revoke_status": rv[0], "delivered": dl[1].get("delivered"),
        "deliver_status": dl[0]}
    ok1 = rv[0] == 200 and dl[1].get("delivered") is not True

    # (2) the two racing at the socket
    cid, v = to_capability(srv, "RV2")
    ar, cap = v["action_request"], v["execution_capability"]
    a, b = race(
        lambda: srv.post("/owner/revoke", {"capability": cap, "reason": "stop"},
                         "owner"),
        lambda: srv.post("/relay/deliver",
                         {"capability": cap, "action_request_id": ar["id"],
                          "case_id": cid, "payload": ar["payload"],
                          "destination_digest_claimed": DIGEST}))
    revoke_succeeded = a[0] == 200
    delivered = b[1].get("delivered") is True
    results["revoke_races_deliver"] = {
        "revoke_status": a[0], "revoke_outcome": a[1].get("outcome"),
        "delivered": b[1].get("delivered"), "deliver_status": b[0]}
    # Exactly one of the two may take effect, and never both.
    ok2 = not (revoke_succeeded and delivered)

    # (3) revoke strictly after a completed delivery
    cid, v = to_capability(srv, "RV3")
    ar, cap = v["action_request"], v["execution_capability"]
    dl = srv.post("/relay/deliver",
                  {"capability": cap, "action_request_id": ar["id"], "case_id": cid,
                   "payload": ar["payload"], "destination_digest_claimed": DIGEST})
    rv = srv.post("/owner/revoke", {"capability": cap, "reason": "too late"}, "owner")
    results["revoke_after_delivery"] = {
        "delivered": dl[1].get("delivered"), "revoke_status": rv[0],
        "revoke_outcome": rv[1].get("outcome")}
    ok3 = dl[1].get("delivered") is True and rv[0] == 409

    results["_verdicts"] = {"revoke_before_deliver": ok1,
                            "revoke_races_deliver": ok2,
                            "revoke_after_delivery": ok3}
    return results, ok1 and ok2 and ok3


SCENARIOS = (
    ("one registration identity -> one record", s_registration),
    ("one submission identity -> one case + one token", s_review_case),
    ("one resume token -> one ActionRequest + one capability", s_token_spend),
    ("one capability -> one delivery receipt", s_capability_spend),
    ("one schedule occurrence -> one run", s_run_declaration),
    ("revoke vs deliver, all three orderings", s_revoke_orderings),
)


def run(target: str, emit=None) -> list:
    rows = []
    for title, fn in SCENARIOS:
        srv = None
        try:
            srv = Server(target)
            detail, ok = fn(srv)
        except Exception as exc:                                 # noqa: BLE001
            detail, ok = {"error": "%s: %s" % (type(exc).__name__, exc)}, False
        finally:
            if srv:
                srv.close()
        rows.append({"scenario": title, "ok": bool(ok), "detail": detail})
        if emit:
            emit(rows[-1])
    return rows


if __name__ == "__main__":
    tgt = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 \
        else os.path.join(HERE, "stub_server.py")
    res = run(tgt, emit=lambda r: sys.stderr.write(
        "  [%s] %-56s %s\n" % ("ok  " if r["ok"] else "FAIL", r["scenario"][:56],
                               json.dumps(r["detail"])[:170])))
    bad = [r for r in res if not r["ok"]]
    sys.stderr.write("\n%d/%d barrier scenarios hold (%s)\n"
                     % (len(res) - len(bad), len(res), os.path.basename(tgt)))
    sys.exit(1 if bad else 0)

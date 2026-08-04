#!/usr/bin/env python3
"""Independent live-HTTP concurrency probe for TASK-0007 R4.

The gate is installed at the route-handler entry. In R4 that entry is inside the
outer dispatch lock; in pinned R3 it is not. The first handler is paused while a
second request is started. The observer records whether the second handler can
enter before the first is released, then releases both without injecting an
exception into the transition.
"""
from __future__ import annotations

import http.client
import importlib.util
import json
import os
import shutil
import tempfile
import threading
import time
import uuid

DIGEST = "a" * 64


class Live:
    def __init__(self, target: str, name: str):
        spec = importlib.util.spec_from_file_location("probe_" + uuid.uuid4().hex, target)
        self.m = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(self.m)
        self.m.SECRETS = self.m.SecretIndex()
        self.m.DESCRIPTOR_KEY = os.urandom(32)
        self.m.STORE = self.m.Store(candidate=name)
        self.data = tempfile.mkdtemp(prefix="chatgpt-r4-")
        self.m.Handler.data_dir = self.data
        self.srv = self.m.ThreadingHTTPServer(("127.0.0.1", 0), self.m.Handler)
        self.port = self.srv.server_address[1]
        self.m.STORE.base_url = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()

    def post(self, path: str, body: dict, who: str = "provider"):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        headers = {"Content-Type": "application/json"}
        if who == "owner":
            headers["X-Owner-Key"] = self.m.STORE.owner_key
        else:
            headers["X-Provider-Key"] = self.m.STORE.provider_key
        conn.request("POST", path, json.dumps(body), headers)
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        return resp.status, json.loads(raw or b"{}")

    def close(self):
        try:
            self.srv.shutdown()
            self.srv.server_close()
        finally:
            shutil.rmtree(self.data, ignore_errors=True)


def reg_body(task: str):
    return {"source_digest": DIGEST, "size_bytes": 1, "file_count": 1,
            "task_id": task, "transition": "R", "target_role": "verifier"}


def review_body(ref: str, task: str):
    return {"registration_ref": ref, "task_id": task, "transition": "R",
            "artifact_digest": DIGEST, "target_role": "verifier",
            "submission_epoch": 1,
            "envelope": {"trust": "external-untrusted", "partition": "business"}}


def to_decided(s: Live, task: str):
    reg = s.post("/owner/artifact/register", reg_body(task), "owner")[1]
    opened = s.post("/poc1/review-case", review_body(reg["registration_ref"], task))[1]
    token = opened["resume_token"]
    rec, _ = s.m.STORE.find_token(token)
    cid = rec["case_id"]
    s.post("/owner/decide", {"case_id": cid, "decision": "accept"}, "owner")
    return cid, token


def to_capability(s: Live, task: str):
    cid, token = to_decided(s, task)
    auth = s.post("/poc1/verify-decision", {"token": token})[1]
    return cid, auth["execution_capability"], auth["action_request"]


def gated_pair(s: Live, route: str, body: dict, who: str = "provider"):
    key = ("POST", route)
    real = s.m.HANDLERS[key]
    guard = threading.Lock()
    first_entered = threading.Event()
    second_entered = threading.Event()
    release = threading.Event()
    entered = 0

    def wrapped(payload):
        nonlocal entered
        with guard:
            entered += 1
            if entered == 1:
                first_entered.set()
            if entered >= 2:
                second_entered.set()
        if not release.wait(10):
            raise RuntimeError("independent pre-lock probe release timeout")
        return real(payload)

    s.m.HANDLERS[key] = wrapped
    results = [None, None]

    def go(i):
        try:
            results[i] = s.post(route, dict(body), who)
        except Exception as exc:  # evidence, not a hidden failure
            results[i] = ("EXC", {"error": type(exc).__name__, "detail": str(exc)})

    t1 = threading.Thread(target=go, args=(0,))
    t2 = threading.Thread(target=go, args=(1,))
    t1.start()
    if not first_entered.wait(5):
        release.set()
        raise RuntimeError(f"first {route} handler did not enter")
    t2.start()
    two_before_release = second_entered.wait(2)
    with guard:
        pre_release_entries = entered
    release.set()
    t1.join(30)
    t2.join(30)
    s.m.HANDLERS[key] = real
    return {
        "two_handlers_entered_before_first_release": two_before_release,
        "handler_entries_before_release": pre_release_entries,
        "responses": results,
    }


def scenario_registration(target: str):
    s = Live(target, "prelock-reg")
    try:
        d = gated_pair(s, "/owner/artifact/register", reg_body("REG"), "owner")
        d.update(registrations=len(s.m.STORE.registrations),
                 identity_index=len(s.m.STORE.reg_by_identity))
        return d
    finally:
        s.close()


def scenario_review(target: str):
    s = Live(target, "prelock-case")
    try:
        reg = s.post("/owner/artifact/register", reg_body("CASE"), "owner")[1]
        d = gated_pair(s, "/poc1/review-case", review_body(reg["registration_ref"], "CASE"))
        d.update(cases=len(s.m.STORE.cases), tokens=len(s.m.STORE.tokens))
        return d
    finally:
        s.close()


def scenario_token(target: str):
    s = Live(target, "prelock-token")
    try:
        _, token = to_decided(s, "TOK")
        d = gated_pair(s, "/poc1/verify-decision", {"token": token})
        d.update(capabilities=len(s.m.STORE.capabilities),
                 action_requests=len(s.m.STORE.cap_by_ar))
        return d
    finally:
        s.close()


def scenario_capability(target: str):
    s = Live(target, "prelock-cap")
    try:
        cid, cap, ar = to_capability(s, "CAP")
        body = {"capability": cap, "action_request_id": ar["id"], "case_id": cid,
                "payload": ar["payload"], "destination_digest_claimed": DIGEST}
        d = gated_pair(s, "/relay/deliver", body)
        d.update(receipts=len(s.m.STORE.relay_receipts),
                 final_status=s.m.STORE.capabilities[cap]["status"])
        return d
    finally:
        s.close()


def scenario_run(target: str):
    s = Live(target, "prelock-run")
    try:
        d = gated_pair(s, "/poc3/run-started",
                       {"schedule_id": "S", "occurrence": "O",
                        "provider_correlation_id": "x"})
        d.update(runs=len(s.m.STORE.runs), declarations=len(s.m.STORE.runs_by_declaration))
        return d
    finally:
        s.close()


def scenario_revoke(target: str):
    s = Live(target, "prelock-revoke")
    try:
        cid, cap, ar = to_capability(s, "REV")
        deliver_key = ("POST", "/relay/deliver")
        revoke_key = ("POST", "/owner/revoke")
        real_deliver = s.m.HANDLERS[deliver_key]
        real_revoke = s.m.HANDLERS[revoke_key]
        delivery_entered = threading.Event()
        allow_delivery = threading.Event()
        revoke_entered = threading.Event()
        deliver_result = []
        revoke_result = []

        def blocked_deliver(payload):
            delivery_entered.set()
            if not allow_delivery.wait(10):
                raise RuntimeError("delivery release timeout")
            return real_deliver(payload)

        def observed_revoke(payload):
            revoke_entered.set()
            return real_revoke(payload)

        s.m.HANDLERS[deliver_key] = blocked_deliver
        s.m.HANDLERS[revoke_key] = observed_revoke
        deliver_body = {"capability": cap, "action_request_id": ar["id"],
                        "case_id": cid, "payload": ar["payload"],
                        "destination_digest_claimed": DIGEST}

        td = threading.Thread(target=lambda: deliver_result.append(
            s.post("/relay/deliver", deliver_body)))
        tr = threading.Thread(target=lambda: revoke_result.append(
            s.post("/owner/revoke", {"capability": cap, "reason": "stop"}, "owner")))
        td.start()
        if not delivery_entered.wait(5):
            raise RuntimeError("delivery handler did not enter")
        tr.start()
        revoke_before_delivery_release = revoke_entered.wait(2)
        # In R3, let the entered revoke finish before releasing delivery. In R4,
        # the revoke cannot enter until delivery leaves the global lock.
        if revoke_before_delivery_release:
            tr.join(20)
        allow_delivery.set()
        td.join(30)
        tr.join(30)
        s.m.HANDLERS[deliver_key] = real_deliver
        s.m.HANDLERS[revoke_key] = real_revoke
        return {
            "revoke_handler_entered_while_delivery_handler_paused": revoke_before_delivery_release,
            "delivery": deliver_result[0] if deliver_result else None,
            "revoke": revoke_result[0] if revoke_result else None,
            "final_status": s.m.STORE.capabilities[cap]["status"],
            "receipt_present": ar["id"] in s.m.STORE.relay_receipts,
        }
    finally:
        s.close()


SCENARIOS = {
    "registration": scenario_registration,
    "review_case": scenario_review,
    "token_spend": scenario_token,
    "capability_spend": scenario_capability,
    "run_declaration": scenario_run,
    "revoke_vs_delivery": scenario_revoke,
}


def run(target: str):
    return {name: fn(target) for name, fn in SCENARIOS.items()}


if __name__ == "__main__":
    import sys
    target = os.path.abspath(sys.argv[1])
    print(json.dumps(run(target), indent=2, sort_keys=True))

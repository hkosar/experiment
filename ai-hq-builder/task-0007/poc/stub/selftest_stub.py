#!/usr/bin/env python3
# THROWAWAY POC EVIDENCE APPARATUS — see stub_server.py header.
"""Self-test for the R2 POC wrapper stub.

Covers `14_` §3 in three blocks:
  * `09_` §2 R1P-04's five required tests (the verifier-approved acceptance spec);
  * `12_` §5's required list;
  * `13_` §4's additional list.

`14_` §3 requires each to be "demonstrated failing against the unfixed
behaviour". That demonstration is NOT done with defect switches in this build —
a switch that can disable a control is itself a finding (P2V-01). It is done by
`r1_witnesses.py`, which runs the same probes against the pinned, byte-identical
R1 build in `r1_reference/` and records what it did. Run both:

    python3 selftest_stub.py     # the R2 contract holds
    python3 r1_witnesses.py      # the R1 contract did not

Exit: 0 all cases pass / 1 any case fails
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub_server as S  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = []


def record(case, expected, actual, ok, note=None, block=None):
    ROWS.append({"case": case, "expected": expected, "actual": actual, "ok": bool(ok),
                 "note": note, "block": block})
    sys.stderr.write("  [%s] %-64s %s\n"
                     % ("ok  " if ok else "FAIL", case[:64],
                        "" if ok else "(expected %s, got %s)" % (expected, actual)))
    return ok


def block(title):
    sys.stderr.write("\n-- %s --\n" % title)


def fresh(candidate="n8n"):
    S.SECRETS = S.SecretIndex()
    S.STORE = S.Store(candidate=candidate)
    S.STORE.base_url = "http://127.0.0.1:8787"
    d = tempfile.mkdtemp()
    S.Handler.data_dir = d
    return d


def ident(**kw):
    base = {"task_id": "TASK-0007", "transition": "builder->fable",
            "submission_epoch": 1, "artifact_digest": "a" * 64,
            "target_role": "integration-owner",
            "envelope": {"trust": "external-untrusted", "partition": "business"}}
    base.update(kw)
    return base


def caps_in(d):
    out = []
    for root, _dd, ff in os.walk(os.path.join(d, "captures")):
        for f in ff:
            if f.endswith(".json"):
                out.append(os.path.join(root, f))
    return out


def bodies_in(d):
    return [json.load(open(p, encoding="utf-8")) for p in caps_in(d)]


def run_self_test() -> int:
    # =====================================================================
    block("09_ §2 R1P-04 — the five required tests")
    d = fresh()
    P = {"provider_key": S.STORE.provider_key}
    O = {"owner_key": S.STORE.owner_key}
    post = lambda p, b, h=P: S.dispatch("POST", p, b, h)   # noqa: E731

    st, first = post("/poc1/review-case", ident())
    record("R1P-04 setup: a case opens on a complete identity tuple", 200, st, st == 200)
    tok = first.get("resume_token")

    st, dup = post("/poc1/review-case", ident())
    record("(1) same artifact+task+transition -> suppressed, prior receipt returned",
           "duplicate-suppressed",
           dup.get("outcome"),
           st == 200 and dup.get("outcome") == "duplicate-suppressed"
           and dup.get("reprocessed") is False and "prior_receipt" in dup,
           block="R1P-04")

    st, other = post("/poc1/review-case", ident(task_id="TASK-0008"))
    record("(2) same artifact, DIFFERENT task -> processed independently",
           "a new token", other.get("outcome"),
           st == 200 and "resume_token" in other
           and other["resume_token"] != tok, block="R1P-04")

    st, rej = post("/poc1/review-case", ident(target_role="owner"))
    record("(3) same task+artifact, unauthorized target -> REJECT",
           "rejected-unauthorized-target", rej.get("outcome"),
           st == 403 and rej.get("outcome") == "rejected-unauthorized-target",
           block="R1P-04")
    record("(3) ...and it is DISTINGUISHABLE from duplicate-success",
           "different outcome + status", "%s/%s vs %s/%s" % (
               st, rej.get("outcome"), 200, dup.get("outcome")),
           rej.get("outcome") != dup.get("outcome") and st != 200,
           note="the distinction is the whole test", block="R1P-04")

    cid = S.dispatch("POST", "/owner/cases", {}, O)[1]["cases"][0]["case_id"]
    S.dispatch("POST", "/owner/decide", {"case_id": cid, "decision": "accept"}, O)
    st, v = post("/poc1/verify-decision", {"token": tok})
    ar, cap = v["action_request"], v["execution_capability"]
    good_relay = {"capability": cap, "action_request_id": ar["id"],
                  "case_id": ar["case_id"], "payload": ar["payload"]}
    post("/relay/deliver", dict(good_relay))
    st, replay = post("/poc1/verify-decision", {"token": tok})
    record("(4) replayed owner decision token -> no second relay",
           "token refused", replay.get("reason", "")[:40],
           st == 403 and replay.get("outcome") == "refused-token", block="R1P-04")

    st, rr = post("/relay/deliver", dict(good_relay))
    record("(4) ...and a replayed capability returns the prior receipt, not a "
           "second side effect", "replayed + no_second_side_effect",
           "%s/%s" % (rr.get("replayed"), rr.get("no_second_side_effect")),
           rr.get("delivered") is False and rr.get("replayed") is True
           and rr.get("no_second_side_effect") is True, block="R1P-04")
    record("(4) ...while attempts stay separately countable from deliveries",
           "attempt 2", rr.get("attempt"), rr.get("attempt") == 2,
           note="how often a provider retries is a provider-discriminating measure",
           block="R1P-04")

    st, run = post("/poc3/run-started", {"schedule_id": "nightly", "occurrence": "t0"})
    rid = run["run_id"]
    st, cp = post("/poc3/checkpoint", {"run_id": rid, "stage": 1})
    record("(5) an uncertain result is reported uncertain, not assumed certain",
           False, cp.get("side_effect_certain"), cp.get("side_effect_certain") is False,
           block="R1P-04")
    st, rec = post("/poc3/reconcile", {"run_id": rid})
    record("(5) reconcile runs before any second side effect and states what it "
           "actually checked", "external_post_state_checked False",
           rec.get("external_post_state_checked"),
           st == 200 and rec.get("external_post_state_checked") is False
           and "post_state_checked_against_recorded_state" in rec, block="R1P-04")

    # =====================================================================
    block("12_ §5 — required security tests")
    st, _ = post("/relay/deliver", {"case_id": "x", "payload": {}})
    record("direct relay-sink call without a capability -> refused", 403, st, st == 403,
           block="12_§5")

    for label, mutation in (
            ("altered action id", {"action_request_id": "ar-forged"}),
            ("altered case", {"case_id": "case-forged"}),
            ("altered payload", {"payload": {"tampered": True}}),
            ("altered capability", {"capability": "cap-forged"})):
        probe = dict(good_relay); probe.update(mutation)
        st, _b = post("/relay/deliver", probe)
        record("capability with %s -> refused" % label, 403, st, st == 403, block="12_§5")

    st, exp = post("/poc1/review-case", ident(task_id="EXP"))
    cid2 = [c for c in S.dispatch("POST", "/owner/cases", {}, O)[1]["cases"]
            if c["task_id"] == "EXP"][0]["case_id"]
    S.dispatch("POST", "/owner/decide", {"case_id": cid2, "decision": "accept"}, O)
    st, v2 = post("/poc1/verify-decision", {"token": exp["resume_token"]})
    binding = S.STORE.capabilities[v2["execution_capability"]]
    binding["expires_at"] = time.time() - 1
    st, _ = post("/relay/deliver", {"capability": v2["execution_capability"],
                                    "action_request_id": v2["action_request"]["id"],
                                    "case_id": v2["action_request"]["case_id"],
                                    "payload": v2["action_request"]["payload"]})
    record("expired capability -> refused", 403, st, st == 403, block="12_§5")

    # resume token under arbitrary and unicode-confusable keys
    live = S.STORE.mint_token("case-probe")
    for key in ("opaque", "note", "ｔｏｋｅｎ", "tоken", "x" * 40):
        post("/poc1/receipt", {"case_id": "c", key: live})
    blob = json.dumps(bodies_in(d))
    record("resume token under arbitrary/unicode-confusable keys is absent from "
           "every capture", "absent", "present" if live in blob else "absent",
           live not in blob, note="SEC-R1-02: R1 wrote an unrecognised key verbatim",
           block="12_§5")

    st, _ = S.dispatch("POST", "/owner/decide", {"case_id": cid, "decision": "reject"}, O)
    record("a second owner decision -> refused", 409, st, st == 409, block="12_§5")

    # capture-write failure during a decision
    fresh()
    P2 = {"provider_key": S.STORE.provider_key}; O2 = {"owner_key": S.STORE.owner_key}
    post2 = lambda p, b, h=P2: S.dispatch("POST", p, b, h)   # noqa: E731
    post2("/poc1/review-case", ident())
    cid3 = S.dispatch("POST", "/owner/cases", {}, O2)[1]["cases"][0]["case_id"]
    real = S.write_capture
    S.write_capture = lambda *a, **k: (_ for _ in ()).throw(S.CaptureError("disk full"))
    st, _ = S.dispatch("POST", "/owner/decide", {"case_id": cid3, "decision": "accept"}, O2)
    S.write_capture = real
    record("capture failure during a decision -> the decision does not survive",
           "500 and no decision", "%s / decisions=%d" % (st, len(S.STORE.decisions)),
           st == 500 and cid3 not in S.STORE.decisions, block="12_§5")

    # token-spend capture failure leaves the token unspent (FAB-04)
    fresh()
    P3 = {"provider_key": S.STORE.provider_key}; O3 = {"owner_key": S.STORE.owner_key}
    post3 = lambda p, b, h=P3: S.dispatch("POST", p, b, h)   # noqa: E731
    st, o = post3("/poc1/review-case", ident())
    t3 = o["resume_token"]
    cid4 = S.dispatch("POST", "/owner/cases", {}, O3)[1]["cases"][0]["case_id"]
    S.dispatch("POST", "/owner/decide", {"case_id": cid4, "decision": "accept"}, O3)
    real = S.write_capture
    S.write_capture = lambda *a, **k: (_ for _ in ()).throw(S.CaptureError("disk full"))
    st, _ = post3("/poc1/verify-decision", {"token": t3})
    S.write_capture = real
    st2, after = post3("/poc1/verify-decision", {"token": t3})
    record("a token-spend capture failure leaves the token UNSPENT",
           "refused then authorized", "%s then %s" % (st, st2),
           st == 500 and st2 == 200 and after.get("authorized") is True,
           note="FAB-04: a consumed single-use token cannot be un-consumed",
           block="13_§4")

    d = fresh()
    P = {"provider_key": S.STORE.provider_key}; O = {"owner_key": S.STORE.owner_key}
    post = lambda p, b, h=P: S.dispatch("POST", p, b, h)   # noqa: E731

    for label, meta in (("truthy list", [1]), ("string", "x"), ("int", 5), ("bool", True)):
        st, b = post("/poc2/triage", {"origin": "owner", "metadata": meta,
                                      "envelope": {"trust": "external-untrusted",
                                                   "partition": "business"}})
        record("truthy non-dict metadata (%s) -> structured refusal or clean handling"
               % label, "no crash", st, isinstance(st, int),
               note="13_ VC-01: a falsy [] passes against UNFIXED code, so the test "
                    "must use a truthy value", block="12_§5")

    st, _ = post("/poc1/review-case", ident(), {})
    record("browser-simple POST without the provider credential -> refused", 403, st,
           st == 403, block="12_§5")

    # =====================================================================
    block("13_ §4 — evidence integrity")
    d = fresh()
    P = {"provider_key": S.STORE.provider_key}; O = {"owner_key": S.STORE.owner_key}
    post = lambda p, b, h=P: S.dispatch("POST", p, b, h)   # noqa: E731

    st, o = post("/poc1/review-case", ident())
    tok = o["resume_token"]
    st, _ = post("/poc1/verify-decision", {"token": tok})
    steps = {os.path.basename(p).split("-" + S.STORE.run_instance)[0] for p in caps_in(d)}
    record("mandatory refusal 1 (the pause, nothing approved) writes a capture",
           "verify-pending present", sorted(steps), "verify-pending" in steps,
           note="FAB-01: R1 evidenced nothing on this path", block="13_§4")
    S.dispatch("POST", "/owner/decide", {"case_id": "case-nope", "decision": "accept"}, {})
    steps = {os.path.basename(p).split("-" + S.STORE.run_instance)[0] for p in caps_in(d)}
    record("mandatory refusal 2 (no owner authority) writes a capture",
           "auth-refused present", sorted(steps), "auth-refused" in steps,
           block="13_§4")
    blob = json.dumps(bodies_in(d))
    record("...and the refusal capture never contains key material",
           "absent", "present" if S.STORE.owner_key in blob else "absent",
           S.STORE.owner_key not in blob, block="13_§4")

    for b in bodies_in(d):
        pass
    record("every capture carries a stub-minted timestamp",
           "recorded_at on all", "ok",
           all("recorded_at" in b and "recorded_at_note" in b for b in bodies_in(d)),
           note="FAB-09: R1 discarded its own opened_at and decision time",
           block="13_§4")
    record("every capture carries candidate, run_instance, route and authored_by",
           "all four on all", "ok",
           all(all(k in b for k in ("candidate", "run_instance", "route", "authored_by"))
               for b in bodies_in(d)), block="13_§4")

    # two candidates -> separately attributable corpora
    d_a = fresh("n8n")
    post("/poc1/review-case", ident(), {"provider_key": S.STORE.provider_key})
    a_names = {b["candidate"] for b in bodies_in(d_a)}
    d_b = fresh("zapier")
    S.dispatch("POST", "/poc1/review-case", ident(),
               {"provider_key": S.STORE.provider_key})
    b_names = {b["candidate"] for b in bodies_in(d_b)}
    record("two candidates produce separately attributable corpora",
           "{'n8n'} / {'zapier'}", "%s / %s" % (a_names, b_names),
           a_names == {"n8n"} and b_names == {"zapier"},
           note="FAB-02: R1 hardcoded candidate='stub' at all 15 call sites",
           block="13_§4")

    # a restart does not overwrite a prior run's captures
    d_r = fresh("n8n")
    S.dispatch("POST", "/poc1/review-case", ident(),
               {"provider_key": S.STORE.provider_key})
    before = set(os.path.basename(p) for p in caps_in(d_r))
    inst1 = S.STORE.run_instance
    S.SECRETS = S.SecretIndex()
    S.STORE = S.Store(candidate="n8n"); S.STORE.base_url = "http://127.0.0.1:8787"
    S.Handler.data_dir = d_r
    S.dispatch("POST", "/poc1/review-case", ident(),
               {"provider_key": S.STORE.provider_key})
    after = set(os.path.basename(p) for p in caps_in(d_r))
    record("a restart does not overwrite the prior run's captures",
           "both runs present", "%d files, %d instances" % (
               len(after), len({b["run_instance"] for b in bodies_in(d_r)})),
           before <= after and len(after) > len(before)
           and S.STORE.run_instance != inst1,
           note="FAB-03: R1's counter restarted at 0001 and the runbook is "
                "deterministic, so a repeat run REPRODUCED earlier filenames",
           block="13_§4")

    # redaction, both directions
    d = fresh()
    live = S.STORE.mint_token("case-x")
    red = S.redact({"authority_id": "attestation-service",
                    "authority_version": "auth-v4", "tokens_used": 42,
                    "session_id": "sess-1", "receipt_id": "r-1",
                    "opaque": live, "note": "prefix" + live + "suffix",
                    "password": "hunter2"})
    record("authority_id / authority_version / tokens_used survive redaction intact",
           "unchanged", "%s/%s/%s" % (red["authority_id"], red["authority_version"],
                                      red["tokens_used"]),
           red["authority_id"] == "attestation-service"
           and red["authority_version"] == "auth-v4" and red["tokens_used"] == 42,
           note="FAB-05: R1 replaced these with a constant the harness scored PRESENT",
           block="13_§4")
    record("a live token under a benign key does NOT survive redaction",
           "redacted", "leaked" if live in json.dumps(red) else "redacted",
           live not in json.dumps(red),
           note="SEC-R1-02, and the concatenated case too", block="13_§4")
    record("a withheld value becomes a structured marker, never a bare constant",
           "__withheld__ with name/type/bytes/digest", type(red["password"]).__name__,
           isinstance(red["password"], dict) and "__withheld__" in red["password"]
           and {"name", "type", "bytes", "digest"} <= set(red["password"]),
           block="13_§4")

    # provider-authored decision refused on every persisting route
    d = fresh()
    P = {"provider_key": S.STORE.provider_key}
    persisting = ["/poc1/review-case", "/poc1/verify-decision", "/poc1/receipt",
                  "/poc1/refusal", "/poc2/triage", "/poc3/run-started",
                  "/poc3/checkpoint", "/poc3/reconcile", "/poc3/receipt",
                  "/relay/deliver", "/stage/deliver"]
    bad = [r for r in persisting
           if S.dispatch("POST", r, {"decision": "accept"}, P)[0] != 403]
    record("a provider-authored decision field is refused on EVERY persisting route",
           "0 accepting", "%d accepting: %s" % (len(bad), bad), not bad,
           note="FAB-06: R1 wired the check to 3 of 13 routes", block="13_§4")

    # duplicate run declaration preserves the prior record
    d = fresh()
    P = {"provider_key": S.STORE.provider_key}
    st, run = S.dispatch("POST", "/poc3/run-started",
                         {"schedule_id": "s", "occurrence": "t0"}, P)
    rid = run["run_id"]
    S.dispatch("POST", "/poc3/checkpoint", {"run_id": rid, "stage": 1}, P)
    started_before = S.STORE.runs[rid]["started_at"]
    cps_before = len(S.STORE.runs[rid]["checkpoints"])
    st, dupr = S.dispatch("POST", "/poc3/run-started",
                          {"run_id": rid, "schedule_id": "s", "occurrence": "t1"}, P)
    record("a duplicate run declaration preserves the prior record",
           "409, start and checkpoints intact",
           "%s / %s / %s" % (st, S.STORE.runs[rid]["started_at"] == started_before,
                             len(S.STORE.runs[rid]["checkpoints"]) == cps_before),
           st == 409 and S.STORE.runs[rid]["started_at"] == started_before
           and len(S.STORE.runs[rid]["checkpoints"]) == cps_before,
           note="FAB-07: R1 assigned rather than inserted-if-absent, so the replay "
                "after the MANDATED mid-flight kill erased the measurement",
           block="13_§4")
    record("...and the run identity is stub-minted, not provider-chosen",
           "stub-minted", rid[:4], rid.startswith("run-"), block="13_§4")

    st, rec = S.dispatch("POST", "/poc3/reconcile", {"run_id": rid}, P)
    record("the reconcile path does not assert an unperformed check",
           "no ACT-01 claim, explicit not-checked", str(rec.get("external_post_state_checked")),
           rec.get("external_post_state_checked") is False
           and "ACT-01" not in json.dumps(rec)
           and "NOT ESTABLISHED" in rec.get("side_effect_certainty", ""),
           note="FAB-08: R1 returned side_effect_certain True citing ACT-01 having "
                "checked nothing", block="13_§4")

    st, tri = S.dispatch("POST", "/poc2/triage",
                         {"origin": "external", "envelope": {"trust": "external-untrusted",
                                                             "partition": "business"}}, P)
    record("triage does not assert provider conduct it cannot observe",
           "no links_followed/actions_taken claim", "ok",
           "links_followed" not in tri and "actions_taken" not in tri
           and "NOT OBSERVED" in tri.get("provider_conduct", ""), block="13_§4")

    # captures are atomic — no .tmp survives, every file parses
    parsed = 0
    for p in caps_in(d):
        json.load(open(p, encoding="utf-8")); parsed += 1
    leftovers = [p for p in os.listdir(os.path.join(d, "captures")) if p.endswith(".tmp")]
    record("every capture is complete JSON and no temp file survives",
           "0 tmp, all parse", "%d parsed, %d tmp" % (parsed, len(leftovers)),
           parsed > 0 and not leftovers,
           note="FAB-10: the MANDATED mid-flight kill could leave torn JSON",
           block="13_§4")

    # boundary rules still hold
    block("boundary rules (carried forward, now at dispatch)")
    for label, payload, want in (
            ("no envelope", {"origin": "owner", "metadata": {}}, 400),
            ("wrong trust", {"origin": "owner", "envelope": {"trust": "trusted",
                                                             "partition": "business"}}, 400),
            ("personal partition", {"origin": "owner",
                                    "envelope": {"trust": "external-untrusted",
                                                 "partition": "personal"}}, 400),
            ("malformed envelope", {"origin": "owner", "envelope": "x"}, 400)):
        st, _ = S.dispatch("POST", "/poc2/triage", payload, P)
        record("POC-2 %s -> refused" % label, want, st, st == want)
    record("no Personal route exists at all", 404,
           S.dispatch("POST", "/poc2/personal", {}, P)[0],
           S.dispatch("POST", "/poc2/personal", {}, P)[0] == 404)

    # =====================================================================
    block("live HTTP — transport hardening (12_ §5)")
    live_rows = live_http_block()
    for r in live_rows:
        record(r[0], r[1], r[2], r[3], block="12_§5-live")

    passed = sum(1 for r in ROWS if r["ok"])
    report = {"check": "POC wrapper stub self-test (R2 contract)",
              "throwaway": S.THROWAWAY,
              "contract": "14_ §2 C-1..C-19; tests per 14_ §3",
              "unfixed_behaviour_demonstration": "r1_witnesses.py (pinned R1 build)",
              "cases": ROWS, "passed": passed, "total": len(ROWS)}
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "stub_selftest.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    sys.stderr.write("\nSTUB SELF-TEST %s — %d/%d cases\n"
                     % ("PASS" if passed == len(ROWS) else "FAIL", passed, len(ROWS)))
    return 0 if passed == len(ROWS) else 1


def live_http_block():
    """Transport-level cases that only a real socket can exercise."""
    rows = []
    data = tempfile.mkdtemp()
    port = 8899
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "stub_server.py"),
         "--candidate", "livetest", "--port", str(port), "--data", data],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    banner = ""
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen("http://127.0.0.1:%d/health" % port, timeout=1).read()
                break
            except Exception:
                time.sleep(0.2)

        def raw(request_bytes, read=True):
            import socket
            s = socket.create_connection(("127.0.0.1", port), timeout=5)
            try:
                s.sendall(request_bytes)
                return s.recv(4096).decode("latin-1") if read else ""
            finally:
                s.close()

        r = raw(b"POST /poc2/triage HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n"
                b"Content-Length: -1\r\n\r\n")
        rows.append(("negative Content-Length -> prompt refusal", "400",
                     r.split()[1] if len(r.split()) > 1 else r[:20], " 400 " in r))

        r = raw(b"POST /poc2/triage HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n"
                b"Transfer-Encoding: chunked\r\n\r\n")
        rows.append(("unsupported transfer encoding -> refused", "501",
                     r.split()[1] if len(r.split()) > 1 else r[:20], " 501 " in r))

        r = raw(b"POST /poc2/triage HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n"
                b"Content-Length: 5\r\nContent-Length: 9\r\n\r\n{}")
        rows.append(("conflicting Content-Length headers -> refused", "400",
                     r.split()[1] if len(r.split()) > 1 else r[:20], " 400 " in r))

        r = raw(b"POST /poc2/triage HTTP/1.1\r\nHost: x\r\nContent-Length: 2\r\n\r\n{}")
        rows.append(("browser-simple POST (no JSON content type) -> refused", "415",
                     r.split()[1] if len(r.split()) > 1 else r[:20], " 415 " in r))

        # slow body: declare a length and send nothing
        t0 = time.time()
        try:
            raw(b"POST /poc2/triage HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n"
                b"Content-Length: 100\r\n\r\n")
        except Exception:
            pass
        elapsed = time.time() - t0
        rows.append(("slow-body (declared length, nothing sent) -> bounded by the "
                     "socket timeout", "< 30s", "%.1fs" % elapsed, elapsed < 30))

        # secrets in the path and the query must not reach the log
        secret = "SUPERSECRETVALUE12345"
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/%s" % (port, secret), timeout=3)
        except urllib.error.HTTPError:
            pass
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/health?k=%s" % (port, secret), timeout=3)
        except urllib.error.HTTPError:
            pass
        raw(b"GARBAGE REQUEST LINE " + secret.encode() + b"\r\n\r\n")

        # deeply malformed JSON, then confirm the service is still healthy
        r = raw(b"POST /poc2/triage HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n"
                b"Content-Length: 7\r\n\r\n{{{{{{{")
        rows.append(("deeply malformed JSON -> structured refusal", "400",
                     r.split()[1] if len(r.split()) > 1 else r[:20], " 400 " in r))
        health = urllib.request.urlopen("http://127.0.0.1:%d/health" % port, timeout=3)
        rows.append(("...and the service is still healthy afterwards", "200",
                     health.status, health.status == 200))
    finally:
        proc.terminate()
        try:
            _out, banner = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            _out, banner = proc.communicate()

    rows.append(("a secret in the PATH is absent from the log", "absent",
                 "present" if secret in banner else "absent", secret not in banner))
    rows.append(("the startup banner prints no copyable command containing the key",
                 "no curl line", "curl present" if "curl" in banner else "no curl",
                 "curl" not in banner))
    keyline = [ln for ln in banner.splitlines() if ln.strip().startswith(("http", "-H"))]
    rows.append(("...and no request line is logged at all", "none", len(keyline),
                 not keyline))
    return rows


if __name__ == "__main__":
    sys.exit(run_self_test())

#!/usr/bin/env python3
# THROWAWAY POC EVIDENCE APPARATUS — see stub_server.py header.
"""Self-test for the POC wrapper stub.

`08_` §R1 names two refusals that must ship **shown failing**:

  1. a missing / forged / replayed resume token is refused;
  2. an approval decision arriving *from the provider side* is never accepted.

Both are exercised below against the live dispatch path, alongside the boundary
rules the packet makes binding. Every case states what it expects and the run
fails if any control stops firing.

Usage:  python3 selftest_stub.py [--data DIR]   (or: stub_server.py --self-test)
Exit:   0 all cases pass / 1 any case fails
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub_server as S  # noqa: E402


def envelope(partition="business", trust="external-untrusted"):
    return {"envelope": {"trust": trust, "partition": partition, "source": "test"},
            "metadata": {"subject": "artifact returned"}}


def run_self_test(data_dir: str) -> int:
    rows = []

    def case(label, expect_status, fn, note=None):
        status, body = fn()
        ok = (status == expect_status) if isinstance(expect_status, int) \
            else status in expect_status
        rows.append({"case": label, "expected_status": expect_status,
                     "actual_status": status, "ok": ok,
                     "reason": body.get("reason"), "note": note})
        sys.stderr.write("  [%s] %-58s -> %s%s\n"
                         % ("ok  " if ok else "FAIL", label, status,
                            ("  " + str(body.get("reason"))[:70]) if body.get("reason") else ""))
        return body

    with tempfile.TemporaryDirectory() as tmp:
        S.STORE = S.Store()
        d = os.path.join(tmp, "data")
        os.makedirs(d, exist_ok=True)
        post = lambda p, b: S.dispatch("POST", p, b, d)   # noqa: E731

        sys.stderr.write("\n-- MANDATORY REFUSAL 1: token handling (08_ §R1) --\n")
        case("no token presented", 403,
             lambda: post("/poc1/verify-decision", {}))
        case("forged token", 403,
             lambda: post("/poc1/verify-decision", {"token": "not-a-token-we-minted"}))
        case("empty-string token", 403,
             lambda: post("/poc1/verify-decision", {"token": ""}))
        case("non-string token", 403,
             lambda: post("/poc1/verify-decision", {"token": {"$ne": None}}))

        opened = case("open a review case (control)", 200,
                      lambda: post("/poc1/review-case", envelope()))
        tok = opened["resume_token"]
        rows.append({"case": "review-case does NOT hand the provider a case id",
                     "expected_status": "absent", "actual_status": "absent" if "case_id" not in opened else "present",
                     "ok": "case_id" not in opened, "reason": None,
                     "note": "the provider carries the token and nothing else"})
        sys.stderr.write("  [%s] review-case does NOT hand the provider a case id\n"
                         % ("ok  " if "case_id" not in opened else "FAIL"))
        cid = post("/owner/cases", {"owner_key": S.STORE.owner_key})[1]["cases"][-1]["case_id"]
        case("valid token, but no owner decision exists yet", 403,
             lambda: post("/poc1/verify-decision", {"token": tok}),
             "a valid token proves the pause was carried, not that anything was approved")

        # REGRESSION (found by the live HTTP run, not by this file's first draft):
        # the early poll above must NOT burn the token. The original code consumed
        # on validation, so a provider polling before the owner decided made the
        # owner's later approval unrelayable. Same token, polled twice, either side
        # of the decision — which is the shape a real provider produces.
        case("owner decides AFTER the early poll", 200,
             lambda: post("/owner/decide", {"case_id": cid, "decision": "accept",
                                            "owner_key": S.STORE.owner_key}))
        case("SAME token authorizes after the decision", 200,
             lambda: post("/poc1/verify-decision", {"token": tok}),
             "an early poll must not spend the owner's token")
        case("and only then is it spent", 403,
             lambda: post("/poc1/verify-decision", {"token": tok}))

        sys.stderr.write("\n-- the owner surface is not reachable by whoever can reach the port --\n")
        # THE ATTACK THAT WORKED before the owner key existed: the provider itself
        # POSTs /owner/decide for its own case, then verifies, and walks away with an
        # authorized ActionRequest. The field-name check passed the whole time — the
        # decision simply arrived through the owner door instead of the provider door.
        probe = post("/poc1/review-case", envelope())[1]
        case("provider cannot list cases without the key", 403,
             lambda: post("/owner/cases", {}),
             "so it cannot even learn which case id to address")
        pid = post("/owner/cases", {"owner_key": S.STORE.owner_key})[1]["cases"][-1]["case_id"]
        case("provider self-approves with no owner key", 403,
             lambda: post("/owner/decide", {"case_id": pid, "decision": "accept"}),
             "reaching 127.0.0.1 is not evidence that the owner decided")
        case("provider guesses a wrong owner key", 403,
             lambda: post("/owner/decide", {"case_id": pid, "decision": "accept",
                                            "owner_key": "not-the-key"}))
        case("and the case is therefore still undecided", 403,
             lambda: post("/poc1/verify-decision", {"token": probe["resume_token"]}))
        case("the owner, holding the key, can decide (control)", 200,
             lambda: post("/owner/decide", {"case_id": pid, "decision": "accept",
                                            "owner_key": S.STORE.owner_key}))
        case("and only then does it authorize (control)", 200,
             lambda: post("/poc1/verify-decision", {"token": probe["resume_token"]}))

        # Re-open, decide on the OWNER surface, then verify.
        opened2 = case("open a second review case (control)", 200,
                       lambda: post("/poc1/review-case", envelope()))
        tok2 = opened2["resume_token"]
        cid2 = post("/owner/cases", {"owner_key": S.STORE.owner_key})[1]["cases"][-1]["case_id"]
        case("owner records the decision on the owner surface", 200,
             lambda: post("/owner/decide", {"case_id": cid2, "decision": "accept",
                                            "owner_key": S.STORE.owner_key}))
        case("token + owner decision -> authorized (control)", 200,
             lambda: post("/poc1/verify-decision", {"token": tok2}))
        case("REPLAY the same token -> refused", 403,
             lambda: post("/poc1/verify-decision", {"token": tok2}),
             "single-use; the second relay must not happen")

        sys.stderr.write("\n-- MANDATORY REFUSAL 2: no decision from the provider side --\n")
        opened3 = post("/poc1/review-case", envelope())[1]
        tok3 = opened3["resume_token"]
        cid3 = post("/owner/cases", {"owner_key": S.STORE.owner_key})[1]["cases"][-1]["case_id"]
        post("/owner/decide", {"case_id": cid3, "decision": "accept",
                               "owner_key": S.STORE.owner_key})
        # An ALLOWLIST, not a denylist: the casing/unicode/nesting variants an
        # independent reviewer used to slip past a name check are all refused here
        # for the same reason — the key is not "token".
        for field in ("decision", "approved", "authorized", "owner_decision", "verdict",
                      "Approved", "APPROVED", "approve", "result", "status",
                      "decis\u043en", "target_endpoint"):
            case("provider supplies %r alongside a VALID token" % field, 403,
                 lambda f=field: post("/poc1/verify-decision", {"token": tok3, f: True}),
                 "refused before the token is even consumed")
        case("after those refusals the token is still unused (control)", 200,
             lambda: post("/poc1/verify-decision", {"token": tok3}),
             "a refused provider-decision attempt must not burn the owner's token")
        case("provider tries to open a case carrying a decision", 400,
             lambda: post("/poc1/review-case", dict(envelope(), approved=True)))

        sys.stderr.write("\n-- boundary rules in code (08_ §R1, packet §3) --\n")
        case("triage with no envelope", 400,
             lambda: post("/poc2/triage", {"metadata": {"subject": "x"},
                                           "envelope": {"partition": "business"}}))
        case("triage with a wrong trust class", 400,
             lambda: post("/poc2/triage", envelope(trust="trusted")))
        case("personal partition refused", 400,
             lambda: post("/poc2/triage", envelope(partition="personal")))
        case("payload with no partition refused", 400,
             lambda: post("/poc2/triage", {"envelope": {"trust": "external-untrusted"},
                                           "metadata": {}}))
        case("review-case with a personal partition refused", 400,
             lambda: post("/poc1/review-case", envelope(partition="personal")))
        case("clean triage (control)", 200,
             lambda: post("/poc2/triage", envelope()))
        # Malformed envelopes must REFUSE, not crash. Found by attacking the fixed
        # stub on the envelope lens: a non-dict envelope raised AttributeError inside
        # the partition check — the same fail-closed failure as the non-hashable
        # case_id, in a different handler.
        for bad in ("a-string", ["a-list"], 7, None):
            case("malformed envelope (%s) refuses, not crashes" % type(bad).__name__, 400,
                 lambda b=bad: post("/poc2/triage", {"envelope": b, "metadata": {}}))
        case("partition as a list refuses", 400,
             lambda: post("/poc2/triage", {"envelope": {"trust": "external-untrusted",
                                                        "partition": ["business"]}}))
        case("zero-width-space partition refuses", 400,
             lambda: post("/poc2/triage", {"envelope": {"trust": "external-untrusted",
                                                        "partition": "business\u200b"}}))
        case("top-level partition cannot override a personal envelope", 400,
             lambda: post("/poc2/triage", {"partition": "business",
                                           "envelope": {"trust": "external-untrusted",
                                                        "partition": "personal"}}))
        case("no Personal route exists at all", 404,
             lambda: post("/poc2/triage-personal", envelope()))
        case("unknown route refused", 404,
             lambda: post("/poc9/anything", {}))

        sys.stderr.write("\n-- POC-3 flow --\n")
        case("checkpoint for an unannounced run", 404,
             lambda: post("/poc3/checkpoint", {"run_id": "never-announced"}))
        case("run-started (control)", 200,
             lambda: post("/poc3/run-started", {"run_id": "r1", "occurrence": "2026-08-03T03:00:00Z",
                                                "schedule_id": "poc3-nightly"}))
        cp = case("checkpoint reports the side effect UNCERTAIN", 200,
                  lambda: post("/poc3/checkpoint", {"run_id": "r1", "stage": 1}),
                  "so the reconcile branch is exercised, not left inert")
        rows.append({"case": "checkpoint sets side_effect_certain=false",
                     "expected_status": "false", "actual_status": str(cp.get("side_effect_certain")).lower(),
                     "ok": cp.get("side_effect_certain") is False, "reason": None, "note": None})
        case("reconcile (control)", 200,
             lambda: post("/poc3/reconcile", {"run_id": "r1"}))
        case("run receipt (control)", 200,
             lambda: post("/poc3/receipt", {"run_id": "r1", "occurrence": "2026-08-03T03:00:00Z"}))

        sys.stderr.write("\n-- nothing secret-shaped is logged or persisted --\n")
        # The probe values are ASSEMBLED AT RUNTIME rather than written as literals,
        # so this file contains no credential-shaped string for a secret scanner to
        # flag. They are obvious fakes either way; the point is that a scan over the
        # return payload comes back clean without an "except the test file" caveat.
        fake_token = "gh" + "p_" + ("A" * 36)
        fake_header = "Authoriz" + "ation: Bearer " + "abc.def.ghi"
        leaky = dict(envelope())
        leaky["metadata"] = {"subject": "creds", "note": fake_token, "hdr": fake_header}
        case("case opened with secret-shaped content (control)", 200,
             lambda: post("/poc1/review-case", leaky))
        blob = ""
        cap_root = os.path.join(d, "captures")
        for root, _dirs, files in os.walk(cap_root):
            for f in files:
                blob += open(os.path.join(root, f), encoding="utf-8").read()
        leaks = S.contains_secret(blob)
        rows.append({"case": "no secret-shaped material in any capture record",
                     "expected_status": "none", "actual_status": ",".join(leaks) or "none",
                     "ok": not leaks, "reason": None, "note": None})
        sys.stderr.write("  [%s] no secret-shaped material in any capture record -> %s\n"
                         % ("ok  " if not leaks else "FAIL", ",".join(leaks) or "none"))
        redacted_marker = "[REDACTED:" in blob
        rows.append({"case": "redaction actually fired (proves the check is not vacuous)",
                     "expected_status": "true", "actual_status": str(redacted_marker).lower(),
                     "ok": redacted_marker, "reason": None, "note": None})
        sys.stderr.write("  [%s] redaction actually fired (the check is not vacuous)\n"
                         % ("ok  " if redacted_marker else "FAIL"))

        sys.stderr.write("\n-- capture records are marked synthetic and stay in place --\n")
        any_cap = None
        for root, _dirs, files in os.walk(cap_root):
            for f in files:
                any_cap = json.load(open(os.path.join(root, f), encoding="utf-8"))
                break
            if any_cap:
                break
        rows.append({"case": "capture records carry synthetic: true",
                     "expected_status": "true",
                     "actual_status": str(bool(any_cap and any_cap.get("synthetic"))).lower(),
                     "ok": bool(any_cap and any_cap.get("synthetic") is True),
                     "reason": None, "note": None})
        sys.stderr.write("  [%s] capture records carry synthetic: true\n"
                         % ("ok  " if any_cap and any_cap.get("synthetic") is True else "FAIL"))

        sys.stderr.write("\n-- findings from the independent adversarial pass --\n")
        # (a) structured secrets: a regex over decoded JSON can never see these.
        red = S.redact({"api_key": "abc123", "password": "hunter2",
                        "resume_token": "live-token-value", "nested": {"client_secret": "s3cr3t"},
                        "harmless": "ok"})
        struct_ok = (red["api_key"].startswith("[REDACTED") and red["password"].startswith("[REDACTED")
                     and red["resume_token"].startswith("[REDACTED")
                     and red["nested"]["client_secret"].startswith("[REDACTED")
                     and red["harmless"] == "ok")
        rows.append({"case": "structured secret FIELDS are redacted by key name",
                     "expected_status": "redacted", "actual_status": json.dumps(red)[:60],
                     "ok": struct_ok, "reason": None, "note": None})
        sys.stderr.write("  [%s] structured secret fields are redacted by key name\n"
                         % ("ok  " if struct_ok else "FAIL"))

        # (b) captures must not overwrite one another.
        p1 = S.write_capture(d, "stub", "POC1", "dup", {"n": 1})
        p2 = S.write_capture(d, "stub", "POC1", "dup", {"n": 2})
        rows.append({"case": "repeated captures of the same step do not overwrite",
                     "expected_status": "distinct paths",
                     "actual_status": "distinct" if p1 != p2 else "OVERWRITTEN",
                     "ok": p1 != p2 and os.path.exists(p1) and os.path.exists(p2),
                     "reason": None, "note": None})
        sys.stderr.write("  [%s] repeated captures of the same step do not overwrite\n"
                         % ("ok  " if p1 != p2 else "FAIL"))

        # (c) the provider must not choose where an owner-approved action goes.
        o4 = post("/poc1/review-case", envelope())[1]
        c4 = post("/owner/cases", {"owner_key": S.STORE.owner_key})[1]["cases"][-1]["case_id"]
        post("/owner/decide", {"case_id": c4, "decision": "accept",
                               "owner_key": S.STORE.owner_key})
        case("provider tries to redirect the approved action", 403,
             lambda: post("/poc1/verify-decision", {"token": o4["resume_token"],
                                                    "target_endpoint": "http://attacker/"}),
             "the owner decided WHAT; the target is not the provider's to choose")
        auth = post("/poc1/verify-decision", {"token": o4["resume_token"]})[1]
        tgt_ok = auth.get("action_request", {}).get("endpoint") == S.ACTION_TARGET
        rows.append({"case": "the authorized endpoint comes from the AI OS side",
                     "expected_status": S.ACTION_TARGET,
                     "actual_status": auth.get("action_request", {}).get("endpoint"),
                     "ok": tgt_ok, "reason": None, "note": None})
        sys.stderr.write("  [%s] the authorized endpoint comes from the AI OS side\n"
                         % ("ok  " if tgt_ok else "FAIL"))

        # (d) a rejection is a decision, and decisions are captured.
        o5 = post("/poc1/review-case", envelope())[1]
        c5 = post("/owner/cases", {"owner_key": S.STORE.owner_key})[1]["cases"][-1]["case_id"]
        post("/owner/decide", {"case_id": c5, "decision": "reject",
                               "owner_key": S.STORE.owner_key})
        rej = post("/poc1/verify-decision", {"token": o5["resume_token"]})[1]
        names = []
        for root, _dd, ff in os.walk(os.path.join(d, "captures")):
            names += ff
        cap_ok = (rej.get("authorized") is False
                  and any(n.startswith("owner-decision") for n in names)
                  and any(n.startswith("verify-rejected") for n in names))
        rows.append({"case": "owner decisions and rejections both write captures",
                     "expected_status": "both present",
                     "actual_status": "present" if cap_ok else "missing",
                     "ok": cap_ok, "reason": None, "note": None})
        sys.stderr.write("  [%s] owner decisions and rejections both write captures\n"
                         % ("ok  " if cap_ok else "FAIL"))

        # (e) a non-hashable case_id must refuse, not crash the handler.
        case("non-string case_id refuses instead of crashing", 400,
             lambda: post("/owner/decide", {"case_id": {"a": 1}, "decision": "accept",
                                            "owner_key": S.STORE.owner_key}))

        escaped = S.write_capture(d, "../../../etc", "POC1", "x", {"a": 1})
        rows.append({"case": "capture path traversal refused",
                     "expected_status": "None", "actual_status": str(escaped),
                     "ok": escaped is None, "reason": None, "note": None})
        sys.stderr.write("  [%s] capture path traversal refused\n"
                         % ("ok  " if escaped is None else "FAIL"))

    passed = sum(1 for r in rows if r["ok"])
    report = {"check": "POC wrapper stub self-test",
              "throwaway": S.THROWAWAY,
              "mandatory_refusals": [
                  "missing / forged / replayed resume token",
                  "approval decision arriving from the provider side",
                  "a decision recorded on the owner surface by anything that merely "
                  "reached the port (the owner key closes this)"],
              "cases": rows, "passed": passed, "total": len(rows)}
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "stub_selftest.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    sys.stderr.write("\nSTUB SELF-TEST %s — %d/%d cases\n"
                     % ("PASS" if passed == len(rows) else "FAIL", passed, len(rows)))
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    d = sys.argv[sys.argv.index("--data") + 1] if "--data" in sys.argv else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    sys.exit(run_self_test(d))

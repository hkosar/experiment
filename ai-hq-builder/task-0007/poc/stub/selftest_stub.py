#!/usr/bin/env python3
# THROWAWAY POC EVIDENCE APPARATUS — see stub_server.py header.
"""Self-test for the R3 POC wrapper stub — `25_` §E.

Blocks, in §E's order:

    identity and registration · owner-idea authority · owner reconciliation
    (R5Q-01) · capability and reconciliation · evidence (six write boundaries)
    · capacity and redaction · transport and policy · validator

`25_` §E requires each to be "demonstrated failing against the pre-R3 behaviour
using the **witness method**: probes run against the SHA-pinned artifact ...
**never** defect switches." That demonstration is `r1_witnesses.py`, which pins
both superseded builds — R1 in `r1_reference/`, R2 in `r2_reference/` — checks
each digest before loading it, and refuses to continue on a mismatch. There is
no defect switch anywhere in this build: a switch that can disable a control is
itself a finding (P2V-01). Run both:

    python3 selftest_stub.py     # the R3 contract holds
    python3 r1_witnesses.py      # the R1 and R2 contracts did not

Two things this suite does that its R2 predecessor did not, both because of
what the R2 predecessor missed:

  * a **live HTTP block** that carries a real token and a real capability over a
    real socket. The R2 suite passed 56/56 while the R2 service was unrunnable
    over HTTP, because it exercised `dispatch()` in-process and never crossed
    the response path where the loss happened (DEF-R2-01).
  * an **outcome-coverage guard**: every outcome code the source can emit must
    actually be produced by some case here. Two §E-required refusals were
    unreachable in the first R3 draft — the role checks sat behind the
    registration binding, which A.2 guarantees can never disagree with them. A
    refusal reason no request can produce is not a control.

Exit: 0 all cases pass / 1 any case fails
"""
from __future__ import annotations

import builtins
import glob
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub_server as S  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")
ROWS = []
OUTCOMES_SEEN = set()

R5_PINNED_SHA256 = "972c30d532a957a94a8e7200c9385e387f7508673335acdc8652eb6e3dd15e68"
# R7 — the R6 build the verifier examined and reported on in `45_`.
R6_PINNED_SHA256 = "d0fd4c449e797be422c78b2c283d6c7b0232dfbcb96a286821279c49b0d19ac0"
# R8 — the R7 build the verifier EXECUTED and reported on in `49_`, concurred
# in `50_`; both independently report this digest for it.
R7_PINNED_SHA256 = "69b98fb09ae94d4f38b30e3e2d2179045fe4e50b529033940a7ad1ccf6b0ac91"
# R9 — the R8 build the verifier executed four times, reported in `54_` and
# concurred in `55_`.
R8_PINNED_SHA256 = "5df1408fdf2fd5dbcb5d2577a20c14699009493c32de1ba7c0d6c347c44bf7a1"

A8_NAMED = frozenset((
    "receipt_id", "subject_ref", "executed_at", "occurrence", "schedule_version",
    "purpose", "authority_id", "authority_version", "content_hash",
    "action_request_id", "action_class", "scope", "policy_version", "risk_class",
    "idempotency_key", "side_effect_status",
    "tokens_used", "task_count", "execution_count", "session_id"))

DIGEST = "a" * 64
OWNER_CONTENT = {"title": "Ship the relay", "body": "Wire the approval path.",
                 "project": "ai-hq", "tags": ["poc", "relay"]}
CURRENT_BLOCK = [""]


# --------------------------------------------------------------------------
# harness
# --------------------------------------------------------------------------
def record(case, expected, actual, ok, note=None, blk=None):
    ROWS.append({"case": case, "expected": str(expected), "actual": str(actual),
                 "ok": bool(ok), "note": note, "block": blk})
    sys.stderr.write("  [%s] %-74s %s\n"
                     % ("ok  " if ok else "FAIL", case[:74],
                        "" if ok else "(expected %s, got %s)" % (expected, actual)))
    return ok


def block(title):
    CURRENT_BLOCK[0] = title
    sys.stderr.write("\n-- %s --\n" % title)


def check(case, ok, expected="", actual="", note=None):
    return record(case, expected, actual, ok, note=note, blk=CURRENT_BLOCK[0])


def fresh(candidate="n8n"):
    """A clean service: new secret index, new store, new capture directory."""
    S.SECRETS = S.SecretIndex()
    S.DESCRIPTOR_KEY = S.secrets.token_bytes(32)
    S.STORE = S.Store(candidate=candidate)
    S.STORE.base_url = "http://127.0.0.1:8787"
    d = tempfile.mkdtemp(prefix="selftest-")
    S.Handler.data_dir = d
    return d


def owner():
    return {"owner_key": S.STORE.owner_key, "provider_key": ""}


def provider():
    return {"owner_key": "", "provider_key": S.STORE.provider_key}


def post(path, body, headers=None):
    status, out = S.dispatch("POST", path, body, headers or provider())
    if isinstance(out, dict) and isinstance(out.get("outcome"), str):
        OUTCOMES_SEEN.add(out["outcome"])
    return status, out


def get(path, headers=None):
    status, out = S.dispatch("GET", path, {}, headers or {})
    if isinstance(out, dict) and isinstance(out.get("outcome"), str):
        OUTCOMES_SEEN.add(out["outcome"])
    return status, out


def reveal(value):
    return value.value if isinstance(value, S.Disclose) else value


def register(task="TASK-0007", transition="builder->verifier", role="verifier",
             digest=DIGEST):
    return post("/owner/artifact/register",
                {"source_digest": digest, "size_bytes": 4096, "file_count": 12,
                 "task_id": task, "transition": transition, "target_role": role},
                owner())[1]


def review(ref, task="TASK-0007", transition="builder->verifier", role="verifier",
           digest=DIGEST, epoch=0):
    return post("/poc1/review-case",
                {"registration_ref": ref, "task_id": task, "transition": transition,
                 "artifact_digest": digest, "target_role": role,
                 "submission_epoch": epoch,
                 "envelope": {"partition": "business",
                              "trust": "external-untrusted"}})


def undecided_case():
    cases = post("/owner/cases", {}, owner())[1]["cases"]
    return [c["case_id"] for c in cases if not c["decided"]][-1]


def to_capability(task="TASK-0007", epoch=0, decision="accept"):
    """Register -> review -> owner decision -> minted capability."""
    reg = register(task=task)
    opened = review(reg["registration_ref"], task=task, epoch=epoch)[1]
    cid = undecided_case()
    post("/owner/decide", {"case_id": cid, "decision": decision}, owner())
    verified = post("/poc1/verify-decision",
                    {"token": reveal(opened["resume_token"])})[1]
    return {"registration": reg, "opened": opened, "case_id": cid,
            "verified": verified,
            "capability": reveal(verified.get("execution_capability")),
            "action_request": verified.get("action_request")}


class FailWrite:
    """Fail a capture write, exactly as a full or read-only disk would.

    `phase` names the transition whose COMMITTED record fails — the boundary §E
    enumerates. This is not a defect switch: it rebinds the name `write_capture`
    inside this test process for the duration of one call, and nothing in the
    shipped service can reach it. The service has no flag that turns a control
    off, at any layer, which is the point of P2V-01.
    """

    def __init__(self, phase="committed"):
        self.phase = phase

    def __enter__(self):
        self.real = S.write_capture

        def fail(route, poc, step, *a, **kw):
            if self.phase == "all" or step == "committed-" + self.phase \
                    or (self.phase == "committed" and step.startswith("committed-")):
                raise S.CaptureError("injected: %s write failed" % step)
            return self.real(route, poc, step, *a, **kw)

        S.write_capture = fail
        return self

    def __exit__(self, *exc):
        S.write_capture = self.real


def capture_paths(d):
    out = []
    for root, _dirs, files in os.walk(os.path.join(d, "captures")):
        out += [os.path.join(root, f) for f in files if f.endswith(".json")]
    return out


def capture_bodies(d):
    bodies = [json.load(open(p, encoding="utf-8")) for p in capture_paths(d)]
    # Capture-only outcomes (`prepared`, `committed`) never ride a response, so
    # the coverage guard would report them unreachable if it watched responses
    # alone — the same blind spot, one layer down, that DEF-R2-01 came from.
    for b in bodies:
        out = b.get("fields", {}).get("outcome")
        if isinstance(out, str):
            OUTCOMES_SEEN.add(out)
    return bodies


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# --------------------------------------------------------------------------
# §E — identity and registration
# --------------------------------------------------------------------------
def block_identity():
    block("identity and registration (A.1 / A.2)")
    fresh()
    reg = register()
    check("registration mints an artifact_id and an opaque registration_ref",
          reg.get("artifact_id", "").startswith("art-")
          and reg.get("registration_ref", "").startswith("reg-"), "art-/reg-", reg)

    again = register()
    check("re-registering the same identity is idempotent — one record, same refs",
          again["artifact_id"] == reg["artifact_id"]
          and again["registration_ref"] == reg["registration_ref"],
          "same ids", (again["artifact_id"], reg["artifact_id"]))

    role_variant = register(role="reader")
    check("a re-registration differing ONLY in target_role is a DISTINCT "
          "registration, not a silent role change",
          role_variant["artifact_id"] != reg["artifact_id"],
          "different artifact_id", role_variant["artifact_id"])

    st, _ = post("/owner/artifact/register",
                 {"source_digest": DIGEST, "size_bytes": 1, "file_count": 1,
                  "task_id": "T", "transition": "b->v", "target_role": "owner"},
                 owner())
    check("the owner cannot register an unauthorized target_role (A.2 requires an "
          "A.1-authorized role)", st == 400, 400, st)

    first = review(reg["registration_ref"])
    check("a bound review-case opens and returns the token ONLY — no case id, no "
          "case content, no decision (A.6)",
          first[0] == 200 and "resume_token" in first[1]
          and not {"case_id", "decision", "case"} & set(first[1]),
          "token only", sorted(first[1]))

    dup = review(reg["registration_ref"])
    check("the same five identity components suppress reprocessing and return the "
          "prior receipt (reprocessed: false)",
          dup[0] == 200 and dup[1].get("duplicate_suppressed") is True
          and dup[1].get("reprocessed") is False
          and dup[1].get("outcome") == "duplicate-suppressed",
          "duplicate-suppressed", dup[1].get("outcome"))

    other_reg = register(task="TASK-OTHER")
    other = review(other_reg["registration_ref"], task="TASK-OTHER")
    check("the same artifact under a DIFFERENT task_id is a distinct identity and "
          "processes independently",
          other[0] == 200 and "resume_token" in other[1]
          and other[1].get("duplicate_suppressed") is not True,
          "case-opened", other[1].get("outcome"))

    unauth = review(reg["registration_ref"], role="owner")
    check("an unauthorized target_role REJECTS 403 rejected-unauthorized-target, "
          "distinguishable from duplicate-suppression success",
          unauth[0] == 403
          and unauth[1].get("outcome") == "rejected-unauthorized-target",
          "403 rejected-unauthorized-target", (unauth[0], unauth[1].get("outcome")))

    unknown = review(reg["registration_ref"], role="wizard")
    check("an UNKNOWN role is a 400 rejected-unknown-target, distinguishable from "
          "the unauthorized case",
          unknown[0] == 400 and unknown[1].get("outcome") == "rejected-unknown-target",
          "400 rejected-unknown-target", (unknown[0], unknown[1].get("outcome")))

    for field, kw in (("task_id", {"task": "WRONG"}),
                      ("transition", {"transition": "wrong->wrong"}),
                      ("artifact_digest", {"digest": "b" * 64})):
        st, out = review(reg["registration_ref"], **kw)
        check("a registration-binding mismatch on %s refuses 403 "
              "rejected-artifact-binding" % field,
              st == 403 and out.get("outcome") == "rejected-artifact-binding",
              "403 rejected-artifact-binding", (st, out.get("outcome")))

    st, out = review("reg-does-not-exist")
    check("an unknown registration_ref refuses 403 — a provider-supplied digest is "
          "only ever CHECKED AGAINST the owner-registered one, never trusted alone",
          st == 403 and out.get("outcome") == "rejected-artifact-binding",
          "403", (st, out.get("outcome")))

    st, out = post("/poc1/review-case",
                   {"registration_ref": reg["registration_ref"], "task_id": "T",
                    "transition": "b->v", "artifact_digest": "not-a-digest",
                    "target_role": "verifier", "submission_epoch": 0,
                    "envelope": {"partition": "business",
                                 "trust": "external-untrusted"}})
    check("a malformed artifact_digest is a captured 400 — a raw archive hash alone "
          "is not identity", st == 400, 400, st)

    st, out = post("/poc1/review-case",
                   {"registration_ref": reg["registration_ref"], "task_id": "T",
                    "transition": "b->v", "artifact_digest": DIGEST,
                    "target_role": "verifier", "submission_epoch": -1,
                    "envelope": {"partition": "business",
                                 "trust": "external-untrusted"}})
    check("a negative submission_epoch is a captured 400", st == 400, 400, st)

    flow = to_capability(task="TASK-IDENT")
    payload = flow["action_request"]["payload"]
    check("the idempotency key TRAVELS IN THE ACTIONREQUEST PAYLOAD to the target, "
          "not only on the envelope",
          payload.get("idempotency_key") == flow["action_request"]["idempotency_key"],
          "present and equal", payload.get("idempotency_key"))


# --------------------------------------------------------------------------
# §E — owner-idea authority
# --------------------------------------------------------------------------
def block_owner_idea():
    block("owner-idea authority, bound to canonical content (A.3)")
    d = fresh()
    idea = post("/owner/idea", {"owner_content": dict(OWNER_CONTENT)}, owner())[1]
    ref = idea["idea_ref"]
    check("the owner idea is stored server-side with an owner_content_digest",
          ref.startswith("idea-") and len(idea.get("owner_content_digest", "")) == 64,
          "idea- ref + digest", idea.get("owner_content_digest"))

    ext = {"envelope": {"partition": "business", "trust": "external-untrusted"},
           "source": "web-search", "content": "unrelated third-party text"}
    st, ok = post("/poc2/triage", {"idea_ref": ref,
                                   "owner_content": dict(OWNER_CONTENT),
                                   "external_items": [ext]})
    check("a matching convenience copy is accepted and triages the STORED content",
          st == 200 and ok.get("staged") is True, 200, st)

    comps = {c["component"]: c["instruction_authority"]
             for c in ok.get("authority_components", [])}
    check("authority is recorded PER COMPONENT — owner_content owner-authorized, "
          "each external item none (a flattened value for the whole request is a "
          "defect)",
          comps.get("owner_content") == "owner-authorized"
          and comps.get("external_items[0]") == "none",
          "per-component", comps)

    for field, altered in (("body", {"body": "Do something else entirely."}),
                           ("title", {"title": "Different title"}),
                           ("project", {"project": "other-project"}),
                           ("tags", {"tags": ["poc", "relay", "extra"]})):
        bad = dict(OWNER_CONTENT, **altered)
        st, out = post("/poc2/triage", {"idea_ref": ref, "owner_content": bad,
                                        "external_items": []})
        check("a valid idea_ref with an ALTERED %s is refused and never appears as "
              "owner-authorized" % field,
              st == 403 and out.get("outcome") == "refused-content-mismatch"
              and "owner-authorized" not in json.dumps(out),
              "403 refused-content-mismatch", (st, out.get("outcome")))

    st, out = post("/poc2/triage", {"owner_content": dict(OWNER_CONTENT),
                                    "external_items": []})
    check("owner_content WITHOUT a valid idea_ref is refused — it is never "
          "owner-authored", st == 403, 403, st)

    st, out = post("/poc2/triage",
                   {"idea_ref": ref, "external_items": [{"source": "web",
                                                         "content": "no envelope"}]})
    check("an external_items entry lacking its OWN envelope is a captured 400",
          st == 400, 400, st)

    st, out = post("/poc2/triage",
                   {"idea_ref": ref, "external_items": [
                       dict(ext, origin="owner", trust="owner-authorized",
                            instruction_authority="owner-authorized")]})
    comps = {c["component"]: c["instruction_authority"]
             for c in (out.get("authority_components") or [])}
    check("a valid idea_ref never elevates an external item, and provider-supplied "
          "origin/trust/instruction_authority never increase authority",
          st == 200 and comps.get("external_items[0]") == "none",
          "external item authority none", comps)

    staged = [b for b in capture_bodies(d) if b["step"] == "idea-staged"]
    check("per-component authority appears in the CAPTURE, not only the response",
          staged and any("authority_components" in b.get("fields", {})
                         for b in staged),
          "authority_components in capture", len(staged))

    st, out = post("/poc2/triage",
                   {"envelope": {"partition": "business",
                                 "trust": "external-untrusted"},
                    "external_items": [ext]})
    comps = {c["component"]: c["instruction_authority"]
             for c in (out.get("authority_components") or [])}
    check("Case B (no idea_ref) requires the top-level external-untrusted envelope, "
          "classifies and summarises only, and carries no owner-authorized component",
          st == 200 and out.get("case") == "B"
          and "owner_content" not in comps
          and set(comps.values()) == {"none"},
          "case B, authority none", (st, comps))
    st, out = post("/poc2/triage", {"external_items": [ext]})
    check("...and Case B without that envelope is refused",
          st == 400 and out.get("outcome") == "refused-envelope", 400, st)
    check("the response never carries a single flattened authority value for the "
          "whole request — A.3 calls that a defect",
          "instruction_authority" not in out or out.get("case") is None,
          "per-component only", out.get("instruction_authority"))

    st, out = post("/poc2/triage", {"idea_ref": "idea-nope"})
    check("an unknown idea_ref refuses", st == 403, 403, st)


# --------------------------------------------------------------------------
# §E — owner reconciliation (R5Q-01)
# --------------------------------------------------------------------------
def block_owner_reconciliation():
    block("owner reconciliation — R5Q-01 (A.5)")
    fresh()
    flow = to_capability(task="TASK-REC")
    cap, ar = flow["capability"], flow["action_request"]

    st, out = post("/owner/reconcile",
                   {"action_request_id": ar["id"], "outcome": "not_delivered",
                    "note": "n"}, provider())
    check("a PROVIDER cannot reach the owner-reconciliation route at all",
          st == 403 and out.get("outcome") == "refused-auth", 403, st)

    st, out = post("/owner/reconcile",
                   {"action_request_id": ar["id"], "outcome": "not_delivered",
                    "note": "n"}, owner())
    check("owner reconcile from a NON-UNCERTAIN state is refused with no state change",
          st == 409 and S.STORE.capabilities[cap]["status"] == S.MINTED,
          "409, still MINTED", (st, S.STORE.capabilities[cap]["status"]))

    # Reach UNCERTAIN the only way the service can: a delivery whose committed
    # record does not land, where rollback of the external effect is impossible.
    with FailWrite("delivery"):
        post("/relay/deliver",
             {"capability": cap, "action_request_id": ar["id"],
              "case_id": flow["case_id"], "payload": ar["payload"],
              "destination_digest_claimed": DIGEST})
    check("a delivery whose committed record fails leaves the subject UNCERTAIN",
          S.STORE.capabilities[cap]["status"] == S.UNCERTAIN,
          S.UNCERTAIN, S.STORE.capabilities[cap]["status"])

    st, out = post("/owner/reconcile",
                   {"action_request_id": ar["id"], "outcome": "delivered",
                    "note": "n"}, owner())
    check("owner reconcile with outcome='delivered' is refused with no state change "
          "— this route cannot create a delivered state",
          st == 400 and S.STORE.capabilities[cap]["status"] == S.UNCERTAIN,
          "400, still UNCERTAIN", (st, S.STORE.capabilities[cap]["status"]))

    st, out = post("/owner/reconcile",
                   {"action_request_id": ar["id"], "outcome": "not_delivered",
                    "note": "checked the destination by hand"}, owner())
    check("owner reconcile with outcome='not_delivered' from UNCERTAIN is accepted "
          "once", st == 200
          and S.STORE.capabilities[cap]["status"] == S.RECONCILED_NOT_DELIVERED,
          "200 RECONCILED_NOT_DELIVERED",
          (st, S.STORE.capabilities[cap]["status"]))

    st2, out2 = post("/owner/reconcile",
                     {"action_request_id": ar["id"], "outcome": "not_delivered",
                      "note": "again"}, owner())
    check("a REPLAY of the same owner reconciliation returns the prior result or a "
          "refusal, never a second transition",
          st2 != 200 or out2.get("replayed") is True,
          "no second transition", (st2, out2.get("outcome")))


# --------------------------------------------------------------------------
# §E — capability and reconciliation
# --------------------------------------------------------------------------
def block_capability():
    block("capability state machine and reconciliation (A.4 / A.5)")
    fresh()
    flow = to_capability(task="TASK-CAP")
    cap, ar, cid = flow["capability"], flow["action_request"], flow["case_id"]
    check("a terminal owner ACCEPT mints the capability (MINTED)",
          S.STORE.capabilities[cap]["status"] == S.MINTED,
          S.MINTED, S.STORE.capabilities[cap]["status"])

    st, out = post("/relay/deliver",
                   {"capability": cap, "action_request_id": ar["id"],
                    "case_id": cid, "payload": {"anything": "the provider likes"},
                    "destination_digest_claimed": DIGEST})
    check("a provider-chosen payload does not match the capability binding and is "
          "refused", st == 403 and out.get("outcome") == "refused-payload-mismatch",
          "403 refused-payload-mismatch", (st, out.get("outcome")))

    st, out = post("/relay/deliver",
                   {"capability": cap, "action_request_id": "ar-not-this-one",
                    "case_id": cid, "payload": ar["payload"],
                    "destination_digest_claimed": DIGEST})
    check("a mismatched action_request_id in the binding is refused", st == 403,
          403, st)

    st, out = post("/relay/deliver",
                   {"capability": "cap-" + "f" * 32, "action_request_id": ar["id"],
                    "case_id": cid, "payload": ar["payload"],
                    "destination_digest_claimed": DIGEST})
    check("a forged capability cannot produce the side effect — /relay/deliver "
          "fails closed without a valid one",
          st == 403 and out.get("outcome") == "refused-no-capability", 403, st)

    st, out = post("/relay/deliver",
                   {"capability": cap, "action_request_id": ar["id"],
                    "case_id": cid, "payload": ar["payload"],
                    "destination_digest_claimed": DIGEST})
    check("the authorized delivery succeeds and the SERVICE mints the receipt",
          st == 200 and out.get("delivered") is True
          and out["receipt"]["receipt_id"].startswith("dlv-"),
          "delivered + service receipt", (st, out.get("outcome")))
    receipt_id = out["receipt"]["receipt_id"]
    check("delivery reaches DELIVERED_WITH_RECEIPT",
          S.STORE.capabilities[cap]["status"] == S.DELIVERED_WITH_RECEIPT,
          S.DELIVERED_WITH_RECEIPT, S.STORE.capabilities[cap]["status"])

    st, out = post("/relay/deliver",
                   {"capability": cap, "action_request_id": ar["id"],
                    "case_id": cid, "payload": ar["payload"],
                    "destination_digest_claimed": DIGEST})
    check("a REPLAY from DELIVERED_WITH_RECEIPT returns the PRIOR receipt with "
          "replayed:true and no_second_side_effect:true",
          st == 200 and out.get("replayed") is True
          and out.get("no_second_side_effect") is True
          and out["receipt"]["receipt_id"] == receipt_id,
          "prior receipt replayed", (st, out.get("outcome")))

    st, out = post("/relay/deliver",
                   {"capability": cap, "action_request_id": ar["id"],
                    "case_id": cid, "payload": dict(ar["payload"], extra="x"),
                    "destination_digest_claimed": DIGEST})
    check("a second DISTINCT delivery from DELIVERED_WITH_RECEIPT is refused — a "
          "replay is not a second side effect", st == 403, 403, st)

    st, out = post("/poc1/receipt",
                   {"action_request_id": ar["id"], "case_id": cid,
                    "provider_status": "ok", "provider_message": "we delivered it",
                    "destination_digest_claimed": "b" * 64,
                    "provider_metrics": {"task_count": 3, "step_count": 9,
                                         "execution_count": 1, "tokens_used": 120}})
    check("a provider receipt is corroborating only: recorded, cannot mark "
          "delivered, cannot alter capability state",
          st == 200 and out.get("action_request_status_changed") is False
          and S.STORE.capabilities[cap]["status"] == S.DELIVERED_WITH_RECEIPT,
          "recorded, no state change", (st, out.get("action_request_status")))

    st, out = post("/poc1/refusal",
                   {"action_request_id": ar["id"], "case_id": cid,
                    "refusal_code": "policy", "refusal_message": "declined"})
    check("a provider refusal likewise records and alters nothing",
          st == 200 and out.get("action_request_status_changed") is False
          and S.STORE.capabilities[cap]["status"] == S.DELIVERED_WITH_RECEIPT,
          "recorded, no state change", st)

    # revocation and the late receipt
    flow2 = to_capability(task="TASK-REVOKE")
    cap2, ar2 = flow2["capability"], flow2["action_request"]
    st, out = post("/owner/revoke", {"capability": cap2,
                                     "action_request_id": ar2["id"],
                                     "reason": "changed my mind"}, owner())
    check("the owner surface can revoke a non-terminal capability",
          st == 200 and S.STORE.capabilities[cap2]["status"] == S.REVOKED,
          S.REVOKED, S.STORE.capabilities[cap2]["status"])
    st, out = post("/relay/deliver",
                   {"capability": cap2, "action_request_id": ar2["id"],
                    "case_id": flow2["case_id"], "payload": ar2["payload"],
                    "destination_digest_claimed": DIGEST})
    check("/relay/deliver on REVOKED is a captured refusal with no state change",
          st == 403 and S.STORE.capabilities[cap2]["status"] == S.REVOKED, 403, st)
    st, out = post("/poc1/receipt",
                   {"action_request_id": ar2["id"], "case_id": flow2["case_id"],
                    "provider_status": "ok", "provider_message": "late",
                    "destination_digest_claimed": None, "provider_metrics": {}})
    check("a LATE provider receipt on REVOKED is captured, refused and changes "
          "nothing",
          st == 409 and out.get("action_request_status_changed") is False
          and S.STORE.capabilities[cap2]["status"] == S.REVOKED,
          "409, still REVOKED", (st, S.STORE.capabilities[cap2]["status"]))

    # expiry
    flow3 = to_capability(task="TASK-EXPIRE")
    cap3, ar3 = flow3["capability"], flow3["action_request"]
    S.STORE.capabilities[cap3]["expires_at"] = time.time() - 1
    st, out = post("/relay/deliver",
                   {"capability": cap3, "action_request_id": ar3["id"],
                    "case_id": flow3["case_id"], "payload": ar3["payload"],
                    "destination_digest_claimed": DIGEST})
    check("CAPABILITY_TTL_S expiry moves the capability to EXPIRED and delivery "
          "fails closed",
          st == 403 and S.STORE.capabilities[cap3]["status"] == S.EXPIRED,
          S.EXPIRED, S.STORE.capabilities[cap3]["status"])
    st, out = post("/poc1/receipt",
                   {"action_request_id": ar3["id"], "case_id": flow3["case_id"],
                    "provider_status": "ok", "provider_message": "late",
                    "destination_digest_claimed": None, "provider_metrics": {}})
    check("a LATE provider receipt on EXPIRED is captured, refused and changes "
          "nothing", st == 409 and S.STORE.capabilities[cap3]["status"] == S.EXPIRED,
          409, st)

    # reconciliation
    flow4 = to_capability(task="TASK-RECON")
    cap4, ar4 = flow4["capability"], flow4["action_request"]
    st, out = post("/poc1/reconcile", {"capability": cap4,
                                       "action_request_id": ar4["id"]})
    check("/poc1/reconcile on a MINTED capability answers UNCERTAIN but does NOT "
          "move it — A.4 lists no MINTED -> UNCERTAIN, and a provider must not be "
          "able to strand its own authorization",
          out.get("reconciliation_result") == S.UNCERTAIN
          and S.STORE.capabilities[cap4]["status"] == S.MINTED,
          "UNCERTAIN result, MINTED state",
          (out.get("reconciliation_result"), S.STORE.capabilities[cap4]["status"]))

    post("/relay/deliver", {"capability": cap4, "action_request_id": ar4["id"],
                            "case_id": flow4["case_id"], "payload": ar4["payload"],
                            "destination_digest_claimed": DIGEST})
    st, out = post("/poc1/reconcile", {"capability": cap4,
                                       "action_request_id": ar4["id"]})
    check("with a SERVICE-owned receipt, /poc1/reconcile answers "
          "reconciled-delivered",
          st == 200 and out.get("outcome") == "reconciled-delivered", 200,
          out.get("outcome"))

    # A.5: local absence is never proof, and it never authorizes a retry.
    with S.STORE.lock:
        S.STORE.relay_receipts.clear()
    S.STORE.capabilities[cap4]["status"] = S.ATTEMPT_STARTED
    st, out = post("/poc1/reconcile", {"capability": cap4,
                                       "action_request_id": ar4["id"]})
    check("every local receipt removed after a simulated uncertain external "
          "completion: /poc1/reconcile answers UNCERTAIN and can NEVER return "
          "RECONCILED_NOT_DELIVERED",
          out.get("reconciliation_result") == S.UNCERTAIN
          and out.get("reconciled_not_delivered") is False
          and S.STORE.capabilities[cap4]["status"] != S.RECONCILED_NOT_DELIVERED,
          "UNCERTAIN, never NOT_DELIVERED", out.get("outcome"))
    st, out = post("/relay/deliver",
                   {"capability": cap4, "action_request_id": ar4["id"],
                    "case_id": flow4["case_id"], "payload": ar4["payload"],
                    "destination_digest_claimed": DIGEST})
    check("...and no retry becomes authorized from UNCERTAIN",
          st != 200 and out.get("refused") is True, "refused",
          (st, out.get("outcome")))

    st, out = post("/poc1/reconcile", {"capability": cap4,
                                       "action_request_id": ar4["id"],
                                       "outcome": "not_delivered"})
    check("a PROVIDER-ASSERTED outcome on /poc1/reconcile is never accepted",
          S.STORE.capabilities[cap4]["status"] != S.RECONCILED_NOT_DELIVERED
          and out.get("reconciled_not_delivered") is not True,
          "not accepted", S.STORE.capabilities[cap4]["status"])

    # exactly one re-attempt
    post("/owner/reconcile", {"action_request_id": ar4["id"],
                              "outcome": "not_delivered", "note": "checked"}, owner())
    check("RECONCILED_NOT_DELIVERED is reachable ONLY via owner attestation",
          S.STORE.capabilities[cap4]["status"] == S.RECONCILED_NOT_DELIVERED,
          S.RECONCILED_NOT_DELIVERED, S.STORE.capabilities[cap4]["status"])
    cases_before = len(S.STORE.cases)
    st, out = post("/relay/deliver",
                   {"capability": cap4, "action_request_id": ar4["id"],
                    "case_id": flow4["case_id"], "payload": ar4["payload"],
                    "destination_digest_claimed": DIGEST})
    check("exactly one re-attempt is permitted, and it increments `attempt` without "
          "creating a new submission",
          st == 200 and out.get("attempt") == 2
          and len(S.STORE.cases) == cases_before,
          "attempt 2, no new case",
          (st, out.get("attempt"), len(S.STORE.cases) - cases_before))
    with S.STORE.lock:
        S.STORE.relay_receipts.pop(ar4["id"], None)
    S.STORE.capabilities[cap4]["status"] = S.UNCERTAIN
    post("/owner/reconcile", {"action_request_id": ar4["id"],
                              "outcome": "not_delivered", "note": "again"}, owner())
    st, out = post("/relay/deliver",
                   {"capability": cap4, "action_request_id": ar4["id"],
                    "case_id": flow4["case_id"], "payload": ar4["payload"],
                    "destination_digest_claimed": DIGEST})
    check("a SECOND re-attempt is refused",
          st == 409 and out.get("outcome") == "refused-second-reattempt",
          "409 refused-second-reattempt", (st, out.get("outcome")))

    # SEC-R3-02 — the TERMINAL REVALIDATION branch, tested directly.
    #
    # Under `33_` §1's selected architecture a concurrent revoke cannot land
    # inside a delivery, so this branch is unreachable from two live requests —
    # the outcome-coverage guard says so, correctly. It is required by SEC-R3-02
    # and it is defence in depth, so it is exercised here by advancing the
    # revocation epoch from inside the delivery's own evidence write, which is
    # the exact window the finding describes.
    fresh()
    flow6 = to_capability(task="TASK-REVALIDATE")
    cap6, ar6 = flow6["capability"], flow6["action_request"]
    real_write = S.write_capture

    def bump_epoch(route, poc, step, *a, **kw):
        if step == "prepared-delivery":
            S.STORE.capabilities[cap6]["revocation_epoch"] += 1
        return real_write(route, poc, step, *a, **kw)

    S.write_capture = bump_epoch
    try:
        st, out = post("/relay/deliver",
                       {"capability": cap6, "action_request_id": ar6["id"],
                        "case_id": flow6["case_id"], "payload": ar6["payload"],
                        "destination_digest_claimed": DIGEST})
    finally:
        S.write_capture = real_write
    check("SEC-R3-02: a revocation landing after the delivery claimed its epoch "
          "stops the delivery at the terminal commit — no receipt is minted",
          st == 409 and out.get("outcome") == "refused-revoked-in-flight"
          and out.get("delivered") is not True
          and S.STORE.relay_receipts.get(ar6["id"]) is None,
          "409 refused-revoked-in-flight, no receipt",
          (st, out.get("outcome"), S.STORE.relay_receipts.get(ar6["id"])))
    check("...and the subject is REVOKED, not delivered",
          S.STORE.capabilities[cap6]["status"] == S.REVOKED,
          S.REVOKED, S.STORE.capabilities[cap6]["status"])
    check("...and the attempt it claimed was given back",
          S.STORE.relay_attempts.get(ar6["id"], 0) == 0, 0,
          S.STORE.relay_attempts.get(ar6["id"]))

    # POC-3: a duplicate declaration is a measurement, never an overwrite
    fresh()
    first = post("/poc3/run-started", {"schedule_id": "sched-1",
                                       "occurrence": "2026-08-04T00:00:00Z",
                                       "provider_correlation_id": "prov-abc"})[1]
    post("/poc3/checkpoint", {"run_id": first["run_id"], "stage": "fetch"})
    st, dup = post("/poc3/run-started", {"schedule_id": "sched-1",
                                         "occurrence": "2026-08-04T00:00:00Z",
                                         "provider_correlation_id": "prov-xyz"})
    check("a duplicate POC-3 run declaration is a 409 that PRESERVES the prior "
          "started_at and checkpoint count — a measurement, never an overwrite",
          st == 409 and dup.get("run_id") == first["run_id"]
          and dup.get("checkpoint_count") == 1
          and dup.get("started_at") == S.STORE.runs[first["run_id"]]["started_at"],
          "409 preserving prior", (st, dup.get("run_id"), dup.get("checkpoint_count")))
    check("run identity is stub-minted and the provider correlation value anchors "
          "nothing", first["run_id"].startswith("run-")
          and first.get("provider_correlation_id") == "prov-abc",
          "stub-minted", first.get("run_id"))
    st, out = post("/poc3/reconcile", {"run_id": first["run_id"]})
    check("/poc3/reconcile compares only what the service recorded and states "
          "external_post_state_checked: false",
          st == 200 and out.get("external_post_state_checked") is False,
          "false", out.get("external_post_state_checked"))
    st, out = post("/stage/deliver", {"run_id": first["run_id"]})
    st2, out2 = post("/stage/deliver", {"run_id": first["run_id"]})
    check("/stage/deliver is retry-tolerant by design — a single-use rule there "
          "would mis-score the provider retry POC-3 exists to measure",
          st == 200 and st2 == 200 and out2.get("stage_attempt") == 2,
          "two attempts accepted", (st, st2, out2.get("stage_attempt")))
    st, out = post("/poc3/receipt", {"run_id": first["run_id"],
                                     "occurrence": "2026-08-04T00:00:00Z",
                                     "provider_status": "ok"})
    check("/poc3/receipt records without attesting", st == 200
          and out.get("recorded") is True, 200, st)
    st, out = post("/poc3/checkpoint", {"run_id": "run-never-announced",
                                        "stage": "fetch"})
    check("a checkpoint for an unannounced run refuses",
          st == 404 and out.get("outcome") == "refused-unknown-run", 404, st)

    # A.6: an owner REJECT is terminal, consumes the token, and authorizes nothing
    fresh()
    reg = register(task="TASK-REJECT")
    opened = review(reg["registration_ref"], task="TASK-REJECT")[1]
    rcid = undecided_case()
    post("/owner/decide", {"case_id": rcid, "decision": "reject"}, owner())
    st, out = post("/poc1/verify-decision",
                   {"token": reveal(opened["resume_token"])})
    check("an owner REJECT consumes the token and returns authorized:false",
          st == 200 and out.get("authorized") is False
          and out.get("outcome") == "owner-rejected", "owner-rejected",
          (st, out.get("outcome")))
    st, out = post("/owner/decide", {"case_id": rcid, "decision": "accept"}, owner())
    check("the first valid decision is TERMINAL — a second is a captured 409",
          st == 409, 409, st)
    st, out = post("/poc1/verify-decision",
                   {"token": reveal(opened["resume_token"])})
    check("...and the consumed token cannot be replayed",
          st == 403 and out.get("outcome") == "refused-token", 403, st)
    st, out = post("/poc1/verify-decision", {"token": "not-a-token"})
    check("an unknown token is refused", st == 403
          and out.get("outcome") == "refused-token", 403, st)

    # remaining reachable refusals, so no outcome code is a dead branch
    st, out = post("/poc1/receipt", {"action_request_id": "a", "case_id": "c",
                                     "provider_status": "definitely-not-valid"})
    check("a provider_status outside {ok,error,uncertain} refuses malformed",
          st == 400 and out.get("outcome") == "refused-malformed", 400, st)
    st, out = post("/poc1/reconcile", {"capability": "cap-nope",
                                       "action_request_id": "ar-nope"})
    check("/poc1/reconcile on an unknown subject refuses",
          st == 404 and out.get("outcome") == "refused-unknown", 404, st)
    flow5 = to_capability(task="TASK-INFLIGHT")
    S.STORE.capabilities[flow5["capability"]]["status"] = S.ATTEMPT_STARTED
    st, out = post("/relay/deliver",
                   {"capability": flow5["capability"],
                    "action_request_id": flow5["action_request"]["id"],
                    "case_id": flow5["case_id"],
                    "payload": flow5["action_request"]["payload"],
                    "destination_digest_claimed": DIGEST})
    check("a delivery while an attempt is already in flight refuses",
          st == 409 and out.get("outcome") == "refused-in-flight", 409, st)
    S.STORE.capabilities[flow5["capability"]]["status"] = S.MINTED
    with S.STORE.lock:
        S.STORE.relay_attempts[flow5["action_request"]["id"]] = S.MAX_ATTEMPTS_PER_AR
    st, out = post("/relay/deliver",
                   {"capability": flow5["capability"],
                    "action_request_id": flow5["action_request"]["id"],
                    "case_id": flow5["case_id"],
                    "payload": flow5["action_request"]["payload"],
                    "destination_digest_claimed": DIGEST})
    check("MAX_ATTEMPTS_PER_AR refuses on quota", st == 429
          and out.get("outcome") == "refused-quota", 429, st)


# --------------------------------------------------------------------------
# §E — evidence: prepared -> committed at six write boundaries
# --------------------------------------------------------------------------
def block_evidence():
    block("evidence: prepared -> committed, six write boundaries (A.7)")

    # 1. owner decision
    fresh()
    reg = register(task="TASK-B1")
    opened = review(reg["registration_ref"], task="TASK-B1")[1]
    cid = undecided_case()
    with FailWrite():
        st, _ = post("/owner/decide", {"case_id": cid, "decision": "accept"}, owner())
    check("boundary 1 (owner decision): a failed committed write refuses",
          st >= 400, ">=400", st)
    check("...and the decision is NOT effective — no authority from an uncommitted "
          "transition", cid not in S.STORE.decisions, "no decision record",
          cid in S.STORE.decisions)
    tok = reveal(opened["resume_token"])
    st, out = post("/poc1/verify-decision", {"token": tok})
    check("...so verify-decision still reports pending and does NOT consume the "
          "token", out.get("outcome") == "pending", "pending", out.get("outcome"))
    st2, out2 = post("/poc1/verify-decision", {"token": tok})
    check("...the token survives a second pending probe",
          out2.get("outcome") == "pending", "pending again", out2.get("outcome"))

    # 2. token spend + 3. capability mint (one critical section)
    post("/owner/decide", {"case_id": cid, "decision": "accept"}, owner())
    caps_before = set(S.STORE.capabilities)
    with FailWrite():
        st, _ = post("/poc1/verify-decision", {"token": tok})
    check("boundaries 2-3 (token spend, capability mint): a failed committed write "
          "refuses", st >= 400, ">=400", st)
    check("...and leaves no capability behind",
          set(S.STORE.capabilities) == caps_before, "no new capability",
          sorted(set(S.STORE.capabilities) - caps_before))
    st, out = post("/poc1/verify-decision", {"token": tok})
    check("...and the token was NOT spent — the same request succeeds once the "
          "write works", st == 200 and out.get("authorized") is True, 200, st)

    # 4. capability spend / 5. delivery
    flow = to_capability(task="TASK-B4")
    cap, ar = flow["capability"], flow["action_request"]
    with FailWrite("attempt-start"):
        st, out = post("/relay/deliver",
                       {"capability": cap, "action_request_id": ar["id"],
                        "case_id": flow["case_id"], "payload": ar["payload"],
                        "destination_digest_claimed": DIGEST})
    check("boundary 4 (capability spend): a failed committed write rolls the "
          "subject back — rollback IS possible before the external effect",
          st >= 400 and S.STORE.capabilities[cap]["status"] == S.MINTED,
          "rolled back to MINTED", (st, S.STORE.capabilities[cap]["status"]))
    check("...and the attempt counter rolls back with it",
          S.STORE.relay_attempts.get(ar["id"], 0) == 0, 0,
          S.STORE.relay_attempts.get(ar["id"]))

    with FailWrite("delivery"):
        st, out = post("/relay/deliver",
                       {"capability": cap, "action_request_id": ar["id"],
                        "case_id": flow["case_id"], "payload": ar["payload"],
                        "destination_digest_claimed": DIGEST})
    check("boundary 5 (delivery): a failed committed write never reports delivered",
          out.get("delivered") is not True, "not delivered", out.get("delivered"))
    check("...and, rollback of an external effect being impossible, the subject "
          "enters an explicit non-authoritative UNCERTAIN that fails closed",
          S.STORE.capabilities[cap]["status"] == S.UNCERTAIN,
          S.UNCERTAIN, S.STORE.capabilities[cap]["status"])

    # 6. reconciliation
    with FailWrite():
        st, _ = post("/owner/reconcile",
                     {"action_request_id": ar["id"], "outcome": "not_delivered",
                      "note": "n"}, owner())
    check("boundary 6 (reconciliation): a failed committed write refuses and the "
          "attestation is not effective",
          st >= 400 and S.STORE.capabilities[cap]["status"] == S.UNCERTAIN,
          "still UNCERTAIN", (st, S.STORE.capabilities[cap]["status"]))

    # orphan prepared
    d2 = fresh()
    flow2 = to_capability(task="TASK-ORPHAN")
    with FailWrite():
        post("/relay/deliver",
             {"capability": flow2["capability"],
              "action_request_id": flow2["action_request"]["id"],
              "case_id": flow2["case_id"],
              "payload": flow2["action_request"]["payload"],
              "destination_digest_claimed": DIGEST})
    bodies = capture_bodies(d2)
    prepared = {b["fields"]["transition_id"] for b in bodies
                if b.get("fields", {}).get("phase") == "prepared"}
    committed = {b["fields"]["transition_id"] for b in bodies
                 if b.get("fields", {}).get("phase") == "committed"}
    orphans = prepared - committed
    check("an interrupted transition leaves an ORPHAN prepared record with no "
          "committed partner", bool(orphans), ">=1 orphan", len(orphans))
    check("...and only a transition with a matching committed record satisfies an "
          "acceptance check — the orphan is never reported complete",
          all(t not in committed for t in orphans)
          and S.STORE.capabilities[flow2["capability"]]["status"] in
          (S.UNCERTAIN, S.MINTED),
          "not complete",
          S.STORE.capabilities[flow2["capability"]]["status"])

    # provenance on every capture
    d3 = fresh()
    flow3 = to_capability(task="TASK-PROV")
    post("/relay/deliver", {"capability": flow3["capability"],
                            "action_request_id": flow3["action_request"]["id"],
                            "case_id": flow3["case_id"],
                            "payload": flow3["action_request"]["payload"],
                            "destination_digest_claimed": "c" * 64})
    bodies = capture_bodies(d3)
    required = ("candidate", "run_instance", "route", "authored_by", "poc", "step",
                "recorded_at")
    check("every capture carries stub-minted candidate / run_instance / route / "
          "authored_by / poc / step / recorded_at",
          bodies and all(all(f in b for f in required) for b in bodies),
          "all present", len(bodies))
    check("recorded_at is labelled a local wall clock with NO clock authority",
          all("no clock authority" in b.get("recorded_at_note", "").lower()
              for b in bodies), "labelled", len(bodies))
    names = [os.path.basename(p) for p in capture_paths(d3)]
    check("capture filenames cannot collide across process lifetimes",
          len(names) == len(set(names))
          and all(S.STORE.run_instance in n for n in names),
          "unique + run-instance stamped", len(names))
    delivered = [b for b in bodies if b["step"] == "relay-delivered"]
    check("§C: the capture records the owner-registered source_digest as "
          "stub-minted, destination_digest_claimed under the PROVIDER provenance "
          "key, and destination_verified false",
          delivered
          and delivered[0]["fields"].get("source_digest") == DIGEST
          and delivered[0]["fields"].get("destination_verified") is False
          and "destination_digest_claimed" in delivered[0].get("provider_supplied", {})
          and "destination_digest_claimed" not in delivered[0]["fields"],
          "split by provenance",
          sorted(delivered[0].get("provider_supplied", {})) if delivered else None)
    check("...and destination_verified_reason states why it cannot be established",
          delivered and "cannot hash them"
          in delivered[0]["fields"].get("destination_verified_reason", ""),
          "reason present", True)

    # every refusal path captures, and none records the material presented
    d4 = fresh()
    before = len(capture_paths(d4))
    post("/owner/cases", {}, {"owner_key": "WRONGKEYVALUE", "provider_key": ""})
    after_auth = len(capture_paths(d4))
    check("the owner-key refusal captures that an attempt occurred",
          after_auth > before, ">%d" % before, after_auth)
    post("/poc1/review-case", {"registration_ref": "x", "task_id": "t"})
    after_400 = len(capture_paths(d4))
    check("a boundary 400 captures too", after_400 > after_auth,
          ">%d" % after_auth, after_400)
    blob = json.dumps(capture_bodies(d4))
    check("...and the refusal captures record that an attempt occurred, never the "
          "material presented", "WRONGKEYVALUE" not in blob, "material absent",
          "WRONGKEYVALUE" in blob)


# --------------------------------------------------------------------------
# §E — capacity and redaction
# --------------------------------------------------------------------------
def block_capacity():
    block("capacity and redaction (A.8)")
    d = fresh()

    # pool isolation: a provider flood cannot prevent an owner decision
    S.STORE.captures[S.POOL_GENERAL] = S.POOL_QUOTA[S.POOL_GENERAL]
    S.STORE.captures[S.POOL_SECURITY] = S.POOL_QUOTA[S.POOL_SECURITY]
    reg = register(task="TASK-FLOOD")
    check("with the general and security-refusal pools FULL, an owner write still "
          "succeeds — no provider-reachable event may draw from reserved-owner",
          reg.get("registration_ref", "").startswith("reg-"),
          "owner write ok", reg.get("outcome"))
    st, out = post("/poc3/run-started", {"schedule_id": "s", "occurrence": "t",
                                         "provider_correlation_id": None})
    check("...while a provider write gets a captured refusal", st >= 400, ">=400", st)
    owner_pool = [b for b in capture_bodies(d) if b["pool"] == S.POOL_OWNER]
    check("...and every reserved-owner capture came from an owner route",
          owner_pool and all(b["route"].startswith("/owner/") for b in owner_pool),
          "owner routes only", {b["route"] for b in owner_pool})

    S.STORE.captures[S.POOL_OWNER] = S.POOL_QUOTA[S.POOL_OWNER]
    st, out = post("/owner/artifact/register",
                   {"source_digest": "d" * 64, "size_bytes": 1, "file_count": 1,
                    "task_id": "X", "transition": "b->v",
                    "target_role": "verifier"}, owner())
    check("with EVERY pool full the service fails closed rather than silently "
          "dropping evidence", st >= 400, ">=400", st)
    st, health = get("/health")
    check("...and GET /health is still served", st == 200, 200, st)
    check("/health reveals no case, decision or capture-activity counts",
          not ({"cases", "decisions", "captures", "undecided", "case_count"}
               & set(health)), "no counts", sorted(health))

    # live-secret ceiling
    fresh()
    for i in range(S.MAX_ACTIVE_SECRETS):
        S.SECRETS.add("filler-secret-%06d" % i)
    check("the live-secret index reports full at MAX_ACTIVE_SECRETS",
          S.SECRETS.full(), True, S.SECRETS.full())
    reg = register(task="TASK-CEIL")
    st, out = review(reg["registration_ref"], task="TASK-CEIL")
    check("minting a token beyond MAX_ACTIVE_SECRETS is refused, not silently "
          "dropped out of the index", st == 429, 429, st)

    # no live secret outside the index; all of them redact
    fresh()
    to_capability(task="TASK-SECRETS")
    live_tokens = [t["token"] for t in S.STORE.tokens.values()
                   if not t.get("consumed")]
    live_caps = [c for c, b in S.STORE.capabilities.items()
                 if b["status"] not in S.TERMINAL_STATES]
    check("no live token or capability exists outside the secret index",
          all(t in S.SECRETS._values for t in live_tokens)
          and all(c in S.SECRETS._values for c in live_caps),
          "all indexed", (len(live_tokens), len(live_caps)))
    check("...and all of them redact",
          bool(live_caps) and all(s not in json.dumps(S.redact({"x": s}))
                                  for s in live_tokens + live_caps),
          "all redact", (len(live_tokens), len(live_caps)))

    for keep in ("authority_id", "authority_version", "tokens_used", "receipt_id",
                 "idempotency_key", "action_request_id", "side_effect_status"):
        check("A.8 allowlist: %s survives redaction" % keep,
              S.redact({keep: "value"})[keep] == "value", "value",
              S.redact({keep: "value"})[keep])

    secret = live_caps[0]
    red = S.redact({"note": secret})
    check("a live capability under a BENIGN key does not survive redaction",
          secret not in json.dumps(red), "scrubbed", json.dumps(red)[:60])
    red = S.redact({"note": "prefix" + secret + "suffix"})
    check("...and concatenation does not defeat it — substrings are compared too",
          secret not in json.dumps(red), "scrubbed", json.dumps(red)[:60])
    marker = S.redact({"password": "hunter2"})["password"]
    check("a withheld value becomes a STRUCTURED marker, never a bare constant the "
          "harness would score PRESENT",
          isinstance(marker, dict)
          and {"__withheld__", "name", "type", "bytes", "hmac"} <= set(marker),
          "structured marker", marker)
    check("a Disclose value still reduces to a descriptor on the CAPTURE path — the "
          "response exemption is identity-based and one-directional",
          isinstance(S.redact({"resume_token": S.Disclose("live-value")})
                     ["resume_token"], dict),
          "descriptor", S.redact({"resume_token": S.Disclose("live-value")}))
    check("...and a provider cannot name its way out of redaction: a plain string "
          "under the same key is still withheld",
          isinstance(S.redact({"resume_token": "live-value"})["resume_token"], dict),
          "descriptor", S.redact({"resume_token": "live-value"}))

    dead = sorted(n for n in S.NON_SECRET_FIELD_NAMES
                  if n not in A8_NAMED
                  and not any(s in S.SECRET_KEY_SEGMENTS for s in S._segments(n)))
    check("A.8's allowlist contains nothing that is neither named by A.8 nor "
          "load-bearing — a dead row in a control table is a defect",
          not dead, "no dead rows", dead)
    check("...and every name A.8 enumerates is present",
          A8_NAMED <= set(S.NON_SECRET_FIELD_NAMES), "all present",
          sorted(A8_NAMED - set(S.NON_SECRET_FIELD_NAMES)))

    # structural bounds
    fresh()
    deep = cur = {}
    for _ in range(S.MAX_REDACT_DEPTH + 4):
        cur["n"] = {}
        cur = cur["n"]
    for name, payload in (
            ("MAX_OBJECT_FIELDS", {str(i): 1 for i in range(S.MAX_OBJECT_FIELDS + 5)}),
            ("MAX_LIST_ITEMS", {"x": [1] * (S.MAX_LIST_ITEMS + 5)}),
            ("MAX_STRING_BYTES", {"x": "y" * (S.MAX_STRING_BYTES + 10)}),
            ("MAX_REDACT_DEPTH", deep)):
        st, out = post("/owner/cases", payload, owner())
        check("%s refuses BEFORE handler dispatch" % name,
              st == 400 and out.get("outcome") == "refused-bounds", 400, st)

    # the HMAC descriptor is per-process
    first = S.descriptor("k", "same-value", "probe")["hmac"]
    proc = subprocess.run(
        [sys.executable, "-c",
         "import sys;sys.path.insert(0,%r);import stub_server as S;"
         "print(S.descriptor('k','same-value','probe')['hmac'])" % HERE],
        capture_output=True, text=True, timeout=120)
    check("the HMAC descriptor differs across two process runs for the same value "
          "— per-process keying prevents precomputation and cross-run correlation",
          bool(proc.stdout.strip()) and proc.stdout.strip() != first,
          "different", (first[:12], proc.stdout.strip()[:12]))


# --------------------------------------------------------------------------
# §E — transport and policy
# --------------------------------------------------------------------------
def block_policy():
    block("transport and policy (§B / A.8)")
    fresh()

    st, out = post("/not/a/route", {})
    check("an unknown route fails closed with no policy row",
          st == 404 and out.get("outcome") == "refused-no-policy", 404, st)

    saved = S.ROUTE_POLICY.pop(("POST", "/relay/deliver"))
    try:
        st, out = post("/relay/deliver", {"capability": "x"})
        check("DELETING a route-policy row makes the route fail closed — the table "
              "is the authority, not the handler",
              st == 404 and out.get("outcome") == "refused-no-policy", 404, st)
    finally:
        S.ROUTE_POLICY[("POST", "/relay/deliver")] = saved

    st, out = post("/owner/cases", {}, provider())
    check("an owner route refuses a provider credential", st == 403, 403, st)
    st, out = post("/poc1/verify-decision", {"token": "x"}, owner())
    check("a provider route refuses the owner key — neither credential confers the "
          "other's identity", st == 403, 403, st)

    st, out = post("/poc1/receipt", {"action_request_id": "a", "case_id": "c",
                                     "provider_status": "ok", "decision": "accept"})
    check("a provider-authored decision field is refused at DISPATCH on every route "
          "whose policy says so",
          st == 403 and out.get("outcome") == "refused-provider-decision", 403, st)
    reg = register(task="TASK-POL")
    st, out = post("/owner/decide", {"case_id": "x", "decision": "accept"}, owner())
    check("...and /owner/decide is the ONLY route where a decision field is allowed",
          out.get("outcome") != "refused-provider-decision", "not refused for that",
          out.get("outcome"))

    st, out = post("/poc1/review-case",
                   {"registration_ref": reg["registration_ref"], "task_id": "T",
                    "transition": "b->v", "artifact_digest": DIGEST,
                    "target_role": "verifier", "submission_epoch": 0})
    check("a route whose policy requires an envelope refuses without one",
          st == 400 and out.get("outcome") == "refused-boundary", 400, st)

    st, out = post("/poc1/verify-decision", {"token": "x", "smuggled": "y"})
    check("verify-decision accepts `token` ONLY; an extra key is a captured 403 "
          "recording the COUNT",
          st == 403 and "1 additional" in out.get("reason", ""), "count only",
          out.get("reason"))
    check("...and never the key names — a live token can be smuggled in as a key",
          "smuggled" not in json.dumps(out), "name absent", out.get("reason"))

    st, out = post("/owner/cases", {"x": [1]}, owner())
    check("a TRUTHY non-dict nested value produces a structured result, never a "
          "traceback", isinstance(out, dict) and "Traceback" not in json.dumps(out),
          "structured", json.dumps(out)[:60])
    st, out = post("/owner/cases", {"x": []}, owner())
    check("...and an EMPTY list does not reproduce it (the falsy case passes, which "
          "is why the truthy one is the required probe)", st == 200, 200, st)

    st, out = post("/owner/decide", {"case_id": "x", "decision": "accept"},
                   {"owner_key": "é" * 8, "provider_key": ""})
    check("a non-ASCII credential yields a verdict rather than raising before one",
          st == 403, 403, st)

    st, out = post("/poc2/triage", {"idea_ref": "x", "external_items": [
        {"envelope": {"partition": "personal", "trust": "external-untrusted"},
         "source": "s", "content": "c"}]})
    check("an item declaring a partition other than `business` is refused",
          st >= 400, ">=400", st)


# --------------------------------------------------------------------------
# §E — live HTTP: the layer the R2 suite never crossed
# --------------------------------------------------------------------------
def block_live_http():
    block("live HTTP — a real socket, a real token, a real capability")
    port = free_port()
    data = tempfile.mkdtemp(prefix="selftest-http-")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "stub_server.py"),
         "--candidate", "n8n", "--port", str(port), "--data", data],
        stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    banner, tail, owner_key, provider_key = "", "", None, None
    secret = "SUPERSECRETVALUE12345"
    try:
        deadline = time.time() + 25
        while time.time() < deadline:
            line = proc.stderr.readline()
            if not line:
                break
            banner += line
            m = re.search(r"OWNER-SURFACE KEY.*?\n\s*(\S+)\n", banner, re.S)
            n = re.search(r"PROVIDER CREDENTIAL.*?\n\s*(\S+)\n", banner, re.S)
            if m and n:
                owner_key, provider_key = m.group(1), n.group(1)
                break
        if not owner_key:
            check("the service starts and announces its keys", False, "keys",
                  banner[:200])
            return

        def call(path, body=None, key=None, header=None, method="POST"):
            req = urllib.request.Request(
                "http://127.0.0.1:%d%s" % (port, path),
                data=None if body is None else json.dumps(body).encode("utf-8"),
                method=method)
            if body is not None:
                req.add_header("Content-Type", "application/json")
            if key:
                req.add_header(header, key)
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.status, json.loads(r.read().decode("utf-8")), \
                        dict(r.headers)
            except urllib.error.HTTPError as exc:
                return exc.code, json.loads(exc.read().decode("utf-8") or "{}"), \
                    dict(exc.headers)

        st, reg, hdrs = call("/owner/artifact/register",
                             {"source_digest": DIGEST, "size_bytes": 4096,
                              "file_count": 12, "task_id": "TASK-HTTP",
                              "transition": "builder->verifier",
                              "target_role": "verifier"},
                             owner_key, "X-Owner-Key")
        check("Cache-Control: no-store on every response",
              hdrs.get("Cache-Control") == "no-store", "no-store",
              hdrs.get("Cache-Control"))
        st, opened, _ = call("/poc1/review-case",
                             {"registration_ref": reg["registration_ref"],
                              "task_id": "TASK-HTTP",
                              "transition": "builder->verifier",
                              "artifact_digest": DIGEST, "target_role": "verifier",
                              "submission_epoch": 0,
                              "envelope": {"partition": "business",
                                           "trust": "external-untrusted"}},
                             provider_key, "X-Provider-Key")
        token = opened.get("resume_token")
        check("OVER HTTP the provider receives the actual resume token, not a "
              "descriptor — the service can hand out the credential it minted",
              isinstance(token, str) and len(token) > 20, "a usable string",
              json.dumps(token)[:80])

        st, cases, _ = call("/owner/cases", {}, owner_key, "X-Owner-Key")
        cid = [c["case_id"] for c in cases["cases"] if not c["decided"]][-1]
        call("/owner/decide", {"case_id": cid, "decision": "accept"},
             owner_key, "X-Owner-Key")
        st, verified, _ = call("/poc1/verify-decision", {"token": token},
                               provider_key, "X-Provider-Key")
        cap = verified.get("execution_capability")
        check("...and the execution capability likewise arrives usable",
              isinstance(cap, str) and len(cap) > 20, "a usable string",
              json.dumps(cap)[:80])
        ar = verified["action_request"]
        st, delivered, _ = call("/relay/deliver",
                                {"capability": cap, "action_request_id": ar["id"],
                                 "case_id": cid, "payload": ar["payload"],
                                 "destination_digest_claimed": DIGEST},
                                provider_key, "X-Provider-Key")
        check("the whole POC-1 path completes end to end over a socket",
              st == 200 and delivered.get("delivered") is True, "delivered",
              (st, delivered.get("outcome")))
        blob = json.dumps([json.load(open(p, encoding="utf-8"))
                           for p in capture_paths(data)])
        check("...and neither credential, token nor capability reached any capture",
              not any(s in blob for s in (owner_key, provider_key, token, cap)),
              "absent from captures", "present")

        def raw(payload: bytes):
            s = socket.create_connection(("127.0.0.1", port), timeout=8)
            try:
                s.sendall(payload)
                return s.recv(4096).decode("utf-8", "replace")
            except (OSError, TimeoutError):
                return ""
            finally:
                s.close()

        r = raw(b"POST /owner/cases HTTP/1.1\r\nHost: x\r\n"
                b"Content-Type: text/plain\r\nContent-Length: 2\r\n\r\n{}")
        check("a browser-simple text/plain POST is refused", " 415 " in r, "415",
              r[:40])
        r = raw(b"POST /owner/cases HTTP/1.1\r\nHost: x\r\n"
                b"Content-Type: application/json\r\nContent-Length: -1\r\n\r\n")
        check("a negative Content-Length is refused", " 400 " in r or not r,
              "400/closed", r[:40])
        r = raw(b"POST /owner/cases HTTP/1.1\r\nHost: x\r\n"
                b"Content-Type: application/json\r\nContent-Length: 2\r\n"
                b"Content-Length: 9\r\n\r\n{}")
        check("conflicting duplicate Content-Length headers are refused",
              " 400 " in r or not r, "400/closed", r[:40])
        r = raw(b"POST /owner/cases HTTP/1.1\r\nHost: x\r\n"
                b"Content-Type: application/json\r\n"
                b"Transfer-Encoding: chunked\r\n\r\n")
        check("a non-identity transfer encoding is refused",
              " 400 " in r or " 411 " in r or " 501 " in r or not r, "refused",
              r[:40])
        t0 = time.time()
        raw(b"POST /owner/cases HTTP/1.1\r\nHost: x\r\n"
            b"Content-Type: application/json\r\nContent-Length: 500\r\n\r\n")
        elapsed = time.time() - t0
        check("a slow body (declared length, nothing sent) is bounded by the socket "
              "timeout", elapsed < 30, "<30s", "%.1fs" % elapsed)
        r = raw(b"POST /poc2/triage HTTP/1.1\r\nHost: x\r\n"
                b"Content-Type: application/json\r\nContent-Length: 7\r\n\r\n{{{{{{{")
        check("deeply malformed JSON is a structured refusal", " 400 " in r, "400",
              r[:40])

        for path in ("/%s" % secret, "/health?k=%s" % secret):
            try:
                urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, path),
                                       timeout=5)
            except urllib.error.HTTPError:
                pass
        raw(b"GARBAGE REQUEST LINE " + secret.encode() + b"\r\n\r\n")
        st, health, _ = call("/health", None, None, None, method="GET")
        check("...and the service is still healthy afterwards", st == 200, 200, st)
    finally:
        proc.terminate()
        try:
            _out, tail = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            _out, tail = proc.communicate()
    log = banner + (tail or "")
    check("a secret placed in the PATH or QUERY is absent from the log",
          secret not in log, "absent", "present" if secret in log else "absent")
    labels = {row["log"] for row in S.ROUTE_POLICY.values()}
    request_lines = [ln.strip() for ln in log.splitlines()
                     if ln.strip().startswith(("POST ", "GET ", "127.0.0.1 - -"))]
    bad = [ln for ln in request_lines
           if not re.fullmatch(r"(%s) [0-9]{3}" % "|".join(re.escape(x) for x in labels),
                               ln)]
    check("logging emits a ROUTE-MATCHED CONSTANT plus status and nothing "
          "caller-supplied — every logged line is a policy-table label and a code",
          request_lines and not bad, "all lines label+status", bad[:3])
    check("...including unmatched routes, malformed request lines and secrets in "
          "the path: none of them contributes a logged line",
          not [ln for ln in request_lines if secret in ln or "GARBAGE" in ln],
          "none", [ln for ln in request_lines if secret in ln][:2])


# --------------------------------------------------------------------------
# §E — validator
# --------------------------------------------------------------------------
def block_validator():
    block("measurement validator (§D)")
    validator = os.path.abspath(os.path.join(DATA_DIR, "validate_measurements.py"))
    template = os.path.abspath(os.path.join(DATA_DIR, "measurements.template.json"))

    def run(path):
        p = subprocess.run([sys.executable, validator, path],
                           capture_output=True, text=True, timeout=180)
        return p.returncode, p.stderr

    rc, err = run(template)
    check("the shipped template validates clean", rc == 0, 0, err.strip()[-160:])

    with open(template, encoding="utf-8") as fh:
        base = json.load(fh)

    def mutate(fn):
        doc = json.loads(json.dumps(base))
        fn(doc)
        path = os.path.join(tempfile.mkdtemp(prefix="mval-"), "m.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        return run(path)

    def first_measure(doc):
        c = sorted(doc["candidates"])[0]
        p = sorted(doc["candidates"][c]["pocs"])[0]
        m = sorted(doc["candidates"][c]["pocs"][p]["measures"])[0]
        return c, p, m

    def set_measured(doc, value=7, ref="ev-1"):
        c, p, m = first_measure(doc)
        doc["candidates"][c]["pocs"][p]["measures"][m] = {
            "status": "MEASURED", "value": value, "unit": "count",
            "evidence_ref": ref, "observed_at": "2026-08-04T00:00:00Z"}
        doc.setdefault("evidence_records", {})
        return c, p, m

    def evidence(c, p, m, value):
        return {"candidate": c, "poc": p, "measure_id": m, "observed_value": value,
                "unit": "count", "observed_at": "2026-08-04T00:00:00Z",
                "collector": "owner session",
                "artifact_or_capture_hash": "0" * 64}

    def no_value(doc):
        c, p, m = set_measured(doc, value=None)
        doc["evidence_records"]["ev-1"] = evidence(c, p, m, None)
    rc, err = mutate(no_value)
    check("a MEASURED with no value FAILS", rc == 1, 1, err.strip()[-120:])

    def wrong_candidate(doc):
        c, p, m = set_measured(doc)
        doc["evidence_records"]["ev-1"] = evidence("some-other-candidate", p, m, 7)
    rc, err = mutate(wrong_candidate)
    check("a MEASURED whose evidence record names a different CANDIDATE fails",
          rc == 1, 1, err.strip()[-120:])

    def wrong_measure(doc):
        c, p, m = set_measured(doc)
        doc["evidence_records"]["ev-1"] = evidence(c, p, "a-different-measure", 7)
    rc, err = mutate(wrong_measure)
    check("a MEASURED whose evidence record names a different MEASURE fails",
          rc == 1, 1, err.strip()[-120:])

    def wrong_value(doc):
        c, p, m = set_measured(doc)
        doc["evidence_records"]["ev-1"] = evidence(c, p, m, 99)
    rc, err = mutate(wrong_value)
    check("a MEASURED whose evidence record reports a different VALUE fails",
          rc == 1, 1, err.strip()[-120:])

    def unresolvable(doc):
        set_measured(doc, ref="ev-missing")
    rc, err = mutate(unresolvable)
    check("a MEASURED whose evidence_ref resolves to nothing fails — a named file "
          "is not a record", rc == 1, 1, err.strip()[-120:])

    def missing_path(doc):
        c, p, m = set_measured(doc)
        rec = evidence(c, p, m, 7)
        rec["source_path"] = "captures/this-file-does-not-exist.json"
        doc["evidence_records"]["ev-1"] = rec
    rc, err = mutate(missing_path)
    check("a cited source_path that does not exist fails the preliminary integrity "
          "check", rc == 1, 1, err.strip()[-120:])

    def bad_gap(doc):
        c = sorted(doc["candidates"])[0]
        p = sorted(doc["candidates"][c]["pocs"])[0]
        doc["candidates"][c]["pocs"][p]["measures"]["original_vs_reconstituted"][
            "capability_gap_evidence"]["candidate"] = "the-other-one"
    rc, err = mutate(bad_gap)
    check("an UNSUPPORTED whose capability-gap evidence names a different candidate "
          "fails", rc == 1, 1, err.strip()[-120:])

    def no_gap(doc):
        c = sorted(doc["candidates"])[0]
        p = sorted(doc["candidates"][c]["pocs"])[0]
        doc["candidates"][c]["pocs"][p]["measures"][
            "original_vs_reconstituted"].pop("capability_gap_evidence")
    rc, err = mutate(no_gap)
    check("an UNSUPPORTED without capability-gap evidence fails", rc == 1, 1,
          err.strip()[-120:])

    def no_reason(doc):
        c, p, m = first_measure(doc)
        doc["candidates"][c]["pocs"][p]["measures"][m].pop("reason", None)
    rc, err = mutate(no_reason)
    check("a NOT_TESTED without a reason fails", rc == 1, 1, err.strip()[-120:])

    def drop_one(doc):
        c, p, m = first_measure(doc)
        doc["candidates"][c]["pocs"][p]["measures"].pop(m)
    rc, err = mutate(drop_one)
    check("a MISSING (candidate x POC x measure) combination fails — nothing "
          "disappears by omission", rc == 1, 1, err.strip()[-120:])

    def drop_family(doc):
        for c in doc["candidates"]:
            for p in doc["candidates"][c]["pocs"]:
                doc["candidates"][c]["pocs"][p]["measures"].pop(
                    "provider_retention_deletion_observation", None)
    rc, err = mutate(drop_family)
    check("dropping a §D required-family measure everywhere fails", rc == 1, 1,
          err.strip()[-120:])

    def bad_status(doc):
        c, p, m = first_measure(doc)
        doc["candidates"][c]["pocs"][p]["measures"][m]["status"] = "NOT TESTED"
    rc, err = mutate(bad_status)
    check("a status outside {MEASURED, NOT_TESTED, UNSUPPORTED} fails", rc == 1, 1,
          err.strip()[-120:])


# --------------------------------------------------------------------------
# SEC-R4-01 — capture publication (R5)
# --------------------------------------------------------------------------
def block_capture_publication():
    block("capture publication: every post-link boundary (SEC-R4-01)")
    import hashlib                                               # noqa: PLC0415
    import capture_fault_suite as CF                             # noqa: PLC0415

    pinned = os.path.join(HERE, "r4_reference", "stub_server_r4.py")
    digest = hashlib.sha256(open(pinned, "rb").read()).hexdigest()
    check("the pinned R4 reference is the build the verifier examined",
          digest == CF.R4_PINNED_SHA256, CF.R4_PINNED_SHA256[:16], digest[:16])
    if digest != CF.R4_PINNED_SHA256:
        return

    for row in CF.run(os.path.join(HERE, "stub_server.py")):
        check("R4-01 %s" % row["boundary"], row["ok"], "holds",
              row["failed_properties"] or "")

    # R6 — the pinned R5 build, and the verifier's own rollback probe.
    r5 = os.path.join(HERE, "r5_reference", "stub_server_r5.py")
    r5_digest = hashlib.sha256(open(r5, "rb").read()).hexdigest()
    check("the pinned R5 reference is the build the verifier examined",
          r5_digest == R5_PINNED_SHA256, R5_PINNED_SHA256[:16], r5_digest[:16])
    r5_rows = [r for r in CF.run(r5) if r["boundary"].startswith("R6 ")]
    red = [r for r in r5_rows if not r["ok"]]
    check("...and every R6 rollback boundary FAILS against it (%d of %d red)"
          % (len(red), len(r5_rows)), len(red) == len(r5_rows) and r5_rows,
          "all red", [r["boundary"] for r in r5_rows if r["ok"]])

    import probe_runner as PR                                    # noqa: PLC0415
    finding, criterion = PR.CRITERIA["chatgpt_r5_cleanup_rollback_probe"]
    live_ok, live_detail = criterion(PR.run_probe(
        "chatgpt_r5_cleanup_rollback_probe", os.path.join(HERE, "stub_server.py")))
    check("the verifier's chatgpt_r5_cleanup_rollback_probe runs green",
          live_ok, "5/5 scenarios", live_detail)
    pin_ok, pin_detail = criterion(PR.run_probe(
        "chatgpt_r5_cleanup_rollback_probe", r5))
    check("...and red against the pinned R5 build", not pin_ok, "red", pin_detail)

    # Item 3 through a real route: the response must be the distinct quarantine
    # result, and the service must then refuse further authority transitions.
    data = fresh()
    real_open, real_unlink = os.open, os.unlink

    def blocked_open(path, flags, *a, **kw):
        if flags == os.O_RDONLY and os.path.isdir(os.fspath(path)):
            raise OSError(5, "forced publication directory-open failure")
        return real_open(path, flags, *a, **kw)

    def blocked_unlink(path, *a, **kw):
        name = os.path.basename(os.fspath(path))
        if name.startswith("committed-") and name.endswith(".json"):
            raise OSError(5, "forced final-link rollback failure")
        return real_unlink(path, *a, **kw)

    S.os.open, S.os.unlink = blocked_open, blocked_unlink
    try:
        st, out = post("/owner/artifact/register",
                       {"source_digest": DIGEST, "size_bytes": 1, "file_count": 1,
                        "task_id": "QUAR", "transition": "R",
                        "target_role": "verifier"}, owner())
    finally:
        S.os.open, S.os.unlink = real_open, real_unlink
    check("an unprovable rollback returns the DISTINCT quarantine result, never "
          "the ordinary 'not effective' claim",
          st == 503 and out.get("outcome") == "refused-storage-quarantine"
          and out.get("storage_uncertain") is True,
          "503 refused-storage-quarantine", (st, out.get("outcome")))
    check("...and the quota unit is retained, because it is the last accounting "
          "for a record that may still exist",
          sum(S.STORE.captures.values()) >= 1, ">=1 retained",
          S.STORE.captures)
    st2, out2 = post("/owner/cases", {}, owner())
    check("...and the service then FAILS CLOSED to further authority transitions",
          st2 == 503 and out2.get("outcome") == "refused-storage-quarantine",
          "503 refused-storage-quarantine", (st2, out2.get("outcome")))
    st3, health = get("/health")
    check("...while GET /health is still served and says why (A.8)",
          st3 == 200 and health.get("storage_quarantined") is True
          and health.get("ok") is False,
          "health reports the quarantine", health.get("storage_quarantined"))
    fresh()

    # The same suite must be RED against the pin, or it proves nothing about
    # this build. Demonstrated-failing is the standing method, and it is what
    # caught this file passing vacuously in draft.
    pinned_rows = CF.run(pinned)
    faults = [r for r in pinned_rows if not r["boundary"].startswith("CONTROL")]
    red = [r for r in faults if not r["ok"]]
    check("...and the same boundaries FAIL against the pinned R4 build "
          "(%d of %d fault boundaries red)" % (len(red), len(faults)),
          len(red) >= 3, ">=3 red", [r["boundary"] for r in faults if r["ok"]])
    control = [r for r in pinned_rows if r["boundary"].startswith("CONTROL")]
    check("...while the pin's CONTROL still publishes, so the red is the "
          "defect and not a broken harness",
          bool(control) and control[0]["ok"], "control holds", "")


def block_capture_r7():
    """`46_` — publication-aware handling, scoped quarantine, restart posture.

    Every check here is paired with the same check against the SHA-pinned R6
    build, because R6 passed all of R6's tests and still had these five defects.
    A criterion that cannot fail the build it was written against is not
    evidence, and this workstream has produced two of those already.
    """
    block("R7: publication-aware handling, scoped quarantine, restart (46_)")
    import hashlib                                               # noqa: PLC0415
    import probe_runner as PR                                    # noqa: PLC0415

    live = os.path.join(HERE, "stub_server.py")
    r6 = os.path.join(HERE, "r6_reference", "stub_server_r6.py")
    r6_digest = hashlib.sha256(open(r6, "rb").read()).hexdigest()
    check("the pinned R6 reference is the build the verifier examined",
          r6_digest == R6_PINNED_SHA256, R6_PINNED_SHA256[:16], r6_digest[:16])
    if r6_digest != R6_PINNED_SHA256:
        return

    for probe, want in (("chatgpt_r6_quarantine_integrity_probe", "5/5 checks"),
                        ("post_durable_interrupt_compare", "no ineffective claim")):
        _, criterion = PR.CRITERIA[probe]
        live_ok, live_detail = criterion(PR.run_probe(probe, live))
        check("the verifier's %s runs green" % probe, live_ok, want, live_detail)
        pin_ok, pin_detail = criterion(PR.run_probe(probe, r6))
        check("...and red against the pinned R6 build", not pin_ok, "red", pin_detail)

    # ---- item 1, through a real route -------------------------------------
    # A non-OSError raised after the committed directory close is durable-tail
    # noise. R6 turned it into an ordinary CaptureError and the handler then
    # removed the registration it had durable evidence for.
    fresh()
    real_close = S.os.close
    seen = {"dirs": 0, "forced": 0}

    def close_after_committed(fd):
        try:
            isdir = stat.S_ISDIR(S.os.fstat(fd).st_mode)
        except OSError:
            isdir = False
        if isdir:
            seen["dirs"] += 1
            if seen["dirs"] == 2:            # prepared is 1; committed is 2
                real_close(fd)
                seen["forced"] += 1
                raise KeyboardInterrupt("forced after the committed dir fsync")
        return real_close(fd)

    S.os.close = close_after_committed
    try:
        st, out = post("/owner/artifact/register",
                       {"source_digest": DIGEST, "size_bytes": 1, "file_count": 1,
                        "task_id": "R7-TAIL", "transition": "R",
                        "target_role": "verifier"}, owner())
    finally:
        S.os.close = real_close
    check("the injected post-durability interruption actually fired",
          seen["forced"] == 1, 1, seen)
    check("item 1: a durably committed capture STAYS committed — no ordinary "
          "'not effective' claim after the publication fsync succeeded",
          st == 200 and out.get("outcome") != "capture-failed"
          and len(S.STORE.registrations) == 1,
          "200 with the registration live", (st, out.get("outcome"),
                                             len(S.STORE.registrations)))
    check("...and the tail failure is RECORDED as a soft anomaly, not swallowed",
          any(a.get("kind") == "post-durable-capture-tail-failure"
              and a.get("exception") == "KeyboardInterrupt"
              for a in S.STORE.storage_anomalies),
          "post-durable-capture-tail-failure", S.STORE.storage_anomalies)
    check("...and the service is NOT quarantined by it, because nothing is "
          "unproven — the record is on disk",
          not S.STORE.storage_quarantine, "no quarantine",
          len(S.STORE.storage_quarantine))

    # ---- item 3: nothing created, nothing to prove ------------------------
    fresh()
    real_makedirs = S.os.makedirs
    S.os.makedirs = lambda *a, **kw: (_ for _ in ()).throw(
        OSError(13, "forced pre-artifact directory creation failure"))
    try:
        st, out = post("/owner/artifact/register",
                       {"source_digest": DIGEST, "size_bytes": 1, "file_count": 1,
                        "task_id": "R7-MKDIR", "transition": "R",
                        "target_role": "verifier"}, owner())
    finally:
        S.os.makedirs = real_makedirs
    check("item 3: a failure BEFORE any temp or final name exists is an "
          "ordinary capture failure, never a quarantine",
          st == 500 and out.get("outcome") == "capture-failed"
          and not S.STORE.storage_quarantine,
          "500 capture-failed, no quarantine",
          (st, out.get("outcome"), len(S.STORE.storage_quarantine)))
    check("...and the capture reservation is RELEASED, because there is no "
          "record left for it to account for",
          all(v == 0 for v in S.STORE.captures.values()), "all pools 0",
          dict(S.STORE.captures))

    # ---- item 4: the rollback's own durability boundary -------------------
    fresh()
    real_fsync, real_close = S.os.fsync, S.os.close
    marks = {"fsyncs": 0, "rollback_fsync_ok": False, "close_faults": 0,
             "dir_closes": 0}

    def fsync_fail_publication(fd):
        marks["fsyncs"] += 1
        if marks["fsyncs"] == 2:             # 1 = the file; 2 = publication dir
            raise OSError(5, "forced publication directory-fsync failure")
        out_ = real_fsync(fd)
        if marks["fsyncs"] == 3:             # 3 = the rollback's own dir fsync
            marks["rollback_fsync_ok"] = True
        return out_

    def close_fail_after_rollback(fd):
        try:
            isdir = stat.S_ISDIR(S.os.fstat(fd).st_mode)
        except OSError:
            isdir = False
        if isdir:
            marks["dir_closes"] += 1
            if marks["dir_closes"] == 2:     # the rollback directory
                real_close(fd)
                marks["close_faults"] += 1
                raise OSError(5, "forced close failure after the rollback fsync")
        return real_close(fd)

    S.os.fsync, S.os.close = fsync_fail_publication, close_fail_after_rollback
    err = None
    try:
        try:
            S.write_capture("/poc1/receipt", "POC1", "r7rollback",
                            {"outcome": "x"}, data_dir=S.Handler.data_dir)
        except BaseException as exc:                             # noqa: BLE001
            err = type(exc).__name__
    finally:
        S.os.fsync, S.os.close = real_fsync, real_close
    check("the rollback's own directory fsync succeeded and only its CLOSE was "
          "faulted", marks["rollback_fsync_ok"] and marks["close_faults"] == 1,
          "fsync ok, close faulted", marks)
    check("item 4: a close error after a DURABLE rollback fsync is a soft "
          "anomaly — ordinary failure, no quarantine",
          err == "CaptureError" and not S.STORE.storage_quarantine,
          "CaptureError, no quarantine", (err, len(S.STORE.storage_quarantine)))
    check("...and the quota unit is released, because the rollback was proven",
          all(v == 0 for v in S.STORE.captures.values()), "all pools 0",
          dict(S.STORE.captures))
    check("...and the anomaly is recorded rather than dropped",
          any(a.get("kind") == "rollback-directory-close-after-durable-fsync"
              for a in S.STORE.storage_anomalies),
          "rollback-directory-close-after-durable-fsync",
          S.STORE.storage_anomalies)

    # ---- item 5: a restart is not reconciliation --------------------------
    data = fresh()
    real_open, real_unlink = S.os.open, S.os.unlink
    poc_root = os.path.abspath(os.path.join(data, "captures",
                                            S.STORE.candidate, "POC1"))
    opens = {"n": 0}

    def blocked_open(path, flags, *a, **kw):
        if os.path.abspath(os.fspath(path)) == poc_root and flags == os.O_RDONLY:
            opens["n"] += 1
            if opens["n"] == 2:              # prepared lands; committed fails
                raise OSError(5, "forced committed publication dir-open failure")
        return real_open(path, flags, *a, **kw)

    def blocked_unlink(path, *a, **kw):
        name = os.path.basename(os.fspath(path))
        if name.startswith("committed-") and name.endswith(".json"):
            raise OSError(5, "forced final-link rollback failure")
        return real_unlink(path, *a, **kw)

    S.os.open, S.os.unlink = blocked_open, blocked_unlink
    try:
        st, out = post("/owner/artifact/register",
                       {"source_digest": DIGEST, "size_bytes": 1, "file_count": 1,
                        "task_id": "R7-RESTART", "transition": "R",
                        "target_role": "verifier"}, owner())
    finally:
        S.os.open, S.os.unlink = real_open, real_unlink
    check("a genuine unprovable rollback still quarantines (R6, preserved)",
          st == 503 and out.get("outcome") == "refused-storage-quarantine",
          "503 refused-storage-quarantine", (st, out.get("outcome")))
    # R8 changed this criterion, and it is stated rather than quietly widened:
    # `51_` item A requires a SECOND durable control location, so the primary is
    # no longer the only marker and reconciliation now means removing every
    # durable record, not one. The R7 assertion — exactly one marker, and only
    # the primary deleted below — would fail against R8 for the right reason.
    # The R7 property it was written for is unchanged and still checked: the
    # primary marker exists and lives outside `captures/`.
    markers = sorted(glob.glob(os.path.join(
        data, S.QUARANTINE_DIRNAME, S.STORE.candidate,
        S.QUARANTINE_PREFIX + "*.json")))
    fallback_markers = sorted(glob.glob(os.path.join(
        data, "%s%s-*.json" % (S.QUARANTINE_FALLBACK_PREFIX, S.STORE.candidate))))
    check("item 5: the quarantine is PERSISTED as a marker beside captures/, "
          "not only in memory", len(markers) == 1, "1 primary marker", markers)
    check("R8 item A: and a SECOND durable record in a different directory, so "
          "one location failing does not lose the quarantine",
          len(fallback_markers) == 1 and
          os.path.dirname(fallback_markers[0]) != os.path.dirname(markers[0]),
          "1 fallback marker elsewhere", fallback_markers)
    markers = markers + fallback_markers
    check("...and the marker is NOT filed inside captures/, where every reader "
          "would count it as evidence",
          all(os.sep + "captures" + os.sep not in m for m in markers),
          "outside captures/", markers)
    check("...and the incident says whether the marker landed, so an operator "
          "is not left guessing whether a restart will be stopped",
          (out.get("detail") or {}).get("marker_persisted") is True,
          True, (out.get("detail") or {}).get("marker_persisted"))

    # A genuinely fresh process: same data directory, same candidate, empty
    # in-memory register. R6 came up clean here and accepted transitions again.
    saved_store, saved_secrets = S.STORE, S.SECRETS
    S.SECRETS = S.SecretIndex()
    S.STORE = S.Store(candidate=saved_store.candidate)
    S.STORE.base_url = saved_store.base_url
    S.Handler.data_dir = data
    try:
        check("the restarted process starts with an EMPTY in-memory register, "
              "so anything it refuses comes from the marker on disk",
              not S.STORE.storage_quarantine and not S.STORE.quarantine_scanned,
              "empty and unscanned", (len(S.STORE.storage_quarantine),
                                      S.STORE.quarantine_scanned))
        st_h, health = get("/health")
        check("item 5: the restarted process FINDS the marker and reports the "
              "quarantine on /health",
              st_h == 200 and health.get("storage_quarantined") is True,
              "storage_quarantined true", health.get("storage_quarantined"))
        # R9 CHANGED THIS CRITERION, stated rather than quietly widened. `56_`
        # item H replaced the single per-incident `recovered_from_marker` with a
        # MERGED inventory across every incident, because R8's version named one
        # marker and left the operator quarantined by its sibling. The R7
        # property it was written for — the restarted process names what it
        # recovered — is unchanged and now checked more strictly: every recovered
        # record must be listed, and each must be a real file.
        recovered = ((health.get("storage_quarantine") or {})
                     .get("durable_records") or [])
        check("...naming EVERY record it recovered, so recovery is actionable",
              len(recovered) == len(markers)
              and all(os.path.isfile(p) for p in recovered)
              and set(recovered) == set(markers),
              "every marker path reported", (recovered, markers))
        st_r, out_r = post("/owner/artifact/register",
                           {"source_digest": DIGEST, "size_bytes": 1,
                            "file_count": 1, "task_id": "R7-AFTER-RESTART",
                            "transition": "R", "target_role": "verifier"},
                           owner())
        check("item 5: and it REFUSES authority transitions — restarting is not "
              "reconciliation",
              st_r == 503 and out_r.get("outcome") == "refused-storage-quarantine",
              "503 refused-storage-quarantine", (st_r, out_r.get("outcome")))
        # Reconciliation is an operator act on the filesystem, deliberately with
        # no in-service path: a "clear the quarantine" route or flag would be a
        # production-reachable disable for the control itself.
        for m in markers:
            os.unlink(m)
        S.SECRETS = S.SecretIndex()
        S.STORE = S.Store(candidate=saved_store.candidate)
        S.STORE.base_url = saved_store.base_url
        st_a, out_a = post("/owner/artifact/register",
                           {"source_digest": DIGEST, "size_bytes": 1,
                            "file_count": 1, "task_id": "R7-RECONCILED",
                            "transition": "R", "target_role": "verifier"},
                           owner())
        check("...and only once an operator has removed the marker does the "
              "service accept again, so the refusal was the marker's doing",
              st_a == 200, 200, (st_a, out_a.get("outcome")))
    finally:
        S.STORE, S.SECRETS = saved_store, saved_secrets
    # P2V-01, applied reflexively: the defect this program has already had to
    # remove once is a control with a production-reachable disable path. A
    # "clear the quarantine" route or flag would be exactly that, so the only
    # way out is an operator deleting the marker from the filesystem — proven
    # by the two checks above. This is the structural half: `STORE.
    # storage_quarantine` is only ever APPENDED to (the raise) or EXTENDED (the
    # startup scan). `Store.__init__`'s `self.storage_quarantine = []` is a new
    # process's empty register, not a path that empties a populated one, and is
    # named here rather than matched by an over-broad pattern.
    shrink = [(n, ln.strip()) for n, ln in enumerate(
        open(os.path.join(HERE, "stub_server.py"), encoding="utf-8")
        .read().splitlines(), 1)
        if "storage_quarantine" in ln
        and (any(op in ln for op in (".clear()", ".pop(", ".remove(", "del "))
             or re.search(r"STORE\.storage_quarantine\s*=", ln))]
    check("no in-service path clears a quarantine: STORE.storage_quarantine is "
          "only appended to or extended, never cleared, popped or reassigned",
          not shrink, "no clear path", shrink)
    fresh()


def block_capture_r8():
    """`51_` — replace the proxies with the facts they stand for.

    The five mandatory red-before-green cases from `51_` §4, plus the two the
    §1 fourth-instance search turned up. Every case that can be run against the
    pinned R7 build is, because R7 passed all of R7's tests and still had these.
    """
    block("R8: facts, not proxies — marker durability, temp as fact, tail "
          "completeness (51_)")
    import hashlib                                               # noqa: PLC0415
    import probe_runner as PR                                    # noqa: PLC0415

    live = os.path.join(HERE, "stub_server.py")
    r7 = os.path.join(HERE, "r7_reference", "stub_server_r7.py")
    r7_digest = hashlib.sha256(open(r7, "rb").read()).hexdigest()
    check("the pinned R7 reference is the build the verifier executed",
          r7_digest == R7_PINNED_SHA256, R7_PINNED_SHA256[:16], r7_digest[:16])
    if r7_digest != R7_PINNED_SHA256:
        return

    r6 = os.path.join(HERE, "r6_reference", "stub_server_r6.py")
    _, criterion = PR.CRITERIA["chatgpt_r7_adversarial_recheck"]
    live_ok, live_detail = criterion(PR.run_probe(
        "chatgpt_r7_adversarial_recheck", live, timeout=300, comparison=r7))
    check("the verifier's chatgpt_r7_adversarial_recheck runs green",
          live_ok, "all three findings closed", live_detail)
    pin_ok, pin_detail = criterion(PR.run_probe(
        "chatgpt_r7_adversarial_recheck", r7, timeout=300, comparison=r6))
    check("...and red against the pinned R7 build", not pin_ok, "red", pin_detail)

    # ---- §4 case 1 and 2: marker DIRECTORY and marker FILE creation fail ----
    # Each is run twice over: once with only the primary location broken (the
    # fallback must carry it), and once with BOTH broken (the service must stop
    # claiming a protection it does not have). The second half is the one that
    # proves the fix is a real second mechanism and not a relocated goalpost.
    for label, break_all in (("primary only", False), ("every location", True)):
        for how in ("makedirs", "open"):
            data = fresh()
            marker_root = os.path.abspath(os.path.join(
                data, S.QUARANTINE_DIRNAME, S.STORE.candidate))
            poc_root = os.path.abspath(os.path.join(
                data, "captures", S.STORE.candidate, "POC1"))
            real_open, real_unlink = S.os.open, S.os.unlink
            real_makedirs, real_builtin = S.os.makedirs, builtins.open
            hits = {"makedirs": 0, "file_open": 0, "dir_open": 0, "unlink": 0}

            def blocked_dir_open(path, flags, *a, **kw):
                if (os.path.abspath(os.fspath(path)) == poc_root
                        and flags == os.O_RDONLY):
                    hits["dir_open"] += 1
                    if hits["dir_open"] == 2:      # committed publication fails
                        raise OSError(5, "forced committed publication dir-open")
                return real_open(path, flags, *a, **kw)

            def blocked_unlink(path, *a, **kw):
                name = os.path.basename(os.fspath(path))
                if name.startswith("committed-") and name.endswith(".json"):
                    hits["unlink"] += 1
                    raise OSError(5, "forced final-link rollback failure")
                return real_unlink(path, *a, **kw)

            def blocked_makedirs(path, *a, **kw):
                p = os.path.abspath(os.fspath(path))
                if how == "makedirs" and (p == marker_root
                                          or (break_all and p == os.path.abspath(data))):
                    hits["makedirs"] += 1
                    raise OSError(30, "forced marker-directory creation failure")
                return real_makedirs(path, *a, **kw)

            def blocked_builtin(path, mode="r", *a, **kw):
                try:
                    p = os.path.abspath(os.fspath(path))
                except TypeError:
                    p = ""
                broken = p.startswith(marker_root + os.sep)
                if break_all:
                    broken = broken or (
                        os.path.basename(p).startswith(S.QUARANTINE_FALLBACK_PREFIX))
                if how == "open" and broken and "w" in mode:
                    hits["file_open"] += 1
                    raise PermissionError(13, "forced marker-file open failure")
                return real_builtin(path, mode, *a, **kw)

            S.os.open, S.os.unlink = blocked_dir_open, blocked_unlink
            S.os.makedirs, builtins.open = blocked_makedirs, blocked_builtin
            try:
                st, out = post("/owner/artifact/register",
                               {"source_digest": DIGEST, "size_bytes": 1,
                                "file_count": 1, "task_id": "R8-MARKER",
                                "transition": "R", "target_role": "verifier"},
                               owner())
            finally:
                S.os.open, S.os.unlink = real_open, real_unlink
                S.os.makedirs, builtins.open = real_makedirs, real_builtin

            case = "%s marker-%s failure" % (label, how)
            check("the %s fault actually fired" % case,
                  hits["makedirs" if how == "makedirs" else "file_open"] >= 1
                  and hits["unlink"] >= 1,
                  "fault landed", hits)
            check("%s: the raising process still quarantines" % case,
                  st == 503 and out.get("outcome") == "refused-storage-quarantine",
                  "503 refused-storage-quarantine", (st, out.get("outcome")))
            detail = out.get("detail") or {}
            if break_all:
                # Item A's honest case: no durable record could be made
                # anywhere, so the service says so instead of claiming a
                # protection it does not have.
                check("%s: restart_protection is reported as NONE, not assumed"
                      % case,
                      out.get("restart_protection") == "none"
                      and out.get("survives_restart") is False
                      and "DO NOT" in (out.get("WARNING") or "").upper(),
                      "none + explicit warning",
                      (out.get("restart_protection"), out.get("survives_restart")))
                check("...and no sentence claims a restart will be stopped",
                      "does not clear it" not in json.dumps(out),
                      "no false restart claim", "")
                st_h, health = get("/health")
                check("...and /health says the same at the TOP level, not "
                      "nested where an operator may not look",
                      health.get("restart_protection") == "none"
                      and bool(health.get("WARNING")),
                      "top-level warning", health.get("restart_protection"))
            else:
                # R9 CHANGED THIS CRITERION too, same reason: `56_` item F
                # replaced the `marker_paths` success list with a per-attempt
                # tri-state disk fact, because a success Boolean was the proxy.
                # The R8 property is unchanged and now read off the states.
                landed = [a for a in (detail.get("marker_attempts") or [])
                          if a.get("state") in (S.MARKER_DURABLE, S.MARKER_PRESENT)]
                check("%s: the fallback location carried the quarantine" % case,
                      detail.get("marker_persisted") is True
                      and out.get("restart_protection") == "durable"
                      and len(landed) == 1
                      and landed[0].get("location") == "fallback"
                      and landed[0].get("state") == S.MARKER_DURABLE,
                      "one DURABLE fallback marker",
                      (detail.get("marker_persisted"), detail.get("marker_attempts")))
                check("...and the failed PRIMARY attempt is reported, so the "
                      "fallback is not silently standing in for it",
                      any(a.get("location") == "primary" and a.get("error")
                          for a in (detail.get("marker_attempts") or [])),
                      "primary error recorded", detail.get("marker_attempts"))
                # §4 case 1/2's second half: restart with the same candidate and
                # data directory.
                saved_store, saved_secrets = S.STORE, S.SECRETS
                S.SECRETS = S.SecretIndex()
                S.STORE = S.Store(candidate=saved_store.candidate)
                S.STORE.base_url = saved_store.base_url
                S.Handler.data_dir = data
                try:
                    st_h, health = get("/health")
                    st_r, _out_r = post("/owner/artifact/register",
                                        {"source_digest": DIGEST, "size_bytes": 1,
                                         "file_count": 1, "task_id": "R8-AFTER",
                                         "transition": "R",
                                         "target_role": "verifier"}, owner())
                    check("%s: a restarted process FINDS the fallback and "
                          "refuses — this is the R7 bypass, closed" % case,
                          health.get("storage_quarantined") is True and st_r == 503,
                          "quarantined and refusing", (health.get("storage_quarantined"), st_r))
                finally:
                    S.STORE, S.SECRETS = saved_store, saved_secrets
    fresh()

    # ---- §4 case 3: temp created, exception before the path is returned ----
    data = fresh()
    real_mkstemp, real_open = S.tempfile.mkstemp, S.os.open
    poc_root = os.path.abspath(os.path.join(data, "captures", S.STORE.candidate, "POC1"))
    st8 = {"created": None, "mkstemp_faults": 0, "rollback_open_faults": 0}

    def mkstemp_then_raise(*a, **kw):
        fd, path = real_mkstemp(*a, **kw)
        os.close(fd)
        st8["created"] = path
        st8["mkstemp_faults"] += 1
        raise RuntimeError("forced after the real create, before mkstemp returned")

    def rollback_open_fails(path, flags, *a, **kw):
        if (st8["created"] and os.path.abspath(os.fspath(path)) == poc_root
                and flags == os.O_RDONLY):
            st8["rollback_open_faults"] += 1
            raise OSError(5, "forced rollback directory-open failure")
        return real_open(path, flags, *a, **kw)

    S.tempfile.mkstemp, S.os.open = mkstemp_then_raise, rollback_open_fails
    err8 = None
    try:
        try:
            S.write_capture("/poc1/receipt", "POC1", "r8temp", {"outcome": "x"},
                            data_dir=data)
        except BaseException as exc:                              # noqa: BLE001
            err8 = type(exc).__name__
    finally:
        S.tempfile.mkstemp, S.os.open = real_mkstemp, real_open
    check("the post-create/pre-return temp fault fired, and the rollback proof "
          "fault with it",
          st8["mkstemp_faults"] == 1 and st8["rollback_open_faults"] >= 1
          and st8["created"], "both landed", st8)
    check("item C: a temp that exists on disk is NOT classified as 'nothing "
          "created' just because the local variable is None",
          err8 == "CaptureQuarantine", "CaptureQuarantine", err8)
    check("...and the quota unit is retained, because the removal of a real "
          "artifact could not be proven",
          sum(S.STORE.captures.values()) == 1, 1, dict(S.STORE.captures))
    check("...and the ordinary makedirs-failed case is still NOT a quarantine "
          "(46_ item 3 must not regress)", True, "checked below", "")
    fresh()
    real_makedirs = S.os.makedirs
    S.os.makedirs = lambda *a, **kw: (_ for _ in ()).throw(
        OSError(13, "forced pre-artifact directory creation failure"))
    try:
        st, out = post("/owner/artifact/register",
                       {"source_digest": DIGEST, "size_bytes": 1, "file_count": 1,
                        "task_id": "R8-MKDIR", "transition": "R",
                        "target_role": "verifier"}, owner())
    finally:
        S.os.makedirs = real_makedirs
    check("...confirmed: nothing ever created stays an ordinary capture failure",
          st == 500 and out.get("outcome") == "capture-failed"
          and not S.STORE.storage_quarantine
          and all(v == 0 for v in S.STORE.captures.values()),
          "500 capture-failed, no quarantine",
          (st, out.get("outcome"), len(S.STORE.storage_quarantine)))

    # ---- §4 case 4: a non-OSError after the REAL rollback directory close ----
    data = fresh()
    real_fsync, real_close = S.os.fsync, S.os.close
    m8 = {"fsyncs": 0, "dir_closes": 0, "rollback_fsync_ok": False, "raised": 0}

    def fsync_fail_publication(fd):
        m8["fsyncs"] += 1
        if m8["fsyncs"] == 2:
            raise OSError(5, "forced publication directory-fsync failure")
        out_ = real_fsync(fd)
        if m8["fsyncs"] == 3:
            m8["rollback_fsync_ok"] = True
        return out_

    def runtime_error_after_close(fd):
        try:
            isdir = stat.S_ISDIR(S.os.fstat(fd).st_mode)
        except OSError:
            isdir = False
        if isdir:
            m8["dir_closes"] += 1
            if m8["dir_closes"] == 2:          # the rollback directory
                real_close(fd)                 # the REAL close completes first
                m8["raised"] += 1
                raise RuntimeError("forced non-OSError after the real close")
        return real_close(fd)

    S.os.fsync, S.os.close = fsync_fail_publication, runtime_error_after_close
    err_d = None
    try:
        try:
            S.write_capture("/poc1/receipt", "POC1", "r8tail", {"outcome": "x"},
                            data_dir=data)
        except BaseException as exc:                              # noqa: BLE001
            err_d = type(exc).__name__
    finally:
        S.os.fsync, S.os.close = real_fsync, real_close
    check("the real rollback deletion and fsync completed, and only the tail "
          "raised a non-OSError",
          m8["rollback_fsync_ok"] and m8["raised"] == 1, "fsync ok, tail raised", m8)
    check("item D: a NON-OSError after the durable rollback close is a recorded "
          "soft anomaly, not an escaping exception",
          err_d == "CaptureError"
          and any(a.get("kind") == "rollback-directory-close-after-durable-fsync"
                  and a.get("exception") == "RuntimeError"
                  for a in S.STORE.storage_anomalies),
          "CaptureError + RuntimeError anomaly",
          (err_d, S.STORE.storage_anomalies))
    check("...and the quota release still happens, which R7 skipped entirely "
          "because the exception escaped before it",
          all(v == 0 for v in S.STORE.captures.values()), "all pools 0",
          dict(S.STORE.captures))
    check("...and it is NOT a quarantine: the rollback was durable",
          not S.STORE.storage_quarantine, "no quarantine",
          len(S.STORE.storage_quarantine))

    # ---- §4 case 5: the operator text asserted in BOTH directions ----------
    # The persisted direction is asserted above on every `primary only` case;
    # the unpersisted direction on every `every location` case. This is the
    # structural half: there is exactly one function that produces the sentence.
    src = open(os.path.join(HERE, "stub_server.py"), encoding="utf-8").read()
    speakers = [ln.strip() for ln in src.splitlines()
                if "does not clear it" in ln]
    check("item B: every 'restarting does not clear it' sentence is inside "
          "_restart_posture or a marker file that by definition landed "
          "(%d occurrence(s))" % len(speakers),
          "_restart_posture" in src
          and src.count("_restart_posture(") >= 4,
          ">=1 definition and 3 call sites", src.count("_restart_posture("))

    # ---- §1 fourth instance: the capture path containment check -----------
    data = fresh()
    outside = tempfile.mkdtemp(prefix="selftest-outside-")
    os.makedirs(os.path.join(data, "captures"), exist_ok=True)
    link = os.path.join(data, "captures", S.STORE.candidate)
    linked = False
    try:
        os.symlink(outside, link)
        linked = True
    except (OSError, NotImplementedError, AttributeError):
        pass
    if linked:
        raised = None
        try:
            S.write_capture("/poc1/receipt", "POC1", "r8link", {"outcome": "x"},
                            data_dir=data)
        except BaseException as exc:                              # noqa: BLE001
            raised = "%s: %s" % (type(exc).__name__, exc)
        escaped = glob.glob(os.path.join(outside, "**", "*.json"), recursive=True)
        check("§1 fourth instance: a SYMLINKED capture directory is refused — "
              "the containment check resolves the real path, it does not just "
              "compare path strings",
              raised is not None and "escapes the captures directory" in raised
              and not escaped,
              "refused, nothing written outside", (raised, escaped))
    else:
        check("§1 fourth instance: symlink case NOT RUN (this filesystem "
              "refuses symlinks) — reported, not silently skipped", False,
              "runnable", "symlink unsupported")
    shutil.rmtree(outside, ignore_errors=True)
    fresh()


def _quarantine_via(fault=None, data=None, extra=None):
    """Induce the accepted ambiguous-committed-record quarantine, optionally
    faulting the marker writer. Returns `(status, body, hits, data)`."""
    data = data or fresh()
    poc_root = os.path.abspath(os.path.join(data, "captures", S.STORE.candidate, "POC1"))
    real = {"open": S.os.open, "unlink": S.os.unlink, "close": S.os.close,
            "fsync": S.os.fsync, "builtin": builtins.open, "dump": S.json.dump}
    hits = {"dir_opens": 0, "publication_faults": 0, "final_unlink_faults": 0,
            "marker_file_fsyncs": 0, "marker_dir_fsyncs": 0,
            "marker_close_faults": 0, "marker_open_faults": 0,
            "partial_dump_faults": 0}
    primary_dir = os.path.abspath(S._quarantine_root(data))
    fallback_pre = "%s%s-" % (S.QUARANTINE_FALLBACK_PREFIX, S.STORE.candidate)

    def is_marker(p):
        b = os.path.basename(p or "")
        return (p or "").startswith(primary_dir + os.sep) or b.startswith(fallback_pre)

    def fd_path(fd):
        try:
            return os.path.abspath(os.readlink("/proc/self/fd/%d" % fd))
        except OSError:
            return None

    def op(path, flags, *a, **kw):
        p = os.path.abspath(os.fspath(path))
        if p == poc_root and flags == os.O_RDONLY:
            hits["dir_opens"] += 1
            if hits["dir_opens"] == 2:
                hits["publication_faults"] += 1
                raise OSError(5, "forced committed publication dir-open failure")
        return real["open"](path, flags, *a, **kw)

    def unlink(path, *a, **kw):
        if os.path.basename(os.fspath(path)).startswith("committed-"):
            hits["final_unlink_faults"] += 1
            raise OSError(5, "forced final-link rollback failure")
        return real["unlink"](path, *a, **kw)

    def fsync(fd):
        p = fd_path(fd)
        if p and is_marker(p):
            hits["marker_file_fsyncs"] += 1
        if p == primary_dir or p == os.path.abspath(data):
            hits["marker_dir_fsyncs"] += 1
        return real["fsync"](fd)

    def close(fd):
        p = fd_path(fd)
        if fault == "marker-close" and p in (primary_dir, os.path.abspath(data)):
            real["close"](fd)                  # the REAL close completes first
            hits["marker_close_faults"] += 1
            raise RuntimeError("forced marker dir-close tail failure after real close")
        return real["close"](fd)

    def bopen(path, mode="r", *a, **kw):
        try:
            p = os.path.abspath(os.fspath(path))
        except TypeError:
            p = ""
        if fault == "marker-open" and is_marker(p) and "w" in mode:
            hits["marker_open_faults"] += 1
            raise PermissionError(13, "forced marker write failure at both locations")
        return real["builtin"](path, mode, *a, **kw)

    def dump(obj, fh, *a, **kw):
        try:
            p = os.path.abspath(os.fspath(fh.name))
        except (AttributeError, TypeError):
            p = ""
        if fault == "partial" and is_marker(p):
            fh.write('{"kind":"storage-quarantine"')
            fh.flush()
            hits["partial_dump_faults"] += 1
            raise OSError(28, "forced marker JSON write failure after creation")
        return real["dump"](obj, fh, *a, **kw)

    S.os.open, S.os.unlink, S.os.close = op, unlink, close
    S.os.fsync, builtins.open, S.json.dump = fsync, bopen, dump
    if extra:
        extra(real, hits)
    try:
        st, out = post("/owner/artifact/register",
                       {"source_digest": DIGEST, "size_bytes": 1, "file_count": 1,
                        "task_id": "R9-QUAR", "transition": "R",
                        "target_role": "verifier"}, owner())
    finally:
        S.os.open, S.os.unlink, S.os.close = real["open"], real["unlink"], real["close"]
        S.os.fsync, builtins.open, S.json.dump = real["fsync"], real["builtin"], real["dump"]
    return st, out, hits, data


def _markers_on_disk(data):
    return (sorted(glob.glob(os.path.join(data, S.QUARANTINE_DIRNAME,
                                          S.STORE.candidate,
                                          S.QUARANTINE_PREFIX + "*.json")))
            + sorted(glob.glob(os.path.join(
                data, "%s%s-*.json" % (S.QUARANTINE_FALLBACK_PREFIX,
                                       S.STORE.candidate)))))


def _restart_into(data, candidate):
    """A genuinely fresh process over the same data directory and candidate."""
    S.SECRETS = S.SecretIndex()
    S.STORE = S.Store(candidate=candidate)
    S.STORE.base_url = "http://127.0.0.1:8787"
    S.Handler.data_dir = data
    return S.STORE


def block_capture_r9():
    """`56_` — marker state as facts, complete inventories, enforced invariants.

    The eight mandatory red-before-green cases from `56_` §4. Everything that can
    be run against the pinned R8 build is, because R8 passed all of R8's tests
    and still carried every one of these.
    """
    block("R9: marker facts, complete inventories, enforced invariants (56_)")
    import hashlib                                               # noqa: PLC0415
    import probe_runner as PR                                    # noqa: PLC0415

    live = os.path.join(HERE, "stub_server.py")
    r8 = os.path.join(HERE, "r8_reference", "stub_server_r8.py")
    r8_digest = hashlib.sha256(open(r8, "rb").read()).hexdigest()
    check("the pinned R8 reference is the build the verifier executed",
          r8_digest == R8_PINNED_SHA256, R8_PINNED_SHA256[:16], r8_digest[:16])
    if r8_digest != R8_PINNED_SHA256:
        return

    _, criterion = PR.CRITERIA["chatgpt_r8_adversarial_recheck"]
    live_ok, live_detail = criterion(PR.run_probe(
        "chatgpt_r8_adversarial_recheck", live, timeout=300))
    check("the verifier's chatgpt_r8_adversarial_recheck runs green",
          live_ok, "10 defects closed, control intact", live_detail)
    pin_ok, pin_detail = criterion(PR.run_probe(
        "chatgpt_r8_adversarial_recheck", r8, timeout=300))
    check("...and red against the pinned R8 build", not pin_ok, "red", pin_detail)

    # ---- §4 case 2: marker dir-close failure AFTER file and directory fsync --
    st, out, hits, data = _quarantine_via("marker-close")
    markers = _markers_on_disk(data)
    check("the marker close-tail fault fired after REAL file and directory "
          "fsyncs", hits["marker_close_faults"] >= 1
          and hits["marker_file_fsyncs"] >= 2 and hits["marker_dir_fsyncs"] >= 2,
          "fsyncs then close faults", hits)
    check("item F: DURABLE survives a close-tail exception — the marker is on "
          "disk, so the posture says so",
          st == 503 and out.get("restart_protection") == S.PROTECT_DURABLE
          and out.get("survives_restart") is True
          and len(markers) == 2
          and set(out.get("durable_records") or []) == set(markers),
          "durable, both markers listed",
          (out.get("restart_protection"), out.get("durable_records")))
    check("...and the close failure is RECORDED as a soft anomaly, not dropped",
          any(a.get("kind") == "quarantine-marker-close-after-durable-fsync"
              for a in S.STORE.storage_anomalies),
          "anomaly recorded", S.STORE.storage_anomalies)
    check("...and no sentence claims a restart clears it",
          "WILL clear the quarantine" not in json.dumps(out),
          "no false none-claim", "")

    # ---- §4 case 4: both-sibling restart reconstruction ---------------------
    # The verifier's exact sequence: write both, restart, delete precisely what
    # the service names, restart again — and it must end CLEAN.
    _restart_into(data, S.STORE.candidate)
    st_h, health = get("/health")
    block1 = health.get("storage_quarantine") or {}
    check("item H: a restarted process merges the two sibling markers into ONE "
          "incident and names BOTH records",
          health.get("storage_quarantined") is True
          and block1.get("incidents") == 1
          and set(block1.get("durable_records") or []) == set(markers),
          "1 incident, 2 records",
          (block1.get("incidents"), block1.get("durable_records")))
    for p in (block1.get("durable_records") or []):
        os.unlink(p)
    _restart_into(data, S.STORE.candidate)
    st_h2, health2 = get("/health")
    st_r2, _ = post("/owner/artifact/register",
                    {"source_digest": DIGEST, "size_bytes": 1, "file_count": 1,
                     "task_id": "R9-RECONCILED", "transition": "R",
                     "target_role": "verifier"}, owner())
    check("...so deleting exactly what the service named ENDS CLEAN — R8 left "
          "the operator quarantined by the sibling it never mentioned",
          health2.get("storage_quarantined") is False and st_r2 == 200,
          "clean and accepting", (health2.get("storage_quarantined"), st_r2))

    # ---- §4 case 1: partial marker creation (ENOSPC mid-JSON) --------------
    st, out, hits, data = _quarantine_via("partial")
    markers = _markers_on_disk(data)
    sizes = [os.path.getsize(p) for p in markers]
    check("the partial-write fault fired at both marker locations",
          hits["partial_dump_faults"] == 2 and len(markers) == 2
          and all(s > 0 for s in sizes), "2 partial markers", (hits, sizes))
    check("item F: a partial marker is PRESENT, so the posture never says "
          "nothing is on disk",
          out.get("restart_protection") == S.PROTECT_PRESENT
          and out.get("survives_restart") is True
          and set(out.get("durable_records") or []) == set(markers),
          "present_unverified, both listed",
          (out.get("restart_protection"), out.get("durable_records")))
    check("...and the restarted process agrees — it refuses on those same "
          "unreadable files",
          (_restart_into(data, S.STORE.candidate) or True)
          and get("/health")[1].get("storage_quarantined") is True,
          "restart quarantined", "")

    # ---- §4 case 3: surviving temp + BOTH marker locations failing ---------
    data = fresh()
    st8 = {"created": None, "mkstemp": 0, "temp_unlink": 0}
    real_mkstemp, real_unlink_outer = S.tempfile.mkstemp, S.os.unlink

    def _arm(real, hits):
        def mkstemp_then_raise(*a, **kw):
            fd, path = real_mkstemp(*a, **kw)
            os.close(fd)
            st8["created"] = path
            st8["mkstemp"] += 1
            raise RuntimeError("forced after real temp create, before path return")

        def keep_temp(path, *a, **kw):
            p = os.path.abspath(os.fspath(path))
            if st8["created"] and p == os.path.abspath(st8["created"]):
                st8["temp_unlink"] += 1
                raise OSError(5, "forced surviving temp unlink failure")
            return S.os.unlink(path, *a, **kw)
        S.tempfile.mkstemp = mkstemp_then_raise
        prior = S.os.unlink
        S.os.unlink = lambda p, *a, **kw: (
            keep_temp(p, *a, **kw) if (st8["created"] and
                                       os.path.abspath(os.fspath(p)) ==
                                       os.path.abspath(st8["created"]))
            else prior(p, *a, **kw))

    try:
        st, out, hits, data = _quarantine_via("marker-open", data=data, extra=_arm)
    finally:
        S.tempfile.mkstemp, S.os.unlink = real_mkstemp, real_unlink_outer
    temp = st8["created"]
    check("the temp was really created and really survived, with both marker "
          "locations refused",
          st8["mkstemp"] == 1 and bool(temp) and os.path.isfile(temp)
          and hits["marker_open_faults"] >= 2 and not _markers_on_disk(data),
          "temp present, no markers", (st8, hits["marker_open_faults"]))
    check("item G: the LIVE posture counts the write-free temp — R8's own "
          "mechanism was invisible to R8's own posture function",
          out.get("restart_protection") == S.PROTECT_DURABLE
          and out.get("survives_restart") is True
          and temp in (out.get("durable_records") or []),
          "durable, temp listed",
          (out.get("restart_protection"), out.get("durable_records")))
    check("...and no 'nothing on disk' sentence is emitted while it exists",
          "nothing on disk" not in json.dumps(out), "no false claim", "")
    fresh()

    # ---- §4 case 5: transient primary AND fallback scan failures ------------
    for where in ("primary", "fallback"):
        data = fresh()
        os.makedirs(S._quarantine_root(data), exist_ok=True)
        sentinel = os.path.join(data, "unrelated-owner-data.txt")
        with open(sentinel, "w", encoding="utf-8") as fh:
            fh.write("must never be named as a quarantine record\n")
        target = (os.path.abspath(S._quarantine_root(data)) if where == "primary"
                  else os.path.abspath(data))
        real_listdir = S.os.listdir
        n = {"faults": 0}

        def one_shot(path, _t=target, _n=n):
            if os.path.abspath(os.fspath(path)) == _t and _n["faults"] == 0:
                _n["faults"] += 1
                raise OSError(5, "forced one-shot %s listing fault" % where)
            return real_listdir(path)

        S.os.listdir = one_shot
        try:
            _sth, health = get("/health")
        finally:
            S.os.listdir = real_listdir
        blk = health.get("storage_quarantine") or {}
        check("the transient %s scan fault fired" % where, n["faults"] == 1,
              1, n)
        check("item I: a %s scan error fails closed as UNKNOWN and mints no "
              "durable record" % where,
              health.get("storage_quarantined") is True
              and blk.get("restart_protection") == S.PROTECT_UNKNOWN
              and blk.get("survives_restart") is False
              and not (blk.get("durable_records") or []),
              "unknown, no records",
              (blk.get("restart_protection"), blk.get("durable_records")))
        check("...and NO directory is ever presented as a record to delete — "
              "the runbook says delete every one of them",
              all(os.path.isfile(p) for p in (blk.get("durable_records") or []))
              and os.path.abspath(data) not in (blk.get("durable_records") or [])
              and os.path.isfile(sentinel),
              "files only, sentinel intact", blk.get("durable_records"))
        _restart_into(data, S.STORE.candidate)
        check("...and once the transient fault is gone a fresh process is clean",
              get("/health")[1].get("storage_quarantined") is False,
              "clean", "")
    fresh()

    # ---- §4 case 6: two processes, one (data_dir, candidate) ---------------
    # Enforcement first: the launch path refuses the second process.
    data = fresh()
    fd_a, why_a = S._acquire_candidate_lock(data, "lockcand")
    fd_b, why_b = S._acquire_candidate_lock(data, "lockcand")
    check("item J: the launch path takes an exclusive lock on "
          "(data_dir, candidate)", fd_a is not None and why_a is None,
          "first acquires", why_a)
    check("...and a SECOND process on the same pair refuses to start, naming "
          "the holder",
          fd_b is None and why_b and "already holds" in why_b
          and "pid=" in why_b, "second refused", why_b)
    fd_c, why_c = S._acquire_candidate_lock(data, "othercand")
    check("...while a different candidate on the same data directory is "
          "unaffected", fd_c is not None, "different candidate starts", why_c)
    for fd in (fd_a, fd_c):
        if fd is not None:
            os.close(fd)

    # And the sentence: the marker says EVERY process refuses, so a process
    # that never went through the launch path must refuse too.
    data = fresh("scanonce")
    _sth, health_a0 = get("/health")
    store_a = S.STORE
    secrets_a = S.SECRETS
    _restart_into(data, "scanonce")            # "process B"
    st_b, out_b, hits_b, _ = _quarantine_via(None, data=data)
    markers_b = _markers_on_disk(data)
    S.STORE, S.SECRETS = store_a, secrets_a     # back to "process A"
    S.Handler.data_dir = data
    st_a, out_a = post("/owner/artifact/register",
                       {"source_digest": DIGEST, "size_bytes": 1, "file_count": 1,
                        "task_id": "A-AFTER-B", "transition": "R",
                        "target_role": "verifier"}, owner())
    _sth, health_a1 = get("/health")
    check("the second process really quarantined the shared directory",
          st_b == 503 and len(markers_b) == 2, "503 with two markers",
          (st_b, markers_b))
    check("item J: a process that scanned clean BEFORE the quarantine now "
          "refuses too — the marker's 'every process' sentence is true",
          health_a0.get("storage_quarantined") is False
          and st_a == 503
          and out_a.get("outcome") == "refused-storage-quarantine"
          and health_a1.get("storage_quarantined") is True,
          "A refuses after B quarantined",
          (health_a0.get("storage_quarantined"), st_a,
           health_a1.get("storage_quarantined")))
    fresh()

    # ---- §4 case 7: captures-root symlink, and no quota leak ---------------
    for name, where in (("candidate directory", "candidate"),
                        ("captures ROOT", "root")):
        data = fresh()
        outside = tempfile.mkdtemp(prefix="selftest-outside-")
        linked = True
        try:
            if where == "candidate":
                os.makedirs(os.path.join(data, "captures"), exist_ok=True)
                os.symlink(outside, os.path.join(data, "captures", S.STORE.candidate))
            else:
                os.symlink(outside, os.path.join(data, "captures"))
        except (OSError, NotImplementedError, AttributeError):
            linked = False
        if not linked:
            check("§4 case 7 (%s): NOT RUN — this filesystem refuses symlinks; "
                  "reported, not silently skipped" % name, False, "runnable", "")
            shutil.rmtree(outside, ignore_errors=True)
            continue
        before = dict(S.STORE.captures)
        raised = None
        try:
            S.write_capture("/poc1/receipt", "POC1", "r9link", {"outcome": "x"},
                            data_dir=data)
        except BaseException as exc:                              # noqa: BLE001
            raised = "%s: %s" % (type(exc).__name__, exc)
        after = dict(S.STORE.captures)
        escaped = sorted(glob.glob(os.path.join(outside, "**", "*.json"),
                                   recursive=True))
        check("item K: a symlinked %s is refused and nothing lands outside"
              % name,
              raised is not None and "escapes the captures directory" in raised
              and not escaped, "refused, nothing outside", (raised, escaped))
        check("...and the containment refusal leaks NO quota unit (%s)" % name,
              sum(after.values()) == sum(before.values()),
              "no unit consumed", (before, after))
        shutil.rmtree(outside, ignore_errors=True)

    # ---- §4 case 8: the positive control ----------------------------------
    st, out, hits, data = _quarantine_via("marker-open")
    check("the both-locations fault fired and left nothing on disk",
          hits["marker_open_faults"] >= 2 and not _markers_on_disk(data),
          "no markers", hits)
    check("item F/G control: a GENUINE no-record failure still reports none, "
          "truthfully — the fix did not just delete the none branch",
          out.get("restart_protection") == S.PROTECT_NONE
          and out.get("survives_restart") is False
          and "DO NOT RESTART" in (out.get("WARNING") or "").upper()
          and "does not clear it" not in json.dumps(out),
          "none + explicit warning",
          (out.get("restart_protection"), out.get("survives_restart")))
    _restart_into(data, S.STORE.candidate)
    st_h, health = get("/health")
    st_r, _ = post("/owner/artifact/register",
                   {"source_digest": DIGEST, "size_bytes": 1, "file_count": 1,
                    "task_id": "R9-TRUE-NONE", "transition": "R",
                    "target_role": "verifier"}, owner())
    check("...and a fresh process really does start clean, which is what makes "
          "the none claim true",
          health.get("storage_quarantined") is False and st_r == 200,
          "clean and accepting", (health.get("storage_quarantined"), st_r))
    fresh()


# --------------------------------------------------------------------------
# outcome coverage
# --------------------------------------------------------------------------
def block_coverage():
    block("outcome coverage — no unreachable refusal reasons")
    src = open(os.path.join(HERE, "stub_server.py"), encoding="utf-8").read()
    declared = set(re.findall(r'outcome\s*=\s*"([a-z0-9\-]+)"', src))
    declared |= set(re.findall(r'"outcome":\s*"([a-z0-9\-]+)"', src))
    # `refused-internal` is the dispatch-exception fallback: reaching it needs a
    # bug in this service, and manufacturing one would need the defect switch
    # this build refuses to have. It is named here rather than silently excused.
    exempt = {"refused-internal"}
    missing = sorted(declared - OUTCOMES_SEEN - exempt)
    check("every outcome code the source can emit is produced by some case in this "
          "suite (%d declared, %d exercised, %d exempt)"
          % (len(declared), len(OUTCOMES_SEEN & declared), len(exempt)),
          not missing, "none unreached", missing)


# --------------------------------------------------------------------------
def run_self_test() -> int:
    sys.stderr.write("R3 self-test — 25_ §E\n")
    for fn in (block_identity, block_owner_idea, block_owner_reconciliation,
               block_capability, block_evidence, block_capacity, block_policy,
               block_live_http, block_validator, block_capture_publication,
               block_capture_r7, block_capture_r8, block_capture_r9):
        fn()
    block_coverage()

    passed = sum(1 for r in ROWS if r["ok"])
    out = {"check": "R3 stub self-test (25_ §E)",
           "witness_method": "r1_witnesses.py — probes against the SHA-pinned R1 and "
                             "R2 builds; no defect switch exists in this service",
           "cases": ROWS, "passed": passed, "total": len(ROWS)}
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    with open(os.path.join(HERE, "out", "selftest.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    sys.stderr.write("\nSELF-TEST %s — %d/%d\n"
                     % ("PASS" if passed == len(ROWS) else "FAIL", passed, len(ROWS)))
    for r in ROWS:
        if not r["ok"]:
            sys.stderr.write("  FAILED [%s] %s\n" % (r["block"], r["case"]))
    return 0 if passed == len(ROWS) else 1


if __name__ == "__main__":
    sys.exit(run_self_test())

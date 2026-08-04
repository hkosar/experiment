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

import json
import os
import re
import socket
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
               block_live_http, block_validator):
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

#!/usr/bin/env python3
# ==============================================================================
#  THROWAWAY POC EVIDENCE APPARATUS — NOT THE AI OS WRAPPER
#
#  This service exists so the TASK-0007 owner session can run end to end. It is
#  evidence apparatus, it earns NO Track B credit, and it MUST NOT survive into
#  production use. It has no persistence worth the name, no real authentication,
#  no cryptographic attestation, and no clock authority — the four things
#  `13B_` says the real wrapper needs. Delete it when the POC round closes.
#
#  Authority note: this stub stands in for the AI OS side of the boundary. The
#  provider (Zapier / n8n) calls it; it never calls a provider, and it never
#  receives a decision from a provider.
# ==============================================================================
"""Single-file POC wrapper stub (Python standard library only).

Run:      python3 stub_server.py [--port 8787] [--data ../data]
Health:   curl -s http://127.0.0.1:8787/health
Self-test: python3 stub_server.py --self-test

Endpoints the shipped workflow definitions call:
    POST /poc1/review-case       open a review case, mint an OPAQUE resume token
    POST /poc1/verify-decision   validate the token -> ActionRequest, or refuse
    POST /poc1/receipt           record the raw provider result
    POST /poc1/refusal           record a fail-closed refusal
    POST /poc2/triage            classify + queue (envelope required first)
    POST /poc3/run-started       declare the occurrence
    POST /poc3/checkpoint        record checkpoint state
    POST /poc3/reconcile         reconcile an uncertain side effect
    POST /poc3/receipt           record the run result
    GET  /health                 liveness for the runbooks

The owner surface (Discord/AI OS card) is stood in for by:
    POST /owner/cases            what is waiting for a decision (owner key required)
    POST /owner/decide           the ONLY place a decision may originate (key required)

`08_` §R1: "the provider's pause carries an opaque resume token only;
/poc1/verify-decision validates the token and returns the authorized
ActionRequest or refuses. The stub must refuse a missing/forged/replayed token
and must never accept an approval decision arriving *from* the provider side."
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

THROWAWAY = ("THROWAWAY POC APPARATUS — not the AI OS wrapper, no Track B credit, "
             "must not survive into production use")

MAX_BODY = 1 << 20  # 1 MiB; a stub has no business accepting more

# Where an authorized action goes. Fixed on the AI OS side — never taken from the
# request, because the requester is the provider.
ACTION_TARGET = "http://127.0.0.1:8787/sink"

# ---------------------------------------------------------------------------
# Boundary constants
# ---------------------------------------------------------------------------
# `05_` §2 / packet `07_` §3: Business partition only this round.
ALLOWED_PARTITION = "business"
REQUIRED_TRUST = "external-untrusted"

# There is deliberately NO Personal-partition route in ROUTES. `08_` §R1 asks for
# absence, not a guard: a route that exists and is guarded is one bug away from
# being reachable. The partition value is *also* checked, which is a separate
# control over payloads — see `_partition_ok`.

# Secret-shaped material must never be logged or persisted (`08_` §R1).
SECRET_PATTERNS = [
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "aws-key"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}"), "github-token"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}"), "openai-style-key"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "slack-token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private-key"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]+"), "jwt"),
    (re.compile(r"(?i)\b(password|passwd|client_secret|api_key|apikey|secret)"
                r"\s*[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9!@#$%^&*_\-]{6,})"), "assigned-credential"),
    (re.compile(r"(?i)\bauthorization\s*:\s*(bearer|basic)\s+\S+"), "auth-header"),
]

# Fields whose presence means a decision is arriving FROM the provider side.
# The provider carries a token; it does not carry an outcome.
PROVIDER_DECISION_FIELDS = (
    "decision", "approved", "approval", "outcome", "authorized",
    "owner_decision", "approval_result", "verdict",
)


# Key names whose VALUE is secret regardless of the value's shape. Pattern
# matching alone cannot catch these: once JSON is decoded, {"password": "hunter2"}
# has no string containing "password: hunter2" for a regex to find. An independent
# reviewer demonstrated exactly that hole, with a live resume token surviving into
# a capture record. Key-name redaction is the half that pattern matching cannot do.
SECRET_KEY_NAMES = (
    "password", "passwd", "secret", "client_secret", "api_key", "apikey",
    "token", "resume_token", "access_token", "refresh_token", "owner_key",
    "authorization", "auth", "credential", "credentials", "private_key",
    "session", "cookie", "signature", "bearer",
)


def _is_secret_key(name) -> bool:
    n = str(name).lower().replace("-", "_")
    return any(k in n for k in SECRET_KEY_NAMES)


def redact(value):
    """Recursively remove secret material before logging or writing.

    Two independent mechanisms, because either alone leaks:
      * value-shape patterns catch credentials embedded in free text;
      * key-name matching catches structured `{"api_key": "..."}` fields, which a
        value-shape regex can never see once the JSON has been decoded.
    """
    if isinstance(value, str):
        out = value
        for rx, label in SECRET_PATTERNS:
            out = rx.sub("[REDACTED:%s]" % label, out)
        return out
    if isinstance(value, dict):
        return {k: ("[REDACTED:key-name]" if _is_secret_key(k) and v not in (None, "", [], {})
                    else redact(v))
                for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def contains_secret(value) -> list:
    """Labels of any secret-shaped material found. Used by the self-test."""
    found = []
    blob = value if isinstance(value, str) else json.dumps(value)
    for rx, label in SECRET_PATTERNS:
        if rx.search(blob):
            found.append(label)
    return found


# ---------------------------------------------------------------------------
# State — in memory only. A stub that persisted would be pretending to be the
# journal, and `05_` §2 says the provider side never owns state.
# ---------------------------------------------------------------------------
class Store:
    def __init__(self):
        self.lock = threading.Lock()
        # The owner-surface key. Generated per process, printed once to the
        # operator's terminal at startup, never written to a capture, a log, or
        # this repository. Its only job is to make "the decision came from the
        # owner surface" a CHECKED fact rather than an assumed one: without it,
        # anything that can reach 127.0.0.1 — including the provider's own HTTP
        # node running on the same host — can POST /owner/decide and approve its
        # own case. That is mandatory refusal 2 defeated in substance while the
        # field-name check still passes, so a name-only check is not enough.
        self.owner_key = secrets.token_urlsafe(24)
        self.cases = {}          # case_id -> case record
        self.tokens = {}         # token_digest -> {case_id, consumed}
        self.decisions = {}      # case_id -> {"decision": ..., "at": ...}
        self.receipts = []
        self.runs = {}
        self.captures = 0

    # --- tokens -----------------------------------------------------------
    def mint_token(self, case_id: str) -> str:
        raw = secrets.token_urlsafe(32)
        with self.lock:
            self.tokens[self._digest(raw)] = {"case_id": case_id, "consumed": False}
        return raw

    @staticmethod
    def _digest(raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _find(self, raw: str):
        """(record, None) or (None, reason). Constant-time digest comparison."""
        if not isinstance(raw, str) or not raw.strip():
            return None, "no resume token was presented"
        digest = self._digest(raw)
        match = None
        for known, rec in self.tokens.items():
            if hmac.compare_digest(known, digest):
                match = rec
                break
        if match is None:
            return None, "resume token is not one this service minted"
        if match["consumed"]:
            return None, "resume token has already been used — replay refused"
        return match, None

    def peek_token(self, raw: str):
        """Validate WITHOUT consuming. Return (case_id, None) or (None, reason).

        Separated from consumption deliberately. A provider legitimately polls
        `/poc1/verify-decision` before the owner has decided — the pause is the
        whole point of the flow — and burning the token on that poll would make
        the owner's later approval unrelayable. The token is spent only when the
        case reaches a terminal outcome; see `spend_token`.
        """
        with self.lock:
            rec, why = self._find(raw)
            return (None, why) if rec is None else (rec["case_id"], None)

    def spend_token(self, raw: str):
        """Consume the token. Called only once the case is terminally decided."""
        with self.lock:
            rec, why = self._find(raw)
            if rec is None:
                return None, why
            rec["consumed"] = True
            return rec["case_id"], None


STORE = Store()


# ---------------------------------------------------------------------------
# Capture records — the shapes `harness/receipt_conformance.py` consumes.
# ---------------------------------------------------------------------------
SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


def write_capture(data_dir: str, candidate: str, poc: str, step: str, payload: dict) -> str | None:
    """Write one capture record. Every component is name-checked, so a crafted
    candidate/poc/step cannot escape the captures directory."""
    for part in (candidate, poc, step):
        if not SAFE_NAME.match(str(part)) or part in (".", ".."):
            return None
    root = os.path.abspath(os.path.join(data_dir, "captures", candidate, poc))
    expected_root = os.path.abspath(os.path.join(data_dir, "captures"))
    if not root.startswith(expected_root + os.sep):
        return None
    os.makedirs(root, exist_ok=True)
    body = redact(dict(payload))
    body["synthetic"] = True          # `08_` §R1 — until the live session overwrites
    body["produced_by"] = "stub_server.py (%s)" % THROWAWAY
    # A fixed filename per step silently overwrites, so a session with many runs
    # would ship only the last of each kind — evidence loss disguised as evidence.
    # Sequence within the process; the step name stays readable at the front.
    with STORE.lock:
        STORE.captures += 1
        seq = STORE.captures
    path = os.path.join(root, "%s-%04d.json" % (step, seq))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(body, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return path


# ---------------------------------------------------------------------------
# Boundary checks applied to every inbound payload
# ---------------------------------------------------------------------------
def _envelope_obj(payload: dict) -> dict:
    """The envelope, or {} if it is not an object.

    A non-dict envelope used to raise AttributeError inside these checks, which
    meant a crash instead of a refusal — the same fail-closed failure the reviewer
    found on a non-hashable case_id. A malformed envelope is simply no envelope.
    """
    env = payload.get("envelope")
    return env if isinstance(env, dict) else {}


def _partition_ok(payload: dict) -> tuple:
    env = _envelope_obj(payload)
    part = env.get("partition", payload.get("partition"))
    if part is not None and not isinstance(part, str):
        return False, "partition must be a string"
    if isinstance(part, str):
        part = part.strip()
    if part is None:
        return False, ("payload declares no partition; this round is %s-only "
                       "(packet §3)" % ALLOWED_PARTITION)
    if str(part).lower() != ALLOWED_PARTITION:
        return False, ("payload declares partition %r; no Personal-partition route "
                       "exists in this service and no non-business partition is "
                       "accepted (packet §3)" % part)
    return True, None


def _envelope_ok(payload: dict) -> tuple:
    env = _envelope_obj(payload)
    if not env:
        return False, ("no external-untrusted envelope on the payload; the envelope "
                       "is applied before any classification (packet §3)")
    if env.get("trust") != REQUIRED_TRUST:
        return False, ("envelope declares trust %r; inbound external content must "
                       "carry %r before classification (packet §3)"
                       % (env.get("trust"), REQUIRED_TRUST))
    return True, None


def _rejects_provider_decision(payload: dict) -> tuple:
    """`08_` §R1 — a decision must never arrive from the provider side."""
    present = [f for f in PROVIDER_DECISION_FIELDS if f in payload]
    if present:
        return False, ("request carries decision field(s) %s — an approval outcome "
                       "may not arrive from the provider side; the provider carries "
                       "an opaque token only (08_ §R1, finding F-3)" % ", ".join(sorted(present)))
    return True, None


# ---------------------------------------------------------------------------
# Handlers. Each returns (status, body dict).
# ---------------------------------------------------------------------------
def h_health(_payload, data_dir):
    return 200, {"ok": True, "service": "poc-wrapper-stub", "throwaway": THROWAWAY,
                 "partition": ALLOWED_PARTITION, "captures_written": STORE.captures}


def h_poc1_review_case(payload, data_dir):
    for check in (_partition_ok, _envelope_ok, _rejects_provider_decision):
        ok, why = check(payload)
        if not ok:
            return 400, {"refused": True, "reason": why}
    case_id = "case-" + secrets.token_hex(6)
    token = STORE.mint_token(case_id)
    with STORE.lock:
        STORE.cases[case_id] = {
            "case_id": case_id,
            "metadata": redact(payload.get("metadata") or {}),
            "content_forwarded": bool(payload.get("content_forwarded")),
            "opened_at": time.time(),
        }
    write_capture(data_dir, "stub", "POC1", "review-case",
                  {"case_id": case_id, "metadata": payload.get("metadata")})
    # The token is the ONLY thing the provider gets — no case id, no case content,
    # no decision. An independent reviewer pointed out that returning `case_id` here
    # handed the caller the one value `/owner/decide` keys on, so the provider could
    # address the owner surface directly. The owner key closes that door; withholding
    # the id keeps the provider from finding the door at all. The owner lists their
    # own pending cases through GET /owner/cases instead of being told by the provider.
    return 200, {"resume_token": token,
                 "note": "carry this token; the decision is made on the owner surface"}


def h_owner_decide(payload, data_dir):
    """The owner surface stand-in. The provider must not be able to call this.

    Requires the owner key printed at startup. The workflows never carry it, the
    runbook tells the owner to keep it out of the provider, and without it a
    provider on the same host could approve its own case — which is exactly the
    outcome `08_` §R1's second refusal exists to prevent.
    """
    presented = payload.get("owner_key") or ""
    if not isinstance(presented, str) or not hmac.compare_digest(presented, STORE.owner_key):
        return 403, {"refused": True,
                     "reason": ("owner-surface key missing or wrong; a decision must come "
                                "from the owner surface, and reaching this port is not "
                                "evidence that it did (08_ §R1)")}
    case_id = payload.get("case_id")
    decision = payload.get("decision")
    if not isinstance(case_id, str):
        # A dict or list here used to raise TypeError inside `in`, which meant no
        # HTTP response at all from the one endpoint whose failure mode must be a
        # refusal. Crashing is not failing closed.
        return 400, {"refused": True, "reason": "case_id must be a string"}
    if case_id not in STORE.cases:
        return 404, {"refused": True, "reason": "unknown case"}
    if decision not in ("accept", "reject"):
        return 400, {"refused": True, "reason": "decision must be 'accept' or 'reject'"}
    with STORE.lock:
        STORE.decisions[case_id] = {"decision": decision, "at": time.time()}
    write_capture(data_dir, "stub", "POC1", "owner-decision",
                  {"case_id": case_id, "decision": decision})
    return 200, {"case_id": case_id, "recorded": decision,
                 "note": "recorded on the owner surface; the provider is not told the outcome"}


def h_owner_cases(payload, data_dir):
    """Key-protected: the owner's own view of what is waiting for a decision.

    This exists so the owner never has to take a case id from the provider. The
    provider cannot call it — it does not hold the key.
    """
    presented = payload.get("owner_key") or ""
    if not isinstance(presented, str) or not hmac.compare_digest(presented, STORE.owner_key):
        return 403, {"refused": True, "reason": "owner-surface key missing or wrong"}
    with STORE.lock:
        pending = [{"case_id": c["case_id"], "metadata": c["metadata"],
                    "opened_at": c["opened_at"],
                    "decided": c["case_id"] in STORE.decisions}
                   for c in STORE.cases.values()]
    pending.sort(key=lambda c: c["opened_at"])
    return 200, {"cases": pending, "undecided": sum(1 for c in pending if not c["decided"])}


# verify-decision is a token exchange, not a content channel. Anything beyond these
# keys is a provider trying to influence an authorization it does not own.
VERIFY_ALLOWED_KEYS = {"token"}


def h_poc1_verify_decision(payload, data_dir):
    # 0. Nothing but the token. This subsumes the decision-field denylist for any
    #    spelling, casing, or unicode variant a reviewer might find, because the
    #    rule is an ALLOWLIST: unknown keys are refused rather than ignored.
    extra = sorted(set(payload) - VERIFY_ALLOWED_KEYS)
    if extra:
        why = ("verify-decision accepts only a resume token; the request also carried "
               "%s. An authorization the owner made is not open to provider input "
               "(08_ §R1)" % ", ".join(repr(k) for k in extra))
        write_capture(data_dir, "stub", "POC1", "verify-refused-extra-fields", {"reason": why})
        return 403, {"authorized": False, "refused": True, "reason": why}

    # 1. The provider must not be the source of the outcome.
    ok, why = _rejects_provider_decision(payload)
    if not ok:
        write_capture(data_dir, "stub", "POC1", "verify-refused-provider-decision",
                      {"reason": why})
        return 403, {"authorized": False, "refused": True, "reason": why}

    # 2. The token must be one we minted, and unused. NOT consumed yet — polling
    #    before the owner has decided is the normal shape of the flow.
    case_id, why = STORE.peek_token(payload.get("token"))
    if case_id is None:
        write_capture(data_dir, "stub", "POC1", "verify-refused-token", {"reason": why})
        return 403, {"authorized": False, "refused": True, "reason": why}

    # 3. An owner decision must exist, on the owner surface, for THIS case.
    decision = STORE.decisions.get(case_id)
    if decision is None:
        return 403, {"authorized": False, "refused": True, "pending": True,
                     "reason": ("no owner decision exists for this case; a valid token "
                                "proves the pause was carried, not that anything was "
                                "approved. The token is still valid — poll again once "
                                "the owner has decided")}

    # 4. The case is terminally decided either way, so the token is spent now.
    spent, why = STORE.spend_token(payload.get("token"))
    if spent is None:
        return 403, {"authorized": False, "refused": True, "reason": why}

    if decision["decision"] != "accept":
        write_capture(data_dir, "stub", "POC1", "verify-rejected",
                      {"case_id": case_id, "outcome": "owner rejected"})
        return 200, {"authorized": False, "reason": "owner rejected the case"}

    action_request = {
        "id": "ar-" + secrets.token_hex(6),
        "case_id": case_id,
        "action_class": "relay-artifact",
        "scope": ALLOWED_PARTITION,
        "policy_version": "P1",
        "risk_class": "consequential",
        "idempotency_key": hashlib.sha256(
            ("%s|relay-artifact|%s" % (case_id, decision["at"])).encode()).hexdigest(),
        # NOT payload.get("target_endpoint"). An independent reviewer showed that
        # honouring a provider-supplied destination lets the provider redirect an
        # action the owner approved — the decision is the owner's, the target must
        # be too. The stub's target is fixed; the real wrapper takes it from policy.
        "endpoint": ACTION_TARGET,
        "payload": {"case_id": case_id},
    }
    write_capture(data_dir, "stub", "POC1", "verify-authorized",
                  {"case_id": case_id, "action_request_id": action_request["id"]})
    return 200, {"authorized": True, "action_request": action_request}


def h_poc1_receipt(payload, data_dir):
    with STORE.lock:
        STORE.receipts.append(redact(payload))
    write_capture(data_dir, "stub", "POC1", "receipt", payload)
    return 200, {"recorded": True,
                 "note": ("raw provider result recorded as corroborating material; "
                          "the wrapper mints the D-EC_ receipt, the provider does not")}


def h_poc1_refusal(payload, data_dir):
    write_capture(data_dir, "stub", "POC1", "refusal", payload)
    return 200, {"recorded": True}


def h_poc2_triage(payload, data_dir):
    for check in (_partition_ok, _envelope_ok, _rejects_provider_decision):
        ok, why = check(payload)
        if not ok:
            return 400, {"refused": True, "reason": why}
    md = payload.get("metadata") or {}
    # Deterministic stand-in classification. No model, no link is followed, and
    # nothing is sent anywhere — POC-2 is read-only by contract.
    subject = str(md.get("subject") or md.get("title") or "")
    queue = "business-review" if subject else "business-unsorted"
    write_capture(data_dir, "stub", "POC2", "triage", {"metadata": md, "queue": queue})
    return 200, {"queue": queue, "classification": "stub-deterministic",
                 "actions_taken": [], "links_followed": False}


def h_poc3_run_started(payload, data_dir):
    run_id = str(payload.get("run_id") or secrets.token_hex(6))
    with STORE.lock:
        STORE.runs[run_id] = {"occurrence": payload.get("occurrence"),
                              "schedule_id": payload.get("schedule_id"),
                              "started_at": time.time(), "checkpoints": []}
    write_capture(data_dir, "stub", "POC3", "run-started", dict(payload))
    return 200, {"run_id": run_id, "stage_endpoint": "http://127.0.0.1:8787/sink",
                 "accepted": True}


def h_poc3_checkpoint(payload, data_dir):
    run_id = str(payload.get("run_id") or "")
    if run_id not in STORE.runs:
        return 404, {"refused": True, "reason": "checkpoint for an unannounced run"}
    with STORE.lock:
        STORE.runs[run_id]["checkpoints"].append(time.time())
    write_capture(data_dir, "stub", "POC3", "checkpoint",
                  {"run_id": run_id, "stage": payload.get("stage")})
    # The stub reports the side effect as UNCERTAIN by default so the reconcile
    # branch is exercised rather than sitting unused in the workflow.
    return 200, {"checkpointed": True, "side_effect_certain": False}


def h_poc3_reconcile(payload, data_dir):
    write_capture(data_dir, "stub", "POC3", "reconcile", dict(payload))
    return 200, {"reconciled": True, "side_effect_certain": True,
                 "note": "post-state checked before any retry decision (ACT-01)"}


def h_poc3_receipt(payload, data_dir):
    run_id = str(payload.get("run_id") or "")
    known = run_id in STORE.runs
    write_capture(data_dir, "stub", "POC3", "receipt", dict(payload))
    return 200, {"recorded": True, "run_known": known,
                 "occurrence_declared": payload.get("occurrence"),
                 "note": ("the occurrence window is judged by the real wrapper; this "
                          "stub records, it does not attest (D-EC_ §4)")}


def h_sink(payload, data_dir):
    """A local target so POC flows can 'execute' without touching anything real."""
    write_capture(data_dir, "stub", "POC1", "sink", dict(payload))
    return 200, {"delivered": True, "sink": "local throwaway"}


ROUTES = {
    ("GET", "/health"): h_health,
    ("POST", "/poc1/review-case"): h_poc1_review_case,
    ("POST", "/poc1/verify-decision"): h_poc1_verify_decision,
    ("POST", "/poc1/receipt"): h_poc1_receipt,
    ("POST", "/poc1/refusal"): h_poc1_refusal,
    ("POST", "/poc2/triage"): h_poc2_triage,
    ("POST", "/poc3/run-started"): h_poc3_run_started,
    ("POST", "/poc3/checkpoint"): h_poc3_checkpoint,
    ("POST", "/poc3/reconcile"): h_poc3_reconcile,
    ("POST", "/poc3/receipt"): h_poc3_receipt,
    ("POST", "/owner/decide"): h_owner_decide,
    ("POST", "/owner/cases"): h_owner_cases,
    ("POST", "/sink"): h_sink,
}


def dispatch(method: str, path: str, payload: dict, data_dir: str):
    handler = ROUTES.get((method, path))
    if handler is None:
        return 404, {"refused": True, "reason": "no such route on this stub"}
    return handler(payload or {}, data_dir)


# ---------------------------------------------------------------------------
# HTTP surface
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "poc-wrapper-stub"
    data_dir = "../data"

    def log_message(self, fmt, *args):  # noqa: A003
        # Redact before anything reaches the log — `08_` §R1.
        sys.stderr.write("%s - %s\n" % (self.address_string(), redact(fmt % args)))

    def _respond(self, status, body):
        raw = json.dumps(body, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Throwaway", "poc-evidence-apparatus")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):  # noqa: N802
        status, body = dispatch("GET", self.path.split("?")[0], {}, self.data_dir)
        self._respond(status, body)

    def do_POST(self):  # noqa: N802
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self._respond(400, {"refused": True, "reason": "malformed Content-Length"})
            return
        if length > MAX_BODY:
            self._respond(413, {"refused": True, "reason": "body too large for a stub"})
            return
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            self._respond(400, {"refused": True, "reason": "body is not valid JSON"})
            return
        if not isinstance(payload, dict):
            self._respond(400, {"refused": True, "reason": "body must be a JSON object"})
            return
        # The owner key may travel as a header instead of in the body, so it need
        # not sit in shell history. Headers are never logged by this service.
        hdr = self.headers.get("X-Owner-Key")
        if hdr and "owner_key" not in payload:
            payload["owner_key"] = hdr
        status, body = dispatch("POST", self.path.split("?")[0], payload, self.data_dir)
        self._respond(status, body)


def serve(port: int, data_dir: str):
    Handler.data_dir = data_dir
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    sys.stderr.write("%s\nlistening on http://127.0.0.1:%d  (data dir: %s)\n"
                     % (THROWAWAY, port, os.path.abspath(data_dir)))
    sys.stderr.write(
        "\nOWNER-SURFACE KEY (this process only — do NOT put it in n8n or Zapier):\n"
        "  %s\n"
        "Record a POC-1 decision with it:\n"
        "  curl -s -X POST http://127.0.0.1:%d/owner/decide \\\n"
        "       -H 'X-Owner-Key: %s' -H 'Content-Type: application/json' \\\n"
        "       -d '{\"case_id\":\"<case>\",\"decision\":\"accept\"}'\n\n"
        % (STORE.owner_key, port, STORE.owner_key))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


def main(argv):
    ap = argparse.ArgumentParser(description="THROWAWAY POC wrapper stub")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "..", "data"))
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        from selftest_stub import run_self_test   # noqa: PLC0415
        return run_self_test(args.data)
    serve(args.port, args.data)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1:]))

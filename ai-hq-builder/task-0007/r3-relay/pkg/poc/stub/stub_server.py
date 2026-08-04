#!/usr/bin/env python3
# ==============================================================================
#  THROWAWAY POC EVIDENCE APPARATUS — NOT THE AI OS WRAPPER
#
#  This service exists so the TASK-0007 owner session can run end to end. It is
#  evidence apparatus, it earns NO Track B credit, and it MUST NOT survive into
#  production use. It has no durable persistence, no real authentication, no
#  cryptographic attestation, and no clock authority — four of the things
#  `13B_` says the real wrapper needs. Delete it when the POC round closes.
#
#  Authority note: this stub stands in for the AI OS side of the boundary. The
#  provider (Zapier / n8n) calls it; it never calls a provider, and it never
#  receives a decision from a provider.
#
#  R2 build. Implements the corrected endpoint contract in `14_` §2 (C-1..C-19),
#  which governs where it disagrees with any earlier document.
# ==============================================================================
"""Single-file POC wrapper stub (Python standard library only).

Run:       python3 stub_server.py --candidate n8n [--port 8787] [--data ../data]
Health:    curl -s http://127.0.0.1:8787/health
Self-test: python3 selftest_stub.py

Provider-facing (require the provider credential, X-Provider-Key):
    POST /poc1/review-case       bind the identity tuple, mint an OPAQUE token
    POST /poc1/verify-decision   token -> authorized ActionRequest + capability
    POST /poc1/receipt           record the raw provider result
    POST /poc1/refusal           record a fail-closed refusal
    POST /poc2/triage            classify + stage (envelope required first)
    POST /poc3/run-started       declare an occurrence; run id is stub-minted
    POST /poc3/checkpoint        record checkpoint state
    POST /poc3/reconcile         reconcile an uncertain side effect
    POST /poc3/receipt           record the run result
    POST /relay/deliver          the POC-1 side effect; capability required
    POST /stage/deliver          the POC-3 stage target; retry-tolerant

Owner-facing (require the owner key, X-Owner-Key — never given to a provider):
    POST /owner/cases            what is waiting for a decision
    POST /owner/decide           the ONLY place a decision may originate

Open:
    GET  /health                 liveness for the runbooks
"""
from __future__ import annotations

import argparse
import errno
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

THROWAWAY = ("THROWAWAY POC APPARATUS — not the AI OS wrapper, no Track B credit, "
             "must not survive into production use")

MAX_BODY = 1 << 20            # 1 MiB; a stub has no business accepting more
SOCKET_TIMEOUT_S = 10         # C-15: closes connect-and-send-nothing, which no
                              # length bound can reach
CAPABILITY_TTL_S = 300        # C-3: short lifetime
MAX_CASES = 5000              # C-15: bounded counts
MAX_RECEIPTS = 5000
MAX_CAPTURES = 20000
MAX_RUNS = 5000
MAX_REDACT_DEPTH = 12         # C-16: cap recursion in redaction

ALLOWED_PARTITION = "business"
REQUIRED_TRUST = "external-untrusted"

# --------------------------------------------------------------------------
# C-2 — target ROLE table. The service resolves role -> endpoint from here; it
# never takes a destination from the request. R1's control, and its reason:
# honouring a provider-supplied destination lets the provider redirect an action
# the owner approved — the decision is the owner's, the target must be too.
# --------------------------------------------------------------------------
TARGET_ROLES = {
    "integration-owner": "/relay/deliver",
    "verifier": "/relay/deliver",
    "reader": "/relay/deliver",
}
# Roles that exist but may not receive a relay in this round. Declared so that an
# unauthorized role is distinguishable from an unknown one, and both from a
# duplicate-suppression success — R1P-04 test (3) is exactly that distinction.
UNAUTHORIZED_ROLES = {"owner", "release-executor"}

STAGE_TARGET_PATH = "/stage/deliver"

# --------------------------------------------------------------------------
# C-9 — per-endpoint capture allowlists. Anything not named is reduced to a
# descriptor (name, type, byte length, non-reversible digest) rather than
# persisted verbatim, so an arbitrary provider payload cannot smuggle content
# into the corpus. Stub-minted fields live at the top level; provider-supplied
# content lives under PROVIDER_KEY, so no provider-authored object can read as a
# stub-authored record.
# --------------------------------------------------------------------------
PROVIDER_KEY = "provider_supplied"
CAPTURE_ALLOWLIST = {
    "/poc1/review-case": ("task_id", "transition", "artifact_digest", "target_role",
                          "submission_epoch", "case_id", "idempotency_key", "outcome"),
    "/poc1/verify-decision": ("case_id", "action_request_id", "outcome", "reason"),
    "/poc1/receipt": ("case_id", "action_request_id", "outcome"),
    "/poc1/refusal": ("case_id", "reason", "outcome"),
    "/poc2/triage": ("origin", "instruction_authority", "classification", "stage",
                     "queue", "outcome"),
    "/poc3/run-started": ("run_id", "schedule_id", "occurrence", "outcome"),
    "/poc3/checkpoint": ("run_id", "stage", "outcome"),
    "/poc3/reconcile": ("run_id", "checked", "outcome"),
    "/poc3/receipt": ("run_id", "occurrence", "outcome"),
    "/relay/deliver": ("case_id", "action_request_id", "attempt", "delivered",
                       "replayed", "outcome"),
    "/stage/deliver": ("run_id", "stage_attempt", "outcome"),
    "/owner/decide": ("case_id", "decision", "outcome", "reason"),
    "/owner/cases": ("outcome",),
}

# --------------------------------------------------------------------------
# C-10 — redaction, corrected in BOTH directions.
#
# Over-redaction destroys evidence the round must measure (FAB-05): R1 matched
# key names by unanchored substring, so `tokens_used` (a named provider billing
# measurement) and `authority_id` / `authority_version` (two of the three
# AUTHORITY-owned fields in the harness's REQUIRED table) were replaced with a
# non-empty constant — which `receipt_conformance.analyse` then scored PRESENT,
# hiding the loss. Under-redaction leaks live secrets (SEC-R1-02): a
# `token_urlsafe` value under an unrecognised key matched no pattern at all.
#
# So: key names match on WHOLE underscore-separated segments, an explicit
# non-secret allowlist protects the D-EC_ field names, and exact-value scrubbing
# compares candidate strings AND their substrings against live secrets by
# constant-time comparison. A withheld value becomes a structured marker
# carrying name, type, length and digest — never a bare constant.
# --------------------------------------------------------------------------
SECRET_KEY_SEGMENTS = frozenset((
    "password", "passwd", "secret", "token", "credential", "credentials",
    "authorization", "auth", "cookie", "signature", "bearer", "apikey", "key",
))
# Names that CONTAIN a secret-looking segment but are evidence, not secrets.
NON_SECRET_FIELD_NAMES = frozenset((
    # D-EC_ REQUIRED table (harness/receipt_conformance.py) — must survive intact
    "receipt_id", "subject_ref", "executed_at", "occurrence", "schedule_version",
    "purpose", "authority_id", "authority_version", "content_hash",
    "action_request_id", "action_class", "scope", "policy_version", "risk_class",
    "idempotency_key", "side_effect_status",
    # named provider measurements
    "tokens_used", "task_count", "execution_count", "session_id",
    # this contract's own identity fields
    "task_id", "artifact_digest", "target_role", "capability_id",
))

SECRET_PATTERNS = [
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "aws-key"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}"), "github-token"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}"), "openai-style-key"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "slack-token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private-key"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]+"), "jwt"),
    (re.compile(r"(?i)\b(password|passwd|client_secret|api_key|apikey)"
                r"\s*[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9!@#$%^&*_\-]{6,})"), "assigned-credential"),
    (re.compile(r"(?i)\bauthorization\s*:\s*(bearer|basic)\s+\S+"), "auth-header"),
]

# Fields whose presence means a decision is arriving FROM the provider side.
PROVIDER_DECISION_FIELDS = frozenset((
    "decision", "approved", "approval", "outcome_decision", "authorized",
    "owner_decision", "approval_result", "verdict", "approve",
))


def _segments(name) -> list:
    return [s for s in re.split(r"[^A-Za-z0-9]+", str(name).lower()) if s]


def _is_secret_key(name) -> bool:
    """Whole-segment match, with an explicit evidence allowlist (C-10)."""
    low = str(name).lower()
    if low in NON_SECRET_FIELD_NAMES:
        return False
    return any(s in SECRET_KEY_SEGMENTS for s in _segments(name))


def _descriptor(name, value, why: str) -> dict:
    """A structured withholding marker. Never a bare constant: a constant scores
    as PRESENT in the harness and thereby hides the loss (FAB-05)."""
    raw = value if isinstance(value, str) else json.dumps(value, sort_keys=True,
                                                          default=str)
    encoded = raw.encode("utf-8", "replace")
    return {"__withheld__": why, "name": str(name), "type": type(value).__name__,
            "bytes": len(encoded),
            "digest": hashlib.sha256(encoded).hexdigest()[:32]}


class SecretIndex:
    """Live secret values, for exact-value scrubbing (C-10).

    Whole-value comparison alone is defeated by concatenation, so candidate
    strings are checked for any live secret appearing as a SUBSTRING. Comparison
    is constant-time per candidate. Values are held as their digests plus their
    lengths so the scan needs no plaintext table walk.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._values = set()

    def add(self, value: str):
        if isinstance(value, str) and value:
            with self._lock:
                self._values.add(value)

    def discard(self, value: str):
        with self._lock:
            self._values.discard(value)

    def snapshot(self) -> tuple:
        with self._lock:
            return tuple(self._values)

    def scrub(self, text: str) -> tuple:
        """Return (text, hit) with any live secret substring replaced."""
        hit = False
        for live in self.snapshot():
            if not live:
                continue
            if len(live) <= len(text) and live in text:
                # constant-time confirmation of the equal-length window
                idx = text.find(live)
                if hmac.compare_digest(text[idx:idx + len(live)], live):
                    text = text.replace(live, "[REDACTED:live-secret]")
                    hit = True
        return text, hit


SECRETS = SecretIndex()


def redact(value, depth: int = 0):
    """Remove secret material before anything is logged or persisted."""
    if depth > MAX_REDACT_DEPTH:
        return {"__withheld__": "recursion-depth", "type": type(value).__name__}
    if isinstance(value, str):
        out, _ = SECRETS.scrub(value)
        for rx, label in SECRET_PATTERNS:
            out = rx.sub("[REDACTED:%s]" % label, out)
        return out
    if isinstance(value, dict):
        clean = {}
        for k, v in value.items():
            key, _ = SECRETS.scrub(str(k))          # FAB-14: keys leak too
            if _is_secret_key(key) and v not in (None, "", [], {}):
                clean[key] = _descriptor(key, v, "secret-key-name")
            else:
                clean[key] = redact(v, depth + 1)
        return clean
    if isinstance(value, list):
        return [redact(v, depth + 1) for v in value]
    return value


def contains_live_secret(blob: str) -> bool:
    _, hit = SECRETS.scrub(blob)
    return hit


def contains_secret(value) -> list:
    """Pattern labels found. Used by the self-test."""
    blob = value if isinstance(value, str) else json.dumps(value, default=str)
    found = [label for rx, label in SECRET_PATTERNS if rx.search(blob)]
    if contains_live_secret(blob):
        found.append("live-secret")
    return found


# --------------------------------------------------------------------------
# State
# --------------------------------------------------------------------------
class CaptureError(Exception):
    """Raised when a capture cannot be committed. C-6: nothing commits after."""


class Store:
    def __init__(self, candidate: str = "unset"):
        self.lock = threading.RLock()
        self.candidate = candidate
        # C-7: a per-process run instance, so filenames cannot collide across
        # process lifetimes. FAB-03: R1's counter restarted at 0001 and the
        # runbook is deterministic, so a repeat run REPRODUCED earlier names.
        self.run_instance = "%s-%s" % (time.strftime("%Y%m%dT%H%M%S"),
                                       uuid.uuid4().hex[:8])
        self.owner_key = secrets.token_urlsafe(24)
        self.provider_key = secrets.token_urlsafe(24)   # C-15, no owner authority
        SECRETS.add(self.owner_key)
        SECRETS.add(self.provider_key)
        self.cases = {}            # case_id -> record
        self.by_identity = {}      # idempotency_key -> case_id
        self.tokens = {}           # digest -> {case_id, consumed}
        self.decisions = {}        # case_id -> immutable decision record
        self.capabilities = {}     # capability_id -> binding
        self.relay_receipts = {}   # action_request_id -> receipt
        self.relay_attempts = {}   # action_request_id -> int
        self.stage_attempts = {}   # run_id -> int
        self.receipts = []
        self.runs = {}
        self.captures = 0
        self.base_url = None

    # --- tokens -----------------------------------------------------------
    @staticmethod
    def _digest(raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def mint_token(self, case_id: str) -> str:
        raw = secrets.token_urlsafe(32)
        with self.lock:
            self.tokens[self._digest(raw)] = {"case_id": case_id, "consumed": False}
        SECRETS.add(raw)               # C-10: live tokens are scrubbed by value
        return raw

    def _find(self, raw: str):
        if not isinstance(raw, str) or not raw.strip():
            return None, "no resume token was presented"
        rec = self.tokens.get(self._digest(raw))     # FAB-17: dict, not a scan
        if rec is None:
            return None, "resume token is not one this service minted"
        if rec["consumed"]:
            return None, "resume token has already been used — replay refused"
        return rec, None

    def peek_token(self, raw: str):
        """Validate WITHOUT consuming: a provider legitimately polls before the
        owner has decided, and burning the token there would make the owner's
        later approval unrelayable."""
        with self.lock:
            rec, why = self._find(raw)
            return (None, why) if rec is None else (rec["case_id"], None)


STORE = Store()


# --------------------------------------------------------------------------
# C-6 / C-7 — capture-before-commit, with identity and provenance
# --------------------------------------------------------------------------
SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


def _split_fields(route: str, payload: dict) -> tuple:
    """(stub_minted, provider_supplied) per the C-9 allowlist."""
    allowed = CAPTURE_ALLOWLIST.get(route, ())
    minted, provider = {}, {}
    for k, v in (payload or {}).items():
        if k in allowed:
            minted[k] = v
        else:
            provider[k] = _descriptor(k, v, "not-allowlisted-for-this-route")
    return minted, provider


def write_capture(route: str, poc: str, step: str, payload: dict,
                  authored_by: str = "stub", data_dir: str = None) -> str:
    """Durably record one transition, or raise CaptureError.

    C-6: temp file in the destination directory, flush, fsync, atomic rename.
    The caller commits in-memory state only after this returns.
    """
    data_dir = data_dir or Handler.data_dir
    candidate = STORE.candidate
    for part in (candidate, poc, step):
        if not SAFE_NAME.match(str(part)) or part in (".", ".."):
            raise CaptureError("unsafe capture path component %r" % part)
    if STORE.captures >= MAX_CAPTURES:
        raise CaptureError("capture ceiling reached")

    root = os.path.abspath(os.path.join(data_dir, "captures", candidate, poc))
    expected = os.path.abspath(os.path.join(data_dir, "captures"))
    if not root.startswith(expected + os.sep):
        raise CaptureError("capture path escapes the captures directory")

    minted, provider = _split_fields(route, payload)
    body = {
        # C-7: stub-minted identity and provenance at the top level.
        "synthetic": True,
        "produced_by": "stub_server.py (%s)" % THROWAWAY,
        "candidate": candidate,                       # C-8 / FAB-02
        "run_instance": STORE.run_instance,           # C-7 / FAB-03
        "route": route,                               # C-7
        "authored_by": authored_by,                   # C-7: owner-surface/provider/stub
        "poc": poc,
        "step": step,
        # FAB-09: a stub-minted time, labelled for exactly what it is.
        "recorded_at": time.time(),
        "recorded_at_note": ("stub-minted local wall clock; NO clock authority "
                             "(13B_ leaves clock discipline to the real wrapper)"),
        "fields": redact(minted),
    }
    if provider:
        body[PROVIDER_KEY] = redact(provider)         # C-9: provenance split

    try:
        os.makedirs(root, exist_ok=True)
        # C-7: exclusive create, so an existing record is never truncated.
        seq = 0
        while True:
            seq += 1
            name = "%s-%s-%04d.json" % (step, STORE.run_instance, seq)
            path = os.path.join(root, name)
            try:
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
                break
            except FileExistsError:
                if seq > 9999:
                    raise CaptureError("cannot allocate a capture filename")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(body, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)          # atomic
        os.close(fd)
        dir_fd = os.open(root, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except CaptureError:
        raise
    except OSError as exc:
        raise CaptureError("capture write failed: %s" % errno.errorcode.get(
            exc.errno, exc.errno))
    with STORE.lock:
        STORE.captures += 1
    return path


# --------------------------------------------------------------------------
# Boundary checks — C-11 applies these at DISPATCH, not per handler.
# --------------------------------------------------------------------------
def _envelope_obj(payload: dict) -> dict:
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
    if part.lower() != ALLOWED_PARTITION:
        return False, ("payload declares partition %r; no Personal-partition route "
                       "exists in this service and no non-business partition is "
                       "accepted (packet §3)" % part)
    return True, None


def _envelope_ok(payload: dict) -> tuple:
    env = _envelope_obj(payload)
    if not env:
        return False, ("no external-untrusted envelope on the payload; the envelope "
                       "is applied before any classification (packet §3)")
    trust = env.get("trust")
    if trust != REQUIRED_TRUST:
        return False, ("envelope declares trust %r; inbound external content must "
                       "carry %r before classification (packet §3)" % (trust, REQUIRED_TRUST))
    return True, None


def _no_provider_decision(payload: dict) -> tuple:
    present = sorted(f for f in payload if str(f).lower() in PROVIDER_DECISION_FIELDS)
    if present:
        return False, ("request carries decision field(s) %s — an approval outcome "
                       "may not arrive from the provider side; the provider carries "
                       "an opaque token only (08_ §R1, finding F-3)"
                       % ", ".join(repr(p) for p in present))
    return True, None


# C-11: the exemption list is explicit and commented, rather than the default
# being "no checks unless a handler remembers". FAB-06: R1 wired the
# provider-decision refusal to 3 of 13 routes.
ENVELOPE_EXEMPT = {
    "/poc1/verify-decision",   # token exchange; carries no content at all
    "/poc1/receipt", "/poc1/refusal",   # record provider results, not inbound content
    "/poc3/run-started", "/poc3/checkpoint", "/poc3/reconcile", "/poc3/receipt",
    "/relay/deliver", "/stage/deliver",
    "/owner/cases", "/owner/decide",    # owner surface, not inbound external content
}
# /owner/decide is the ONE route where a decision field is legitimate — it is the
# owner surface. Everything else refuses one.
DECISION_ALLOWED = {"/owner/decide"}


# --------------------------------------------------------------------------
# Handlers
# --------------------------------------------------------------------------
def _refuse(route, poc, step, status, reason, authored_by="provider", **extra):
    """Refuse AND capture. C-12: every refusal path writes a record."""
    body = {"refused": True, "reason": reason, "outcome": "refused"}
    body.update(extra)
    try:
        write_capture(route, poc, step, dict(body), authored_by=authored_by)
    except CaptureError as exc:
        return 500, {"refused": True, "outcome": "capture-failed",
                     "reason": "refusal could not be recorded: %s" % exc}
    return status, body


def h_health(_payload):
    # FAB-16: no capture counter here — it was an owner-decision-activity oracle.
    return 200, {"ok": True, "service": "poc-wrapper-stub", "throwaway": THROWAWAY,
                 "candidate": STORE.candidate, "run_instance": STORE.run_instance,
                 "partition": ALLOWED_PARTITION,
                 "relay_endpoint": STORE.base_url + "/relay/deliver",
                 "stage_endpoint": STORE.base_url + STAGE_TARGET_PATH}


# ---- C-1: the identity tuple ----------------------------------------------
IDENTITY_FIELDS = ("task_id", "transition", "artifact_digest", "target_role",
                   "submission_epoch")


def _identity_problems(payload: dict) -> list:
    problems = []
    for f in IDENTITY_FIELDS:
        v = payload.get(f)
        if v is None or (isinstance(v, str) and not v.strip()):
            problems.append("%s is required" % f)
        elif f == "submission_epoch":
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                problems.append("submission_epoch must be a non-negative integer")
        elif not isinstance(v, str):
            problems.append("%s must be a string" % f)
        elif f == "artifact_digest" and not re.fullmatch(r"[0-9a-f]{64}", v.strip()):
            problems.append("artifact_digest must be a 64-hex content digest — "
                            "a raw archive hash alone is not identity (R1P-04)")
    return problems


def _idempotency_key(payload: dict) -> str:
    """C-1: derived from ALL FIVE components. R1 used
    sha256(case_id | action_class | decision_time), missing two of the five."""
    canon = json.dumps({f: payload.get(f) for f in IDENTITY_FIELDS},
                       sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def h_poc1_review_case(payload):
    problems = _identity_problems(payload)
    if problems:
        return _refuse("/poc1/review-case", "POC1", "review-case-malformed-identity",
                       400, "identity tuple incomplete or malformed: %s"
                       % "; ".join(problems))

    role = payload["target_role"].strip()
    if role in UNAUTHORIZED_ROLES:
        # R1P-04 test (3): REJECT, and distinguishable from duplicate-success.
        return _refuse("/poc1/review-case", "POC1", "review-case-unauthorized-role",
                       403, "target_role %r is not authorized to receive a relay in "
                       "this round" % role, outcome="rejected-unauthorized-target",
                       target_role=role)
    if role not in TARGET_ROLES:
        return _refuse("/poc1/review-case", "POC1", "review-case-unknown-role",
                       400, "target_role %r is not a known role" % role,
                       outcome="rejected-unknown-target", target_role=role)

    ikey = _idempotency_key(payload)
    with STORE.lock:
        prior = STORE.by_identity.get(ikey)
        if prior is not None:
            # R1P-04 test (1): suppress reprocessing, return the PRIOR receipt.
            existing = STORE.cases[prior]
            try:
                write_capture("/poc1/review-case", "POC1", "review-case-duplicate",
                              {"case_id": prior, "idempotency_key": ikey,
                               "outcome": "duplicate-suppressed",
                               "task_id": payload.get("task_id"),
                               "transition": payload.get("transition"),
                               "artifact_digest": payload.get("artifact_digest"),
                               "target_role": role})
            except CaptureError as exc:
                return 500, {"refused": True, "outcome": "capture-failed",
                             "reason": str(exc)}
            return 200, {"duplicate_suppressed": True,
                         "outcome": "duplicate-suppressed",
                         "prior_receipt": existing["receipt"],
                         "reprocessed": False,
                         "note": "same task, same transition, same artifact — "
                                 "the prior receipt is returned unchanged"}
        if len(STORE.cases) >= MAX_CASES:
            return _refuse("/poc1/review-case", "POC1", "review-case-ceiling",
                           429, "case ceiling reached")

    case_id = "case-" + secrets.token_hex(6)
    receipt = {"receipt_id": "rcpt-" + secrets.token_hex(6),
               "idempotency_key": ikey,
               "task_id": payload["task_id"], "transition": payload["transition"],
               "artifact_digest": payload["artifact_digest"], "target_role": role,
               "submission_epoch": payload["submission_epoch"]}
    try:
        write_capture("/poc1/review-case", "POC1", "review-case",
                      {"case_id": case_id, "idempotency_key": ikey,
                       "task_id": payload["task_id"],
                       "transition": payload["transition"],
                       "artifact_digest": payload["artifact_digest"],
                       "target_role": role,
                       "submission_epoch": payload["submission_epoch"],
                       "outcome": "case-opened"})
    except CaptureError as exc:
        # C-6: capture before commit — no case exists if it was not recorded.
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}

    token = STORE.mint_token(case_id)
    with STORE.lock:
        STORE.cases[case_id] = {"case_id": case_id, "identity": ikey,
                                "receipt": receipt, "target_role": role,
                                "opened_at": time.time()}
        STORE.by_identity[ikey] = case_id
    # The provider gets the token and nothing else — not the case id, which is
    # the value the owner surface keys on.
    return 200, {"resume_token": token, "outcome": "case-opened",
                 "note": "carry this token; the decision is made on the owner surface"}


def h_owner_cases(payload):
    with STORE.lock:
        pending = [{"case_id": c["case_id"], "task_id": c["receipt"]["task_id"],
                    "transition": c["receipt"]["transition"],
                    "target_role": c["target_role"], "opened_at": c["opened_at"],
                    "decided": c["case_id"] in STORE.decisions}
                   for c in STORE.cases.values()]
    pending.sort(key=lambda c: c["opened_at"])
    return 200, {"cases": pending, "undecided": sum(1 for c in pending if not c["decided"])}


def h_owner_decide(payload):
    case_id = payload.get("case_id")
    decision = payload.get("decision")
    if not isinstance(case_id, str):
        return _refuse("/owner/decide", "POC1", "owner-decide-malformed", 400,
                       "case_id must be a string", authored_by="owner-surface")
    if case_id not in STORE.cases:
        return _refuse("/owner/decide", "POC1", "owner-decide-unknown-case", 404,
                       "unknown case", authored_by="owner-surface")
    if decision not in ("accept", "reject"):
        return _refuse("/owner/decide", "POC1", "owner-decide-bad-decision", 400,
                       "decision must be 'accept' or 'reject'",
                       authored_by="owner-surface")

    with STORE.lock:
        # C-5: the first valid decision is TERMINAL. R1 rebound unconditionally,
        # so a reject could be overwritten by an accept and mint an ActionRequest
        # for a case the owner had rejected.
        if case_id in STORE.decisions:
            prior = STORE.decisions[case_id]
            return _refuse("/owner/decide", "POC1", "owner-decide-already-decided",
                           409, "case %s is already decided (%s); the first valid "
                           "decision is terminal" % (case_id, prior["decision"]),
                           authored_by="owner-surface", case_id=case_id,
                           decision=prior["decision"])
        record = {"decision": decision, "at": time.time(), "case_id": case_id}

    try:
        write_capture("/owner/decide", "POC1", "owner-decision",
                      {"case_id": case_id, "decision": decision,
                       "outcome": "decision-recorded"}, authored_by="owner-surface")
    except CaptureError as exc:
        # C-6: nothing commits if the record did not land.
        return 500, {"refused": True, "outcome": "capture-failed",
                     "reason": "decision not recorded, and therefore not taken: %s" % exc}
    with STORE.lock:
        if case_id in STORE.decisions:            # lost a race; stay terminal
            return 409, {"refused": True, "reason": "case already decided"}
        STORE.decisions[case_id] = record
    return 200, {"case_id": case_id, "recorded": decision, "terminal": True,
                 "note": "recorded on the owner surface; the provider is not told "
                         "the outcome"}


VERIFY_ALLOWED_KEYS = {"token"}


def h_poc1_verify_decision(payload):
    extra = sorted(set(payload) - VERIFY_ALLOWED_KEYS)
    if extra:
        return _refuse("/poc1/verify-decision", "POC1", "verify-refused-extra-fields",
                       403, "verify-decision accepts only a resume token; the request "
                       "also carried %d additional field(s). An authorization the "
                       "owner made is not open to provider input (08_ §R1)" % len(extra),
                       # FAB-14: the COUNT, never the key names — a live token can
                       # be smuggled in as a key.
                       outcome="refused-extra-fields")

    case_id, why = STORE.peek_token(payload.get("token"))
    if case_id is None:
        return _refuse("/poc1/verify-decision", "POC1", "verify-refused-token",
                       403, why, outcome="refused-token")

    # C-5: decision lookup and token consumption in ONE critical section against
    # an immutable decision record. R1 read STORE.decisions with no lock held and
    # took one only for the spend — a genuine check-then-act gap.
    with STORE.lock:
        decision = STORE.decisions.get(case_id)
        if decision is None:
            pending = True
        else:
            pending = False
            rec, tok_why = STORE._find(payload.get("token"))
            if rec is None:
                return _refuse("/poc1/verify-decision", "POC1", "verify-refused-token",
                               403, tok_why, outcome="refused-token")

    if pending:
        # FAB-01: this is one of the two events the POC exists to demonstrate.
        return _refuse("/poc1/verify-decision", "POC1", "verify-pending", 403,
                       "no owner decision exists for this case; a valid token proves "
                       "the pause was carried, not that anything was approved. The "
                       "token is still valid — poll again once the owner has decided",
                       outcome="pending", case_id=case_id)

    case = STORE.cases[case_id]
    if decision["decision"] != "accept":
        try:
            write_capture("/poc1/verify-decision", "POC1", "verify-rejected",
                          {"case_id": case_id, "outcome": "owner-rejected"})
        except CaptureError as exc:
            return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
        with STORE.lock:
            rec, _ = STORE._find(payload.get("token"))
            if rec:
                rec["consumed"] = True
                SECRETS.discard(payload.get("token"))
        return 200, {"authorized": False, "outcome": "owner-rejected",
                     "reason": "owner rejected the case"}

    action_request = {
        "id": "ar-" + secrets.token_hex(6),
        "case_id": case_id,
        "action_class": "relay-artifact",
        "scope": ALLOWED_PARTITION,
        "policy_version": "P1",
        "risk_class": "consequential",
        "idempotency_key": case["identity"],      # C-1: the five-component key
        "target_role": case["target_role"],
        # C-2: resolved server-side from the role table, never from the request.
        "endpoint": STORE.base_url + TARGET_ROLES[case["target_role"]],
        "payload": {"case_id": case_id, "task_id": case["receipt"]["task_id"],
                    "transition": case["receipt"]["transition"],
                    "artifact_digest": case["receipt"]["artifact_digest"],
                    # FAB-15: the key reaches the TARGET, not just the envelope.
                    "idempotency_key": case["identity"]},
    }
    payload_digest = hashlib.sha256(json.dumps(action_request["payload"],
                                               sort_keys=True,
                                               separators=(",", ":")).encode()).hexdigest()
    capability = "cap-" + secrets.token_urlsafe(24)
    binding = {"capability": capability, "action_request_id": action_request["id"],
               "case_id": case_id, "endpoint": action_request["endpoint"],
               "payload_digest": payload_digest, "expires_at": time.time() + CAPABILITY_TTL_S,
               "used": False}

    # C-6 / FAB-04: the capture lands BEFORE the token is spent. A consumed
    # single-use token cannot be un-consumed by anything in this file, so a
    # capture failure there would burn it with zero evidence.
    try:
        write_capture("/poc1/verify-decision", "POC1", "verify-authorized",
                      {"case_id": case_id, "action_request_id": action_request["id"],
                       "outcome": "authorized"})
    except CaptureError as exc:
        return 500, {"refused": True, "outcome": "capture-failed",
                     "reason": "authorization not recorded, and therefore not "
                               "issued; the token remains unspent: %s" % exc}
    with STORE.lock:
        rec, tok_why = STORE._find(payload.get("token"))
        if rec is None:
            return 403, {"authorized": False, "refused": True, "reason": tok_why}
        rec["consumed"] = True
        SECRETS.discard(payload.get("token"))
        STORE.capabilities[capability] = binding
    SECRETS.add(capability)
    return 200, {"authorized": True, "outcome": "authorized",
                 "action_request": action_request,
                 "execution_capability": capability,
                 "capability_expires_in_s": CAPABILITY_TTL_S}


def h_relay_deliver(payload):
    """C-3 — the POC-1 side effect. Fails closed without a valid capability."""
    cap = payload.get("capability")
    with STORE.lock:
        binding = STORE.capabilities.get(cap) if isinstance(cap, str) else None
    if binding is None:
        return _refuse("/relay/deliver", "POC1", "relay-refused-no-capability", 403,
                       "the relay sink requires a single-use execution capability "
                       "minted at authorization; a direct call cannot produce the "
                       "side effect (SEC-R1-01)", outcome="refused-no-capability")
    if time.time() > binding["expires_at"]:
        return _refuse("/relay/deliver", "POC1", "relay-refused-expired", 403,
                       "execution capability has expired", outcome="refused-expired",
                       action_request_id=binding["action_request_id"])
    for field, want in (("action_request_id", binding["action_request_id"]),
                        ("case_id", binding["case_id"])):
        if payload.get(field) != want:
            return _refuse("/relay/deliver", "POC1", "relay-refused-binding", 403,
                           "capability is not bound to the presented %s" % field,
                           outcome="refused-binding")
    body = payload.get("payload")
    digest = hashlib.sha256(json.dumps(body, sort_keys=True,
                                       separators=(",", ":"),
                                       default=str).encode()).hexdigest()
    if digest != binding["payload_digest"]:
        return _refuse("/relay/deliver", "POC1", "relay-refused-payload", 403,
                       "payload digest does not match the capability binding",
                       outcome="refused-payload-mismatch",
                       action_request_id=binding["action_request_id"])

    # C-3: attempts and deliveries stay SEPARATELY countable — "how often did the
    # provider retry" is a provider-discriminating measurement, and a fix that
    # stopped recording attempts would convert it into a stub self-test.
    with STORE.lock:
        arid = binding["action_request_id"]
        STORE.relay_attempts[arid] = STORE.relay_attempts.get(arid, 0) + 1
        attempt = STORE.relay_attempts[arid]
        prior = STORE.relay_receipts.get(arid)
    if prior is not None:
        # R1P-04 test (4) / `12_` §5 test 3: replay returns the PRIOR receipt with
        # an explicit no-second-side-effect marker, not a bare refusal — honest
        # about provider retries, which POC-3 deliberately induces.
        try:
            write_capture("/relay/deliver", "POC1", "relay-replay",
                          {"case_id": binding["case_id"], "action_request_id": arid,
                           "attempt": attempt, "delivered": False, "replayed": True,
                           "outcome": "replayed-no-second-side-effect"})
        except CaptureError as exc:
            return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
        return 200, {"delivered": False, "replayed": True,
                     "no_second_side_effect": True, "attempt": attempt,
                     "receipt": prior, "outcome": "replayed-no-second-side-effect"}

    receipt = {"receipt_id": "dlv-" + secrets.token_hex(6),
               "action_request_id": arid, "case_id": binding["case_id"],
               "delivered_attempt": attempt}
    try:
        write_capture("/relay/deliver", "POC1", "relay-delivered",
                      {"case_id": binding["case_id"], "action_request_id": arid,
                       "attempt": attempt, "delivered": True, "replayed": False,
                       "outcome": "delivered"})
    except CaptureError as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    with STORE.lock:
        STORE.relay_receipts[arid] = receipt
        STORE.capabilities[cap]["used"] = True
    return 200, {"delivered": True, "replayed": False, "attempt": attempt,
                 "receipt": receipt, "outcome": "delivered"}


def h_stage_deliver(payload):
    """C-4 — POC-3's stage target. No case, no owner decision, no ActionRequest,
    and deliberately RETRY-TOLERANT: the round induces a mid-flight kill, and a
    single-use rule here would fail POC-3 outright and mis-score a legitimate
    provider retry, which is the thing POC-3 measures (13_ VC-03)."""
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or run_id not in STORE.runs:
        return _refuse("/stage/deliver", "POC3", "stage-refused-unknown-run", 404,
                       "stage delivery for an unannounced run",
                       outcome="refused-unknown-run")
    with STORE.lock:
        STORE.stage_attempts[run_id] = STORE.stage_attempts.get(run_id, 0) + 1
        attempt = STORE.stage_attempts[run_id]
    try:
        write_capture("/stage/deliver", "POC3", "stage-delivered",
                      {"run_id": run_id, "stage_attempt": attempt,
                       "outcome": "stage-delivered"})
    except CaptureError as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    return 200, {"staged": True, "stage_attempt": attempt, "retry_tolerant": True,
                 "outcome": "stage-delivered"}


def h_poc1_receipt(payload):
    with STORE.lock:
        if len(STORE.receipts) >= MAX_RECEIPTS:
            return _refuse("/poc1/receipt", "POC1", "receipt-ceiling", 429,
                           "receipt ceiling reached")
        STORE.receipts.append(True)          # FAB-17: a count, not a growing corpus
    try:
        write_capture("/poc1/receipt", "POC1", "provider-receipt", dict(payload),
                      authored_by="provider")
    except CaptureError as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    return 200, {"recorded": True, "outcome": "recorded",
                 "note": ("raw provider result recorded as corroborating material; "
                          "the wrapper mints the D-EC_ receipt, the provider does not")}


def h_poc1_refusal(payload):
    try:
        write_capture("/poc1/refusal", "POC1", "provider-refusal", dict(payload),
                      authored_by="provider")
    except CaptureError as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    return 200, {"recorded": True, "outcome": "recorded"}


# ---- POC-2: two envelope cases (09_ §2 R1P-02) ------------------------------
def h_poc2_triage(payload):
    origin = payload.get("origin")
    if origin not in ("owner", "external"):
        return _refuse("/poc2/triage", "POC2", "triage-refused-origin", 400,
                       "origin must be 'owner' (Case A) or 'external' (Case B)",
                       outcome="refused-origin")
    # R1P-02: the two cases differ in INSTRUCTION AUTHORITY, not merely in label.
    # External content may inform classification and must never acquire authority.
    authority = "owner-authorized" if origin == "owner" else "none"
    md = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    subject = md.get("subject") or md.get("title") or ""
    project = md.get("project")
    classification = "existing-project-addition" if project else "new-topic"
    try:
        write_capture("/poc2/triage", "POC2", "idea-staged",
                      {"origin": origin, "instruction_authority": authority,
                       "classification": classification, "stage": "staged",
                       "queue": "business-ideas", "outcome": "staged"})
    except CaptureError as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    return 200, {
        "origin": origin,
        "instruction_authority": authority,
        "classification": classification,
        "staged": True, "queue": "business-ideas",
        "suggested_next": "owner review" if origin == "external" else "schedule",
        "outcome": "staged",
        # C-14 / FAB-08: the stub records; it does not attest to the provider's
        # conduct. R1 asserted `links_followed: False` and `actions_taken: []`,
        # which are claims about the PROVIDER that this service cannot observe.
        "external_action_taken_by_this_service": False,
        "provider_conduct": "NOT OBSERVED BY THIS SERVICE — whether the provider "
                            "followed a link or took an action is measured at the "
                            "provider, not asserted here",
        "subject_present": bool(subject),
    }


# ---- POC-3 ------------------------------------------------------------------
def h_poc3_run_started(payload):
    # C-13: the run identity is minted SERVER-SIDE. R1 let the provider choose it
    # and re-declaring silently overwrote the run — resetting started_at and
    # emptying checkpoints — which is exactly the call a replay after the mandated
    # mid-flight kill makes, destroying POC-3's whole measurement.
    correlation = payload.get("provider_correlation_id")
    declared = payload.get("run_id")
    if isinstance(declared, str) and declared in STORE.runs:
        prior = STORE.runs[declared]
        return _refuse("/poc3/run-started", "POC3", "run-duplicate-declaration", 409,
                       "run %s is already declared; a duplicate declaration is itself "
                       "a POC-3 measurement and does not overwrite the prior record"
                       % declared, outcome="duplicate-run-declaration",
                       run_id=declared,
                       prior_started_at=prior["started_at"],
                       prior_checkpoint_count=len(prior["checkpoints"]))
    with STORE.lock:
        if len(STORE.runs) >= MAX_RUNS:
            return _refuse("/poc3/run-started", "POC3", "run-ceiling", 429,
                           "run ceiling reached")
    run_id = "run-" + secrets.token_hex(6)
    try:
        write_capture("/poc3/run-started", "POC3", "run-started",
                      {"run_id": run_id, "schedule_id": payload.get("schedule_id"),
                       "occurrence": payload.get("occurrence"),
                       "outcome": "run-started"})
    except CaptureError as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    with STORE.lock:
        STORE.runs[run_id] = {"occurrence": payload.get("occurrence"),
                              "schedule_id": payload.get("schedule_id"),
                              "provider_correlation_id": correlation,
                              "started_at": time.time(), "checkpoints": []}
    return 200, {"run_id": run_id, "outcome": "run-started",
                 # C-18: derived from the bound port, never a second literal.
                 "stage_endpoint": STORE.base_url + STAGE_TARGET_PATH,
                 "provider_correlation_id": correlation,
                 "note": "run identity is stub-minted; any provider correlation "
                         "value is carried separately and anchors nothing"}


def h_poc3_checkpoint(payload):
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or run_id not in STORE.runs:
        return _refuse("/poc3/checkpoint", "POC3", "checkpoint-unknown-run", 404,
                       "checkpoint for an unannounced run", outcome="refused-unknown-run")
    try:
        write_capture("/poc3/checkpoint", "POC3", "checkpoint",
                      {"run_id": run_id, "stage": payload.get("stage"),
                       "outcome": "checkpointed"})
    except CaptureError as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    with STORE.lock:
        STORE.runs[run_id]["checkpoints"].append(time.time())
        count = len(STORE.runs[run_id]["checkpoints"])
    return 200, {"checkpointed": True, "checkpoint_count": count,
                 "side_effect_certain": False, "outcome": "checkpointed",
                 "note": "the side effect is reported UNCERTAIN so the reconcile "
                         "branch is exercised rather than left inert"}


def h_poc3_reconcile(payload):
    """C-14 / FAB-08 — perform a real check against recorded state, or say plainly
    that none was performed. R1 returned side_effect_certain: True with the note
    'post-state checked before any retry decision (ACT-01)' having checked
    nothing — not even that the run existed."""
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or run_id not in STORE.runs:
        return _refuse("/poc3/reconcile", "POC3", "reconcile-unknown-run", 404,
                       "reconcile for an unannounced run", outcome="refused-unknown-run")
    with STORE.lock:
        run = STORE.runs[run_id]
        checkpoints = len(run["checkpoints"])
        attempts = STORE.stage_attempts.get(run_id, 0)
    # The one post-state fact this service actually holds.
    checked = {"checkpoints_recorded": checkpoints, "stage_attempts_recorded": attempts}
    try:
        write_capture("/poc3/reconcile", "POC3", "reconcile",
                      {"run_id": run_id, "checked": checked, "outcome": "reconciled"})
    except CaptureError as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    return 200, {
        "outcome": "reconciled",
        "post_state_checked_against_recorded_state": checked,
        # Honest: a real reconciliation reads the EXTERNAL system's post-state.
        # This service has no external system, and says so rather than asserting
        # ACT-01 compliance it did not perform.
        "external_post_state_checked": False,
        "side_effect_certainty": "NOT ESTABLISHED — this service can compare only "
                                 "its own recorded checkpoints and stage attempts; "
                                 "it has no view of an external system's post-state",
    }


def h_poc3_receipt(payload):
    run_id = payload.get("run_id")
    known = isinstance(run_id, str) and run_id in STORE.runs
    try:
        write_capture("/poc3/receipt", "POC3", "run-receipt",
                      {"run_id": run_id if known else None,
                       "occurrence": payload.get("occurrence"),
                       "outcome": "recorded"}, authored_by="provider")
    except CaptureError as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    return 200, {"recorded": True, "run_known": known, "outcome": "recorded",
                 "occurrence_declared": payload.get("occurrence"),
                 "note": ("the occurrence window is judged by the real wrapper; this "
                          "stub records, it does not attest (D-EC_ §4)")}


# --------------------------------------------------------------------------
# Routing
# --------------------------------------------------------------------------
OWNER_ROUTES = {"/owner/cases", "/owner/decide"}
OPEN_ROUTES = {"/health"}

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
    ("POST", "/relay/deliver"): h_relay_deliver,
    ("POST", "/stage/deliver"): h_stage_deliver,
    ("POST", "/owner/cases"): h_owner_cases,
    ("POST", "/owner/decide"): h_owner_decide,
}


def _auth_ok(route: str, headers: dict) -> tuple:
    """C-15 — owner routes need the owner key; provider routes need the provider
    credential, which confers NO owner authority."""
    if route in OPEN_ROUTES:
        return True, None
    presented = headers.get("owner_key") or ""
    if route in OWNER_ROUTES:
        if not isinstance(presented, str) or not _ct_eq(presented, STORE.owner_key):
            return False, ("owner-surface key missing or wrong; a decision must come "
                           "from the owner surface, and reaching this port is not "
                           "evidence that it did (08_ §R1)")
        return True, None
    pk = headers.get("provider_key") or ""
    if not isinstance(pk, str) or not _ct_eq(pk, STORE.provider_key):
        return False, ("provider credential missing or wrong — a browser-simple "
                       "cross-origin POST cannot reach this route (SEC-R1-08)")
    return True, None


def _ct_eq(a: str, b: str) -> bool:
    """FAB-13: hmac.compare_digest requires ASCII-only str; a non-ASCII key used
    to raise TypeError before any authorization verdict was produced."""
    try:
        return hmac.compare_digest(a, b)
    except TypeError:
        return hmac.compare_digest(a.encode("utf-8", "replace"),
                                   b.encode("utf-8", "replace"))


def dispatch(method: str, path: str, payload: dict, headers: dict = None):
    headers = headers or {}
    handler = ROUTES.get((method, path))
    if handler is None:
        return 404, {"refused": True, "reason": "no such route on this stub"}

    ok, why = _auth_ok(path, headers)
    if not ok:
        # C-12: capture the attempt — never the material presented.
        poc = "POC1" if path.startswith(("/poc1", "/owner", "/relay")) else \
              "POC2" if path.startswith("/poc2") else \
              "POC3" if path.startswith(("/poc3", "/stage")) else "POC1"
        try:
            write_capture(path, poc, "auth-refused",
                          {"outcome": "refused-auth", "reason": why},
                          authored_by="owner-surface" if path in OWNER_ROUTES else "provider")
        except CaptureError:
            pass
        return 403, {"refused": True, "reason": why, "outcome": "refused-auth"}

    if method == "POST":
        # C-11 — boundary checks as a DISPATCH DEFAULT, with an explicit,
        # commented exemption list. R1 wired them to 3 of 13 routes.
        if path not in DECISION_ALLOWED:
            good, why = _no_provider_decision(payload)
            if not good:
                poc = "POC2" if path.startswith("/poc2") else \
                      "POC3" if path.startswith(("/poc3", "/stage")) else "POC1"
                return _refuse(path, poc, "provider-decision-refused", 403, why,
                               outcome="refused-provider-decision")
        if path not in ENVELOPE_EXEMPT:
            for check in (_partition_ok, _envelope_ok):
                good, why = check(payload)
                if not good:
                    poc = "POC2" if path.startswith("/poc2") else "POC1"
                    return _refuse(path, poc, "boundary-refused", 400, why,
                                   outcome="refused-boundary")
    return handler(payload or {})


# --------------------------------------------------------------------------
# HTTP surface
# --------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "poc-wrapper-stub"
    data_dir = "../data"
    timeout = SOCKET_TIMEOUT_S

    # C-17 — log a ROUTE-MATCHED CONSTANT plus the status and nothing
    # caller-supplied, under any path. R1 logged the request line, so a secret in
    # the path (no query needed) reached stderr verbatim, and a malformed request
    # line double-logged through send_error before a handler was ever entered.
    def log_message(self, fmt, *args):  # noqa: A003
        return

    def log_request(self, code="-", size="-"):  # noqa: A003
        return

    def log_error(self, fmt, *args):  # noqa: A003
        return

    def _emit(self, matched: str, status: int):
        sys.stderr.write("%s %s\n" % (matched, status))

    def _respond(self, status, body, matched="<unmatched>"):
        raw = json.dumps(redact(body), indent=2, sort_keys=True).encode("utf-8")
        try:
            self.send_response_only(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("X-Throwaway", "poc-evidence-apparatus")
            self.send_header("Cache-Control", "no-store")      # C-17
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            self.wfile.write(raw)
        except OSError:
            pass
        self._emit(matched, status)

    def _headers(self) -> dict:
        return {"owner_key": self.headers.get("X-Owner-Key") or "",
                "provider_key": self.headers.get("X-Provider-Key") or ""}

    def do_GET(self):  # noqa: N802
        path = self.path.split("?")[0]
        matched = path if ("GET", path) in ROUTES else "<unmatched>"
        try:
            status, body = dispatch("GET", path, {}, self._headers())
        except Exception:                                   # C-16
            status, body = 500, {"refused": True, "reason": "internal error"}
        self._respond(status, body, matched)

    def do_POST(self):  # noqa: N802
        path = self.path.split("?")[0]
        matched = path if ("POST", path) in ROUTES else "<unmatched>"

        # C-15 — transport hardening.
        lengths = self.headers.get_all("Content-Length") or []
        if len(set(lengths)) > 1:
            self._respond(400, {"refused": True,
                                "reason": "conflicting Content-Length headers"}, matched)
            return
        if (self.headers.get("Transfer-Encoding") or "").strip().lower() not in ("", "identity"):
            self._respond(501, {"refused": True,
                                "reason": "unsupported transfer encoding"}, matched)
            return
        try:
            length = int(lengths[0]) if lengths else 0
        except ValueError:
            self._respond(400, {"refused": True, "reason": "malformed Content-Length"}, matched)
            return
        if length < 0:
            self._respond(400, {"refused": True,
                                "reason": "negative Content-Length"}, matched)
            return
        if length > MAX_BODY:
            self._respond(413, {"refused": True, "reason": "body too large for a stub"}, matched)
            return
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype != "application/json":
            self._respond(415, {"refused": True,
                                "reason": "Content-Type must be application/json "
                                          "(SEC-R1-08)"}, matched)
            return
        try:
            raw = self.rfile.read(length) if length else b"{}"
        except (OSError, TimeoutError):
            self._respond(408, {"refused": True, "reason": "request body timed out"}, matched)
            return
        if len(raw) != length:
            self._respond(400, {"refused": True, "reason": "short body"}, matched)
            return
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            self._respond(400, {"refused": True, "reason": "body is not valid JSON"}, matched)
            return
        if not isinstance(payload, dict):
            self._respond(400, {"refused": True, "reason": "body must be a JSON object"}, matched)
            return
        try:
            status, body = dispatch("POST", path, payload, self._headers())
        except Exception:                                   # C-16: no traceback out
            status, body = 500, {"refused": True, "reason": "internal error",
                                 "outcome": "refused-internal"}
        self._respond(status, body, matched)


def serve(port: int, data_dir: str, advertise: str = None):
    Handler.data_dir = data_dir
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    bound = srv.server_address[1]
    # C-18: advertised endpoints derive from the BOUND port, with an explicit
    # override for the container case the n8n runbook sets up.
    STORE.base_url = advertise or ("http://127.0.0.1:%d" % bound)
    sys.stderr.write(
        "%s\ncandidate=%s  run_instance=%s\nlistening on http://127.0.0.1:%d "
        "(advertising %s; data dir: %s)\n"
        % (THROWAWAY, STORE.candidate, STORE.run_instance, bound,
           STORE.base_url, os.path.abspath(data_dir)))
    # C-19 / DOC-01: print the keys as bare values, NOT inside a copyable command
    # — a copied command puts the key into shell history. The runbooks read them
    # into a shell variable instead.
    sys.stderr.write(
        "\nOWNER-SURFACE KEY   (owner terminal only; never into a provider):\n  %s\n"
        "PROVIDER CREDENTIAL (for the workflow's HTTP calls; no owner authority):\n  %s\n"
        "\nRead them into shell variables rather than pasting them into commands;\n"
        "the runbooks show the pattern.\n\n"
        % (STORE.owner_key, STORE.provider_key))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


CANDIDATE_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,31}$")


def main(argv):
    ap = argparse.ArgumentParser(description="THROWAWAY POC wrapper stub")
    # C-8: required and name-validated. A defaulted candidate is worse than none,
    # because the corpus then silently attributes one provider's evidence to a
    # placeholder and the round exists to COMPARE two providers.
    ap.add_argument("--candidate", required=True,
                    help="provider namespace for the capture corpus, e.g. n8n or zapier")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--advertise", default=None,
                    help="base URL to advertise (container case), e.g. "
                         "http://host.docker.internal:8787")
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "..", "data"))
    args = ap.parse_args(argv)
    if not CANDIDATE_NAME.match(args.candidate):
        sys.stderr.write("refusing to start: --candidate %r is not a valid name "
                         "(lowercase alphanumeric, dot, dash, underscore)\n"
                         % args.candidate)
        return 2
    global STORE
    STORE = Store(candidate=args.candidate)
    serve(args.port, args.data, args.advertise)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1:]))

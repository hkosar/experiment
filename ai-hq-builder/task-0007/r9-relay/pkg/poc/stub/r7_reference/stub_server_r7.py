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
#  R3 build, implementing `25_` (Revision 5) §A/§B/§C. Where `25_` disagrees with
#  any earlier document, `25_` governs.
#
#  GOVERNING RULE (`25_` line 11), applied throughout:
#      Every authority the service asserts must trace to something the service
#      itself established. A value a caller supplied is corroborating material,
#      never an authority.
# ==============================================================================
"""Single-file POC wrapper stub (Python standard library only).

Run:       python3 stub_server.py --candidate n8n [--port 8787] [--data ../data]
Health:    curl -s http://127.0.0.1:8787/health
Self-test: python3 selftest_stub.py     Witnesses: python3 r1_witnesses.py
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
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

THROWAWAY = ("THROWAWAY POC APPARATUS — not the AI OS wrapper, no Track B credit, "
             "must not survive into production use")

# --------------------------------------------------------------------------
# A.8 — limits, complete and in one place
# --------------------------------------------------------------------------
MAX_BODY = 1 << 20
MAX_REDACT_DEPTH = 12
MAX_OBJECT_FIELDS = 256
MAX_LIST_ITEMS = 1024
MAX_STRING_BYTES = 65536
MAX_ACTIVE_SECRETS = 512
MAX_CASES = 5000
MAX_IDEAS = 5000
MAX_TOKENS = 5000
MAX_DECISIONS = 5000
MAX_ATTEMPTS_PER_AR = 100
MAX_RECEIPTS = 5000
MAX_RUNS = 5000
MAX_CHECKPOINTS_PER_RUN = 1000
MAX_CAPTURES = 20000
CAPABILITY_TTL_S = 300
SOCKET_TIMEOUT_S = 10

# A.8 — three disjoint capture pools.
POOL_GENERAL, POOL_SECURITY, POOL_OWNER = "general", "security-refusal", "reserved-owner"
POOL_QUOTA = {POOL_GENERAL: int(MAX_CAPTURES * 0.70),
              POOL_SECURITY: int(MAX_CAPTURES * 0.15),
              POOL_OWNER: int(MAX_CAPTURES * 0.15)}

ALLOWED_PARTITION = "business"
REQUIRED_TRUST = "external-untrusted"

# A.1 — the service's OWN role table. It never takes a destination from a request.
TARGET_ROLES = {"integration-owner": "/relay/deliver",
                "verifier": "/relay/deliver",
                "reader": "/relay/deliver"}
UNAUTHORIZED_ROLES = {"owner", "release-executor"}
STAGE_TARGET_PATH = "/stage/deliver"

# A.4 — capability states.
MINTED, ATTEMPT_STARTED = "MINTED", "ATTEMPT_STARTED"
DELIVERED_WITH_RECEIPT = "DELIVERED_WITH_RECEIPT"
UNCERTAIN = "UNCERTAIN"
RECONCILED_DELIVERED = "RECONCILED_DELIVERED"
RECONCILED_NOT_DELIVERED = "RECONCILED_NOT_DELIVERED"
REVOKED, EXPIRED = "REVOKED", "EXPIRED"
TERMINAL_STATES = frozenset((DELIVERED_WITH_RECEIPT, RECONCILED_DELIVERED,
                             REVOKED, EXPIRED))
DELIVERED_STATES = frozenset((DELIVERED_WITH_RECEIPT, RECONCILED_DELIVERED))

# --------------------------------------------------------------------------
# §B — the route-policy table, implemented AS DATA.
# Unknown route or missing policy row ⇒ fail closed.
# --------------------------------------------------------------------------
OWNER, PROVIDER, OPEN = "owner", "provider", "open"

ROUTE_POLICY = {
    ("GET", "/health"): {
        "caller": OPEN, "fields": (), "envelope": "n/a", "decision_field": "n/a",
        "log": "GET /health", "quota": None, "pool": None},
    ("POST", "/owner/artifact/register"): {
        "caller": OWNER,
        "fields": ("source_digest", "size_bytes", "file_count", "task_id",
                   "transition", "target_role"),
        "envelope": "exempt", "decision_field": "refused",
        "log": "POST /owner/artifact/register", "quota": None, "pool": POOL_OWNER},
    ("POST", "/owner/idea"): {
        "caller": OWNER, "fields": ("owner_content",), "envelope": "exempt",
        "decision_field": "refused", "log": "POST /owner/idea",
        "quota": "ideas", "pool": POOL_OWNER},
    ("POST", "/owner/cases"): {
        "caller": OWNER, "fields": (), "envelope": "exempt",
        "decision_field": "refused", "log": "POST /owner/cases",
        "quota": None, "pool": POOL_OWNER},
    ("POST", "/owner/decide"): {
        "caller": OWNER, "fields": ("case_id", "decision"), "envelope": "exempt",
        "decision_field": "allowed", "log": "POST /owner/decide",
        "quota": "decisions", "pool": POOL_OWNER},
    ("POST", "/owner/reconcile"): {
        "caller": OWNER, "fields": ("action_request_id", "outcome", "note"),
        "envelope": "exempt", "decision_field": "refused",
        "log": "POST /owner/reconcile", "quota": None, "pool": POOL_OWNER},
    ("POST", "/owner/revoke"): {
        "caller": OWNER, "fields": ("capability", "action_request_id", "reason"),
        "envelope": "exempt", "decision_field": "refused",
        "log": "POST /owner/revoke", "quota": None, "pool": POOL_OWNER},
    ("POST", "/poc1/review-case"): {
        "caller": PROVIDER,
        "fields": ("registration_ref", "task_id", "transition", "artifact_digest",
                   "target_role", "submission_epoch", "envelope"),
        "envelope": "required", "decision_field": "refused",
        "log": "POST /poc1/review-case", "quota": "cases", "pool": POOL_GENERAL},
    ("POST", "/poc1/verify-decision"): {
        "caller": PROVIDER, "fields": ("token",), "envelope": "exempt",
        "decision_field": "refused", "log": "POST /poc1/verify-decision",
        "quota": None, "pool": POOL_GENERAL},
    ("POST", "/poc1/reconcile"): {
        "caller": PROVIDER, "fields": ("capability", "action_request_id"),
        "envelope": "exempt", "decision_field": "refused",
        "log": "POST /poc1/reconcile", "quota": None, "pool": POOL_GENERAL},
    ("POST", "/poc1/receipt"): {
        "caller": PROVIDER,
        "fields": ("action_request_id", "case_id", "provider_status",
                   "provider_message", "destination_digest_claimed",
                   "provider_metrics"),
        "envelope": "exempt", "decision_field": "refused",
        "log": "POST /poc1/receipt", "quota": "receipts", "pool": POOL_GENERAL},
    ("POST", "/poc1/refusal"): {
        "caller": PROVIDER,
        "fields": ("action_request_id", "case_id", "refusal_code", "refusal_message"),
        "envelope": "exempt", "decision_field": "refused",
        "log": "POST /poc1/refusal", "quota": "receipts", "pool": POOL_GENERAL},
    ("POST", "/relay/deliver"): {
        "caller": PROVIDER,
        "fields": ("capability", "action_request_id", "case_id", "payload",
                   "destination_digest_claimed"),
        "envelope": "exempt", "decision_field": "refused",
        "log": "POST /relay/deliver", "quota": "attempts", "pool": POOL_GENERAL,
        "capability_required": True},
    ("POST", "/poc2/triage"): {
        "caller": PROVIDER, "fields": ("idea_ref", "owner_content", "external_items"),
        "envelope": "conditional", "decision_field": "refused",
        "log": "POST /poc2/triage", "quota": "ideas", "pool": POOL_GENERAL},
    ("POST", "/poc3/run-started"): {
        "caller": PROVIDER,
        "fields": ("schedule_id", "occurrence", "provider_correlation_id"),
        "envelope": "exempt", "decision_field": "refused",
        "log": "POST /poc3/run-started", "quota": "runs", "pool": POOL_GENERAL},
    ("POST", "/poc3/checkpoint"): {
        "caller": PROVIDER, "fields": ("run_id", "stage"), "envelope": "exempt",
        "decision_field": "refused", "log": "POST /poc3/checkpoint",
        "quota": "checkpoints", "pool": POOL_GENERAL},
    ("POST", "/poc3/reconcile"): {
        "caller": PROVIDER, "fields": ("run_id",), "envelope": "exempt",
        "decision_field": "refused", "log": "POST /poc3/reconcile",
        "quota": None, "pool": POOL_GENERAL},
    ("POST", "/poc3/receipt"): {
        "caller": PROVIDER, "fields": ("run_id", "occurrence", "provider_status"),
        "envelope": "exempt", "decision_field": "refused",
        "log": "POST /poc3/receipt", "quota": "receipts", "pool": POOL_GENERAL},
    ("POST", "/stage/deliver"): {
        "caller": PROVIDER, "fields": ("run_id",), "envelope": "exempt",
        "decision_field": "refused", "log": "POST /stage/deliver",
        "quota": "stage-attempts", "pool": POOL_GENERAL},
}

PROVIDER_DECISION_FIELDS = frozenset((
    "decision", "approved", "approval", "authorized", "owner_decision",
    "approval_result", "verdict", "approve", "outcome_decision"))

# --------------------------------------------------------------------------
# A.8 — redaction, corrected in both directions
# --------------------------------------------------------------------------
SECRET_KEY_SEGMENTS = frozenset((
    "password", "passwd", "secret", "token", "credential", "credentials",
    "authorization", "auth", "cookie", "signature", "bearer", "apikey", "key",
    "capability"))
# A.8 enumerates this allowlist exactly, and the enumeration is the whole of it.
# An entry that is not either named by A.8 or load-bearing against
# SECRET_KEY_SEGMENTS is a dead table row, so nothing else is carried here: a
# name with no secret segment already survives redaction and needs no entry.
# `test_allowlist_is_exactly_a8` holds this shut.
NON_SECRET_FIELD_NAMES = frozenset((
    # D-EC_ REQUIRED names — the harness scores on these and must see them
    "receipt_id", "subject_ref", "executed_at", "occurrence", "schedule_version",
    "purpose", "authority_id", "authority_version", "content_hash",
    "action_request_id", "action_class", "scope", "policy_version", "risk_class",
    "idempotency_key", "side_effect_status",
    # named provider measurements
    "tokens_used", "task_count", "execution_count", "session_id"))

SECRET_PATTERNS = [
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "aws-key"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}"), "github-token"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}"), "openai-style-key"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "slack-token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private-key"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]+"), "jwt"),
    (re.compile(r"(?i)\b(password|passwd|client_secret|api_key|apikey)"
                r"\s*[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9!@#$%^&*_\-]{6,})"),
     "assigned-credential"),
    (re.compile(r"(?i)\bauthorization\s*:\s*(bearer|basic)\s+\S+"), "auth-header"),
]


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _segments(name) -> list:
    return [s for s in re.split(r"[^A-Za-z0-9]+", str(name).lower()) if s]


def _is_secret_key(name) -> bool:
    low = str(name).lower()
    if low in NON_SECRET_FIELD_NAMES:
        return False
    return any(s in SECRET_KEY_SEGMENTS for s in _segments(name))


class SecretIndex:
    """Live secrets, for exact-value scrubbing including substrings (A.8).

    `MAX_ACTIVE_SECRETS` is a ceiling on how many secrets may be LIVE, never on
    the scan: every live secret is always scanned. Minting past the ceiling is
    refused rather than silently dropping a value out of the index — a secret
    outside the index would not redact, which is the failure this bounds.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._values = set()
        self._reserved = 0

    def add(self, value: str) -> bool:
        if not isinstance(value, str) or not value:
            return True
        with self._lock:
            if value in self._values:
                return True
            if len(self._values) + self._reserved >= MAX_ACTIVE_SECRETS:
                return False
            self._values.add(value)
            return True

    # SEC-R3-03 — reserve admission BEFORE the committed record is written.
    # R3 wrote `capability-mint committed` and then called `add()`, which could
    # refuse; the capability was rolled back but the committed record stayed,
    # so the evidence asserted an authorization that never became effective.
    # Reserving first means the only way past this point is one that can finish.
    def reserve(self) -> bool:
        with self._lock:
            if len(self._values) + self._reserved >= MAX_ACTIVE_SECRETS:
                return False
            self._reserved += 1
            return True

    def commit_reserved(self, value: str):
        with self._lock:
            self._reserved = max(0, self._reserved - 1)
            if isinstance(value, str) and value:
                self._values.add(value)

    def release_reserved(self):
        with self._lock:
            self._reserved = max(0, self._reserved - 1)

    def full(self) -> bool:
        with self._lock:
            return len(self._values) + self._reserved >= MAX_ACTIVE_SECRETS

    def discard(self, value: str):
        with self._lock:
            self._values.discard(value)

    def snapshot(self) -> tuple:
        with self._lock:
            return tuple(self._values)

    def count(self) -> int:
        with self._lock:
            return len(self._values)

    def scrub(self, text: str) -> tuple:
        hit = False
        for live in self.snapshot():
            if live and len(live) <= len(text) and live in text:
                idx = text.find(live)
                if hmac.compare_digest(text[idx:idx + len(live)], live):
                    text = text.replace(live, "[REDACTED:live-secret]")
                    hit = True
        return text, hit


SECRETS = SecretIndex()
# A.8 — per-process descriptor key, random, never persisted. Per-process keying
# prevents precomputation and cross-run correlation of withheld values.
DESCRIPTOR_KEY = secrets.token_bytes(32)


def descriptor(name, value, why: str) -> dict:
    raw = canonical(value)
    encoded = raw.encode("utf-8", "replace")
    mac = hmac.new(DESCRIPTOR_KEY, encoded, hashlib.sha256).hexdigest()[:32]
    return {"__withheld__": why, "name": str(name)[:128],
            "type": type(value).__name__, "bytes": len(encoded), "hmac": mac}


class Disclose:
    """A value the service itself minted, for the one recipient the protocol
    entitles to it, in THIS response only.

    Redaction is unconditional for captures and logs. But the service has to be
    able to hand a provider the resume token and the execution capability it
    minted, or nothing downstream can run at all. Suppressing them in the
    response does not make the apparatus safer, it makes it inoperable — and
    silently, since the caller receives a well-formed body with a descriptor
    where the credential should be. (That is the R2 defect this closes; see the
    Delivery Record, DEF-R2-01.)

    The exemption is **identity-based, never key-name-based**: only a value the
    service wrapped at mint time is disclosed, and only on the response path.
    Provider-supplied material can never arrive as a `Disclose` — JSON has no
    such type — so a caller cannot name its way out of redaction. On every
    other path (`disclose=False`, the default, which is what `write_capture`
    and the log surface use) a `Disclose` reduces to a descriptor, so a stray
    one cannot leak a secret into evidence even by mistake.
    """

    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value

    def __repr__(self):                                  # never reveal by print
        return "<Disclose withheld>"


def redact(value, depth: int = 0, disclose: bool = False):
    if depth > MAX_REDACT_DEPTH:
        return {"__withheld__": "recursion-depth", "type": type(value).__name__}
    if isinstance(value, Disclose):
        return value.value if disclose \
            else descriptor("<disclosed>", value.value, "secret-key-name")
    if isinstance(value, str):
        out, _ = SECRETS.scrub(value)
        for rx, label in SECRET_PATTERNS:
            out = rx.sub("[REDACTED:%s]" % label, out)
        return out
    if isinstance(value, dict):
        clean = {}
        for k, v in list(value.items())[:MAX_OBJECT_FIELDS]:
            key, _ = SECRETS.scrub(str(k))
            if isinstance(v, Disclose) or not (
                    _is_secret_key(key) and v not in (None, "", [], {})):
                clean[key] = redact(v, depth + 1, disclose)
            else:
                clean[key] = descriptor(key, v, "secret-key-name")
        return clean
    if isinstance(value, list):
        return [redact(v, depth + 1, disclose) for v in value[:MAX_LIST_ITEMS]]
    return value


def contains_secret(value) -> list:
    blob = value if isinstance(value, str) else canonical(value)
    found = [label for rx, label in SECRET_PATTERNS if rx.search(blob)]
    if SECRETS.scrub(blob)[1]:
        found.append("live-secret")
    return found


class CaptureError(Exception):
    """A capture could not be committed. A.7: nothing commits after one."""


class CaptureQuarantine(Exception):
    """The capture failed AND its rollback could not be proven (SEC-R4-01).

    Deliberately NOT a subclass of `CaptureError`. Handlers catch `CaptureError`
    and report the ordinary "not effective" result, and reporting that while a
    success-named `committed` record may still be on disk is the exact authority
    contradiction this whole finding exists to eliminate — R5 displaced it into
    the recovery path by swallowing the cleanup failure with `except OSError:
    pass`. Because this is a separate type it passes through those handlers
    untouched and reaches dispatch, which fails the service closed instead.
    """

    def __init__(self, message, detail=None):
        super().__init__(message)
        self.detail = detail or {}


class QuotaError(Exception):
    def __init__(self, message, status=429):
        super().__init__(message)
        self.status = status


# --------------------------------------------------------------------------
# State
# --------------------------------------------------------------------------
class Store:
    def __init__(self, candidate: str = "unset"):
        self.lock = threading.RLock()
        self.candidate = candidate
        self.run_instance = "%s-%s" % (time.strftime("%Y%m%dT%H%M%S"),
                                       uuid.uuid4().hex[:8])
        self.owner_key = secrets.token_urlsafe(24)
        self.provider_key = secrets.token_urlsafe(24)
        SECRETS.add(self.owner_key)
        SECRETS.add(self.provider_key)
        self.base_url = None
        self.registrations = {}        # registration_ref -> record
        self.reg_by_identity = {}      # registration identity -> registration_ref
        self.ideas = {}                # idea_ref -> {content, digest}
        self.cases = {}
        self.by_identity = {}
        self.tokens = {}
        self.decisions = {}
        self.capabilities = {}         # capability -> binding (incl. status)
        self.cap_by_ar = {}            # action_request_id -> capability
        self.relay_receipts = {}
        self.relay_attempts = {}
        self.reattempts = {}           # action_request_id -> count
        self.stage_attempts = {}
        self.receipt_count = 0
        # SEC-R3-06: in-flight reservations. A global quota is checked against
        # `live + pending`, so a reservation cannot be double-spent; `pending`
        # returns to zero whether the transition commits or rolls back. The
        # LIVE counter is the route's own record store (`STORE.cases`,
        # `STORE.ideas`, ... , `receipt_count`) so that the counter which gates
        # a route is the counter that route actually increments.
        self.pending_quota = {}
        # SUBJECT-scoped reservations: (quota, subject) -> units held.
        self.subject_counts = {}
        self.runs = {}
        # (schedule_id, occurrence) -> run_id. §B: run identity is stub-minted,
        # so duplicate detection keys off the declaration, not a provider id.
        self.runs_by_declaration = {}
        self.captures = {POOL_GENERAL: 0, POOL_SECURITY: 0, POOL_OWNER: 0}
        self.uncaptured_refusals = 0   # bounded counter, aggregate only
        # SEC-R4-01 — storage integrity registers.
        #   `storage_quarantine` is HARD: a rollback that could not be proven,
        #   so a success-named record may survive on disk for a transition the
        #   service treats as ineffective. While it is non-empty the service
        #   refuses further authority transitions and requires explicit
        #   recovery, because it can no longer tell the truth about its own
        #   evidence.
        #   `storage_anomalies` is SOFT: something went wrong that does NOT
        #   contradict the record — e.g. a directory-fd close error after the
        #   publication fsync already made the record durable. Recorded and
        #   surfaced, never silently dropped, but it blocks nothing.
        self.storage_quarantine = []
        self.storage_anomalies = []
        # R7 item 5 — the quarantine must outlive the process that raised it.
        # A fresh process starts with an empty register, so before it answers
        # anything it has to look on disk for a marker left by a previous one.
        # The scan cannot run here: callers set `Handler.data_dir` AFTER
        # constructing the Store, so at this point the data directory is not
        # yet known. It runs lazily on the first dispatch instead.
        #
        # Its own lock, never held while acquiring another, so the documented
        # total order (`STORE.lock` -> `SECRETS._lock`) is untouched and
        # `GET /health` — which is deliberately lock-free — cannot be blocked
        # behind a POST that holds `STORE.lock` for its whole duration.
        self.quarantine_scanned = False
        self.quarantine_scan_lock = threading.Lock()
        self.transitions = []          # transition_id -> phase log (in-memory mirror)

    @staticmethod
    def digest(raw: str) -> str:
        return sha256_hex(raw)

    def mint_token(self, case_id: str):
        if len(self.tokens) >= MAX_TOKENS:
            raise QuotaError("token ceiling reached")
        raw = secrets.token_urlsafe(32)
        if not SECRETS.add(raw):
            raise QuotaError("live-secret ceiling reached; refusing to mint a "
                             "token that could not be redacted")
        with self.lock:
            self.tokens[self.digest(raw)] = {"case_id": case_id, "consumed": False}
        return raw

    def find_token(self, raw: str):
        if not isinstance(raw, str) or not raw.strip():
            return None, "no resume token was presented"
        rec = self.tokens.get(self.digest(raw))
        if rec is None:
            return None, "resume token is not one this service minted"
        if rec["consumed"]:
            return None, "resume token has already been used — replay refused"
        return rec, None

    def claim_token(self, raw: str):
        """SEC-R3-01 — read-valid and mark-consumed in ONE step.

        The caller holds the global lock, so this is atomic with respect to
        every other request. A second concurrent verify sees `consumed` already
        set and is refused, which is what makes "one resume token ⇒ one
        ActionRequest ⇒ one capability" true rather than merely usual. R3 read
        the token here and consumed it several steps later, and both racers
        passed the read.
        """
        rec, why = self.find_token(raw)
        if rec is None:
            return None, why
        rec["consumed"] = True
        return rec, None

    def unclaim_token(self, raw: str):
        """Give a claimed token back when its transition did not become
        effective. Without this, a rolled-back mint would burn the token."""
        rec = self.tokens.get(self.digest(raw))
        if rec is not None:
            rec["consumed"] = False

    def retract_token(self, raw: str):
        """Remove a token whose transition never became effective, and release
        its secret-index slot — nothing should hold either."""
        if not isinstance(raw, str):
            return
        self.tokens.pop(self.digest(raw), None)
        SECRETS.discard(raw)


STORE = Store()


# --------------------------------------------------------------------------
# A.7 — prepared → committed evidence, and capture writing
# --------------------------------------------------------------------------
SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


def _pool_for(route: str, refusal: bool, owner_authenticated: bool = False) -> str:
    """A.8 — reserved-owner is for the owner surface, and the owner surface is
    defined by WHO AUTHENTICATED, not by which path was requested.

    R3 chose the pool from the route's policy alone, so an unauthenticated
    caller POSTing to `/owner/decide` with a wrong key produced a refusal
    capture drawn from `reserved-owner`. Anyone can reach that path, which makes
    it a provider-reachable event, and A.8 says no provider-reachable event may
    draw from that pool *under any condition* — an attacker could have filled
    the pool the owner's own decisions depend on. The R3 self-test missed it
    because it asserted reserved-owner captures came from owner ROUTES, which
    was true and beside the point; the branch-specific oracle caught it.
    """
    policy = ROUTE_POLICY.get(("POST", route)) or ROUTE_POLICY.get(("GET", route))
    if policy and policy["caller"] == OWNER and owner_authenticated:
        return POOL_OWNER
    return POOL_SECURITY if refusal else POOL_GENERAL


def _reserve_pool(pool: str):
    """A.8 exhaustion rules. No provider-reachable event may draw from
    reserved-owner under any condition — enforced by `_pool_for`, which only
    ever returns it for an owner-surface route.

    SEC-R3-05: this is a RESERVATION. The unit is consumed only once the
    capture has been durably published; every failure path releases it via
    `_release_pool`, so a failed write leaves no consumed quota behind."""
    with STORE.lock:
        if STORE.captures[pool] < POOL_QUOTA[pool]:
            STORE.captures[pool] += 1
            return True
        return False


def _release_pool(pool: str):
    with STORE.lock:
        if pool in STORE.captures:
            STORE.captures[pool] = max(0, STORE.captures[pool] - 1)



# --------------------------------------------------------------------------
# R7 item 5 — the restart posture: a PERSISTED QUARANTINE MARKER.
#
# `42_` gave the quarantine a register in memory only. A restart with the same
# candidate and the same data directory therefore came up with
# `storage_quarantine == []` and accepted authority transitions again, while the
# ambiguous success-named record was still sitting on disk. Restarting a process
# is not reconciliation, and the gap made the fail-closed guarantee expire the
# moment anyone did the most ordinary operational thing there is.
#
# Of the two options `46_` offers, this build takes the PERSISTED MARKER rather
# than binding the runbook, because the quarantine is a statement about the
# state of a DIRECTORY, not about the state of a process: the ambiguous record
# survives the restart, so the thing that says "this directory is ambiguous"
# must survive it too, and must be found by whoever next opens that directory —
# a different machine, a different operator, a start command nobody read. A
# runbook binding only holds for people who follow the runbook, and it is
# exactly the operator improvising a restart at 2am whom this needs to stop.
#
# The marker lives BESIDE `captures/`, never inside it. A file inside the
# capture tree is a file every reader counts as evidence, and this file is not
# evidence of a transition — it is a statement that the evidence there cannot be
# trusted. Filing it as a capture would make the register lie in a second way.
#
# There is deliberately NO in-service path that clears it. Reconciliation means
# an operator inspecting the ambiguous records and then removing the marker file
# from the filesystem; requiring filesystem access is what makes it explicit. A
# "clear the quarantine" endpoint or flag would be a production-reachable
# disable path for the control, which is the defect class this program has
# already had to remove once.
# --------------------------------------------------------------------------
QUARANTINE_DIRNAME = "storage_quarantine"
QUARANTINE_PREFIX = "quarantine-"


def _quarantine_root(data_dir: str = None):
    """`<data_dir>/storage_quarantine/<candidate>/`, or None if unnameable."""
    base = data_dir or Handler.data_dir
    candidate = str(STORE.candidate)
    if not SAFE_NAME.match(candidate) or candidate in (".", ".."):
        return None
    return os.path.abspath(os.path.join(base, QUARANTINE_DIRNAME, candidate))


def _persist_quarantine(detail: dict, data_dir: str = None):
    """Write the marker a restarted process has to find.

    Best-effort BY CONSTRUCTION, and it says so rather than pretending
    otherwise: this only ever runs on a path where the filesystem has already
    failed, so the write that records the failure can fail too. It therefore
    cannot raise — the caller is about to quarantine the service, and losing
    that because the marker could not be written would be strictly worse than
    an unpersisted marker. What it does instead is record on the incident
    whether the marker landed, so `/health` and the 503 body tell an operator
    whether a restart will still be stopped, instead of assuming it.

    No temp-and-rename: a partial marker is still a marker. Presence is the
    signal, and the startup scan treats an unreadable file as an incident
    rather than as absence, so there is nothing for atomicity to protect.
    """
    root = _quarantine_root(data_dir)
    if root is None:
        detail["marker_persisted"] = False
        detail["marker_error"] = "candidate name is not path-safe; no marker written"
        return
    path = os.path.join(root, "%s%s-%s.json"
                        % (QUARANTINE_PREFIX, STORE.run_instance,
                           uuid.uuid4().hex[:8]))
    marker = {
        "synthetic": True,
        "produced_by": "stub_server.py (%s)" % THROWAWAY,
        "kind": "storage-quarantine",
        "candidate": STORE.candidate,
        "run_instance": STORE.run_instance,
        "raised_at": time.time(),
        "requires": ("explicit operator reconciliation: inspect the records "
                     "named below, decide what the evidence on disk actually "
                     "says, then delete THIS FILE. Until it is gone every "
                     "process using this data directory refuses authority "
                     "transitions. Restarting the service does not clear it."),
        "incident": detail,
    }
    try:
        os.makedirs(root, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(marker, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        dfd = os.open(root, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except BaseException as exc:                                  # noqa: BLE001
        detail["marker_persisted"] = False
        detail["marker_path"] = path
        detail["marker_error"] = "%s: %s" % (type(exc).__name__, exc)
        return
    detail["marker_persisted"] = True
    detail["marker_path"] = path


def _scan_quarantine_markers(data_dir: str = None) -> list:
    """Everything a previous process left behind for this candidate.

    Fails closed on every ambiguity: a marker that cannot be parsed, or a
    directory that cannot be listed, both COUNT AS A QUARANTINE. "I could not
    tell whether this directory is quarantined" is not the same as "it is not",
    and only one of those two readings is safe.
    """
    root = _quarantine_root(data_dir)
    if root is None:
        return []
    try:
        names = sorted(os.listdir(root))
    except FileNotFoundError:
        return []                       # never quarantined; nothing to recover
    except OSError as exc:
        return [{"route": "startup", "step": "quarantine-marker-scan",
                 "problems": ["quarantine directory could not be listed (%s)"
                              % errno.errorcode.get(exc.errno, exc.errno)],
                 "recovered_from_marker": root}]
    found = []
    for name in names:
        if not (name.startswith(QUARANTINE_PREFIX) and name.endswith(".json")):
            continue
        path = os.path.join(root, name)
        try:
            with open(path, encoding="utf-8") as fh:
                marker = json.load(fh)
        except (OSError, ValueError) as exc:
            marker = None
        if isinstance(marker, dict) and isinstance(marker.get("incident"), dict):
            incident = dict(marker["incident"])
            incident["raised_by_run_instance"] = marker.get("run_instance")
        else:
            incident = {"route": "startup", "step": "quarantine-marker-scan",
                        "problems": ["quarantine marker present but unreadable; "
                                     "its presence is the signal"]}
        incident["recovered_from_marker"] = path
        # The embedded copy predates its own persistence — `_persist_quarantine`
        # stamps that on the live incident AFTER writing, so a marker cannot
        # claim to have been written by quoting itself. Reading it back is the
        # proof, so the recovered incident carries the stamp instead.
        incident["marker_persisted"] = True
        incident["marker_path"] = path
        incident["reconcile_by"] = ("inspect the records named here, then delete "
                                    "this marker file; restarting does not clear it")
        found.append(incident)
    return found


def _ensure_quarantine_scanned(data_dir: str = None):
    """Run the marker scan exactly once per process, on the first request.

    Deliberately not in `Store.__init__`: `Handler.data_dir` is assigned after
    the Store is built, so at construction time there is no directory to scan.
    Deliberately not gated on `STORE.lock`: `GET /health` must stay servable
    while a POST holds that lock for its whole duration (A.8).
    """
    with STORE.quarantine_scan_lock:
        if STORE.quarantine_scanned:
            return
        STORE.quarantine_scanned = True
        try:
            recovered = _scan_quarantine_markers(data_dir)
        except BaseException as exc:                              # noqa: BLE001
            recovered = [{"route": "startup", "step": "quarantine-marker-scan",
                          "problems": ["quarantine marker scan failed (%s: %s)"
                                       % (type(exc).__name__, exc)]}]
        STORE.storage_quarantine.extend(recovered)


def _absorb_post_durable(route: str, step: str, exc: BaseException):
    """R7 item 1 — a durably committed capture is committed.

    Once the publication directory fsync has returned, the record is on disk and
    will still be there after a power cut. The only thing left to do is close a
    directory descriptor. R6 nevertheless let a NON-`OSError` out of that tail —
    the inner handler catches `OSError` only — into `except BaseException`,
    which turned it into an ordinary `CaptureError`; `h_owner_artifact_register`
    then tore the registration back out of live state and answered "not
    effective" beside a durable `committed` record reading `REGISTERED`. That is
    SEC-R4-01 for the third time: a caller told a transition did not happen while
    this service's own evidence says it did.

    So after publication no exception may become an ordinary capture failure.
    It is recorded as a soft anomaly — the same treatment item 5 already gave a
    close error after a successful fsync — and the capture returns its path.

    **Judgement call, stated rather than buried:** this absorbs
    `KeyboardInterrupt` and `SystemExit` too, at this one point. Re-raising them
    would satisfy the letter of item 1 (they are not `CaptureError`, and the
    callers' `except (CaptureError, QuotaError)` would not roll anything back)
    while leaving the transition stranded mid-commit with durable evidence and
    no in-memory record — a worse contradiction than the one being fixed, and it
    would abort the verifier's own probe rather than answer it. The scope is one
    `os.close` on a directory fd, after durability; there is no other work in
    the tail for an interrupt to be protecting.
    """
    STORE.storage_anomalies.append(
        {"kind": "post-durable-capture-tail-failure",
         "route": route, "step": step,
         "exception": type(exc).__name__,
         "detail": str(exc)[:200],
         "note": "record already durable; capture stands"})


def _rollback_capture(pool, linked_path, tmp, root, route, step, data_dir=None):
    """Undo a capture that never became durable — provably, or quarantine.

    Raises `CaptureQuarantine` only when there is something on disk whose
    removal could NOT be established. The caller must not convert that into an
    ordinary capture failure: while it is raised, a success-named record may
    still exist for a transition nothing else believes happened.

    R7 item 3 — **nothing created, nothing to prove.** R6 ran the whole proof
    unconditionally, so a failure before any name existed (`os.makedirs`
    failing, say) still tried to fsync a directory that was never made, reported
    "rollback directory fsync failed (ENOENT)" and hard-quarantined the service
    with `surviving_final_path: null` and `surviving_temp_path: null`. Nothing
    survived, because nothing was ever created. That is an ordinary capture
    failure, and quarantining on it is an availability defect — in an owner
    session it locks the stub up for no reason at all.
    """
    if not linked_path and not tmp:
        # No artifact ever existed. There is no ambiguity to preserve, so the
        # reservation goes back and the caller reports the ordinary failure.
        _release_pool(pool)
        return

    problems = []
    # The final path first: it is the one a reader would count as durable
    # evidence, so if only one removal can succeed that is the one that matters.
    for stale, what in ((linked_path, "final-link"), (tmp, "temp")):
        if not stale:
            continue
        try:
            os.unlink(stale)
        except FileNotFoundError:
            pass                      # already gone; that is a proven removal
        except OSError as exc:
            problems.append("%s unlink failed (%s)"
                            % (what, errno.errorcode.get(exc.errno, exc.errno)))

    rollback_durable = False
    if not problems:
        # The removal itself has to be durable, or a crash could resurrect the
        # record the service has just told its caller does not exist.
        #
        # R7 item 4 — the rollback gets the same TRUE DURABILITY BOUNDARY the
        # publication path already has. The removal is durable the instant this
        # fsync returns; a later failure to close the descriptor cannot undo
        # that, so it is a recorded soft anomaly and never a hard quarantine.
        # R6 had the fsync and the close inside one `try`, so a close error
        # quarantined a rollback that had already been made durable.
        try:
            dfd = os.open(root, os.O_RDONLY)
        except OSError as exc:
            problems.append("rollback directory open failed (%s)"
                            % errno.errorcode.get(exc.errno, exc.errno))
        else:
            try:
                os.fsync(dfd)
                rollback_durable = True
            except OSError as exc:
                problems.append("rollback directory fsync failed (%s)"
                                % errno.errorcode.get(exc.errno, exc.errno))
            finally:
                try:
                    os.close(dfd)
                except OSError as exc:
                    if rollback_durable:
                        STORE.storage_anomalies.append(
                            {"kind": "rollback-directory-close-after-durable-fsync",
                             "route": route, "step": step,
                             "errno": errno.errorcode.get(exc.errno, exc.errno)})
                    else:
                        problems.append("rollback directory close failed (%s)"
                                        % errno.errorcode.get(exc.errno, exc.errno))

    if problems:
        detail = {"route": route, "step": step,
                  "surviving_final_path": linked_path,
                  "surviving_temp_path": tmp,
                  "problems": problems,
                  "quota_pool_retained": pool}
        with STORE.lock:
            STORE.storage_quarantine.append(detail)
        # Item 5 — and make it survive this process. `detail` is the same object
        # that is already on the register, so whether the marker landed shows up
        # in `/health` and in the 503 body without a second lookup.
        _persist_quarantine(detail, data_dir)
        # The quota unit is deliberately NOT released: the reservation is the
        # only remaining accounting for a record that may still exist.
        raise CaptureQuarantine(
            "capture rollback could not be established, so this service can no "
            "longer state whether the evidence on disk describes an effective "
            "transition; it is quarantined and fails closed until recovered: %s"
            % "; ".join(problems), detail)
    _release_pool(pool)


def write_capture(route: str, poc: str, step: str, minted: dict = None,
                  authored_by: str = "stub", refusal: bool = False,
                  data_dir: str = None, provider: dict = None,
                  owner_authenticated: bool = None) -> str:
    """A.7 — the top level is reserved for stub-minted fields; provider-supplied
    content lives under a single reserved provenance key.

    Provenance is **declared by the caller**, not inferred: `minted` is what this
    service established, `provider` is what a caller sent. An earlier shape
    guessed provenance from a list of known field names, which meant every newly
    minted field was silently filed as provider-supplied — a capture that
    mislabels its own authorship is worse than one that omits the field, because
    it reads as corroborated when it is not.

    Within `provider`, §B applies: a field the route policy lists keeps its
    (redacted) value; anything else is reduced to a descriptor.
    """
    data_dir = data_dir or Handler.data_dir
    if owner_authenticated is None:
        # Every owner-surface caller reaches a handler only after dispatch has
        # verified the owner key, so `authored_by` is a faithful proxy there.
        # The one path that is NOT authenticated — the auth refusal itself —
        # passes the flag explicitly as False.
        owner_authenticated = authored_by == "owner-surface"
    candidate = STORE.candidate
    for part in (candidate, poc, step):
        if not SAFE_NAME.match(str(part)) or part in (".", ".."):
            raise CaptureError("unsafe capture path component %r" % part)

    pool = _pool_for(route, refusal, owner_authenticated=owner_authenticated)
    if not _reserve_pool(pool):
        if pool == POOL_OWNER:
            raise CaptureError("reserved-owner capture pool exhausted (507)")
        if pool == POOL_GENERAL:
            raise QuotaError("general capture pool exhausted", 429)
        with STORE.lock:
            STORE.uncaptured_refusals += 1
        raise CaptureError("security-refusal pool exhausted; counted in aggregate")

    root = os.path.abspath(os.path.join(data_dir, "captures", candidate, poc))
    expected = os.path.abspath(os.path.join(data_dir, "captures"))
    if not root.startswith(expected + os.sep):
        raise CaptureError("capture path escapes the captures directory")

    policy = ROUTE_POLICY.get(("POST", route)) or ROUTE_POLICY.get(("GET", route))
    allowed = policy["fields"] if policy else ()
    supplied = {}
    for k, v in (provider or {}).items():
        supplied[k] = v if k in allowed \
            else descriptor(k, v, "not-allowlisted-for-this-route")

    body = {
        "synthetic": True,
        "produced_by": "stub_server.py (%s)" % THROWAWAY,
        "candidate": candidate,
        "run_instance": STORE.run_instance,
        "route": route,
        "authored_by": authored_by,
        "poc": poc,
        "step": step,
        "pool": pool,
        "recorded_at": time.time(),
        "recorded_at_note": ("stub-minted local wall clock; NO clock authority "
                             "(13B_ leaves clock discipline to the real wrapper)"),
        "fields": redact(minted or {}),
    }
    if supplied:
        body["provider_supplied"] = redact(supplied)

    # SEC-R3-05 — crash-atomic publication.
    #
    # R3 pre-created the FINAL path with O_EXCL to reserve the name, then wrote
    # a temp file beside it and renamed over it. A failure between those two
    # steps left a zero-byte final file that every reader counts as a capture,
    # and the pool unit had already been consumed. Both are corrected here:
    #
    #   * nothing is created at the final path until the content is durable;
    #   * the temp file is created with O_EXCL under a unique name;
    #   * write → flush → fsync the file → link onto a final path that did not
    #     exist → unlink the temp → fsync the directory;
    #   * any failure removes the temp artifact and RELEASES the pool unit.
    #
    # `os.link` rather than `os.replace` is deliberate: rename silently
    # overwrites, so it cannot express "a final path that did not previously
    # exist". Link fails with FileExistsError instead, which is the guarantee
    # the finding asks for, and it is equally atomic on one filesystem.
    # SEC-R4-01 (R5) — publication is not "published" until the DIRECTORY FSYNC
    # has succeeded.
    #
    # R4 set `published = True` immediately after `os.link`, before the
    # directory fsync. A failure at the directory open or fsync then left the
    # `finally` believing the capture had landed: it kept the reserved quota
    # unit and left the final file on disk, while the caller rolled the
    # transition out of live state. The surviving record read `phase:
    # committed`, `outcome: committed`, `final_status: REGISTERED` — durable
    # evidence asserting authority for a transition that never became
    # effective, which is the exact failure A.7 exists to prevent.
    #
    # Three things are tracked separately now, because "the link succeeded" and
    # "the record is durable" are different facts and conflating them is what
    # produced the defect:
    #   tmp          the temp file, until it is unlinked
    #   linked_path  the final path, from the moment the link succeeds
    #   published    ONLY after the directory fsync returns
    #
    # Any failure after the link therefore removes the final path as well as
    # the temp, and releases the pool unit — including reserved-owner. That
    # also covers the temp-unlink failure, which in R4 cleaned only the temp
    # name and left the final hard link behind.
    tmp = None
    linked_path = None
    published = False
    try:
        os.makedirs(root, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".%s-" % step, suffix=".tmp", dir=root)
        os.close(fd)      # mkstemp already created it exclusively
        # Deliberately `open()` and not `os.fdopen()`: the reviewer's
        # capture_atomicity_probe injects its fault at `builtins.open`, and an
        # implementation that routed around the injection would evade the test
        # rather than pass it.
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(body, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        seq = 0
        while True:
            seq += 1
            if seq > 9999:
                raise CaptureError("cannot allocate a capture filename")
            path = os.path.join(root, "%s-%s-%04d.json"
                                % (step, STORE.run_instance, seq))
            try:
                os.link(tmp, path)      # fails if the final path already exists
                linked_path = path
                break
            except FileExistsError:
                continue
        os.unlink(tmp)
        tmp = None
        dfd = os.open(root, os.O_RDONLY)
        try:
            os.fsync(dfd)
            # SEC-R4-01 item 4 — THE TRUE DURABILITY BOUNDARY. The record is
            # durable the instant this fsync returns. R5 set the flag after the
            # `finally` had also closed the fd, so a close error turned an
            # already-durable committed record into an ordinary rollback claim.
            published = True
        finally:
            try:
                os.close(dfd)
            except OSError as exc:
                # Item 5 — a close failure AFTER a successful fsync cannot undo
                # durability, so it must not roll back live state. It is not
                # swallowed either: it is recorded as a soft anomaly, which
                # blocks nothing and is surfaced on /health.
                STORE.storage_anomalies.append(
                    {"kind": "directory-close-after-durable-fsync",
                     "route": route, "step": step,
                     "errno": errno.errorcode.get(exc.errno, exc.errno)})
    # R7 item 1 — EVERY conversion below is now gated on `published`.
    #
    # Each clause used to fire unconditionally, so an exception raised after the
    # publication fsync had already made the record durable still came out as an
    # ordinary `CaptureError`. `_absorb_post_durable` explains why that is the
    # same authority contradiction as SEC-R4-01 and why absorption is the answer;
    # the point here is that the test is on the DURABILITY FLAG, not on the
    # exception type, because the type never was what distinguished the two
    # cases.
    except (CaptureError, QuotaError) as exc:
        if not published:
            raise
        _absorb_post_durable(route, step, exc)
    except OSError as exc:
        if not published:
            raise CaptureError("capture write failed: %s"
                               % errno.errorcode.get(exc.errno, exc.errno))
        _absorb_post_durable(route, step, exc)
    except BaseException as exc:
        # Before publication, anything that stops the evidence landing is, from
        # the transition's point of view, the same event: the capture failed. It
        # is reported as such so the caller gets a structured refusal instead of
        # an internal error, and so the caller's rollback path runs.
        if not published:
            raise CaptureError("capture write failed: %s" % type(exc).__name__)
        _absorb_post_durable(route, step, exc)
    finally:
        # SEC-R4-01 items 1-3 — the rollback must be PROVEN before the quota is
        # released and before the caller is allowed to say "not effective".
        #
        # R5 released the unit first and then attempted the unlinks inside a
        # bare `except OSError: pass`. If removing the final link failed, the
        # success-named `committed` record survived on disk while the service
        # returned the ordinary ineffective response — the same authority
        # contradiction SEC-R4-01 was opened to eliminate, moved one level down
        # into the recovery path.
        #
        # Now: remove the final link and any temp, make the REMOVAL durable
        # with its own directory fsync, and only then release the reservation.
        # If any of that cannot be established, the service quarantines instead
        # of claiming anything.
        if not published:
            _rollback_capture(pool, linked_path, tmp, root, route, step, data_dir)
    return path


class Transition:
    """A.7 — an authority-bearing transition. Effective only once `committed`
    has durably landed; the in-memory change is provisional until then."""

    def __init__(self, route, poc, name, subject, prior, intended,
                 authored_by="stub", links=None):
        self.id = "txn-" + secrets.token_hex(8)
        self.route, self.poc, self.name = route, poc, name
        self.subject, self.prior, self.intended = subject, prior, intended
        self.authored_by = authored_by
        self.links = links or {}

    def prepare(self):
        write_capture(self.route, self.poc, "prepared-" + self.name,
                      {"transition_id": self.id, "transition": self.name,
                       "prior_status": self.prior, "intended_status": self.intended,
                       "phase": "prepared", "links": self.links,
                       "outcome": "prepared"},
                      authored_by=self.authored_by)

    def commit(self, final_status=None):
        write_capture(self.route, self.poc, "committed-" + self.name,
                      {"transition_id": self.id, "phase": "committed",
                       "final_status": final_status or self.intended,
                       "outcome": "committed"},
                      authored_by=self.authored_by)
        with STORE.lock:
            STORE.transitions.append({"transition_id": self.id, "name": self.name,
                                      "subject": self.subject,
                                      "final_status": final_status or self.intended})


# --------------------------------------------------------------------------
# Boundary checks
# --------------------------------------------------------------------------
def _envelope_obj(payload: dict) -> dict:
    env = payload.get("envelope")
    return env if isinstance(env, dict) else {}


def _partition_ok(env: dict) -> tuple:
    part = env.get("partition")
    if part is not None and not isinstance(part, str):
        return False, "partition must be a string"
    if isinstance(part, str):
        part = part.strip()
    if part is None:
        return False, ("no partition declared; this round is %s-only"
                       % ALLOWED_PARTITION)
    if part.lower() != ALLOWED_PARTITION:
        return False, ("partition %r declared; no Personal-partition route exists "
                       "in this service and no non-business partition is accepted" % part)
    return True, None


def _envelope_ok(payload: dict) -> tuple:
    env = _envelope_obj(payload)
    if not env:
        return False, "no external-untrusted envelope on the payload"
    if env.get("trust") != REQUIRED_TRUST:
        return False, ("envelope declares trust %r; inbound external content must "
                       "carry %r before classification" % (env.get("trust"), REQUIRED_TRUST))
    return _partition_ok(env)


def _no_provider_decision(payload: dict) -> tuple:
    present = sorted(f for f in payload if str(f).lower() in PROVIDER_DECISION_FIELDS)
    if present:
        return False, ("request carries %d decision-shaped field(s) — an approval "
                       "outcome may not arrive from the provider side" % len(present))
    return True, None


def _structural_ok(value, depth=0) -> tuple:
    """A.8 structural bounds, checked BEFORE handler dispatch."""
    if depth > MAX_REDACT_DEPTH:
        return False, "nesting deeper than MAX_REDACT_DEPTH"
    if isinstance(value, str):
        if len(value.encode("utf-8", "replace")) > MAX_STRING_BYTES:
            return False, "string exceeds MAX_STRING_BYTES"
    elif isinstance(value, dict):
        if len(value) > MAX_OBJECT_FIELDS:
            return False, "object exceeds MAX_OBJECT_FIELDS"
        for k, v in value.items():
            ok, why = _structural_ok(k, depth + 1)
            if not ok:
                return ok, why
            ok, why = _structural_ok(v, depth + 1)
            if not ok:
                return ok, why
    elif isinstance(value, list):
        if len(value) > MAX_LIST_ITEMS:
            return False, "array exceeds MAX_LIST_ITEMS"
        for v in value:
            ok, why = _structural_ok(v, depth + 1)
            if not ok:
                return ok, why
    return True, None


def _refuse(route, poc, step, status, reason, authored_by="provider", **extra):
    body = {"refused": True, "reason": reason, "outcome": "refused"}
    body.update(extra)
    try:
        write_capture(route, poc, step, dict(body), authored_by=authored_by,
                      refusal=True)
    except QuotaError as exc:
        return exc.status, {"refused": True, "outcome": "quota",
                            "reason": str(exc)}
    except CaptureError:
        # security-refusal pool exhausted: counted in aggregate, not per-case.
        pass
    return status, body


# --------------------------------------------------------------------------
# SEC-R3-06 — entity quotas: one reservation primitive, one counter per quota,
# and the counter that gates a route is the one that route actually increments.
#
# Scope matters. A GLOBAL quota bounds a service-wide population and can be
# reserved at dispatch. A SUBJECT quota bounds one action request or one run,
# and can only be reserved once the service has resolved the subject itself —
# reserving it at dispatch would mean trusting the caller's claimed id, which
# `25_`'s governing rule forbids. Both are reserved before any state moves and
# both release on failure; see AUDIT-R4-1 in the Delivery Record.
# --------------------------------------------------------------------------
QUOTA_SCOPE = {
    "cases": "global", "ideas": "global", "decisions": "global",
    "receipts": "global", "runs": "global",
    "attempts": "subject", "checkpoints": "subject", "stage-attempts": "subject",
}

# The counter each quota reserves against, and its ceiling. `/owner/idea` and
# `/poc2/triage` are both assigned the `ideas` quota by §B but count different
# things: one stores an owner idea, the other stages a triage. They are given
# separate counters against the same ceiling so that the route is gated by the
# counter it actually increments — SEC-R3-06's own requirement — and so a
# provider flooding triage cannot exhaust the OWNER's ability to register an
# idea, which is the crowd-out shape A.8 guards against on the capture axis.
QUOTA_CEILING = {"cases": lambda: MAX_CASES, "ideas": lambda: MAX_IDEAS,
                 "decisions": lambda: MAX_DECISIONS, "receipts": lambda: MAX_RECEIPTS,
                 "runs": lambda: MAX_RUNS}


def _entity_live(name: str) -> int:
    """The LIVE population a global quota bounds — the route's own records."""
    return {"cases": len(STORE.cases), "ideas": len(STORE.ideas),
            "decisions": len(STORE.decisions), "runs": len(STORE.runs),
            "receipts": STORE.receipt_count}.get(name, 0)


def _reserve_entity(name: str) -> tuple:
    """Reserve one unit of a GLOBAL entity quota. Caller holds STORE.lock."""
    cap = QUOTA_CEILING.get(name, lambda: 1 << 30)()
    used = _entity_live(name) + STORE.pending_quota.get(name, 0)
    if used >= cap:
        return False, ("%s ceiling reached (%d/%d); the request is refused rather "
                       "than accepted past capacity" % (name, used, cap))
    STORE.pending_quota[name] = STORE.pending_quota.get(name, 0) + 1
    return True, None


def _release_entity(name: str):
    """The transition did not become effective — give the unit back."""
    with STORE.lock:
        STORE.pending_quota[name] = max(0, STORE.pending_quota.get(name, 0) - 1)


def _commit_entity(name: str):
    """The transition became effective. `receipts` has no record store of its
    own, so the reservation becomes the increment; every other quota is backed
    by a dict the handler has already inserted into."""
    with STORE.lock:
        STORE.pending_quota[name] = max(0, STORE.pending_quota.get(name, 0) - 1)
        if name == "receipts":
            STORE.receipt_count += 1


def _subject_live(name: str, subject: str) -> int:
    """The LIVE count a subject-scoped quota bounds — again, the counter the
    route itself increments and reports, never a parallel one. A second counter
    kept alongside the real one is the same defect SEC-R3-06 names: the gate
    would move independently of the thing it is gating."""
    if name == "attempts":
        return STORE.relay_attempts.get(subject, 0)
    if name == "stage-attempts":
        return STORE.stage_attempts.get(subject, 0)
    if name == "checkpoints":
        return len(STORE.runs.get(subject, {}).get("checkpoints", []))
    return 0


def _reserve_subject(name: str, subject: str, ceiling: int) -> tuple:
    """Reserve one unit of a SUBJECT-scoped quota, against a subject the SERVICE
    resolved. Caller holds STORE.lock."""
    key = (name, subject)
    used = _subject_live(name, subject) + STORE.subject_counts.get(key, 0)
    if used >= ceiling:
        return False, ("%s ceiling reached for this subject (%d/%d)"
                       % (name, used, ceiling))
    STORE.subject_counts[key] = STORE.subject_counts.get(key, 0) + 1
    return True, None


def _release_subject(name: str, subject: str):
    with STORE.lock:
        key = (name, subject)
        STORE.subject_counts[key] = max(0, STORE.subject_counts.get(key, 0) - 1)


def _commit_subject(name: str, subject: str):
    """The transition became effective; the live counter now carries the unit."""
    with STORE.lock:
        key = (name, subject)
        STORE.subject_counts[key] = max(0, STORE.subject_counts.get(key, 0) - 1)


# --------------------------------------------------------------------------
# Handlers — owner surface
# --------------------------------------------------------------------------
def h_health(_p):
    # A.6: liveness only. No case, decision, or capture-activity counts.
    #
    # SEC-R4-01: storage integrity IS liveness — a quarantined service accepts
    # nothing, and an owner staring at a stalled session needs to see why here
    # rather than guess. These are counts and a kind, never case or decision
    # activity, so A.6's restriction is untouched.
    body = {"ok": not STORE.storage_quarantine,
            "service": "poc-wrapper-stub", "throwaway": THROWAWAY,
            "candidate": STORE.candidate, "run_instance": STORE.run_instance,
            "partition": ALLOWED_PARTITION,
            "relay_endpoint": STORE.base_url + "/relay/deliver",
            "stage_endpoint": STORE.base_url + STAGE_TARGET_PATH,
            "storage_quarantined": bool(STORE.storage_quarantine),
            "storage_anomalies": len(STORE.storage_anomalies)}
    if STORE.storage_quarantine:
        first = STORE.storage_quarantine[0]
        body["storage_quarantine"] = {
            "incidents": len(STORE.storage_quarantine),
            "problems": first.get("problems"),
            "recovery": "explicit operator recovery required; this service will "
                        "accept no further authority transition",
            # R7 item 5 — an operator has to be able to tell the difference
            # between "a restart will still be stopped" and "the marker could
            # not be written, so it will not be". Both are quarantined now; only
            # one of them stays quarantined.
            "marker_persisted": first.get("marker_persisted"),
            "marker_path": first.get("marker_path"),
            "recovered_from_marker": first.get("recovered_from_marker"),
            "reconcile_by": "delete the marker file after reconciling the "
                            "records it names; restarting does not clear it"}
    return 200, body


HEX64 = re.compile(r"^[0-9a-f]{64}$")


def h_owner_artifact_register(p):
    problems = []
    sd = p.get("source_digest")
    if not isinstance(sd, str) or not HEX64.fullmatch(sd.strip() if isinstance(sd, str) else ""):
        problems.append("source_digest must be 64-hex")
    if not isinstance(p.get("size_bytes"), int) or isinstance(p.get("size_bytes"), bool) \
            or p.get("size_bytes") < 0:
        problems.append("size_bytes must be a non-negative integer")
    if not isinstance(p.get("file_count"), int) or isinstance(p.get("file_count"), bool) \
            or p.get("file_count") < 1:
        problems.append("file_count must be a positive integer")
    for f in ("task_id", "transition", "target_role"):
        if not isinstance(p.get(f), str) or not p.get(f).strip():
            problems.append("%s is required" % f)
    role = (p.get("target_role") or "").strip() if isinstance(p.get("target_role"), str) else ""
    if role and role not in TARGET_ROLES:
        problems.append("target_role %r is not an authorized role" % role)
    if problems:
        return _refuse("/owner/artifact/register", "POC1", "register-malformed", 400,
                       "; ".join(problems), authored_by="owner-surface")

    identity = sha256_hex("|".join([sd.strip(), p["task_id"], p["transition"], role]))
    with STORE.lock:
        existing = STORE.reg_by_identity.get(identity)
        if existing:
            rec = STORE.registrations[existing]
            return 200, {"artifact_id": rec["artifact_id"], "registration_ref": existing,
                         "idempotent": True, "outcome": "already-registered",
                         "note": "same registration identity; no second record"}
    artifact_id = "art-" + secrets.token_hex(6)
    ref = "reg-" + secrets.token_urlsafe(24)
    rec = {"artifact_id": artifact_id, "registration_ref": ref, "identity": identity,
           "source_digest": sd.strip(), "size_bytes": p["size_bytes"],
           "file_count": p["file_count"], "task_id": p["task_id"],
           "transition": p["transition"], "target_role": role,
           "registered_at": time.time()}
    txn = Transition("/owner/artifact/register", "POC1", "artifact-register",
                     artifact_id, None, "REGISTERED", authored_by="owner-surface",
                     links={"artifact_id": artifact_id})
    txn.prepare()
    with STORE.lock:
        STORE.registrations[ref] = dict(rec, provisional=True)
        STORE.reg_by_identity[identity] = ref
    try:
        txn.commit()
    except (CaptureError, QuotaError) as exc:
        with STORE.lock:
            STORE.registrations.pop(ref, None)
            STORE.reg_by_identity.pop(identity, None)
        return 500, {"refused": True, "outcome": "capture-failed",
                     "reason": "registration not recorded, and therefore not "
                               "effective: %s" % exc}
    with STORE.lock:
        STORE.registrations[ref]["provisional"] = False
    return 200, {"artifact_id": artifact_id, "registration_ref": ref,
                 "outcome": "registered", "source_digest_is_authoritative": True}


def h_owner_idea(p):
    oc = p.get("owner_content")
    if not isinstance(oc, dict):
        return _refuse("/owner/idea", "POC2", "idea-malformed", 400,
                       "owner_content object is required", authored_by="owner-surface")
    problems = []
    if not isinstance(oc.get("title"), str) or not oc.get("title").strip():
        problems.append("title is required")
    if not isinstance(oc.get("body"), str):
        problems.append("body must be a string")
    if oc.get("project") is not None and not isinstance(oc.get("project"), str):
        problems.append("project must be a string or null")
    tags = oc.get("tags")
    if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
        problems.append("tags must be an array of strings")
    if problems:
        return _refuse("/owner/idea", "POC2", "idea-malformed", 400,
                       "; ".join(problems), authored_by="owner-surface")
    # The `ideas` quota is reserved at dispatch (SEC-R3-06); no second check here.

    stored = {"title": oc["title"], "body": oc["body"],
              "project": oc.get("project"), "tags": sorted(tags)}
    digest = sha256_hex(canonical(stored))
    ref = "idea-" + secrets.token_urlsafe(24)
    txn = Transition("/owner/idea", "POC2", "idea-register", ref, None, "STORED",
                     authored_by="owner-surface", links={"owner_content_digest": digest})
    txn.prepare()
    with STORE.lock:
        STORE.ideas[ref] = {"content": stored, "digest": digest, "provisional": True}
    try:
        txn.commit()
    except (CaptureError, QuotaError) as exc:
        with STORE.lock:
            STORE.ideas.pop(ref, None)
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    with STORE.lock:
        STORE.ideas[ref]["provisional"] = False
    return 200, {"idea_ref": ref, "owner_content_digest": digest, "outcome": "stored",
                 "note": "the content is stored server-side; authority derives from "
                         "this ref and the stored record, never from a copy"}


def h_owner_cases(_p):
    with STORE.lock:
        rows = [{"case_id": c["case_id"], "task_id": c["receipt"]["task_id"],
                 "transition": c["receipt"]["transition"],
                 "target_role": c["target_role"], "opened_at": c["opened_at"],
                 "decided": c["case_id"] in STORE.decisions}
                for c in STORE.cases.values() if not c.get("provisional")]
    rows.sort(key=lambda c: c["opened_at"])
    return 200, {"cases": rows, "undecided": sum(1 for c in rows if not c["decided"])}


def h_owner_decide(p):
    case_id, decision = p.get("case_id"), p.get("decision")
    if not isinstance(case_id, str):
        return _refuse("/owner/decide", "POC1", "decide-malformed", 400,
                       "case_id must be a string", authored_by="owner-surface")
    if case_id not in STORE.cases or STORE.cases[case_id].get("provisional"):
        return _refuse("/owner/decide", "POC1", "decide-unknown-case", 404,
                       "unknown case", authored_by="owner-surface")
    if decision not in ("accept", "reject"):
        return _refuse("/owner/decide", "POC1", "decide-bad-value", 400,
                       "decision must be 'accept' or 'reject'",
                       authored_by="owner-surface")
    with STORE.lock:
        if case_id in STORE.decisions:
            prior = STORE.decisions[case_id]
            return _refuse("/owner/decide", "POC1", "decide-already-decided", 409,
                           "case %s is already decided (%s); the first valid decision "
                           "is terminal" % (case_id, prior["decision"]),
                           authored_by="owner-surface", case_id=case_id)

    txn = Transition("/owner/decide", "POC1", "owner-decision", case_id, "UNDECIDED",
                     decision.upper(), authored_by="owner-surface",
                     links={"case_id": case_id})
    txn.prepare()
    record = {"decision": decision, "at": time.time(), "case_id": case_id,
              "provisional": True}
    with STORE.lock:
        if case_id in STORE.decisions:
            return 409, {"refused": True, "reason": "case already decided"}
        STORE.decisions[case_id] = record
    try:
        txn.commit()
    except (CaptureError, QuotaError) as exc:
        with STORE.lock:
            STORE.decisions.pop(case_id, None)
        return 500, {"refused": True, "outcome": "capture-failed",
                     "reason": "decision not recorded, and therefore not taken: %s" % exc}
    with STORE.lock:
        STORE.decisions[case_id]["provisional"] = False
    return 200, {"case_id": case_id, "recorded": decision, "terminal": True,
                 "note": "recorded on the owner surface; the provider is not told "
                         "the outcome"}


def _capability_for(p):
    cap = p.get("capability")
    arid = p.get("action_request_id")
    with STORE.lock:
        if isinstance(cap, str) and cap in STORE.capabilities:
            return STORE.capabilities[cap]
        if isinstance(arid, str) and arid in STORE.cap_by_ar:
            return STORE.capabilities[STORE.cap_by_ar[arid]]
    return None


def _expire_if_due(b):
    """SEC-R3-04 — expiry is an EVIDENCE-BACKED TRANSITION, not a silent flip.

    `33_` §2 offers two options and requires the choice to be stated. This build
    takes the transition, not the derived state, because A.8 (unchanged this
    round) says *"secrets leave the index the moment they become unusable"* — a
    derived `EXPIRED` has no moment at which anything observes the capability
    becoming unusable, so its secret would sit in the index until a sweeper
    removed it, and a sweeper is itself an unrecorded mutation.

    R3 flipped the status in place and discarded the secret with no prepared
    record, no committed record and no transition history: a state change with
    nothing to explain it, which is exactly what A.7 exists to forbid.

    The caller holds the global lock, so this whole transition is atomic.
    """
    if not b or b["status"] in TERMINAL_STATES or time.time() <= b["expires_at"]:
        return b
    arid = b["action_request_id"]
    txn = Transition("/poc1/expiry", "POC1", "expire", arid, b["status"], EXPIRED,
                     links={"action_request_id": arid,
                            "expires_at": b["expires_at"]})
    try:
        txn.prepare()
    except (CaptureError, QuotaError):
        # No evidence, no transition. The capability stays in its prior state
        # and every authority check below still refuses it on the TTL, so this
        # fails closed rather than granting anything.
        return b
    prior = b["status"]
    b["status"] = EXPIRED
    b["lease"] = None
    try:
        txn.commit(EXPIRED)
    except (CaptureError, QuotaError):
        b["status"] = prior
        return b
    SECRETS.discard(b["capability"])
    return b


def h_owner_revoke(p):
    b = _expire_if_due(_capability_for(p))
    if b is None:
        return _refuse("/owner/revoke", "POC1", "revoke-unknown", 404,
                       "no such capability or action request", authored_by="owner-surface")
    if b["status"] in TERMINAL_STATES:
        return _refuse("/owner/revoke", "POC1", "revoke-terminal", 409,
                       "capability is already terminal (%s); no state change" % b["status"],
                       authored_by="owner-surface", action_request_status=b["status"])
    txn = Transition("/owner/revoke", "POC1", "revoke", b["action_request_id"],
                     b["status"], REVOKED, authored_by="owner-surface",
                     links={"action_request_id": b["action_request_id"]})
    txn.prepare()
    prior = b["status"]
    prior_epoch = b.get("revocation_epoch", 0)
    prior_lease = b.get("lease")
    b["status"] = REVOKED
    # SEC-R3-02 — advance the revocation generation and cancel any uncommitted
    # lease. Any delivery holding the old epoch will fail its terminal
    # revalidation and will not become effective. This is what makes "once
    # revoke has returned success, no later delivery may commit under the
    # revoked generation" a property of the data rather than of the schedule.
    b["revocation_epoch"] = prior_epoch + 1
    b["lease"] = None
    try:
        txn.commit()
    except (CaptureError, QuotaError) as exc:
        b["status"] = prior
        b["revocation_epoch"] = prior_epoch
        b["lease"] = prior_lease
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    SECRETS.discard(b["capability"])
    return 200, {"outcome": "revoked", "action_request_status": REVOKED,
                 "action_request_id": b["action_request_id"]}


def h_owner_reconcile(p):
    """A.5 — the ONLY route that may reach RECONCILED_NOT_DELIVERED, and only
    from UNCERTAIN, and only for the literal outcome `not_delivered` (R5Q-01)."""
    b = _expire_if_due(_capability_for(p))
    if b is None:
        return _refuse("/owner/reconcile", "POC1", "owner-reconcile-unknown", 404,
                       "no such action request", authored_by="owner-surface")
    outcome = p.get("outcome")
    if outcome != "not_delivered":
        return _refuse("/owner/reconcile", "POC1", "owner-reconcile-bad-outcome", 400,
                       "outcome must be the literal 'not_delivered'; this route cannot "
                       "create a delivered state", authored_by="owner-surface",
                       action_request_status=b["status"])
    if b["status"] != UNCERTAIN:
        return _refuse("/owner/reconcile", "POC1", "owner-reconcile-bad-state", 409,
                       "owner reconciliation is valid only while the subject is "
                       "UNCERTAIN; current status is %s — no state change" % b["status"],
                       authored_by="owner-surface", action_request_status=b["status"])
    txn = Transition("/owner/reconcile", "POC1", "owner-attestation",
                     b["action_request_id"], UNCERTAIN, RECONCILED_NOT_DELIVERED,
                     authored_by="owner-surface",
                     links={"action_request_id": b["action_request_id"]})
    txn.prepare()
    b["status"] = RECONCILED_NOT_DELIVERED
    b["owner_attested"] = True
    try:
        txn.commit()
    except (CaptureError, QuotaError) as exc:
        b["status"] = UNCERTAIN
        b["owner_attested"] = False
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    return 200, {"outcome": "reconciled-not-delivered",
                 "action_request_status": RECONCILED_NOT_DELIVERED,
                 "re_attempts_permitted": 1,
                 "note": "owner attestation recorded; exactly one re-attempt is "
                         "permitted under the same submission identity"}


# --------------------------------------------------------------------------
# Handlers — POC-1 provider surface
# --------------------------------------------------------------------------
IDENTITY_FIELDS = ("task_id", "transition", "artifact_digest", "target_role",
                   "submission_epoch")


def _identity_problems(p) -> list:
    out = []
    for f in IDENTITY_FIELDS:
        v = p.get(f)
        if v is None or (isinstance(v, str) and not v.strip()):
            out.append("%s is required" % f)
        elif f == "submission_epoch":
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                out.append("submission_epoch must be a non-negative integer")
        elif not isinstance(v, str):
            out.append("%s must be a string" % f)
        elif f == "artifact_digest" and not HEX64.fullmatch(v.strip()):
            out.append("artifact_digest must be a 64-hex content digest — a raw "
                       "archive hash alone is not identity")
    return out


def idempotency_key(p) -> str:
    return sha256_hex(canonical({f: p.get(f) for f in IDENTITY_FIELDS}))


def h_poc1_review_case(p):
    problems = _identity_problems(p)
    ref = p.get("registration_ref")
    if not isinstance(ref, str) or not ref.strip():
        problems.append("registration_ref is required")
    if problems:
        return _refuse("/poc1/review-case", "POC1", "review-malformed", 400,
                       "; ".join(problems))

    with STORE.lock:
        reg = STORE.registrations.get(ref)
        if reg and reg.get("provisional"):
            reg = None
    if reg is None:
        return _refuse("/poc1/review-case", "POC1", "review-unknown-registration", 403,
                       "unknown or expired registration_ref — the artifact identity "
                       "is owner-registered and a provider-supplied digest is only "
                       "ever checked against it", outcome="rejected-artifact-binding")

    role = p["target_role"].strip()
    # A.1's role verdicts are evaluated BEFORE A.2's registration binding, and
    # the order is load-bearing rather than cosmetic. A.2 requires the
    # registered `target_role` to be an authorized role, so a registration can
    # never hold an unauthorized or unknown one; checking the binding first
    # would mean every unauthorized role failed as `rejected-artifact-binding`
    # and A.1's `rejected-unauthorized-target` / `rejected-unknown-target` were
    # branches no request could reach. §E requires both to be demonstrable, and
    # a refusal reason that cannot be produced is not a control.
    if role in UNAUTHORIZED_ROLES:
        return _refuse("/poc1/review-case", "POC1", "review-unauthorized-role", 403,
                       "target_role %r is not authorized to receive a relay" % role,
                       outcome="rejected-unauthorized-target", target_role=role)
    if role not in TARGET_ROLES:
        return _refuse("/poc1/review-case", "POC1", "review-unknown-role", 400,
                       "target_role %r is not a known role" % role,
                       outcome="rejected-unknown-target", target_role=role)

    for field, registered in (("task_id", reg["task_id"]),
                              ("transition", reg["transition"]),
                              ("target_role", reg["target_role"])):
        if p[field].strip() != registered:
            return _refuse("/poc1/review-case", "POC1", "review-binding-mismatch", 403,
                           "%s does not match the owner-registered value" % field,
                           outcome="rejected-artifact-binding")
    if p["artifact_digest"].strip() != reg["source_digest"]:
        return _refuse("/poc1/review-case", "POC1", "review-binding-mismatch", 403,
                       "artifact_digest does not equal the owner-registered "
                       "source_digest", outcome="rejected-artifact-binding")

    # SEC-R3-01 — insert-if-absent. The duplicate check and the publication are
    # the same critical section (the whole handler runs under the global lock),
    # so two concurrent requests carrying one submission identity cannot both
    # read `prior is None`. The loser returns the WINNER's suppressed-duplicate
    # result, not a second case.
    ikey = idempotency_key(p)
    prior = STORE.by_identity.get(ikey)
    if prior is not None:
        existing = STORE.cases[prior]
        try:
            write_capture("/poc1/review-case", "POC1", "review-duplicate",
                          {"case_id": prior, "idempotency_key": ikey,
                           "task_id": p["task_id"], "transition": p["transition"],
                           "artifact_digest": p["artifact_digest"],
                           "target_role": role, "outcome": "duplicate-suppressed"})
        except (CaptureError, QuotaError) as exc:
            return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
        return 200, {"duplicate_suppressed": True, "outcome": "duplicate-suppressed",
                     "prior_receipt": existing["receipt"], "reprocessed": False}

    case_id = "case-" + secrets.token_hex(6)
    receipt = {"receipt_id": "rcpt-" + secrets.token_hex(6), "idempotency_key": ikey,
               "task_id": p["task_id"], "transition": p["transition"],
               "artifact_digest": p["artifact_digest"], "target_role": role,
               "submission_epoch": p["submission_epoch"],
               "artifact_id": reg["artifact_id"]}

    # SEC-R3-03 — the token is minted and the case published BEFORE the
    # `case-opened` capture is written. R3 wrote the capture first, so a token
    # ceiling reached a line later left a committed record describing a case
    # that did not exist. A committed record must never describe a case that
    # does not exist; on mint failure the only record written is the refusal.
    try:
        token = STORE.mint_token(case_id)
    except QuotaError as exc:
        return _refuse("/poc1/review-case", "POC1", "review-quota", exc.status,
                       str(exc), outcome="refused-quota")
    STORE.cases[case_id] = {"case_id": case_id, "identity": ikey,
                            "receipt": receipt, "target_role": role,
                            "artifact_id": reg["artifact_id"],
                            "source_digest": reg["source_digest"],
                            "opened_at": time.time()}
    STORE.by_identity[ikey] = case_id
    try:
        write_capture("/poc1/review-case", "POC1", "review-case",
                      {"case_id": case_id, "idempotency_key": ikey,
                       "task_id": p["task_id"], "transition": p["transition"],
                       "artifact_digest": p["artifact_digest"], "target_role": role,
                       "submission_epoch": p["submission_epoch"],
                       "artifact_id": reg["artifact_id"], "registration_ref": ref,
                       "outcome": "case-opened"})
    except BaseException as exc:
        # The evidence did not land, so the case does not become effective:
        # roll the whole transition back, leaving no case, no token, no
        # published identity, and no consumed secret-index slot.
        #
        # `BaseException`, not `(CaptureError, QuotaError)`: an earlier draft
        # caught only those two, and the reviewer's barrier probe — which
        # raises `BrokenBarrierError` from inside `write_capture` — left a
        # PUBLISHED CASE WITH NO EVIDENCE behind. Whatever stops the evidence
        # landing, the transition must not survive it. The exception is
        # re-raised so dispatch still turns it into a structured refusal.
        STORE.cases.pop(case_id, None)
        STORE.by_identity.pop(ikey, None)
        STORE.retract_token(token)
        if isinstance(exc, (CaptureError, QuotaError)):
            return 500, {"refused": True, "outcome": "capture-failed",
                         "reason": str(exc)}
        raise
    # Disclose: the provider is the intended recipient of the token the service
    # just minted. Redaction still applies to every other value here, and this
    # token is a descriptor in every capture and log.
    return 200, {"resume_token": Disclose(token), "outcome": "case-opened",
                 "note": "carry this token; the decision is made on the owner surface"}


def h_poc1_verify_decision(p):
    extra = sorted(set(p) - {"token"})
    if extra:
        return _refuse("/poc1/verify-decision", "POC1", "verify-extra-fields", 403,
                       "verify-decision accepts only a resume token; the request also "
                       "carried %d additional field(s)" % len(extra),
                       outcome="refused-extra-fields")
    rec, why = STORE.find_token(p.get("token"))
    if rec is None:
        return _refuse("/poc1/verify-decision", "POC1", "verify-token", 403, why,
                       outcome="refused-token")
    case_id = rec["case_id"]
    decision = STORE.decisions.get(case_id)
    if decision is not None and decision.get("provisional"):
        decision = None

    if decision is None:
        return _refuse("/poc1/verify-decision", "POC1", "verify-pending", 403,
                       "no owner decision exists for this case; a valid token proves "
                       "the pause was carried, not that anything was approved. The "
                       "token is still valid — poll again once the owner has decided",
                       outcome="pending", case_id=case_id)

    case = STORE.cases[case_id]
    if decision["decision"] != "accept":
        txn = Transition("/poc1/verify-decision", "POC1", "token-spend-reject",
                         case_id, "UNSPENT", "SPENT", links={"case_id": case_id})
        txn.prepare()
        # SEC-R3-01: claim the token before the transition can be observed to
        # have happened, so a concurrent verify cannot also spend it.
        claimed, why = STORE.claim_token(p.get("token"))
        if claimed is None:
            return _refuse("/poc1/verify-decision", "POC1", "verify-token", 403, why,
                           outcome="refused-token")
        try:
            txn.commit()
        except (CaptureError, QuotaError) as exc:
            STORE.unclaim_token(p.get("token"))
            return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
        SECRETS.discard(p.get("token"))
        return 200, {"authorized": False, "outcome": "owner-rejected",
                     "reason": "owner rejected the case"}

    ar = {"id": "ar-" + secrets.token_hex(6), "case_id": case_id,
          "action_class": "relay-artifact", "scope": ALLOWED_PARTITION,
          "policy_version": "P1", "risk_class": "consequential",
          "idempotency_key": case["identity"], "target_role": case["target_role"],
          "endpoint": STORE.base_url + TARGET_ROLES[case["target_role"]],
          "payload": {"case_id": case_id, "task_id": case["receipt"]["task_id"],
                      "transition": case["receipt"]["transition"],
                      "artifact_digest": case["receipt"]["artifact_digest"],
                      "idempotency_key": case["identity"]}}
    payload_digest = sha256_hex(canonical(ar["payload"]))

    # SEC-R3-03 — RESERVE the secret-index slot before anything is committed.
    # R3 wrote the `capability-mint` committed record and only then tried to
    # admit the secret; when admission failed the capability was rolled back and
    # the committed record was left behind, asserting an authorization that
    # never became effective.
    if not SECRETS.reserve():
        return _refuse("/poc1/verify-decision", "POC1", "verify-secret-ceiling", 429,
                       "live-secret ceiling reached; refusing to mint a capability "
                       "that could not be redacted", outcome="refused-quota")

    cap = "cap-" + secrets.token_urlsafe(24)
    binding = {"capability": cap, "action_request_id": ar["id"], "case_id": case_id,
               "endpoint": ar["endpoint"], "payload_digest": payload_digest,
               "idempotency_key": case["identity"], "candidate": STORE.candidate,
               "expires_at": time.time() + CAPABILITY_TTL_S, "status": MINTED,
               "owner_attested": False,
               # SEC-R3-02 — the revocation generation. A delivery claims the
               # epoch it saw; `/owner/revoke` advances it; the delivery
               # revalidates at its terminal commit and refuses to become
               # effective under a superseded generation.
               "revocation_epoch": 0, "lease": None}

    # SEC-R3-03 — admission is ATTEMPTED, not merely reserved, before any
    # committed record is written. Reserving capacity is not enough on its own:
    # the reviewer's probe forces `SECRETS.add` itself to refuse, and an
    # implementation that only pre-reserved capacity would sail past that
    # injection rather than pass it. So the real admission happens here, and
    # every path after this point can only fail in ways that roll it back.
    SECRETS.release_reserved()
    if not SECRETS.add(cap):
        return _refuse("/poc1/verify-decision", "POC1", "verify-secret-ceiling", 429,
                       "the capability could not be admitted to the live-secret "
                       "index, so it is not minted and nothing is recorded",
                       outcome="refused-quota")

    # A.7: capture BEFORE the token is spent and before the capability is live.
    txn = Transition("/poc1/verify-decision", "POC1", "capability-mint", ar["id"],
                     None, MINTED, links={"case_id": case_id,
                                          "action_request_id": ar["id"]})
    try:
        txn.prepare()
    except BaseException:
        SECRETS.discard(cap)
        raise
    # SEC-R3-01 — claim the token in the same held lock that read it valid, and
    # before the capability exists. A second concurrent verify finds it spent.
    claimed, why = STORE.claim_token(p.get("token"))
    if claimed is None:
        SECRETS.discard(cap)
        return _refuse("/poc1/verify-decision", "POC1", "verify-token", 403, why,
                       outcome="refused-token")
    STORE.capabilities[cap] = dict(binding, provisional=True)
    STORE.cap_by_ar[ar["id"]] = cap
    try:
        txn.commit(MINTED)
    except BaseException as exc:
        STORE.capabilities.pop(cap, None)
        STORE.cap_by_ar.pop(ar["id"], None)
        STORE.unclaim_token(p.get("token"))
        SECRETS.discard(cap)
        if isinstance(exc, (CaptureError, QuotaError)):
            return 500, {"refused": True, "outcome": "capture-failed",
                         "reason": "authorization not recorded, and therefore not "
                                   "issued; the token remains unspent: %s" % exc}
        raise
    STORE.capabilities[cap]["provisional"] = False
    SECRETS.discard(p.get("token"))
    # Disclose: same rule as the resume token — the provider is the intended
    # recipient of the capability minted for it on this authorization.
    return 200, {"authorized": True, "outcome": "authorized", "action_request": ar,
                 "execution_capability": Disclose(cap),
                 "expires_in_s": CAPABILITY_TTL_S,
                 "action_request_status": MINTED}


def h_relay_deliver(p):
    cap = p.get("capability")
    with STORE.lock:
        b = STORE.capabilities.get(cap) if isinstance(cap, str) else None
        if b and b.get("provisional"):
            b = None
    if b is None:
        return _refuse("/relay/deliver", "POC1", "relay-no-capability", 403,
                       "the relay sink requires a single-use execution capability "
                       "minted at authorization; a direct call cannot produce the "
                       "side effect", outcome="refused-no-capability")
    _expire_if_due(b)
    status = b["status"]
    if status in (EXPIRED, REVOKED):
        return _refuse("/relay/deliver", "POC1", "relay-terminal-state", 403,
                       "capability is %s; no delivery and no state change" % status,
                       outcome="refused-terminal", action_request_status=status)
    for field, want in (("action_request_id", b["action_request_id"]),
                        ("case_id", b["case_id"])):
        if p.get(field) != want:
            return _refuse("/relay/deliver", "POC1", "relay-binding", 403,
                           "capability is not bound to the presented %s" % field,
                           outcome="refused-binding", action_request_status=status)
    if sha256_hex(canonical(p.get("payload"))) != b["payload_digest"]:
        return _refuse("/relay/deliver", "POC1", "relay-payload", 403,
                       "payload digest does not match the capability binding",
                       outcome="refused-payload-mismatch", action_request_status=status)

    arid = b["action_request_id"]
    with STORE.lock:
        prior = STORE.relay_receipts.get(arid)

    if status in DELIVERED_STATES:
        # A.4: replay returns the prior receipt ONLY from a verified-delivered state.
        with STORE.lock:
            STORE.relay_attempts[arid] = STORE.relay_attempts.get(arid, 0) + 1
            attempt = STORE.relay_attempts[arid]
        try:
            write_capture("/relay/deliver", "POC1", "relay-replay",
                          {"case_id": b["case_id"], "action_request_id": arid,
                           "attempt": attempt, "delivered": False, "replayed": True,
                           "action_request_status": status,
                           "outcome": "replayed-no-second-side-effect"})
        except (CaptureError, QuotaError) as exc:
            return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
        return 200, {"delivered": False, "replayed": True, "no_second_side_effect": True,
                     "attempt": attempt, "receipt": prior, "action_request_status": status,
                     "outcome": "replayed-no-second-side-effect"}

    if status == UNCERTAIN:
        return _refuse("/relay/deliver", "POC1", "relay-uncertain", 409,
                       "capability is UNCERTAIN; reconcile before any further delivery",
                       outcome="refused-uncertain", action_request_status=status)
    is_reattempt = status == RECONCILED_NOT_DELIVERED
    if is_reattempt:
        with STORE.lock:
            used = STORE.reattempts.get(arid, 0)
        if used >= 1:
            return _refuse("/relay/deliver", "POC1", "relay-second-reattempt", 409,
                           "exactly one re-attempt is permitted after an owner "
                           "attestation of non-delivery; a second is refused",
                           outcome="refused-second-reattempt", action_request_status=status)
        # The single permitted re-attempt is spent below, only once the
        # attempt-start transition has committed. Spending it here would burn
        # the provider's one retry on a capture failure that made no attempt at
        # all, and A.7 is explicit that "permanently stuck" is not an outcome.
    elif status == ATTEMPT_STARTED:
        return _refuse("/relay/deliver", "POC1", "relay-in-flight", 409,
                       "an attempt is already in flight for this action request",
                       outcome="refused-in-flight", action_request_status=status)

    # SEC-R3-06 — the `attempts` quota is SUBJECT-scoped, so it is reserved
    # here, against the action request the SERVICE resolved from the capability
    # binding, rather than at dispatch against a caller-supplied id.
    used_attempts = STORE.relay_attempts.get(arid, 0)
    ok, why = _reserve_subject("attempts", arid, MAX_ATTEMPTS_PER_AR)
    if not ok:
        return _refuse("/relay/deliver", "POC1", "relay-attempt-ceiling", 429, why,
                       outcome="refused-quota")
    attempt = used_attempts + 1

    # SEC-R3-02 — claim the revocation generation this delivery is authorized
    # under. The claim is re-checked at the terminal commit below; a revoke that
    # lands in between advances the epoch and the delivery does not become
    # effective.
    claimed_epoch = b.get("revocation_epoch", 0)

    # A.7 orders this: the `prepared` record lands BEFORE any state moves, so
    # the attempt counter is only advanced once the transition exists on disk.
    # Incrementing first would leave a counted attempt behind whenever the
    # prepared write failed — a mutation with no transition to explain it.
    txn = Transition("/relay/deliver", "POC1", "attempt-start", arid, status,
                     ATTEMPT_STARTED, authored_by="provider",
                     links={"action_request_id": arid, "attempt": attempt})
    txn.prepare()
    prior_status = b["status"]
    STORE.relay_attempts[arid] = attempt
    _commit_subject("attempts", arid)
    if is_reattempt:
        STORE.reattempts[arid] = STORE.reattempts.get(arid, 0) + 1
    b["status"] = ATTEMPT_STARTED
    b["lease"] = {"epoch": claimed_epoch, "attempt": attempt}
    try:
        txn.commit(ATTEMPT_STARTED)
    except (CaptureError, QuotaError) as exc:
        b["status"] = prior_status
        b["lease"] = None
        STORE.relay_attempts[arid] = used_attempts
        if is_reattempt:
            STORE.reattempts[arid] = used
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}

    # Delivery. The receipt is minted by the SERVICE, once.
    receipt = {"receipt_id": "dlv-" + secrets.token_hex(6), "action_request_id": arid,
               "case_id": b["case_id"], "delivered_attempt": attempt,
               "idempotency_key": b["idempotency_key"]}
    dtxn = Transition("/relay/deliver", "POC1", "delivery", arid, ATTEMPT_STARTED,
                      DELIVERED_WITH_RECEIPT,
                      links={"action_request_id": arid, "receipt_id": receipt["receipt_id"]})
    dtxn.prepare()

    # SEC-R3-02 — THE TERMINAL REVALIDATION. This is the represented side
    # effect's linearization point, and it is the last moment at which the
    # delivery can be stopped. If the owner revoked while this delivery was in
    # flight, the epoch it claimed is stale and the delivery does NOT become
    # effective: no receipt, no DELIVERED_WITH_RECEIPT, and a truthful
    # non-delivery to the caller. R3 had no check here at all, so an
    # acknowledged revocation was silently overwritten by the in-flight relay.
    if b.get("revocation_epoch", 0) != claimed_epoch or b["status"] == REVOKED:
        b["status"] = REVOKED
        b["lease"] = None
        STORE.relay_attempts[arid] = used_attempts
        if is_reattempt:
            STORE.reattempts[arid] = used
        return _refuse("/relay/deliver", "POC1", "relay-revoked-in-flight", 409,
                       "the owner revoked this capability while the delivery was in "
                       "flight; the delivery did not become effective and no receipt "
                       "was minted", outcome="refused-revoked-in-flight",
                       action_request_status=REVOKED, delivered=False)

    STORE.relay_receipts[arid] = receipt
    try:
        dtxn.commit(DELIVERED_WITH_RECEIPT)
    except (CaptureError, QuotaError) as exc:
        # A.7: rollback impossible for an external side effect — the subject enters
        # an explicit non-authoritative UNCERTAIN that fails closed. This is the
        # ONLY service-established path to UNCERTAIN (see the Delivery Record's
        # AUDIT-1: a provider-reported `uncertain` is corroborating, never a
        # transition trigger).
        STORE.relay_receipts.pop(arid, None)
        b["status"] = UNCERTAIN
        b["lease"] = None
        return 500, {"refused": True, "outcome": "uncertain",
                     "action_request_status": UNCERTAIN,
                     "reason": "delivery could not be recorded; the subject is "
                               "UNCERTAIN and fails closed: %s" % exc}
    b["status"] = DELIVERED_WITH_RECEIPT
    b["lease"] = None
    SECRETS.discard(b["capability"])
    src = STORE.cases.get(b["case_id"], {}).get("source_digest")
    try:
        # §C — the authoritative digest is the owner-registered `source_digest`
        # and it is stub-minted; `destination_digest_claimed` is the provider's
        # and is recorded under the provenance key, where nothing can read it as
        # a service conclusion. `destination_verified` is minted false, with the
        # reason, because this service never receives the destination bytes.
        write_capture("/relay/deliver", "POC1", "relay-delivered",
                      {"case_id": b["case_id"], "action_request_id": arid,
                       "attempt": attempt, "delivered": True, "replayed": False,
                       "action_request_status": DELIVERED_WITH_RECEIPT,
                       "source_digest": src,
                       "destination_verified": False,
                       "destination_verified_reason":
                           "this service does not receive destination bytes and "
                           "cannot hash them",
                       "outcome": "delivered"},
                      provider={"destination_digest_claimed":
                                p.get("destination_digest_claimed")})
    except (CaptureError, QuotaError):
        pass
    return 200, {"delivered": True, "replayed": False, "attempt": attempt,
                 "receipt": receipt, "action_request_status": DELIVERED_WITH_RECEIPT,
                 "destination_verified": False,
                 "destination_digest_claimed_is_provider_reported": True,
                 "outcome": "delivered"}


def h_poc1_reconcile(p):
    """A.5 — returns RECONCILED_DELIVERED or UNCERTAIN. Never NOT_DELIVERED."""
    b = _expire_if_due(_capability_for(p))
    if b is None:
        return _refuse("/poc1/reconcile", "POC1", "reconcile-unknown", 404,
                       "no such capability or action request", outcome="refused-unknown")
    arid = b["action_request_id"]
    with STORE.lock:
        service_receipt = STORE.relay_receipts.get(arid)
    if service_receipt is not None:
        if b["status"] not in DELIVERED_STATES:
            txn = Transition("/poc1/reconcile", "POC1", "reconcile-delivered", arid,
                             b["status"], RECONCILED_DELIVERED, authored_by="provider",
                             links={"action_request_id": arid})
            txn.prepare()
            prior = b["status"]
            b["status"] = RECONCILED_DELIVERED
            try:
                txn.commit(RECONCILED_DELIVERED)
            except (CaptureError, QuotaError) as exc:
                b["status"] = prior
                return 500, {"refused": True, "outcome": "capture-failed",
                             "reason": str(exc)}
        return 200, {"outcome": "reconciled-delivered",
                     "action_request_status": b["status"], "receipt": service_receipt,
                     "basis": "a service-owned receipt exists for this action request"}
    # No service-owned receipt. LOCAL ABSENCE IS NEVER PROOF (A.5).
    #
    # Only ATTEMPT_STARTED may move to UNCERTAIN: that is the sole source state
    # A.4 gives for it, and it is the only one where the question "did the
    # external side effect happen?" is even open. Reconciling a MINTED
    # capability — one on which no attempt was ever made — used to move it to
    # UNCERTAIN here, which is not a transition A.4 defines and which a provider
    # could invoke on itself: delivery is refused from UNCERTAIN, so a caller
    # could strand its own authorization and then present the result as grounds
    # for an owner attestation of non-delivery. A state machine that accepts a
    # transition its own table does not list is not enforcing the table.
    if b["status"] == ATTEMPT_STARTED:
        txn = Transition("/poc1/reconcile", "POC1", "reconcile-uncertain", arid,
                         b["status"], UNCERTAIN, authored_by="provider",
                         links={"action_request_id": arid})
        txn.prepare()
        prior = b["status"]
        b["status"] = UNCERTAIN
        try:
            txn.commit(UNCERTAIN)
        except (CaptureError, QuotaError) as exc:
            b["status"] = prior
            return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    # A.5 permits this route two answers only. `reconciliation_result` is the
    # answer to "was it delivered?" and is UNCERTAIN whenever no service-owned
    # receipt exists. `action_request_status` is the capability's actual state,
    # which only moves when A.4 lists the transition — the two are reported
    # separately so neither is read as the other.
    return 200, {"outcome": "uncertain", "reconciliation_result": UNCERTAIN,
                 "action_request_status": b["status"],
                 "reconciled_not_delivered": False,
                 "basis": "no service-owned receipt exists; the absence of a local "
                          "record cannot rule out an external side effect that "
                          "completed before this service recorded it",
                 "next": "an owner attestation on /owner/reconcile is the only route "
                         "to RECONCILED_NOT_DELIVERED in this POC"}


PROVIDER_STATUS = frozenset(("ok", "error", "uncertain"))


def h_poc1_receipt(p):
    """A.6 — corroborating evidence ONLY. Cannot mark delivered, cannot alter
    capability state, cannot satisfy an acceptance check."""
    status = p.get("provider_status")
    if status not in PROVIDER_STATUS:
        return _refuse("/poc1/receipt", "POC1", "receipt-bad-status", 400,
                       "provider_status must be one of ok|error|uncertain",
                       outcome="refused-malformed")
    msg = p.get("provider_message")
    if msg is not None and (not isinstance(msg, str) or len(msg) > 1024):
        return _refuse("/poc1/receipt", "POC1", "receipt-bad-message", 400,
                       "provider_message must be a string of at most 1024 characters",
                       outcome="refused-malformed")
    ddc = p.get("destination_digest_claimed")
    if ddc is not None and (not isinstance(ddc, str) or not HEX64.fullmatch(ddc)):
        return _refuse("/poc1/receipt", "POC1", "receipt-bad-digest", 400,
                       "destination_digest_claimed must be 64-hex or null",
                       outcome="refused-malformed")
    b = _expire_if_due(_capability_for(p))
    before = b["status"] if b else None
    # A.4 invalid transition: a LATE provider receipt on REVOKED or EXPIRED is
    # captured, refused, and changes nothing. Recording it as an ordinary
    # receipt would leave corroborating material for an action the owner had
    # already revoked, or that had timed out, sitting next to a live capability
    # record — the shape a later reader mistakes for delivery.
    if before in (REVOKED, EXPIRED):
        return _refuse("/poc1/receipt", "POC1", "receipt-late-terminal", 409,
                       "the action request is %s; a provider receipt arriving after "
                       "that is recorded as a refusal and changes no state" % before,
                       outcome="refused-late-receipt",
                       action_request_status=before,
                       action_request_status_changed=False)
    try:
        write_capture("/poc1/receipt", "POC1", "provider-receipt",
                      {"outcome": "recorded",
                       "action_request_status": before,
                       "action_request_status_changed": False},
                      authored_by="provider", provider=dict(p))
    except QuotaError as exc:
        return _refuse("/poc1/receipt", "POC1", "receipt-quota", exc.status, str(exc))
    except CaptureError as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    return 200, {"recorded": True, "outcome": "recorded",
                 "action_request_status": before,
                 "action_request_status_changed": False,
                 "note": ("provider-reported and corroborating only: a provider_status "
                          "of 'ok' is a provider claim, never a service conclusion, and "
                          "this route cannot mark an action delivered or alter "
                          "capability state")}


def h_poc1_refusal(p):
    code, msg = p.get("refusal_code"), p.get("refusal_message")
    if code is not None and (not isinstance(code, str) or len(code) > 64):
        return _refuse("/poc1/refusal", "POC1", "refusal-bad-code", 400,
                       "refusal_code must be a string of at most 64 characters",
                       outcome="refused-malformed")
    if msg is not None and (not isinstance(msg, str) or len(msg) > 1024):
        return _refuse("/poc1/refusal", "POC1", "refusal-bad-message", 400,
                       "refusal_message must be a string of at most 1024 characters",
                       outcome="refused-malformed")
    b = _capability_for(p)
    try:
        write_capture("/poc1/refusal", "POC1", "provider-refusal",
                      {"outcome": "recorded",
                       "action_request_status": b["status"] if b else None,
                       "action_request_status_changed": False},
                      authored_by="provider", provider=dict(p))
    except (CaptureError, QuotaError) as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    return 200, {"recorded": True, "outcome": "recorded",
                 "action_request_status": b["status"] if b else None,
                 "action_request_status_changed": False}


# --------------------------------------------------------------------------
# POC-2 — owner-idea authority bound to canonical content (A.3)
# --------------------------------------------------------------------------
def h_poc2_triage(p):
    idea_ref = p.get("idea_ref")
    supplied = p.get("owner_content")
    items = p.get("external_items")
    if items is None:
        items = []
    if not isinstance(items, list):
        return _refuse("/poc2/triage", "POC2", "triage-bad-items", 400,
                       "external_items must be an array", outcome="refused-malformed")
    if len(items) > MAX_LIST_ITEMS:
        return _refuse("/poc2/triage", "POC2", "triage-too-many-items", 400,
                       "external_items exceeds MAX_LIST_ITEMS", outcome="refused-bounds")

    stored = None
    if isinstance(idea_ref, str) and idea_ref:
        with STORE.lock:
            rec = STORE.ideas.get(idea_ref)
            if rec and not rec.get("provisional"):
                stored = rec
        if stored is None:
            return _refuse("/poc2/triage", "POC2", "triage-unknown-idea", 403,
                           "unknown idea_ref", outcome="refused-unknown-idea")

    if supplied is not None:
        if stored is None:
            return _refuse("/poc2/triage", "POC2", "triage-content-without-ref", 403,
                           "owner_content without a valid idea_ref is never "
                           "owner-authored", outcome="refused-unauthenticated-content")
        if not isinstance(supplied, dict):
            return _refuse("/poc2/triage", "POC2", "triage-bad-content", 400,
                           "owner_content must be an object", outcome="refused-malformed")
        norm = {"title": supplied.get("title"), "body": supplied.get("body"),
                "project": supplied.get("project"),
                "tags": sorted(supplied.get("tags") or [])
                if isinstance(supplied.get("tags"), list) else supplied.get("tags")}
        if sha256_hex(canonical(norm)) != stored["digest"]:
            return _refuse("/poc2/triage", "POC2", "triage-content-mismatch", 403,
                           "owner_content does not canonicalize to the stored "
                           "owner_content_digest; it is a convenience copy and never "
                           "replaces stored content",
                           outcome="refused-content-mismatch")

    # Each external item carries its OWN envelope and NEVER inherits authority.
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            return _refuse("/poc2/triage", "POC2", "triage-item-malformed", 400,
                           "external_items[%d] must be an object" % i,
                           outcome="refused-malformed")
        ok, why = _envelope_ok(item)
        if not ok:
            return _refuse("/poc2/triage", "POC2", "triage-item-envelope", 400,
                           "external_items[%d]: %s" % (i, why),
                           outcome="refused-item-envelope")

    if stored is None:
        ok, why = _envelope_ok(p)
        if not ok:
            return _refuse("/poc2/triage", "POC2", "triage-envelope", 400,
                           "Case B requires a top-level external-untrusted envelope: "
                           "%s" % why, outcome="refused-envelope")

    content = stored["content"] if stored else None
    classification = ("existing-project-addition"
                      if (content or {}).get("project") else "new-topic")
    components = ([{"component": "owner_content",
                    "instruction_authority": "owner-authorized",
                    "source": "owner-surface"}] if stored else [])
    components += [{"component": "external_items[%d]" % i,
                    "instruction_authority": "none",
                    "source": (it.get("source") if isinstance(it, dict) else None)}
                   for i, it in enumerate(items)]

    # SEC-R3-06 — a staged triage is a record in the same population the
    # `ideas` quota bounds, so the counter that gates this route is the counter
    # this route increments. R3 gated `/poc2/triage` on `STORE.ideas` while
    # never adding to it, which is why the reviewer's probe drove Case-B triage
    # straight past a full ceiling.
    staged_id = "staged-" + secrets.token_hex(6)
    STORE.ideas[staged_id] = {"kind": "staged-triage", "case": "A" if stored else "B",
                              "idea_ref": idea_ref if stored else None,
                              "staged_at": time.time(), "provisional": True}
    try:
        write_capture("/poc2/triage", "POC2", "idea-staged",
                      {"classification": classification, "stage": "staged",
                       "queue": "business-ideas",
                       "authority_components": components,
                       "outcome": "staged"})
    except BaseException as exc:
        STORE.ideas.pop(staged_id, None)
        if isinstance(exc, (CaptureError, QuotaError)):
            return 500, {"refused": True, "outcome": "capture-failed",
                         "reason": str(exc)}
        raise
    STORE.ideas[staged_id]["provisional"] = False
    return 200, {
        "classification": classification, "staged": True, "queue": "business-ideas",
        "authority_components": components,
        "case": "A" if stored else "B",
        "suggested_next": "owner review" if not stored else "schedule",
        "outcome": "staged",
        "external_action_taken_by_this_service": False,
        "provider_conduct": ("NOT OBSERVED BY THIS SERVICE — whether the provider "
                             "followed a link or took an action is measured at the "
                             "provider, not asserted here"),
        "note": ("authority is recorded per component; a single flattened authority "
                 "value for the whole request would be a defect"),
    }


# --------------------------------------------------------------------------
# POC-3
# --------------------------------------------------------------------------
def _declaration_key(p) -> str:
    """§B POC-3: run identity is stub-minted, so what makes a second call a
    *duplicate declaration* can only be the declaration the provider actually
    made — `(schedule_id, occurrence)`, both listed fields for this route.

    Keying it off a provider-supplied `run_id` (Rev-4 shape) would rest the
    control on a field §B does not list for `/poc3/run-started`: the capture
    reduces an unlisted field to a descriptor, so the evidence would not show
    the value that drove the decision, and a provider naming its own run id
    would be minting identity the service is required to mint. Neither survives
    the `25_` governing rule.
    """
    return canonical([p.get("schedule_id"), p.get("occurrence")])


def h_poc3_run_started(p):
    sched, occ = p.get("schedule_id"), p.get("occurrence")
    if not isinstance(sched, str) or not sched or not isinstance(occ, str) or not occ:
        return _refuse("/poc3/run-started", "POC3", "run-malformed", 400,
                       "schedule_id and occurrence are required non-empty strings; "
                       "without them a declaration has no identity and duplicate "
                       "suppression could not be evaluated",
                       outcome="refused-malformed")
    dkey = _declaration_key(p)
    with STORE.lock:
        prior_id = STORE.runs_by_declaration.get(dkey)
        prior = dict(STORE.runs[prior_id]) if prior_id in STORE.runs else None
    if prior is not None and not prior.get("provisional"):
        # A duplicate run-started is itself a POC-3 measurement, never an
        # overwrite: the prior started_at and checkpoint count are preserved and
        # returned so the duplicate is observable in the evidence.
        return _refuse("/poc3/run-started", "POC3", "run-duplicate", 409,
                       "this schedule occurrence is already declared; a duplicate "
                       "declaration is itself a POC-3 measurement and does not "
                       "overwrite the prior record",
                       outcome="duplicate-run-declaration", run_id=prior_id,
                       started_at=prior["started_at"],
                       checkpoint_count=len(prior["checkpoints"]),
                       declaration_duplicate=True)
    run_id = "run-" + secrets.token_hex(6)
    txn = Transition("/poc3/run-started", "POC3", "run-started", run_id, None,
                     "RUNNING", authored_by="provider", links={"run_id": run_id})
    txn.prepare()
    with STORE.lock:
        STORE.runs[run_id] = {"occurrence": occ,
                              "schedule_id": sched,
                              "declaration_key": dkey,
                              "provider_correlation_id": p.get("provider_correlation_id"),
                              "started_at": time.time(), "checkpoints": [],
                              "provisional": True}
        STORE.runs_by_declaration[dkey] = run_id
        # The stage-attempt counter exists from run creation and reads 0. An
        # absent key and a zero both mean "no attempt recorded", but only the
        # zero says so in the evidence without needing to be interpreted.
        STORE.stage_attempts.setdefault(run_id, 0)
    try:
        txn.commit("RUNNING")
    except (CaptureError, QuotaError) as exc:
        with STORE.lock:
            STORE.runs.pop(run_id, None)
            if STORE.runs_by_declaration.get(dkey) == run_id:
                STORE.runs_by_declaration.pop(dkey, None)
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    with STORE.lock:
        STORE.runs[run_id]["provisional"] = False
    return 200, {"run_id": run_id, "outcome": "run-started",
                 "stage_endpoint": STORE.base_url + STAGE_TARGET_PATH,
                 "provider_correlation_id": p.get("provider_correlation_id"),
                 "note": "run identity is stub-minted; any provider correlation value "
                         "is carried separately and anchors nothing"}


def h_poc3_checkpoint(p):
    run_id = p.get("run_id")
    if not isinstance(run_id, str) or run_id not in STORE.runs \
            or STORE.runs[run_id].get("provisional"):
        return _refuse("/poc3/checkpoint", "POC3", "checkpoint-unknown-run", 404,
                       "checkpoint for an unannounced run", outcome="refused-unknown-run")
    with STORE.lock:
        if len(STORE.runs[run_id]["checkpoints"]) >= MAX_CHECKPOINTS_PER_RUN:
            return _refuse("/poc3/checkpoint", "POC3", "checkpoint-ceiling", 429,
                           "checkpoint ceiling reached")
    txn = Transition("/poc3/checkpoint", "POC3", "checkpoint", run_id, "RUNNING",
                     "CHECKPOINTED", authored_by="provider", links={"run_id": run_id})
    txn.prepare()
    with STORE.lock:
        STORE.runs[run_id]["checkpoints"].append(time.time())
        count = len(STORE.runs[run_id]["checkpoints"])
    try:
        txn.commit("CHECKPOINTED")
    except (CaptureError, QuotaError) as exc:
        with STORE.lock:
            STORE.runs[run_id]["checkpoints"].pop()
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    return 200, {"checkpointed": True, "checkpoint_count": count,
                 "side_effect_certain": False, "outcome": "checkpointed"}


def h_poc3_reconcile(p):
    run_id = p.get("run_id")
    if not isinstance(run_id, str) or run_id not in STORE.runs:
        return _refuse("/poc3/reconcile", "POC3", "reconcile-unknown-run", 404,
                       "reconcile for an unannounced run", outcome="refused-unknown-run")
    with STORE.lock:
        run = STORE.runs[run_id]
        checked = {"checkpoints_recorded": len(run["checkpoints"]),
                   "stage_attempts_recorded": STORE.stage_attempts.get(run_id, 0)}
    txn = Transition("/poc3/reconcile", "POC3", "run-reconcile", run_id, "RUNNING",
                     "RECONCILED", authored_by="provider", links={"run_id": run_id})
    txn.prepare()
    try:
        txn.commit("RECONCILED")
    except (CaptureError, QuotaError) as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    return 200, {"outcome": "reconciled",
                 "post_state_checked_against_recorded_state": checked,
                 "external_post_state_checked": False,
                 "side_effect_certainty": ("NOT ESTABLISHED — this service can compare "
                                           "only its own recorded checkpoints and stage "
                                           "attempts; it has no view of an external "
                                           "system's post-state")}


def h_poc3_receipt(p):
    run_id = p.get("run_id")
    if p.get("provider_status") not in PROVIDER_STATUS:
        return _refuse("/poc3/receipt", "POC3", "receipt-bad-status", 400,
                       "provider_status must be one of ok|error|uncertain",
                       outcome="refused-malformed")
    known = isinstance(run_id, str) and run_id in STORE.runs
    try:
        write_capture("/poc3/receipt", "POC3", "run-receipt",
                      {"run_id": run_id if known else None,
                       "occurrence": p.get("occurrence"), "outcome": "recorded"},
                      authored_by="provider")
    except (CaptureError, QuotaError) as exc:
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    return 200, {"recorded": True, "run_known": known, "outcome": "recorded",
                 "note": "the occurrence window is judged by the real wrapper; this "
                         "stub records, it does not attest"}


def h_stage_deliver(p):
    run_id = p.get("run_id")
    if not isinstance(run_id, str) or run_id not in STORE.runs:
        return _refuse("/stage/deliver", "POC3", "stage-unknown-run", 404,
                       "stage delivery for an unannounced run",
                       outcome="refused-unknown-run")
    # SEC-R3-06 — `stage-attempts` is SUBJECT-scoped (per run), so it is
    # reserved here against the run the service resolved, not at dispatch.
    used = STORE.stage_attempts.get(run_id, 0)
    ok, why = _reserve_subject("stage-attempts", run_id, MAX_ATTEMPTS_PER_AR)
    if not ok:
        return _refuse("/stage/deliver", "POC3", "stage-ceiling", 429, why,
                       outcome="refused-quota")
    attempt = used + 1
    # SEC-R3-04 — the counter moves only once the evidence has landed. R3
    # incremented first, so a `capture-failed` response left the attempt
    # counted: the next successful attempt reported 2 for what was, as far as
    # any evidence showed, the first one. A `capture-failed` response must not
    # leave the counter advanced.
    try:
        write_capture("/stage/deliver", "POC3", "stage-delivered",
                      {"run_id": run_id, "attempt": attempt,
                       "outcome": "stage-delivered"}, authored_by="provider")
    except (CaptureError, QuotaError) as exc:
        _release_subject("stage-attempts", run_id)
        return 500, {"refused": True, "outcome": "capture-failed", "reason": str(exc)}
    STORE.stage_attempts[run_id] = attempt
    _commit_subject("stage-attempts", run_id)
    return 200, {"staged": True, "stage_attempt": attempt, "retry_tolerant": True,
                 "outcome": "stage-delivered"}


HANDLERS = {
    ("GET", "/health"): h_health,
    ("POST", "/owner/artifact/register"): h_owner_artifact_register,
    ("POST", "/owner/idea"): h_owner_idea,
    ("POST", "/owner/cases"): h_owner_cases,
    ("POST", "/owner/decide"): h_owner_decide,
    ("POST", "/owner/reconcile"): h_owner_reconcile,
    ("POST", "/owner/revoke"): h_owner_revoke,
    ("POST", "/poc1/review-case"): h_poc1_review_case,
    ("POST", "/poc1/verify-decision"): h_poc1_verify_decision,
    ("POST", "/poc1/reconcile"): h_poc1_reconcile,
    ("POST", "/poc1/receipt"): h_poc1_receipt,
    ("POST", "/poc1/refusal"): h_poc1_refusal,
    ("POST", "/relay/deliver"): h_relay_deliver,
    ("POST", "/poc2/triage"): h_poc2_triage,
    ("POST", "/poc3/run-started"): h_poc3_run_started,
    ("POST", "/poc3/checkpoint"): h_poc3_checkpoint,
    ("POST", "/poc3/reconcile"): h_poc3_reconcile,
    ("POST", "/poc3/receipt"): h_poc3_receipt,
    ("POST", "/stage/deliver"): h_stage_deliver,
}


def _ct_eq(a: str, b: str) -> bool:
    try:
        return hmac.compare_digest(a, b)
    except TypeError:
        return hmac.compare_digest(a.encode("utf-8", "replace"),
                                   b.encode("utf-8", "replace"))


def _poc_for(route: str) -> str:
    if route.startswith("/poc2"):
        return "POC2"
    if route.startswith(("/poc3", "/stage")):
        return "POC3"
    return "POC1"


def dispatch(method: str, path: str, payload: dict, headers: dict = None):
    """§B — unknown route OR missing policy row ⇒ fail closed.

    R4: this is the single linearization point. Every POST runs inside the
    global transition lock, held continuously from the first precondition read
    to the last committed evidence write, so no two requests can both pass a
    precondition and both become effective (SEC-R3-01).

    `GET /health` deliberately does NOT take the lock: A.8 requires it to be
    served when everything else has failed closed, and it reads no authority
    state.
    """
    headers = headers or {}
    # R7 item 5 — before this process answers ANYTHING, including /health, it
    # has to find out whether a previous process quarantined this data
    # directory. A restart is not reconciliation.
    _ensure_quarantine_scanned()
    if method != "POST":
        return _dispatch_inner(method, path, payload, headers)
    # One lock, held across the whole request. `STORE.lock` is an RLock and the
    # only other lock in the service (SecretIndex's) is never held while
    # acquiring this one, so the acquisition order is total and no cycle — and
    # therefore no deadlock — is possible. See the Delivery Record's audit.
    with STORE.lock:
        # SEC-R4-01 item 3 — fail closed while storage integrity is unproven.
        # A quarantine means a success-named record may exist on disk for a
        # transition nothing else believes happened, so the service can no
        # longer speak truthfully about its own evidence. Every further
        # authority transition is refused until an operator recovers it;
        # `GET /health` still serves and reports why, per A.8.
        if STORE.storage_quarantine:
            return 503, {"refused": True, "outcome": "refused-storage-quarantine",
                         "reason": "capture storage is quarantined: a rollback "
                                   "could not be established, so evidence on "
                                   "disk may contradict this service's state. "
                                   "No further authority transition is accepted "
                                   "until this is recovered explicitly.",
                         "incidents": len(STORE.storage_quarantine),
                         "first_incident": STORE.storage_quarantine[0]}
        return _dispatch_inner(method, path, payload, headers)


def _dispatch_inner(method: str, path: str, payload: dict, headers: dict):
    policy = ROUTE_POLICY.get((method, path))
    handler = HANDLERS.get((method, path))
    if policy is None or handler is None:
        return 404, {"refused": True, "outcome": "refused-no-policy",
                     "reason": "no route-policy row for this request; failing closed"}

    if policy["caller"] != OPEN:
        need = "owner_key" if policy["caller"] == OWNER else "provider_key"
        want = STORE.owner_key if policy["caller"] == OWNER else STORE.provider_key
        got = headers.get(need) or ""
        if not isinstance(got, str) or not _ct_eq(got, want):
            why = ("owner-surface key missing or wrong; a decision must come from the "
                   "owner surface, and reaching this port is not evidence that it did"
                   if policy["caller"] == OWNER else
                   "provider credential missing or wrong")
            try:
                write_capture(path, _poc_for(path), "auth-refused",
                              {"refused": True, "outcome": "refused-auth",
                               "reason": why},
                              authored_by="owner-surface" if policy["caller"] == OWNER
                              else "provider", refusal=True,
                              # The caller did NOT authenticate as the owner —
                              # that is the whole content of this capture — so
                              # it must not draw from the reserved-owner pool.
                              owner_authenticated=False)
            except (CaptureError, QuotaError):
                pass
            return 403, {"refused": True, "reason": why, "outcome": "refused-auth"}

    if method == "POST":
        ok, why = _structural_ok(payload)
        if not ok:
            return _refuse(path, _poc_for(path), "structural-bounds", 400, why,
                           outcome="refused-bounds")
        if policy["decision_field"] == "refused":
            ok, why = _no_provider_decision(payload)
            if not ok:
                return _refuse(path, _poc_for(path), "provider-decision-refused", 403,
                               why, outcome="refused-provider-decision")
        if policy["envelope"] == "required":
            ok, why = _envelope_ok(payload)
            if not ok:
                return _refuse(path, _poc_for(path), "boundary-refused", 400, why,
                               outcome="refused-boundary")
    # SEC-R3-06 — central entity-quota enforcement, BEFORE the handler runs.
    # Global-scope quotas are reserved here; subject-scoped ones (`attempts`,
    # `checkpoints`, `stage-attempts`) are reserved inside the transition
    # against the subject the SERVICE resolved, because the only subject id
    # available at dispatch is the one the caller supplied, and `25_`'s
    # governing rule forbids resting a control on that. See AUDIT-R4-1.
    quota = policy.get("quota")
    reserved = None
    if method == "POST" and quota and QUOTA_SCOPE.get(quota) == "global":
        ok, why = _reserve_entity(quota)
        if not ok:
            return _refuse(path, _poc_for(path), "entity-quota", 429, why,
                           outcome="refused-quota")
        reserved = quota

    status = 500
    try:
        status, body = handler(payload or {})
        return status, body
    except QuotaError as exc:
        # A capture quota reached mid-handler. No evidence, no authority.
        status = exc.status
        return exc.status, {"refused": True, "outcome": "quota", "reason": str(exc)}
    except CaptureQuarantine as exc:
        # Item 3: never the ordinary ineffective claim. This is a DISTINCT
        # result — the transition may or may not be described by durable
        # evidence, and the service says exactly that rather than guessing.
        status = 503
        return 503, {"refused": True, "outcome": "refused-storage-quarantine",
                     "reason": str(exc), "storage_uncertain": True,
                     "transition_effective": "UNKNOWN — evidence on disk may "
                                             "describe this transition as "
                                             "committed; reconcile before use",
                     "detail": exc.detail}
    except CaptureError as exc:
        # A.7: the `prepared` record is written BEFORE state moves, so a failure
        # here means nothing was mutated — the request fails closed with a
        # structured refusal rather than a traceback. Failures of the *committed*
        # write are handled inside each handler, where the rollback lives.
        return 500, {"refused": True, "outcome": "capture-failed",
                     "reason": "an evidence record could not be written; the "
                               "transition is not effective: %s" % exc}
    except Exception as exc:                                     # noqa: BLE001
        # A.8: a route dispatch exception becomes a structured refusal with no
        # traceback in the response. The handler's own rollback has already run
        # (each re-raises after undoing its transition), so nothing is left
        # half-applied by the time this is reported.
        status = 500
        return 500, {"refused": True, "outcome": "refused-internal",
                     "reason": "internal error (%s); the transition did not "
                               "become effective" % type(exc).__name__}
    finally:
        # A reservation is consumed only by a transition that actually became
        # effective. Anything else gives the unit back.
        if reserved is not None:
            if 200 <= status < 300:
                _commit_entity(reserved)
            else:
                _release_entity(reserved)


# --------------------------------------------------------------------------
# HTTP surface
# --------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "poc-wrapper-stub"
    data_dir = "../data"
    timeout = SOCKET_TIMEOUT_S

    def log_message(self, fmt, *args):  # noqa: A003
        return

    def log_request(self, code="-", size="-"):  # noqa: A003
        return

    def log_error(self, fmt, *args):  # noqa: A003
        return

    def _respond(self, status, body, matched="<unmatched>"):
        # `disclose=True` on the response path ONLY: it unwraps values the
        # service minted for this recipient (Disclose) and redacts everything
        # else exactly as a capture would. Captures and logs never pass it.
        raw = json.dumps(redact(body, disclose=True),
                         indent=2, sort_keys=True).encode("utf-8")
        try:
            self.send_response_only(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("X-Throwaway", "poc-evidence-apparatus")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            self.wfile.write(raw)
        except OSError:
            pass
        sys.stderr.write("%s %s\n" % (matched, status))

    def _headers(self):
        return {"owner_key": self.headers.get("X-Owner-Key") or "",
                "provider_key": self.headers.get("X-Provider-Key") or ""}

    def _label(self, method, path):
        policy = ROUTE_POLICY.get((method, path))
        return policy["log"] if policy else "<unmatched>"

    def do_GET(self):  # noqa: N802
        path = self.path.split("?")[0]
        label = self._label("GET", path)
        try:
            status, body = dispatch("GET", path, {}, self._headers())
        except Exception:
            status, body = 500, {"refused": True, "reason": "internal error"}
        self._respond(status, body, label)

    def do_POST(self):  # noqa: N802
        path = self.path.split("?")[0]
        label = self._label("POST", path)
        lengths = self.headers.get_all("Content-Length") or []
        if len(set(lengths)) > 1:
            self._respond(400, {"refused": True,
                                "reason": "conflicting Content-Length headers"}, label)
            return
        te = (self.headers.get("Transfer-Encoding") or "").strip().lower()
        if te not in ("", "identity"):
            self._respond(501, {"refused": True,
                                "reason": "unsupported transfer encoding"}, label)
            return
        try:
            length = int(lengths[0]) if lengths else 0
        except ValueError:
            self._respond(400, {"refused": True, "reason": "malformed Content-Length"}, label)
            return
        if length < 0:
            self._respond(400, {"refused": True, "reason": "negative Content-Length"}, label)
            return
        if length > MAX_BODY:
            self._respond(413, {"refused": True, "reason": "body too large"}, label)
            return
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype != "application/json":
            self._respond(415, {"refused": True,
                                "reason": "Content-Type must be application/json"}, label)
            return
        try:
            raw = self.rfile.read(length) if length else b"{}"
        except (OSError, TimeoutError):
            self._respond(408, {"refused": True, "reason": "request body timed out"}, label)
            return
        if len(raw) != length:
            self._respond(400, {"refused": True, "reason": "short body"}, label)
            return
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            self._respond(400, {"refused": True, "reason": "body is not valid JSON"}, label)
            return
        if not isinstance(payload, dict):
            self._respond(400, {"refused": True, "reason": "body must be a JSON object"}, label)
            return
        try:
            status, body = dispatch("POST", path, payload, self._headers())
        except Exception:
            status, body = 500, {"refused": True, "reason": "internal error",
                                 "outcome": "refused-internal"}
        self._respond(status, body, label)


def serve(port: int, data_dir: str, advertise: str = None):
    Handler.data_dir = data_dir
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    bound = srv.server_address[1]
    STORE.base_url = advertise or ("http://127.0.0.1:%d" % bound)
    sys.stderr.write(
        "%s\ncandidate=%s  run_instance=%s\nlistening on http://127.0.0.1:%d "
        "(advertising %s; data dir: %s)\n"
        % (THROWAWAY, STORE.candidate, STORE.run_instance, bound,
           STORE.base_url, os.path.abspath(data_dir)))
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
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--advertise", default=None)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "..", "data"))
    args = ap.parse_args(argv)
    if not CANDIDATE_NAME.match(args.candidate):
        sys.stderr.write("refusing to start: --candidate %r is not a valid name\n"
                         % args.candidate)
        return 2
    global STORE
    STORE = Store(candidate=args.candidate)
    serve(args.port, args.data, args.advertise)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1:]))

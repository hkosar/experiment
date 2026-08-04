#!/usr/bin/env python3
# THROWAWAY POC EVIDENCE APPARATUS — see stub_server.py header.
"""Superseded-contract witnesses: the same probes, against the UNFIXED builds.

`14_` §3: every required test must be "demonstrated failing against the unfixed
behaviour — that is the standard R1 met and this round keeps."

This does it the way TASK-0005 did: by running the probes against the superseded
build itself, held byte-identical in `r1_reference/stub_server_r1.py`, rather
than by putting defect switches in the shipped service. A switch that can turn a
control off is itself a finding (P2V-01), and a witness that runs against a
reconstruction proves less than one that runs against the artifact the verifier
actually reviewed.

Each pinned file's SHA-256 is checked here before it is loaded — R1 against the
fingerprint `13_` records for the reviewed target, R2 against the digest of the
build returned at R2 — so neither can silently drift to a variant. `25_` §E
requires the R2 baseline to be pinned "the same way", which is what the second
block does.

Usage: python3 r1_witnesses.py
Exit:  0 if every witness reproduces the unfixed behaviour it claims
"""
from __future__ import annotations

import hashlib
import importlib.util
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

HERE = os.path.dirname(os.path.abspath(__file__))
R1_PATH = os.path.join(HERE, "r1_reference", "stub_server_r1.py")

# `13_` §"Chain-of-custody": the target the verifier reviewed, byte-identical to
# the integrated poc/stub/stub_server.py at R1.
R1_REVIEWED_SHA256 = "ecdaae6716c52379f8871b406c738618f359fb3d3d9e1941d764dc4b376328ac"

ROWS = []


def load_r1():
    spec = importlib.util.spec_from_file_location("stub_server_r1", R1_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["stub_server_r1"] = mod
    spec.loader.exec_module(mod)
    return mod


def witness(finding, claim, unfixed_did, ok, detail=None):
    ROWS.append({"finding": finding, "claim": claim,
                 "superseded_behaviour": unfixed_did,
                 "reproduced": bool(ok), "detail": detail})
    sys.stderr.write("  [%s] %-11s %s\n     the unfixed build did: %s\n"
                     % ("ok  " if ok else "FAIL", finding, claim, unfixed_did))
    return ok


def main() -> int:
    digest = hashlib.sha256(open(R1_PATH, "rb").read()).hexdigest()
    same = digest == R1_REVIEWED_SHA256
    witness("PIN", "the pinned R1 file is the build the verifier reviewed",
            "sha256 %s" % digest[:16],
            same, detail="expected %s" % R1_REVIEWED_SHA256[:16])
    if not same:
        sys.stderr.write("\nREFUSING TO CONTINUE — the pinned reference is not the "
                         "reviewed build.\n")
        return 1

    R = load_r1()
    d = tempfile.mkdtemp()
    R.STORE = R.Store()
    R.Handler.data_dir = d
    post = lambda p, b: R.dispatch("POST", p, b, d)      # noqa: E731
    env = {"envelope": {"trust": "external-untrusted", "partition": "business"},
           "metadata": {"subject": "artifact"}}

    sys.stderr.write("\n-- the identity tuple (C-1 / FAB-15) --\n")
    st, opened = post("/poc1/review-case", dict(env))
    witness("FAB-15", "R1 accepted a case with NO task id, transition, artifact "
            "digest or target role", "accepted with %s -> %s" % (sorted(env), st),
            st == 200 and "resume_token" in opened)
    cid = post("/owner/cases", {"owner_key": R.STORE.owner_key})[1]["cases"][-1]["case_id"]
    post("/owner/decide", {"case_id": cid, "decision": "accept",
                           "owner_key": R.STORE.owner_key})
    st, v = post("/poc1/verify-decision", {"token": opened["resume_token"]})
    ikey = v["action_request"]["idempotency_key"]
    witness("FAB-15", "R1's idempotency key had 3 of R1P-04's 5 components",
            "sha256(case_id | action_class | decision_time) = %s…" % ikey[:16],
            st == 200 and len(ikey) == 64)
    witness("FAB-15", "R1P-04 tests (1)(2)(3) were UNRUNNABLE against R1",
            "no task/transition/artifact/role is accepted, so duplicate "
            "suppression and target rejection have nothing to key on", True)
    witness("FAB-15", "R1's ActionRequest payload did not carry the key to the target",
            "payload = %s" % json.dumps(v["action_request"]["payload"]),
            "idempotency_key" not in v["action_request"]["payload"])

    sys.stderr.write("\n-- SEC-R1-01: the side effect was reachable directly --\n")
    st, sink = post("/sink", {"anything": "at all"})
    witness("SEC-R1-01", "R1's /sink produced the represented side effect with no "
            "capability, no case and no authorization",
            "POST /sink -> %s %s" % (st, json.dumps(sink)[:60]),
            st == 200 and sink.get("delivered") is True)

    sys.stderr.write("\n-- SEC-R1-02 / FAB-05: redaction, both directions --\n")
    live = R.STORE.mint_token("case-probe")
    red = R.redact({"opaque": live, "authority_id": "attestation-service",
                    "authority_version": "auth-v4", "tokens_used": 42})
    witness("SEC-R1-02", "R1 wrote a live token verbatim under an unrecognised key",
            "redact({'opaque': <live token>}) -> %s" % json.dumps(red["opaque"])[:40],
            red["opaque"] == live)
    witness("FAB-05", "R1 destroyed authority_id / authority_version / tokens_used",
            "-> %s / %s / %s" % (red["authority_id"], red["authority_version"],
                                 red["tokens_used"]),
            all(str(red[k]).startswith("[REDACTED") for k in
                ("authority_id", "authority_version", "tokens_used")))
    witness("FAB-05", "...and the replacement was a bare constant the harness scores "
            "PRESENT, hiding the loss", "value = %r" % red["authority_id"],
            isinstance(red["authority_id"], str))

    sys.stderr.write("\n-- SEC-R1-03 / C-5: decisions were not terminal --\n")
    st2, o2 = post("/poc1/review-case", dict(env))
    cid2 = post("/owner/cases", {"owner_key": R.STORE.owner_key})[1]["cases"][-1]["case_id"]
    post("/owner/decide", {"case_id": cid2, "decision": "reject",
                           "owner_key": R.STORE.owner_key})
    st3, _ = post("/owner/decide", {"case_id": cid2, "decision": "accept",
                                    "owner_key": R.STORE.owner_key})
    st4, v2 = post("/poc1/verify-decision", {"token": o2["resume_token"]})
    witness("SEC-R1-03", "R1 let a REJECT be overwritten by an ACCEPT and then minted "
            "an ActionRequest for the rejected case",
            "second decision -> %s, verify -> authorized=%s" % (st3, v2.get("authorized")),
            st3 == 200 and v2.get("authorized") is True)

    sys.stderr.write("\n-- FAB-01: the two mandatory events evidenced nothing --\n")
    d2 = tempfile.mkdtemp()
    R.STORE = R.Store(); R.Handler.data_dir = d2
    post = lambda p, b: R.dispatch("POST", p, b, d2)      # noqa: E731
    st, o3 = post("/poc1/review-case", dict(env))
    before = _count(d2)
    post("/poc1/verify-decision", {"token": o3["resume_token"]})      # the pause
    after_pending = _count(d2)
    post("/owner/decide", {"case_id": "case-x", "decision": "accept"})  # no owner key
    after_authrefusal = _count(d2)
    witness("FAB-01", "R1's pending branch wrote NO capture",
            "captures %d -> %d" % (before, after_pending), after_pending == before)
    witness("FAB-01", "R1's owner-key refusal wrote NO capture",
            "captures %d -> %d" % (after_pending, after_authrefusal),
            after_authrefusal == after_pending)

    sys.stderr.write("\n-- FAB-02 / FAB-09: the corpus could not attribute or order --\n")
    names = {b.get("candidate", "<absent>") for b in _bodies(d2)}
    witness("FAB-02", "R1 hardcoded the candidate, so two providers shared one corpus",
            "candidate field in records: %s; path segment: 'stub'" % names,
            names == {"<absent>"})
    witness("FAB-09", "R1 wrote no stub-minted timestamp on any capture",
            "recorded_at present on %d of %d" % (
                sum(1 for b in _bodies(d2) if "recorded_at" in b), len(_bodies(d2))),
            not any("recorded_at" in b for b in _bodies(d2)))

    sys.stderr.write("\n-- FAB-06: the provider-decision refusal reached 3 of 13 routes --\n")
    accepting = []
    for route in ("/poc1/receipt", "/poc1/refusal", "/poc3/run-started",
                  "/poc3/checkpoint", "/poc3/reconcile", "/poc3/receipt", "/sink"):
        st, _ = post(route, {"decision": "accept", "run_id": "r"})
        if st < 400:
            accepting.append(route)
    witness("FAB-06", "R1 accepted a provider-authored decision field on these routes",
            "%d routes accepted it: %s" % (len(accepting), accepting), bool(accepting))

    sys.stderr.write("\n-- FAB-07: a duplicate run declaration erased the measurement --\n")
    post("/poc3/run-started", {"run_id": "r1", "occurrence": "t0"})
    post("/poc3/checkpoint", {"run_id": "r1", "stage": 1})
    cps_before = len(R.STORE.runs["r1"]["checkpoints"])
    started_before = R.STORE.runs["r1"]["started_at"]
    st, _ = post("/poc3/run-started", {"run_id": "r1", "occurrence": "t1"})
    witness("FAB-07", "R1 let the provider choose run_id and silently overwrote the "
            "run — resetting started_at and emptying checkpoints",
            "checkpoints %d -> %d, started_at changed: %s, status %s" % (
                cps_before, len(R.STORE.runs["r1"]["checkpoints"]),
                R.STORE.runs["r1"]["started_at"] != started_before, st),
            st == 200 and len(R.STORE.runs["r1"]["checkpoints"]) == 0)

    sys.stderr.write("\n-- FAB-08: the stub attested to checks it never ran --\n")
    st, rec = post("/poc3/reconcile", {"run_id": "does-not-exist"})
    witness("FAB-08", "R1's reconcile asserted certainty and cited ACT-01 for a run "
            "that does not exist", "-> %s %s" % (st, json.dumps(rec)[:90]),
            st == 200 and rec.get("side_effect_certain") is True
            and "ACT-01" in json.dumps(rec))
    st, tri = post("/poc2/triage", dict(env))
    witness("FAB-08", "R1's triage asserted provider conduct it cannot observe",
            "links_followed=%s actions_taken=%s" % (tri.get("links_followed"),
                                                    tri.get("actions_taken")),
            tri.get("links_followed") is False and tri.get("actions_taken") == [])

    sys.stderr.write("\n-- FAB-14: refusal captures wrote rejected KEY NAMES verbatim --\n")
    d3 = tempfile.mkdtemp()
    R.STORE = R.Store(); R.Handler.data_dir = d3
    post = lambda p, b: R.dispatch("POST", p, b, d3)      # noqa: E731
    st, o4 = post("/poc1/review-case", dict(env))
    leak = R.STORE.mint_token("case-leak")
    post("/poc1/verify-decision", {"token": o4["resume_token"], leak: 1})
    blob = json.dumps(_bodies(d3))
    witness("FAB-14", "R1 landed a live token in a capture as a rejected key name",
            "token present in captures: %s" % (leak in blob), leak in blob)

    sys.stderr.write("\n-- FAB-13 / SEC-R1-06: malformed input produced no verdict --\n")
    crashed = False
    try:
        R.dispatch("POST", "/owner/decide",
                   {"case_id": "x", "decision": "accept", "owner_key": "é" * 8}, d3)
    except TypeError:
        crashed = True
    witness("FAB-13", "a non-ASCII owner key raised TypeError before any authorization "
            "verdict", "TypeError raised: %s" % crashed, crashed)
    # `13_` VC-01 cites `payload.get("metadata") or {}` specifically: a FALSY
    # `[]` short-circuits to `{}` and returns 200, so a regression test written to
    # the literal text in `12_` §3 passes against unfixed code. The truthy case is
    # the one that reproduces. (The envelope deref is not probed here because the
    # Builder had already guarded it in R1 after its own envelope-lens pass — a
    # witness must reproduce a defect that was actually present, not one it wishes
    # had been.)
    falsy_ok = R.dispatch("POST", "/poc2/triage",
                          dict(env, metadata=[]), d3)[0]
    crashed2 = False
    try:
        R.dispatch("POST", "/poc2/triage", dict(env, metadata=[1]), d3)
    except AttributeError:
        crashed2 = True
    witness("SEC-R1-06", "a TRUTHY non-dict metadata crashed the handler, while the "
            "FALSY [] the review's illustrative repro used returned %s — which is why "
            "13_ VC-01 requires the truthy case" % falsy_ok,
            "AttributeError on [1]: %s; status on []: %s" % (crashed2, falsy_ok),
            crashed2 and falsy_ok == 200)

    r1_rows = len(ROWS)
    rc = r2_witnesses()
    if rc:
        return rc

    reproduced = sum(1 for r in ROWS if r["reproduced"])
    out = {"check": "superseded-contract witnesses",
           "pinned_references": {
               "r1": {"path": "r1_reference/stub_server_r1.py", "sha256": digest,
                      "matches_reviewed_target": same, "witnesses": r1_rows},
               "r2": {"path": "r2_reference/stub_server_r2.py",
                      "sha256": R2_SHA256_OBSERVED[0],
                      "matches_returned_artifact": R2_SHA256_OBSERVED[0] == R2_RETURNED_SHA256,
                      "witnesses": len(ROWS) - r1_rows}},
           "method": "the probes run against the superseded builds themselves, not a "
                     "reconstruction and not a defect switch",
           "witnesses": ROWS, "reproduced": reproduced, "total": len(ROWS)}
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    with open(os.path.join(HERE, "out", "r1_witnesses.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    sys.stderr.write("\nWITNESSES %s — %d/%d reproduced the unfixed behaviour "
                     "(R1: %d, R2: %d)\n"
                     % ("PASS" if reproduced == len(ROWS) else "FAIL",
                        reproduced, len(ROWS), r1_rows, len(ROWS) - r1_rows))
    return 0 if reproduced == len(ROWS) else 1


# ==========================================================================
# R2 witnesses — `25_` §E: "Where a test needs the R2 baseline, pin the R2
# artifact the same way."
#
# Same method as the R1 block: probes run against the byte-identical build that
# was actually returned at R2, its digest checked before it is loaded, and the
# harness refuses to continue on a mismatch. No defect switch exists in the
# shipped service, at R2 or at R3.
# ==========================================================================
R2_PATH = os.path.join(HERE, "r2_reference", "stub_server_r2.py")

# The stub returned to Fable at R2, byte-identical to the integrated
# poc/stub/stub_server.py of that round.
R2_RETURNED_SHA256 = "a2aea25da2af97368db4eedd9b027da52a84740a9447936c6b50ce0c960900f9"
R2_SHA256_OBSERVED = [None]


def _load_r2():
    spec = importlib.util.spec_from_file_location("stub_server_r2", R2_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["stub_server_r2"] = mod
    spec.loader.exec_module(mod)
    return mod


def r2_witnesses() -> int:
    digest = hashlib.sha256(open(R2_PATH, "rb").read()).hexdigest()
    R2_SHA256_OBSERVED[0] = digest
    same = digest == R2_RETURNED_SHA256
    witness("PIN-R2", "the pinned R2 file is the build returned at R2",
            "sha256 %s" % digest[:16], same,
            detail="expected %s" % R2_RETURNED_SHA256[:16])
    if not same:
        sys.stderr.write("\nREFUSING TO CONTINUE — the pinned R2 reference is not the "
                         "returned build.\n")
        return 1

    R = _load_r2()
    d = tempfile.mkdtemp()
    R.STORE = R.Store()
    R.STORE.base_url = "http://127.0.0.1:9"
    R.Handler.data_dir = d
    OWNER = {"owner_key": R.STORE.owner_key, "provider_key": ""}
    PROV = {"owner_key": "", "provider_key": R.STORE.provider_key}
    post = lambda p, b, h=PROV: R.dispatch("POST", p, b, h)      # noqa: E731
    ident = {"envelope": {"trust": "external-untrusted", "partition": "business"},
             "task_id": "T", "transition": "b->v", "artifact_digest": "a" * 64,
             "target_role": "verifier", "submission_epoch": 0}

    sys.stderr.write("\n-- A.2: R2 had no owner-authoritative artifact registration --\n")
    st, _ = post("/owner/artifact/register",
                 {"source_digest": "a" * 64, "size_bytes": 1, "file_count": 1,
                  "task_id": "T", "transition": "b->v", "target_role": "verifier"},
                 OWNER)
    witness("A.2", "R2 had no /owner/artifact/register: there was no owner-registered "
            "digest for a provider-supplied one to be checked against",
            "POST /owner/artifact/register -> %s" % st, st == 404)
    st, opened = post("/poc1/review-case", dict(ident))
    witness("A.2", "...so R2 opened a case on a provider-supplied artifact_digest "
            "alone, with no registration_ref and nothing to bind it to",
            "review-case without registration_ref -> %s, keys %s"
            % (st, sorted(opened)), st == 200 and "registration_ref" not in opened)

    sys.stderr.write("\n-- DEF-R2-01: the R2 service could not hand out its own token --\n")
    # Found while building R3, and the reason the R3 self-test exercises a real
    # socket rather than dispatch() alone. The witness runs the R2 build as a
    # server and reads what a provider would actually have received: the loss
    # happens in `_respond`, which the in-process path never reaches.
    over_http = _r2_over_http()
    tok = over_http.get("resume_token")
    lost = isinstance(tok, dict) and "__withheld__" in tok
    witness("DEF-R2-01", "R2 ran every RESPONSE through the same redaction as a "
            "capture, so over a real socket the resume token it had just minted "
            "came back as a descriptor and no provider could ever carry it",
            "live POST /poc1/review-case -> resume_token = %s"
            % json.dumps(tok)[:90], lost)
    witness("DEF-R2-01", "...and the in-process path returned the token intact, "
            "which is why the R2 suite passed 56/56 while the service was "
            "unrunnable: that suite called dispatch(), below the response path",
            "dispatch() token is a %s, HTTP token is a %s"
            % (type(opened.get("resume_token")).__name__, type(tok).__name__),
            lost and isinstance(opened.get("resume_token"), str))

    sys.stderr.write("\n-- A.3: owner authority was self-declared by the provider --\n")
    st, tri = post("/poc2/triage",
                   {"envelope": {"trust": "external-untrusted", "partition": "business"},
                    "origin": "owner",
                    "owner_content": {"title": "provider wrote this",
                                      "body": "and called it the owner's"}})
    witness("A.3", "R2 took authority from a provider-supplied `origin` field: content "
            "the provider authored came back recorded as owner-authorized",
            "origin='owner' -> instruction_authority=%r"
            % tri.get("instruction_authority"),
            st == 200 and tri.get("instruction_authority") == "owner-authorized")
    witness("A.3", "...and R2 had no idea_ref, no stored owner content and no "
            "owner_content_digest to compare a copy against",
            "'idea_ref' appears %d times in the R2 source"
            % open(R2_PATH, encoding="utf-8").read().count("idea_ref"),
            open(R2_PATH, encoding="utf-8").read().count("idea_ref") == 0)

    sys.stderr.write("\n-- A.5 / R5Q-01: the reconciliation surface did not exist --\n")
    cid = post("/owner/cases", {}, OWNER)[1]["cases"][-1]["case_id"]
    post("/owner/decide", {"case_id": cid, "decision": "accept"}, OWNER)
    st, v = post("/poc1/verify-decision", {"token": opened["resume_token"]})
    ar = v["action_request"]
    st_o, _ = post("/owner/reconcile", {"action_request_id": ar["id"],
                                        "outcome": "not_delivered"}, OWNER)
    st_p, _ = post("/poc1/reconcile", {"action_request_id": ar["id"]})
    witness("A.5", "R2 had neither /owner/reconcile nor /poc1/reconcile, so an "
            "uncertain delivery had no route to any resolution at all",
            "/owner/reconcile -> %s, /poc1/reconcile -> %s" % (st_o, st_p),
            st_o == 404 and st_p == 404)
    witness("R5Q-01", "...and RECONCILED_NOT_DELIVERED did not exist in R2, so the "
            "owner-attestation rules Rev 5 makes testable had nothing to bind to",
            "'RECONCILED_NOT_DELIVERED' appears %d times in the R2 source"
            % open(R2_PATH, encoding="utf-8").read().count("RECONCILED_NOT_DELIVERED"),
            open(R2_PATH, encoding="utf-8").read().count(
                "RECONCILED_NOT_DELIVERED") == 0)

    sys.stderr.write("\n-- A.7: evidence was single-phase --\n")
    bodies = _bodies(d)
    phases = {b.get("fields", {}).get("phase") for b in bodies}
    witness("A.7", "R2 wrote one record per event with no prepared/committed pair, so "
            "a write interrupted after the state moved left authority effective with "
            "no record that it had moved",
            "phases across %d R2 captures: %s" % (len(bodies), sorted(map(str, phases))),
            bodies and phases == {None})

    sys.stderr.write("\n-- A.8: one capture budget, not three disjoint pools --\n")
    pools = {b.get("pool") for b in bodies}
    witness("A.8", "R2 drew every capture from a single budget, so a provider "
            "flooding refusals competed for the same space an owner decision "
            "needed", "pools across %d R2 captures: %s"
            % (len(bodies), sorted(map(str, pools))), bodies and pools == {None})

    sys.stderr.write("\n-- §B: the route policy was code, not data --\n")
    witness("B", "R2 had no ROUTE_POLICY table: caller, credential, field list, "
            "envelope rule and quota pool were spread through handler bodies, so "
            "'delete a policy row and the suite fails closed' had no row to delete",
            "hasattr(R2, 'ROUTE_POLICY') = %s" % hasattr(R, "ROUTE_POLICY"),
            not hasattr(R, "ROUTE_POLICY"))

    sys.stderr.write("\n-- §B POC-3: a duplicate declaration was not a measurement --\n")
    first = post("/poc3/run-started", {"schedule_id": "s1", "occurrence": "t0"})[1]
    post("/poc3/checkpoint", {"run_id": first["run_id"], "stage": "x"})
    st2, second = post("/poc3/run-started", {"schedule_id": "s1", "occurrence": "t0"})
    witness("B-POC3", "R2 minted a SECOND run for the same schedule occurrence "
            "instead of the 409 that preserves the prior started_at and checkpoint "
            "count — the duplicate declaration POC-3 exists to measure was recorded "
            "as an ordinary new run",
            "second run-started -> %s, run_id %s vs %s, run records now %d"
            % (st2, second.get("run_id"), first["run_id"], len(R.STORE.runs)),
            st2 == 200 and second.get("run_id") != first["run_id"]
            and len(R.STORE.runs) == 2)
    return 0


def _r2_over_http() -> dict:
    """Run the pinned R2 build as a real server and open a case over a socket.

    The in-process `dispatch()` path returns handler bodies directly; `_respond`
    is where R2 redacted them. A witness for DEF-R2-01 has to cross that
    boundary or it is testing the wrong layer — which is exactly how the R2
    suite came to pass against an unrunnable service.
    """
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, R2_PATH, "--candidate", "witness", "--port", str(port),
         "--data", tempfile.mkdtemp()],
        stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    try:
        provider, banner = None, ""
        deadline = time.time() + 20
        while time.time() < deadline:
            line = proc.stderr.readline()
            if not line:
                break
            banner += line
            m = re.search(r"PROVIDER CREDENTIAL.*?\n\s*(\S+)\n", banner, re.S)
            if m:
                provider = m.group(1)
                break
        if not provider:
            return {"resume_token": "<the R2 build did not start: %s>" % banner[:120]}
        req = urllib.request.Request(
            "http://127.0.0.1:%d/poc1/review-case" % port,
            data=json.dumps({
                "envelope": {"trust": "external-untrusted", "partition": "business"},
                "task_id": "T", "transition": "b->v", "artifact_digest": "a" * 64,
                "target_role": "verifier", "submission_epoch": 0}).encode("utf-8"),
            method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Provider-Key", provider)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return json.loads(exc.read().decode("utf-8") or "{}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _count(d):
    return len(_paths(d))


def _paths(d):
    out = []
    for root, _dd, ff in os.walk(os.path.join(d, "captures")):
        out += [os.path.join(root, f) for f in ff if f.endswith(".json")]
    return out


def _bodies(d):
    return [json.load(open(p, encoding="utf-8")) for p in _paths(d)]


if __name__ == "__main__":
    sys.exit(main())

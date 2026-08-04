#!/usr/bin/env python3
# THROWAWAY POC EVIDENCE APPARATUS — see stub_server.py header.
"""Run the independent reviewer's probe scripts against a named stub build.

`33_` §4 requires the reviewer's own probe scripts to run green against the
reworked build, and `33_` §5 requires the same probes to be demonstrated failing
against the pinned R3 artifact. This module is the shared runner both directions
use — `r1_witnesses.py` points it at `r3_reference/stub_server_r3.py`,
`selftest_stub.py` points it at the live build.

Two rules make the result mean something:

1. **The probes are not edited.** Each script hard-codes the reviewer's own
   absolute `SRC=` path, which does not exist outside its sandbox. The runner
   rewrites that one line and then verifies, line by line, that **every other
   byte is unchanged** — refusing to run the probe if anything else differs. A
   probe I was free to adjust would prove nothing about a build I also wrote.

2. **The pass criteria come from the findings, not from me.** Eight of the nine
   probes have no assertions; they print JSON and the reviewer read it. Each
   criterion below is quoted or directly derived from the corresponding finding
   in `31_`, and `security_probes/README.md` tabulates them next to their source
   so it can be checked that none was weakened in transit.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE_DIR = os.path.join(HERE, "security_probes")
SRC_LINE = re.compile(r"^SRC\s*=\s*'[^']*'\s*$")


class ProbeError(RuntimeError):
    pass


def _retarget(probe_path: str, target: str) -> str:
    """Rewrite ONLY the SRC= line; prove nothing else changed."""
    original = open(probe_path, encoding="utf-8").read().splitlines(keepends=True)
    out, hits = [], 0
    for line in original:
        if SRC_LINE.match(line.rstrip("\n")):
            out.append("SRC=%r\n" % target)
            hits += 1
        else:
            out.append(line)
    if hits != 1:
        raise ProbeError("%s: expected exactly one SRC= line, found %d"
                         % (os.path.basename(probe_path), hits))
    # Prove the substitution is the only difference.
    diffs = [i for i, (a, b) in enumerate(zip(original, out)) if a != b]
    if len(diffs) != 1 or not SRC_LINE.match(original[diffs[0]].rstrip("\n")):
        raise ProbeError("%s: the retarget changed more than the SRC line"
                         % os.path.basename(probe_path))
    if len(original) != len(out):
        raise ProbeError("%s: the retarget changed the line count"
                         % os.path.basename(probe_path))
    path = os.path.join(tempfile.mkdtemp(prefix="probe-"),
                        os.path.basename(probe_path))
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(out)
    return path


def run_probe(name: str, target: str, timeout: int = 180) -> dict:
    """Execute one probe against `target`; return its parsed JSON stdout."""
    probe = os.path.join(PROBE_DIR, name + ".py")
    if not os.path.exists(probe):
        raise ProbeError("probe %s is not present" % name)
    if name in ARGV_PROBES:
        # No retargeting at all: these take the target as argv[1], so they run
        # byte-identical with nothing rewritten.
        argv = [sys.executable, probe, target]
        cwd = PROBE_DIR
    else:
        retargeted = _retarget(probe, target)
        argv = [sys.executable, retargeted]
        cwd = os.path.dirname(retargeted)
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                          cwd=cwd)
    body = proc.stdout.strip()
    if not body:
        raise ProbeError("%s produced no output (rc=%s): %s"
                         % (name, proc.returncode, proc.stderr.strip()[-400:]))
    try:
        return json.loads(body)
    except ValueError:
        # a couple of probes print more than one JSON document
        for chunk in re.findall(r"\{.*\}", body, re.S):
            try:
                return json.loads(chunk)
            except ValueError:
                continue
        raise ProbeError("%s: stdout is not JSON: %s" % (name, body[:300]))


# --------------------------------------------------------------------------
# Pass criteria — each traceable to the finding that states it.
# Every function returns (green: bool, detail: str).
# --------------------------------------------------------------------------
def _c_http_race(r):
    d = r.get("http_review_race", {})
    outs = d.get("outcomes") or []
    green = (d.get("case_count") == 1 and d.get("token_count") == 1
             and outs.count("case-opened") == 1
             and outs.count("duplicate-suppressed") == 1)
    return green, ("cases=%s tokens=%s outcomes=%s"
                   % (d.get("case_count"), d.get("token_count"), outs))


def _c_authority(r):
    t, c = r.get("token_spend", {}), r.get("capability_spend", {})
    caps = [x for x in (t.get("capabilities") or []) if x]
    ars = [x for x in (t.get("action_ids") or []) if x]
    token_green = (t.get("authorized", []).count(True) == 1
                   and len(set(caps)) == 1 and len(set(ars)) == 1
                   and t.get("store_capability_count") == 1)
    rec = [x for x in (c.get("receipt_ids") or []) if x]
    cap_green = ((c.get("delivered") or []).count(True) == 1
                 and len(set(rec)) == 1)
    return token_green and cap_green, (
        "token: authorized=%s caps=%d ars=%d store=%s | capability: delivered=%s receipts=%s"
        % (t.get("authorized"), len(set(caps)), len(set(ars)),
           t.get("store_capability_count"), c.get("delivered"), sorted(set(rec))))


def _c_revoke(r):
    # SEC-R3-02: "Once revocation returns success, no later delivery may become
    # effective under the revoked generation."
    revoked_ok = (r.get("revoke") or [None])[0] == 200
    green = revoked_ok and r.get("final_status") == "REVOKED" and r.get("receipt") is None
    return green, ("revoke=%s final_status=%s receipt=%s"
                   % ((r.get("revoke") or [None])[0], r.get("final_status"),
                      "present" if r.get("receipt") else "none"))


def _one_winner(outcomes, winner, loser):
    """Exactly one winner and the rest truthful losers — SEC-R3-01's cardinality."""
    outs = list(outcomes or [])
    return (outs.count(winner) == 1
            and all(o == loser for o in outs if o != winner)
            and len(outs) >= 2)


def _c_more_races(r):
    # Keyed on the fields the probe actually emits, read from its own recorded
    # output rather than guessed. An earlier draft of this criterion looked for
    # `*_count` keys, found none, and passed VACUOUSLY against the build it was
    # supposed to fail — the exact shape of defect this round exists to remove,
    # so it is named here rather than quietly corrected.
    reg = r.get("registration_race", {})
    run = r.get("run_declaration_race", {})
    green = (reg.get("registrations") == 1
             and len(set(reg.get("refs") or [])) == 1
             and run.get("runs") == 1
             and len(set(run.get("run_ids") or [])) == 1)
    return green, ("registrations=%s distinct_refs=%s | runs=%s distinct_run_ids=%s"
                   % (reg.get("registrations"), len(set(reg.get("refs") or [])),
                      run.get("runs"), len(set(run.get("run_ids") or []))))


# `security_probes` runs eight sub-probes; each gets its own branch-specific
# criterion, traceable to the finding it evidences.
def _s_review(d):
    return d.get("case_count") == 1 and d.get("token_count") == 1


def _s_token(d):
    return (d.get("authorized", []).count(True) == 1
            and d.get("capability_count") == 1
            and len(set(d.get("action_request_ids") or [])) == 1)


def _s_capability(d):
    return (d.get("delivered", []).count(True) == 1
            and len(set(d.get("receipt_ids") or [])) == 1)


def _s_expiry(d):
    # SEC-R3-04: expiry must not be a silent status flip. Either an
    # evidence-backed transition (named captures + a transition delta) or a
    # derived state; this build chose the transition, so both must be present.
    return bool(d.get("expiration_named_captures")) and d.get("transition_count_delta", 0) > 0


def _s_secret_index(d):
    # SEC-R3-03: no `committed` record for a capability mint that never became
    # effective. capability_count 0 => commit_count must be 0.
    return d.get("commit_count") == 0 and d.get("capability_count") == 0


def _s_case_capture(d):
    # SEC-R3-03: no `case-opened` capture describing a case that does not exist.
    steps = [c.get("step") for c in (d.get("captures") or [])]
    outs = [c.get("fields", {}).get("outcome") for c in (d.get("captures") or [])]
    if d.get("case_count") == 0:
        return "review-case" not in steps and "case-opened" not in outs
    return True


def _s_revoke(d):
    return (d.get("revoke_status") == 200
            and d.get("final_capability_status") == "REVOKED"
            and d.get("receipt_present") is False
            and d.get("relay_delivered") is not True)


def _s_stage(d):
    # NOTE ON THIS ORACLE, because the field name invites the wrong reading.
    # `attempt_after_failure` is sampled at result-construction time, i.e. AFTER
    # both the forced-failure attempt and the following successful one. The
    # finding's requirement — "a capture-failed response must not leave the
    # counter advanced" — therefore means the counter reads 1 here (only the
    # successful attempt counted) and the successful attempt reports itself as
    # attempt 1. The R3 build recorded 2 and 2. An earlier draft of this
    # criterion demanded 0, which no correct build could produce.
    return d.get("attempt_after_failure") == 1 and d.get("second_attempt") == 1


SECURITY_SUBCHECKS = {
    "concurrent_review_case": ("SEC-R3-01", _s_review),
    "concurrent_token_spend": ("SEC-R3-01", _s_token),
    "concurrent_capability_spend": ("SEC-R3-01", _s_capability),
    "expiry_without_transition_evidence": ("SEC-R3-04", _s_expiry),
    "false_capability_commit_on_secret_index_failure": ("SEC-R3-03", _s_secret_index),
    "false_case_opened_capture_on_token_failure": ("SEC-R3-03", _s_case_capture),
    "revoke_vs_delivery_race": ("SEC-R3-02", _s_revoke),
    "stage_attempt_mutates_without_capture": ("SEC-R3-04", _s_stage),
}


def _c_security(r):
    results, missing = {}, []
    for key, (finding, check) in sorted(SECURITY_SUBCHECKS.items()):
        if key not in r:
            missing.append(key)
            results[key] = False
            continue
        results[key] = bool(check(r[key]))
    green = bool(results) and all(results.values()) and not missing
    failed = sorted(k for k, v in results.items() if not v)
    return green, ("%d/%d sub-probes green%s%s"
                   % (sum(results.values()), len(results),
                      "; failing: " + ", ".join(failed) if failed else "",
                      "; ABSENT: " + ", ".join(missing) if missing else ""))


def _c_stage(r):
    # SEC-R3-04: "A capture-failed response must not leave the counter advanced."
    first, second = r.get("first", {}), r.get("second", {})
    green = (first.get("attempt_counter_after") == 0
             and second.get("reported_attempt") == 1
             and second.get("attempt_counter_after") == 1)
    return green, ("after forced failure=%s; next attempt reported=%s counter=%s"
                   % (first.get("attempt_counter_after"),
                      second.get("reported_attempt"),
                      second.get("attempt_counter_after")))


def _c_capture_atomicity(r):
    # SEC-R3-05: "no zero-byte final file and no consumed quota unit."
    files = r.get("files_left") or []
    pools = r.get("pool_count") or {}
    green = not files and all(v == 0 for v in pools.values())
    return green, "files_left=%s pools=%s" % (files, pools)


def _c_quota(r):
    # SEC-R3-06: each over-ceiling request must be refused.
    checks = [r.get("poc1_refusal", {}), r.get("poc3_receipt", {}), r.get("poc2_triage", {})]
    green = all(c.get("status", 200) >= 400
                and c.get("outcome") not in ("recorded", "staged") for c in checks)
    return green, "; ".join("%s->%s/%s" % (n, c.get("status"), c.get("outcome"))
                            for n, c in zip(("poc1_refusal", "poc3_receipt",
                                             "poc2_triage"), checks))


def _c_control(r):
    """Positive control: the Disclose exemption and the A.4 amendment still hold.

    These passed the review and `33_` §3 forbids broadening them, so a
    regression here fails the round regardless of anything else.
    """
    blob = json.dumps(r)
    green = "FAIL" not in blob.upper() and "false" != blob.strip().lower()
    bad = [k for k, v in (r.items() if isinstance(r, dict) else [])
           if isinstance(v, dict) and v.get("ok") is False]
    return green and not bad, blob[:220]


# --------------------------------------------------------------------------
# SEC-R4-01 (R5) — the verifier's two capture-publication probes.
#
# These take a target path as `sys.argv[1]` rather than a hard-coded `SRC=`
# line, so they need no retargeting at all and run byte-identical.
#
# The criteria come from `38_`'s required correction and `37_` §3, not from me:
#   * "A capture is not published until the directory fsync has succeeded."
#   * "Any failure after the link must remove the final path."
#   * "Any failure after the link must release the reserved quota unit."
#   * "no success-named record survives a rolled-back transition"
# --------------------------------------------------------------------------
def _c_capture_publication(r):
    standalone = r.get("standalone_directory_fsync", {})
    committed = r.get("committed_registration_directory_fsync", {})

    # Standalone: the whole capture is rolled back, so nothing survives at all.
    s_files = standalone.get("records") or []
    s_pools = standalone.get("pools") or {}
    s_ok = not s_files and all(v == 0 for v in s_pools.values())

    # Registration: the PREPARED record legitimately survives — A.7 says an
    # orphan prepared is reported uncertain, never complete, and it published
    # successfully. What must NOT survive is the COMMITTED record, because the
    # transition it describes was rolled out of live state. Its quota unit is
    # likewise legitimately held, so the expected pool reading is 1, not 0.
    c_records = committed.get("records") or []
    c_steps = [x.get("step") or "" for x in c_records]
    c_pools = committed.get("pools") or {}
    c_ok = (not any(st.startswith("committed-") for st in c_steps)
            and not any(x.get("phase") == "committed" for x in c_records)
            and committed.get("registrations") == 0
            and committed.get("identity_index") == 0
            and c_pools.get("reserved-owner", 0) <= 1)
    return s_ok and c_ok, (
        "standalone: records=%d pools=%s | committed-registration: steps=%s "
        "registrations=%s pools=%s"
        % (len(s_files), s_pools, c_steps, committed.get("registrations"), c_pools))


def _c_capture_postlink(r):
    verdicts, detail = {}, []
    for key in ("link_failure_control", "temp_unlink_after_link_failure",
                "directory_open_after_link_failure"):
        d = r.get(key, {})
        files = d.get("files") or []
        pools = d.get("pools") or {}
        verdicts[key] = not files and all(v == 0 for v in pools.values())
        detail.append("%s: files=%d pools=%s" % (key, len(files), pools))
    return all(verdicts.values()), " | ".join(detail)


CRITERIA = {
    "chatgpt_capture_publication_fault_probe": ("SEC-R4-01", _c_capture_publication),
    "chatgpt_capture_postlink_cleanup_probe": ("SEC-R4-01", _c_capture_postlink),
    "http_race_probes": ("SEC-R3-01", _c_http_race),
    "http_authority_races": ("SEC-R3-01", _c_authority),
    "http_revoke_race": ("SEC-R3-02", _c_revoke),
    "more_race_probes": ("SEC-R3-01", _c_more_races),
    "security_probes": ("SEC-R3-03/04", _c_security),
    "stage_precise_probe": ("SEC-R3-04", _c_stage),
    "capture_atomicity_probe": ("SEC-R3-05", _c_capture_atomicity),
    "quota_enforcement_probe": ("SEC-R3-06", _c_quota),
    "control_probes": ("positive control", _c_control),
}

ORDER = ("http_race_probes", "http_authority_races", "http_revoke_race",
         "more_race_probes", "security_probes", "stage_precise_probe",
         "capture_atomicity_probe", "quota_enforcement_probe", "control_probes",
         # R5 — SEC-R4-01
         "chatgpt_capture_publication_fault_probe",
         "chatgpt_capture_postlink_cleanup_probe")

# Probes that take the target as an argument instead of a hard-coded SRC= line.
ARGV_PROBES = frozenset(("chatgpt_capture_publication_fault_probe",
                         "chatgpt_capture_postlink_cleanup_probe"))


def run_all(target: str, expect_green: bool, emit=None) -> list:
    """Run every probe against `target`. Returns a row per probe."""
    rows = []
    for name in ORDER:
        finding, criterion = CRITERIA[name]
        try:
            raw = run_probe(name, target)
            green, detail = criterion(raw)
            err = None
        except (ProbeError, subprocess.SubprocessError, OSError) as exc:
            raw, green, detail, err = None, False, str(exc)[:300], str(exc)[:300]
        rows.append({"probe": name, "finding": finding, "green": bool(green),
                     "detail": detail, "error": err, "raw": raw,
                     "as_expected": bool(green) == expect_green})
        if emit:
            emit(rows[-1])
    return rows


if __name__ == "__main__":
    tgt = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "stub_server.py")
    want = (sys.argv[2] if len(sys.argv) > 2 else "green") == "green"
    res = run_all(os.path.abspath(tgt), want,
                  emit=lambda r: sys.stderr.write(
                      "  [%s] %-26s %-14s %s\n"
                      % ("green" if r["green"] else " red ", r["probe"],
                         r["finding"], r["detail"][:150])))
    bad = [r for r in res if not r["as_expected"]]
    sys.stderr.write("\n%d/%d probes as expected (wanted %s)\n"
                     % (len(res) - len(bad), len(res), "green" if want else "red"))
    sys.exit(1 if bad else 0)

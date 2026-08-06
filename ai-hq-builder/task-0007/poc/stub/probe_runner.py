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


# R8 — the verifier's adversarial re-check probe binds TWO absolute paths at
# module level (`R7 = os.path.abspath('…')` / `R6 = os.path.abspath('…')`)
# instead of one `SRC=` line, and takes no argv. It gets the same treatment the
# `SRC=` probes get: rewrite exactly those two lines, then prove line by line
# that nothing else moved. `R7` is the build under test and `R6` the older
# comparison build the probe diffs it against, so the pair is what the runner
# supplies — for the green run (live, pinned R7) and for the red run
# (pinned R7, pinned R6), which reproduces the verifier's own comparison.
PAIR_LINE = re.compile(r"^(R6|R7)\s*=\s*os\.path\.abspath\('[^']*'\)\s*$")
PAIR_PROBES = frozenset(("chatgpt_r7_adversarial_recheck",))


def _retarget_pair(probe_path: str, under_test: str, comparison: str) -> str:
    """Rewrite ONLY the two path-binding lines; prove nothing else changed."""
    original = open(probe_path, encoding="utf-8").read().splitlines(keepends=True)
    want = {"R7": under_test, "R6": comparison}
    out, hits = [], {}
    for line in original:
        m = PAIR_LINE.match(line.rstrip("\n"))
        if m:
            name = m.group(1)
            hits[name] = hits.get(name, 0) + 1
            out.append("%s = os.path.abspath(%r)\n" % (name, want[name]))
        else:
            out.append(line)
    if sorted(hits) != ["R6", "R7"] or set(hits.values()) != {1}:
        raise ProbeError("%s: expected exactly one R6= and one R7= binding, "
                         "found %r" % (os.path.basename(probe_path), hits))
    diffs = [i for i, (a, b) in enumerate(zip(original, out)) if a != b]
    if len(diffs) != 2 or not all(PAIR_LINE.match(original[i].rstrip("\n"))
                                  for i in diffs):
        raise ProbeError("%s: the retarget changed more than the two path lines"
                         % os.path.basename(probe_path))
    if len(original) != len(out):
        raise ProbeError("%s: the retarget changed the line count"
                         % os.path.basename(probe_path))
    path = os.path.join(tempfile.mkdtemp(prefix="probe-"),
                        os.path.basename(probe_path))
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(out)
    return path


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


def run_probe(name: str, target: str, timeout: int = 180,
              comparison: str = None) -> dict:
    """Execute one probe against `target`; return its parsed JSON stdout."""
    probe = os.path.join(PROBE_DIR, name + ".py")
    if not os.path.exists(probe):
        raise ProbeError("probe %s is not present" % name)
    if name in PAIR_PROBES:
        if not comparison:
            raise ProbeError("%s needs a comparison build; it diffs two targets"
                             % name)
        retargeted = _retarget_pair(probe, target, comparison)
        argv = [sys.executable, retargeted]
        cwd = os.path.dirname(retargeted)
    elif name in ARGV_PROBES:
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
    """R5's criterion, superseded by `42_` items 1 and 7.

    R5 required "no file, no quota" from every post-link failure. R6 releases
    the quota only once the rollback is PROVEN, so a scenario whose rollback
    cannot be established must instead end in the distinct quarantine result —
    and may legitimately retain both the evidence and its unit. The
    ordinary-failure branch is unchanged and still strict.
    """
    verdicts, detail = {}, []
    for key in ("link_failure_control", "temp_unlink_after_link_failure",
                "directory_open_after_link_failure"):
        d = r.get(key, {})
        files = d.get("files") or []
        pools = d.get("pools") or {}
        quarantined = ((d.get("error") or {}).get("type") == "CaptureQuarantine")
        verdicts[key] = quarantined or (not files
                                        and all(v == 0 for v in pools.values()))
        detail.append("%s: %s files=%d pools=%s"
                      % (key, "quarantined" if quarantined else "ordinary",
                         len(files), pools))
    return all(verdicts.values()), " | ".join(detail)


def _c_rollback(r):
    """SEC-R4-01 final — `42_` item 7, applied scenario by scenario.

    "Every non-control scenario must produce either proven cleanup or an
    explicit quarantined/uncertain state — never a normal ineffective claim
    alongside surviving committed evidence."
    """
    def quarantined(d):
        return (d.get("error") or {}).get("type") == "CaptureQuarantine"

    v = {}
    # Rollback of the final link fails => the record may survive => quarantine.
    v["standalone_final_link_cleanup_failure"] = quarantined(
        r.get("standalone_final_link_cleanup_failure", {}))
    # Same, reached through a real route: the RESPONSE must say quarantined and
    # must not be the ordinary "not effective" claim.
    c = r.get("committed_final_link_cleanup_failure", {})
    v["committed_final_link_cleanup_failure"] = (
        (c.get("body") or {}).get("outcome") == "refused-storage-quarantine"
        and (c.get("body") or {}).get("storage_uncertain") is True)
    # The rollback removed the record AND made the removal durable: a third
    # fsync had to happen, and nothing may survive.
    f = r.get("rollback_directory_fsync", {})
    v["rollback_directory_fsync"] = (
        f.get("rollback_directory_fsync_observed") is True
        and not (f.get("records") or [])
        and all(x == 0 for x in (f.get("pools") or {}).values()))
    # Durable publication, then a close error: the record STAYS, and the
    # transition is not rolled back (items 4 and 5).
    pc = r.get("post_fsync_close_plus_cleanup_failure", {})
    v["post_fsync_close_plus_cleanup_failure"] = (
        pc.get("error") is None and bool(pc.get("returned"))
        and sum((pc.get("pools") or {}).values()) == 1)
    # A temp that cannot be removed even on retry is a hidden artifact =>
    # quarantine, never an ordinary failure.
    v["persistent_temp_cleanup_failure"] = quarantined(
        r.get("persistent_temp_cleanup_failure", {}))

    failed = sorted(k for k, ok in v.items() if not ok)
    return not failed, ("%d/%d scenarios%s" % (sum(v.values()), len(v),
                                               "; failing: " + ", ".join(failed)
                                               if failed else ""))


def _c_r6_quarantine(r):
    """`46_` items 1, 3, 4 and 5, plus the R6 property that must not move.

    Four of the probe's five summary flags name a DEFECT, so the criterion is
    that they are `False`; the fifth names the confirmed R6 behaviour and must
    stay `True`. Each is paired here with a check that the probe's fault
    actually landed, because "no spurious quarantine" is trivially satisfiable
    by an injection that never fires — which is exactly how a suite of mine
    passed 5/5 against the build it existed to fail at R5.
    """
    s = r.get("summary") or {}
    pd = r.get("post_durable_non_oserror") or {}
    pm = r.get("preartifact_makedirs_failure") or {}
    rc = r.get("rollback_close_after_fsync") or {}
    fr = r.get("fail_closed_and_restart") or {}
    restart = fr.get("restart") or {}

    def pools_empty(d):
        return all(v == 0 for v in (d.get("pools") or {"x": 1}).values())

    v = {
        # Item 1 — a durably committed capture is committed.
        "item 1: no ordinary ineffective claim beside a durable committed record": (
            s.get("ordinary_failure_with_durable_committed_evidence") is False
            and (pd.get("fault_calls") or {}).get("forced", 0) >= 1
            and pd.get("status") == 200
            and pd.get("registrations") == 1),
        # Item 3 — nothing created, nothing to prove.
        "item 3: no quarantine when no artifact was ever created": (
            s.get("preartifact_spurious_quarantine") is False
            and (pm.get("fault_calls") or {}).get("makedirs_faults", 0) >= 1
            and not (pm.get("records") or [])
            and not (pm.get("quarantine") or [])
            and pools_empty(pm)),
        # Item 4 — the rollback's own durability boundary.
        "item 4: a close error after a durable rollback fsync is a soft anomaly": (
            s.get("post_rollback_fsync_spurious_quarantine") is False
            and (rc.get("fault_calls") or {}).get(
                "rollback_directory_fsync_succeeded") is True
            and (rc.get("fault_calls") or {}).get("rollback_close_faults", 0) >= 1
            and not (rc.get("records") or [])
            and not (rc.get("quarantine") or [])
            and pools_empty(rc)),
        # Item 5 — a restart is not reconciliation.
        "item 5: a fresh process finds the quarantine and still refuses": (
            s.get("restart_bypasses_explicit_recovery") is False
            and (restart.get("health") or [0, {}])[1].get("storage_quarantined") is True
            and (restart.get("register") or [0])[0] == 503
            and restart.get("quarantine_count", 0) >= 1),
        # R6, confirmed by the verifier: this must not have moved.
        "R6 preserved: the raising process itself still fails closed": (
            s.get("current_process_fail_closed") is True),
    }
    failed = sorted(k for k, ok in v.items() if not ok)
    return not failed, ("%d/%d checks%s" % (sum(v.values()), len(v),
                                            "; failing: " + "; ".join(failed)
                                            if failed else ""))


def _c_post_durable(r):
    """`46_` item 2 — the exact red-before-green probe, on its own.

    A non-`OSError` interruption raised immediately after the real committed
    directory close must leave no ordinary ineffective claim beside the
    committed record. The probe prints one row per target; run through here it
    gets one.
    """
    rows = r if isinstance(r, list) else [r]
    if not rows:
        return False, "no rows"
    detail, ok = [], True
    for row in rows:
        forced = (row.get("calls") or {}).get("forced", 0)
        body = row.get("body") or {}
        committed = [x for x in (row.get("records") or [])
                     if x.get("phase") == "committed"]
        good = (forced >= 1                       # the interruption really fired
                and bool(committed)               # a durable committed record exists
                and row.get("status") == 200
                and body.get("outcome") != "capture-failed"
                and row.get("registrations") == 1
                and row.get("identity_index") == 1)
        ok = ok and good
        detail.append("%s: forced=%d status=%s outcome=%s committed=%d regs=%s"
                      % (os.path.basename(str(row.get("target"))), forced,
                         row.get("status"), body.get("outcome"),
                         len(committed), row.get("registrations")))
    return ok, " | ".join(detail)


def _c_r7_adversarial(r):
    """`49_` §2/§3/§4 as `51_` items A, C and D restate them.

    The probe's three predicates all name a DEFECT, so the criterion is that
    each is `False`. Every one is paired with a check that the injected fault
    actually fired — `51_` §4 makes fault-landed assertions standing practice,
    and here they carry unusual weight: two of these three fixes could be faked
    by a build that simply stopped calling the thing the probe patches.
    """
    marker = r.get("marker_write_failures") or []
    item3 = r.get("item3_untracked_temp_compare") or []
    item4 = r.get("item4_non_oserror_compare") or []
    v, detail = {}, []

    # Item A — a marker that could not be written must not reopen clean.
    for m in marker:
        how = m.get("failure")
        calls = m.get("fault_calls") or {}
        fired = calls.get("marker_makedirs_faults", 0) if how == "makedirs" \
            else calls.get("marker_open_faults", 0)
        v["item A: marker-%s failure does not permit restart bypass" % how] = (
            m.get("restart_bypassed") is False
            and fired >= 1                       # the marker fault landed
            and calls.get("final_unlink_faults", 0) >= 1   # a REAL quarantine
            and (m.get("initial") or [0])[0] == 503
            and (m.get("restart_health") or [0, {}])[1].get(
                "storage_quarantined") is True
            and (m.get("restart_register") or [0])[0] == 503
            and m.get("restart_quarantine_count", 0) >= 1)
        detail.append("A/%s: fired=%s restart_quarantined=%s register=%s"
                      % (how, fired,
                         (m.get("restart_health") or [0, {}])[1].get("storage_quarantined"),
                         (m.get("restart_register") or [0])[0]))

    # Item C — the build under test is the LAST row; the probe runs the
    # comparison build first.
    if item3:
        m = item3[-1]
        calls = m.get("fault_calls") or {}
        v["item C: a temp that exists on disk is not 'nothing created'"] = (
            m.get("ordinary_release_with_existing_temp") is False
            and calls.get("mkstemp_faults", 0) >= 1      # the probe's patch fired
            and calls.get("created_path")                # a real temp was made
            and calls.get("rollback_open_faults", 0) >= 1
            and (m.get("error") or {}).get("type") == "CaptureQuarantine"
            and sum((m.get("pools") or {}).values()) == 1)
        detail.append("C: mkstemp_fired=%s rollback_fired=%s err=%s pools=%s"
                      % (calls.get("mkstemp_faults"), calls.get("rollback_open_faults"),
                         (m.get("error") or {}).get("type"), m.get("pools")))

    if item4:
        m = item4[-1]
        calls = m.get("fault_calls") or {}
        v["item D: a non-OSError after the durable rollback close is soft"] = (
            m.get("violates_item4") is False
            and calls.get("rollback_fsync_succeeded") is True
            and calls.get("runtime_close_faults", 0) >= 1
            and len(m.get("anomalies") or []) >= 1
            and all(x == 0 for x in (m.get("pools") or {"x": 1}).values())
            and not (m.get("quarantine") or []))
        detail.append("D: fsync_ok=%s tail_fired=%s anomalies=%d pools=%s"
                      % (calls.get("rollback_fsync_succeeded"),
                         calls.get("runtime_close_faults"),
                         len(m.get("anomalies") or []), m.get("pools")))

    if len(v) != 4:
        return False, "probe produced %d of 4 expected scenarios" % len(v)
    failed = sorted(k for k, ok in v.items() if not ok)
    return not failed, ("%d/%d | %s%s" % (sum(v.values()), len(v),
                                          " | ".join(detail),
                                          "; FAILING: " + "; ".join(failed)
                                          if failed else ""))


def _c_r8_adversarial(r):
    """`54_`'s findings as `56_` items F-K restate them.

    Ten of the probe's eleven summary flags name a DEFECT, so the criterion is
    that each is `False`. The eleventh is the verifier's own POSITIVE CONTROL —
    a genuine no-record failure reported truthfully — and it must stay `True`.
    Without it every one of the ten is satisfiable by a build that simply never
    says `none`, which is the shape a lazy fix would take.

    Each is paired with a check that the injected fault fired and, where the
    finding is about an inventory, that the inventory is actually usable.
    """
    s = r.get("summary") or {}
    pd = r.get("post_durable_marker_close_misclassified") or {}
    fp = r.get("failed_primary_is_unlisted_durable_record") or {}
    ri = r.get("restart_inventory_loses_sibling_marker") or {}
    so = r.get("scan_once_two_process_bypass") or {}
    ts = r.get("transient_scan_error_mislabelled_durable") or {}
    ctl = r.get("both_marker_writes_fail_truthfully_without_disk_fact") or {}
    wf = r.get("writefree_temp_exists_but_live_response_claims_none") or {}
    pm = r.get("partial_marker_files_exist_but_live_response_claims_none") or {}
    fse = r.get("fallback_scan_error_reports_data_directory_as_record") or {}
    rp = r.get("realpath_fix_edges") or {}

    def files_only(paths):
        return all(not os.path.isdir(p) for p in (paths or []))

    v = {
        # Item F — a durably fsynced marker cannot be erased by its close tail.
        "F: post-durable marker close keeps DURABLE": (
            s.get("post_durable_marker_close_false_none_claim") is False
            and len((pd.get("faults") or {}).get("marker_close_fault_paths") or []) == 2
            and len((pd.get("faults") or {}).get("marker_dir_fsync_paths") or []) == 2
            and (pd.get("body_restart_fields") or {}).get("restart_protection") != "none"),
        # Item F — presence is the signal; a partial marker is still a marker.
        "F: a partial marker is not 'nothing on disk'": (
            s.get("partial_marker_live_false_none_claim") is False
            and len((pm.get("faults") or {}).get("partial_dump_fault_paths") or []) == 2
            and (pm.get("body_restart_fields") or {}).get("restart_protection") != "none"),
        # Item G — the live temp fact reaches the live posture.
        "G: a surviving temp counts in the raising process": (
            s.get("writefree_temp_live_false_none_claim") is False
            and (wf.get("faults") or {}).get("mkstemp_faults") == 1
            and wf.get("temp_exists") is True
            and (wf.get("body_restart_fields") or {}).get("restart_protection") != "none"),
        # Item H — a durable primary stays in the inventory.
        "H: a close-tail anomaly does not delist a real marker": (
            s.get("failed_primary_reconciliation_inventory_incomplete") is False
            and len((fp.get("faults") or {}).get("marker_close_fault_paths") or []) == 1
            and not (fp.get("remaining_before_restart") or [])
            and (fp.get("restart_health") or [0, {}])[1].get(
                "storage_quarantined") is False),
        # Item H — the sibling relationship survives a restart, and the
        # delete-what-is-named sequence ends CLEAN.
        "H: restart reconstruction ends clean": (
            s.get("restart_inventory_loses_sibling_marker") is False
            and len(ri.get("initial_durable_records") or []) == 2
            and len(ri.get("restart_durable_records") or []) == 2
            and (ri.get("second_restart_health_after_deleting_every_reported_record")
                 or [0, {}])[1].get("storage_quarantined") is False),
        # Item I — a scan error is never a durable record.
        "I: a transient primary scan error mints no durable record": (
            s.get("transient_scan_error_false_durable_claim") is False
            and (ts.get("faults") or {}).get("primary_faults") == 1
            and not (((ts.get("first_health") or [0, {}])[1].get(
                "storage_quarantine") or {}).get("durable_records") or [])),
        # Item I — and never names a directory an operator is told to delete.
        "I: a fallback scan error never names the data directory": (
            s.get("fallback_scan_error_dangerous_false_inventory") is False
            and (fse.get("faults") or {}).get("fallback_list_faults") == 1
            and files_only(((fse.get("first_health") or [0, {}])[1].get(
                "storage_quarantine") or {}).get("durable_records"))
            and fse.get("sentinel_exists") is True),
        # Item J — the scan-once bypass, executed and closed.
        "J: a process that scanned clean first still refuses": (
            s.get("scan_once_two_process_bypass") is False
            and (so.get("a_initial_health") or [0, {}])[1].get(
                "storage_quarantined") is False
            and so.get("b_quarantine_status") == 503
            and (so.get("a_register_after_marker_created") or [0])[0] == 503),
        # Item K — containment.
        "K: no quota leaks on a containment refusal": (
            s.get("candidate_symlink_quota_leak") is False
            and (rp.get("candidate_symlink") or {}).get("refused") is True),
        "K: a captures-ROOT symlink is refused, not resolved through": (
            s.get("captures_root_symlink_accepted") is False
            and not ((rp.get("captures_root_symlink") or {})
                     .get("physical_files_outside_data_dir") or [])),
        # The verifier's positive control — this one must stay TRUE.
        "CONTROL: a genuine no-record failure still reports none truthfully": (
            s.get("both_marker_fail_truthful_none_control") is True
            and len((ctl.get("faults") or {}).get("marker_open_fault_paths") or []) == 2
            and (ctl.get("restart_register") or [0])[0] == 200),
    }
    if len(s) != 11:
        return False, "probe produced %d of 11 summary flags" % len(s)
    failed = sorted(k for k, ok in v.items() if not ok)
    return not failed, ("%d/%d checks%s" % (sum(v.values()), len(v),
                                            "; failing: " + "; ".join(failed)
                                            if failed else ""))


CRITERIA = {
    "chatgpt_r8_adversarial_recheck": ("SEC-R4-01 R9", _c_r8_adversarial),
    "chatgpt_r7_adversarial_recheck": ("SEC-R4-01 R8", _c_r7_adversarial),
    "chatgpt_r6_quarantine_integrity_probe": ("SEC-R4-01 R7", _c_r6_quarantine),
    "post_durable_interrupt_compare": ("SEC-R4-01 R7 item 2", _c_post_durable),
    "chatgpt_r5_cleanup_rollback_probe": ("SEC-R4-01 final", _c_rollback),
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
         "chatgpt_capture_postlink_cleanup_probe",
         # R6 — SEC-R4-01 final
         "chatgpt_r5_cleanup_rollback_probe",
         # R7 — publication-aware handling, scoped quarantine, restart posture
         "chatgpt_r6_quarantine_integrity_probe",
         "post_durable_interrupt_compare",
         # R8 — facts, not proxies
         "chatgpt_r7_adversarial_recheck",
         # R9 — marker facts, complete inventories, enforced invariants
         "chatgpt_r8_adversarial_recheck")

# Probes that take the target as an argument instead of a hard-coded SRC= line.
ARGV_PROBES = frozenset(("chatgpt_capture_publication_fault_probe",
                         "chatgpt_capture_postlink_cleanup_probe",
                         "chatgpt_r5_cleanup_rollback_probe",
                         "chatgpt_r6_quarantine_integrity_probe",
                         "post_durable_interrupt_compare",
                         "chatgpt_r8_adversarial_recheck"))


def run_all(target: str, expect_green: bool, emit=None, comparison: str = None) -> list:
    """Run every probe against `target`. Returns a row per probe.

    `comparison` is the older build the PAIR probes diff `target` against. It
    defaults to the pin immediately below `target`: `r7_reference` when the
    target is the live build, `r6_reference` when the target is `r7_reference`,
    so a full run in either direction supplies the right pair without the
    caller having to know which probes need one.
    """
    rows = []
    if comparison is None:
        pins = os.path.join(HERE, "r7_reference", "stub_server_r7.py")
        comparison = (os.path.join(HERE, "r6_reference", "stub_server_r6.py")
                      if os.path.abspath(target) == os.path.abspath(pins) else pins)
    for name in ORDER:
        finding, criterion = CRITERIA[name]
        try:
            raw = run_probe(name, target, comparison=comparison)
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

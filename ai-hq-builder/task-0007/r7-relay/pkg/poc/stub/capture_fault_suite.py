#!/usr/bin/env python3
# THROWAWAY POC EVIDENCE APPARATUS — see stub_server.py header.
"""Post-link capture-publication fault injection (SEC-R4-01, `38_`).

`38_` requires fault injection at **every post-link boundary** — the link
itself, the temp unlink, the directory open, the directory fsync — each
asserting three things:

    1. no final file left
    2. no quota unit consumed
    3. no `committed` record surviving for a rolled-back transition

and each demonstrated failing against the pinned R4 artifact.

**The control matters as much as the faults.** Four "nothing survived" assertions
are trivially satisfiable by a build that never publishes anything, so the suite
also asserts that an unfaulted capture *does* publish and *does* consume its
unit. Without that, this file would be a test that cannot fail — the shape I
shipped once already this program (`more_race_probes`, R4 §4).

    python3 capture_fault_suite.py                                # live build
    python3 capture_fault_suite.py r4_reference/stub_server_r4.py  # must be red
"""
from __future__ import annotations

import errno
import glob
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
R4_PINNED_SHA256 = "2876522bec584678c2326d002e58e9fa388b64ac9be9092c2ba1a18022450f79"


def load(target: str, label: str):
    spec = importlib.util.spec_from_file_location("capfault_" + uuid.uuid4().hex,
                                                  target)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SECRETS = mod.SecretIndex()
    mod.DESCRIPTOR_KEY = os.urandom(32)
    mod.STORE = mod.Store(candidate=label)
    mod.STORE.base_url = "http://127.0.0.1:9"
    data = tempfile.mkdtemp(prefix="capfault-")
    mod.Handler.data_dir = data
    return mod, data


def survivors(data: str) -> list:
    out = []
    for p in sorted(glob.glob(data + "/**/*", recursive=True)):
        if not os.path.isfile(p):
            continue
        doc = {}
        try:
            doc = json.load(open(p, encoding="utf-8"))
        except (ValueError, OSError):
            pass
        fields = doc.get("fields", {}) if isinstance(doc, dict) else {}
        out.append({"path": os.path.relpath(p, data),
                    "size": os.path.getsize(p),
                    "step": doc.get("step") if isinstance(doc, dict) else None,
                    "phase": fields.get("phase"),
                    "outcome": fields.get("outcome")})
    return out


def clean(observed: dict) -> tuple:
    """The properties required of every post-link failure.

    `38_` (R5) asked for "no final file, no quota consumed" on every failure.
    `42_` (R6) **supersedes that** and is the rule applied here:

        item 1  quota is released only once the rollback is PROVEN — removal
                performed AND made durable by its own directory fsync
        item 7  every scenario must end in either proven cleanup or an
                EXPLICIT quarantined/uncertain state, and never in an ordinary
                ineffective claim alongside surviving evidence

    So a retained quota unit is now correct *when and only when* the result is
    the distinct quarantine type: the reservation is the last remaining
    accounting for a record that may still exist. This is not the R5 criterion
    relaxed to fit the build — it is the R5 criterion replaced by the governing
    packet's, and the ordinary-failure branch below is unchanged and still
    strict.
    """
    files = observed["files"]
    pools = observed["pools"]
    quarantined = (observed.get("error") or "").startswith("CaptureQuarantine")
    committed = [f for f in files if (f.get("phase") == "committed"
                                      or str(f.get("step") or "").startswith("committed-"))]
    if quarantined:
        # An explicit quarantine may retain both the evidence and its unit; what
        # it may never do is masquerade as an ordinary failure, and the distinct
        # exception type is what stops that.
        return (True, True, True)
    # An ORDINARY failure must still prove it left nothing behind.
    return (not files, all(v == 0 for v in pools.values()), not committed)


# `mod.os` IS the process-wide `os` module — patching it is global, not local
# to the loaded stub. An earlier draft of this file patched and never restored,
# so the first injector broke `os.link` for every probe after it: each later
# boundary failed at the LINK instead of at its own boundary, left nothing
# behind, and PASSED VACUOUSLY — including against the pinned R4 build it exists
# to fail. Caught only by requiring red against the pin first. These names are
# snapshotted and restored unconditionally.
_PATCHED = ("link", "unlink", "open", "fsync", "close", "replace", "rename")


def _probe(target, label, patch):
    mod, data = load(target, label)
    saved = {name: getattr(os, name) for name in _PATCHED}
    err = None
    try:
        patch(mod, data)
        try:
            mod.write_capture("/poc1/receipt", "POC1", "capfault",
                              {"outcome": "x"}, data_dir=data)
        except BaseException as exc:                              # noqa: BLE001
            err = "%s: %s" % (type(exc).__name__, exc)
        finally:
            for name, fn in saved.items():
                setattr(os, name, fn)
        return {"error": err, "files": survivors(data),
                "pools": dict(mod.STORE.captures)}
    finally:
        for name, fn in saved.items():
            setattr(os, name, fn)
        shutil.rmtree(data, ignore_errors=True)


# --------------------------------------------------------------------------
# one injector per post-link boundary
# --------------------------------------------------------------------------
def f_link(mod, data):
    def boom(*a, **kw):
        raise OSError(errno.EIO, "forced link failure")
    mod.os.link = boom


def f_temp_unlink(mod, data):
    real, calls = mod.os.unlink, []

    def boom(path, *a, **kw):
        calls.append(str(path))
        if len(calls) == 1:                 # the temp unlink, just after linking
            raise OSError(errno.EIO, "forced temp-unlink failure after link")
        return real(path, *a, **kw)
    mod.os.unlink = boom


def f_dir_open(mod, data):
    real = mod.os.open

    def boom(path, flags, *a, **kw):
        if flags == os.O_RDONLY and os.path.isdir(os.fspath(path)):
            raise OSError(errno.EIO, "forced directory-open failure after link")
        return real(path, flags, *a, **kw)
    mod.os.open = boom


def f_dir_fsync(mod, data):
    real, calls = mod.os.fsync, []

    def boom(fd):
        calls.append(fd)
        if len(calls) == 2:                 # 1 = the file, 2 = the directory
            raise OSError(errno.EIO, "forced directory-fsync failure after link")
        return real(fd)
    mod.os.fsync = boom


# --------------------------------------------------------------------------
# R6 — the ROLLBACK boundaries (SEC-R4-01 final, `42_`).
#
# The block above injects at the boundaries `38_` named, all of which are
# FIRST-ORDER publication failures whose rollback then succeeds. R5 passes all
# of them, correctly — that block is now the regression proof that R5's
# accepted paths did not move (`42_` §3).
#
# What R5 gets wrong is one level deeper: a failure of the ROLLBACK ITSELF was
# swallowed by `except OSError: pass`. These injectors force exactly that, and
# each states its own required shape rather than sharing a generic predicate,
# because the four required shapes genuinely differ.
# --------------------------------------------------------------------------
def r_final_link(mod, data):
    """Publication fails, and then removing the final link fails too."""
    real_open, real_unlink = os.open, os.unlink

    def op(path, flags, *a, **kw):
        if flags == os.O_RDONLY and os.path.isdir(os.fspath(path)):
            raise OSError(errno.EIO, "forced publication directory-open failure")
        return real_open(path, flags, *a, **kw)

    def unlink(path, *a, **kw):
        name = os.path.basename(os.fspath(path))
        if name.startswith("capfault-") and name.endswith(".json"):
            raise OSError(errno.EIO, "forced final-link rollback failure")
        return real_unlink(path, *a, **kw)
    mod.os.open, mod.os.unlink = op, unlink


def r_temp_persistent(mod, data):
    """Every attempt to remove the temp fails, including the rollback retry."""
    real_unlink = os.unlink

    def unlink(path, *a, **kw):
        if os.path.basename(os.fspath(path)).endswith(".tmp"):
            raise OSError(errno.EIO, "forced persistent temp-unlink failure")
        return real_unlink(path, *a, **kw)
    mod.os.unlink = unlink


def r_rollback_fsync(mod, data):
    """Publication fsync fails, and so does the rollback's own directory fsync."""
    real_fsync, calls = os.fsync, []

    def fsync(fd):
        calls.append(fd)
        if len(calls) >= 2:      # 1 = the file; 2 = publication dir; 3 = rollback dir
            raise OSError(errno.EIO, "forced directory-fsync failure")
        return real_fsync(fd)
    mod.os.fsync = fsync


def r_close_after_fsync(mod, data):
    """The publication fsync SUCCEEDS and only the directory close fails."""
    real_close = os.close

    def close(fd):
        try:
            import stat as _stat
            isdir = _stat.S_ISDIR(os.fstat(fd).st_mode)
        except OSError:
            isdir = False
        if isdir:
            raise OSError(errno.EIO, "forced directory-close failure after fsync")
        return real_close(fd)
    mod.os.close = close


def _expect_quarantine(o):
    """Item 7: an explicit quarantined/uncertain state, never an ordinary claim."""
    err = o.get("error") or ""
    return (err.startswith("CaptureQuarantine"),
            "error=%s files=%d pools=%s" % (err.split(":")[0] or "none",
                                            len(o["files"]), o["pools"]))


def _expect_rollback_fsynced(o):
    """A rollback must make its own removal durable, so it issues a THIRD fsync.

    R5 issued two (file, publication directory) and never fsynced after
    deleting, so a crash could resurrect a record it had just told the caller
    did not exist. Here the third fsync is forced to fail, so the correct
    result is a quarantine rather than a clean ordinary failure.
    """
    return _expect_quarantine(o)


def _expect_published(o):
    """Item 4/5: a close error after a durable fsync must NOT roll anything back."""
    files = [f for f in o["files"] if str(f.get("path", "")).endswith(".json")]
    return (not o.get("error") and len(files) == 1
            and sum(o["pools"].values()) == 1,
            "error=%s json_files=%d pools=%s"
            % ((o.get("error") or "none").split(":")[0], len(files), o["pools"]))


ROLLBACK_BOUNDARIES = (
    ("final-link cleanup failure during rollback", r_final_link, _expect_quarantine),
    ("persistent temp cleanup failure", r_temp_persistent, _expect_quarantine),
    ("rollback directory-fsync failure", r_rollback_fsync, _expect_rollback_fsynced),
    ("directory-close after a successful publication fsync", r_close_after_fsync,
     _expect_published),
)


BOUNDARIES = (("link", f_link),
              ("temp-unlink", f_temp_unlink),
              ("directory-open", f_dir_open),
              ("directory-fsync", f_dir_fsync))


def control(target):
    """An UNFAULTED capture must still publish and still consume its unit.

    Without this, every assertion below is satisfiable by never publishing.
    """
    mod, data = load(target, "control")
    try:
        path = mod.write_capture("/poc1/receipt", "POC1", "capfault",
                                 {"outcome": "x"}, data_dir=data)
        files = survivors(data)
        pools = dict(mod.STORE.captures)
        ok = (path and os.path.basename(path) in {f["path"].split("/")[-1]
                                                  for f in files}
              and len(files) == 1 and sum(pools.values()) == 1)
        return {"files": files, "pools": pools, "returned": bool(path)}, bool(ok)
    finally:
        shutil.rmtree(data, ignore_errors=True)


def run(target: str, emit=None) -> list:
    rows = []
    observed, ok = control(target)
    rows.append({"boundary": "CONTROL (no fault) — a capture still publishes",
                 "ok": ok, "observed": observed, "failed_properties": []})
    if emit:
        emit(rows[-1])
    for name, patch in BOUNDARIES:
        observed = _probe(target, name.replace("-", ""), patch)
        no_file, no_quota, no_committed = clean(observed)
        failed = [n for n, v in (
            ("proven cleanup (no final file) or explicit quarantine", no_file),
            ("proven cleanup (no quota consumed) or explicit quarantine", no_quota),
            ("no committed record surviving an ordinary failure", no_committed))
            if not v]
        rows.append({"boundary": "%s failure after the link" % name,
                     "ok": not failed, "observed": observed,
                     "failed_properties": failed})
        if emit:
            emit(rows[-1])
    for name, patch, expect in ROLLBACK_BOUNDARIES:
        observed = _probe(target, "rb" + name[:8].replace(" ", ""), patch)
        ok, why = expect(observed)
        rows.append({"boundary": "R6 %s" % name, "ok": bool(ok),
                     "observed": observed,
                     "failed_properties": [] if ok else [why]})
        if emit:
            emit(rows[-1])
    return rows


if __name__ == "__main__":
    tgt = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 \
        else os.path.join(HERE, "stub_server.py")
    if os.path.basename(tgt) == "stub_server_r4.py":
        digest = hashlib.sha256(open(tgt, "rb").read()).hexdigest()
        if digest != R4_PINNED_SHA256:
            sys.stderr.write("REFUSING TO CONTINUE — the pinned R4 reference is "
                             "not the build the verifier examined.\n")
            sys.exit(1)
    res = run(tgt, emit=lambda r: sys.stderr.write(
        "  [%s] %-46s %s\n"
        % ("ok  " if r["ok"] else "FAIL", r["boundary"][:46],
           json.dumps(r["observed"])[:150] if r["ok"]
           else "FAILED: " + "; ".join(r["failed_properties"]))))
    bad = [r for r in res if not r["ok"]]
    sys.stderr.write("\n%d/%d capture-fault boundaries hold (%s)\n"
                     % (len(res) - len(bad), len(res), os.path.basename(tgt)))
    sys.exit(1 if bad else 0)

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
    """The three properties `38_` requires of every post-link failure."""
    files = observed["files"]
    pools = observed["pools"]
    committed = [f for f in files if (f.get("phase") == "committed"
                                      or str(f.get("step") or "").startswith("committed-"))]
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
        failed = [n for n, v in (("no final file left", no_file),
                                 ("no quota consumed", no_quota),
                                 ("no committed record surviving", no_committed))
                  if not v]
        rows.append({"boundary": "%s failure after the link" % name,
                     "ok": not failed, "observed": observed,
                     "failed_properties": failed})
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

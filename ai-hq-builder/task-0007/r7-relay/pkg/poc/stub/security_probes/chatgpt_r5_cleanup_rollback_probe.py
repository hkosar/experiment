#!/usr/bin/env python3
"""Independent R5 capture rollback / cleanup-boundary probe.

Exercises boundaries omitted by the R5 supplied fault suites:
  * failure to unlink the already-created final link during rollback;
  * failure after publication-directory fsync but before `published=True` (directory close);
  * absence of a directory fsync after rollback deletion;
  * repeated failure to remove the temp name during rollback.
"""
from __future__ import annotations

import errno
import glob
import importlib.util
import json
import os
import shutil
import stat
import sys
import tempfile
import uuid
from typing import Any


def load(target: str, label: str):
    spec = importlib.util.spec_from_file_location("r5rollback_" + uuid.uuid4().hex, target)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.SECRETS = mod.SecretIndex()
    mod.DESCRIPTOR_KEY = os.urandom(32)
    mod.STORE = mod.Store(candidate=label)
    mod.STORE.base_url = "http://127.0.0.1:9"
    data = tempfile.mkdtemp(prefix="chatgpt-r5-rollback-")
    mod.Handler.data_dir = data
    return mod, data


def records(data: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    paths: list[str] = []
    for root, _dirs, names in os.walk(data):
        paths.extend(os.path.join(root, name) for name in names)
    for p in sorted(paths):
        doc: Any = {}
        try:
            with open(p, encoding="utf-8") as fh:
                doc = json.load(fh)
        except Exception:
            doc = {}
        fields = doc.get("fields", {}) if isinstance(doc, dict) else {}
        out.append({
            "file": os.path.relpath(p, data),
            "size": os.path.getsize(p),
            "step": doc.get("step") if isinstance(doc, dict) else None,
            "phase": fields.get("phase") if isinstance(fields, dict) else None,
            "outcome": fields.get("outcome") if isinstance(fields, dict) else None,
            "final_status": fields.get("final_status") if isinstance(fields, dict) else None,
        })
    return out


def invoke_capture(mod, data: str, step: str):
    ret = None
    err = None
    try:
        ret = mod.write_capture(
            "/poc1/receipt", "POC1", step, {"outcome": "x"}, data_dir=data
        )
    except BaseException as exc:  # evidence probe: capture exact public failure shape
        err = {"type": type(exc).__name__, "text": str(exc)}
    return ret, err


def standalone_cleanup_unlink_failure(target: str):
    """Force rollback, then make removal of the final link fail."""
    mod, data = load(target, "cleanupunlink")
    real_open, real_unlink = mod.os.open, mod.os.unlink
    root = os.path.abspath(os.path.join(data, "captures", "cleanupunlink", "POC1"))
    calls = {"directory_open_faults": 0, "final_cleanup_unlink_faults": 0}

    def op(path, flags, *args, **kwargs):
        if os.path.abspath(os.fspath(path)) == root and flags == os.O_RDONLY:
            calls["directory_open_faults"] += 1
            raise OSError(errno.EIO, "forced publication directory-open failure")
        return real_open(path, flags, *args, **kwargs)

    def unlink(path, *args, **kwargs):
        name = os.path.basename(os.fspath(path))
        if name.startswith("cleanupfinal-") and name.endswith(".json"):
            calls["final_cleanup_unlink_faults"] += 1
            raise OSError(errno.EIO, "forced final-link rollback cleanup failure")
        return real_unlink(path, *args, **kwargs)

    mod.os.open, mod.os.unlink = op, unlink
    try:
        ret, err = invoke_capture(mod, data, "cleanupfinal")
    finally:
        mod.os.open, mod.os.unlink = real_open, real_unlink
    try:
        return {
            "returned": ret,
            "error": err,
            "fault_calls": calls,
            "records": records(data),
            "pools": dict(mod.STORE.captures),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def committed_cleanup_unlink_failure(target: str):
    """Fail committed publication and then fail removal of its final link."""
    mod, data = load(target, "commitcleanup")
    real_open, real_unlink = mod.os.open, mod.os.unlink
    root = os.path.abspath(os.path.join(data, "captures", "commitcleanup", "POC1"))
    dir_open_count = 0
    calls = {"committed_directory_open_faults": 0, "final_cleanup_unlink_faults": 0}

    def op(path, flags, *args, **kwargs):
        nonlocal dir_open_count
        if os.path.abspath(os.fspath(path)) == root and flags == os.O_RDONLY:
            dir_open_count += 1
            if dir_open_count == 2:  # prepared succeeds; committed publication fails
                calls["committed_directory_open_faults"] += 1
                raise OSError(errno.EIO, "forced committed publication directory-open failure")
        return real_open(path, flags, *args, **kwargs)

    def unlink(path, *args, **kwargs):
        name = os.path.basename(os.fspath(path))
        if name.startswith("committed-artifact-register-") and name.endswith(".json"):
            calls["final_cleanup_unlink_faults"] += 1
            raise OSError(errno.EIO, "forced committed final-link rollback cleanup failure")
        return real_unlink(path, *args, **kwargs)

    mod.os.open, mod.os.unlink = op, unlink
    try:
        status, body = mod.dispatch(
            "POST",
            "/owner/artifact/register",
            {
                "source_digest": "a" * 64,
                "size_bytes": 1,
                "file_count": 1,
                "task_id": "R5-CLEANUP",
                "transition": "ROLLBACK",
                "target_role": "verifier",
            },
            {"owner_key": mod.STORE.owner_key},
        )
    finally:
        mod.os.open, mod.os.unlink = real_open, real_unlink
    try:
        return {
            "status": status,
            "body": body,
            "fault_calls": calls,
            "registrations": len(mod.STORE.registrations),
            "identity_index": len(mod.STORE.reg_by_identity),
            "transition_mirror": list(mod.STORE.transitions),
            "records": records(data),
            "pools": dict(mod.STORE.captures),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def rollback_directory_fsync_absence(target: str):
    """Raise on publication fsync once; a durable rollback should issue another dir fsync."""
    mod, data = load(target, "rollbackfsync")
    real_fsync = mod.os.fsync
    calls: list[int] = []

    def fsync(fd):
        calls.append(fd)
        if len(calls) == 2:  # file fsync is 1; publication directory fsync is 2
            raise OSError(errno.EIO, "forced publication directory-fsync failure")
        return real_fsync(fd)

    mod.os.fsync = fsync
    try:
        ret, err = invoke_capture(mod, data, "rollbackfsync")
    finally:
        mod.os.fsync = real_fsync
    try:
        return {
            "returned": ret,
            "error": err,
            "fsync_calls": len(calls),
            "rollback_directory_fsync_observed": len(calls) >= 3,
            "records": records(data),
            "pools": dict(mod.STORE.captures),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def post_fsync_close_and_cleanup_failure(target: str):
    """Prove the record was directory-fsynced, then fail close and final-link cleanup."""
    mod, data = load(target, "postfsyncclose")
    real_close, real_unlink, real_fsync = mod.os.close, mod.os.unlink, mod.os.fsync
    calls = {"directory_fsync_successes": 0, "directory_close_faults": 0,
             "final_cleanup_unlink_faults": 0}

    def fsync(fd):
        mode = mod.os.fstat(fd).st_mode
        out = real_fsync(fd)
        if stat.S_ISDIR(mode):
            calls["directory_fsync_successes"] += 1
        return out

    def close(fd):
        mode = mod.os.fstat(fd).st_mode
        if stat.S_ISDIR(mode):
            calls["directory_close_faults"] += 1
            raise OSError(errno.EIO, "forced directory close failure after successful fsync")
        return real_close(fd)

    def unlink(path, *args, **kwargs):
        name = os.path.basename(os.fspath(path))
        if name.startswith("postclose-") and name.endswith(".json"):
            calls["final_cleanup_unlink_faults"] += 1
            raise OSError(errno.EIO, "forced cleanup failure after durable directory fsync")
        return real_unlink(path, *args, **kwargs)

    mod.os.fsync, mod.os.close, mod.os.unlink = fsync, close, unlink
    try:
        ret, err = invoke_capture(mod, data, "postclose")
    finally:
        mod.os.fsync, mod.os.close, mod.os.unlink = real_fsync, real_close, real_unlink
    try:
        return {
            "returned": ret,
            "error": err,
            "fault_calls": calls,
            "records": records(data),
            "pools": dict(mod.STORE.captures),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def persistent_temp_cleanup_failure(target: str):
    """Make both the primary temp unlink and its rollback retry fail."""
    mod, data = load(target, "templeak")
    real_unlink = mod.os.unlink
    calls = {"temp_unlink_faults": 0}

    def unlink(path, *args, **kwargs):
        name = os.path.basename(os.fspath(path))
        if name.startswith(".templeak-") and name.endswith(".tmp"):
            calls["temp_unlink_faults"] += 1
            raise OSError(errno.EIO, "forced persistent temp unlink failure")
        return real_unlink(path, *args, **kwargs)

    mod.os.unlink = unlink
    try:
        ret, err = invoke_capture(mod, data, "templeak")
    finally:
        mod.os.unlink = real_unlink
    try:
        return {
            "returned": ret,
            "error": err,
            "fault_calls": calls,
            "records": records(data),
            "pools": dict(mod.STORE.captures),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def main(target: str):
    return {
        "target": os.path.abspath(target),
        "standalone_final_link_cleanup_failure": standalone_cleanup_unlink_failure(target),
        "committed_final_link_cleanup_failure": committed_cleanup_unlink_failure(target),
        "rollback_directory_fsync": rollback_directory_fsync_absence(target),
        "post_fsync_close_plus_cleanup_failure": post_fsync_close_and_cleanup_failure(target),
        "persistent_temp_cleanup_failure": persistent_temp_cleanup_failure(target),
    }


if __name__ == "__main__":
    target = os.path.abspath(sys.argv[1])
    print(json.dumps(main(target), indent=2, sort_keys=True))

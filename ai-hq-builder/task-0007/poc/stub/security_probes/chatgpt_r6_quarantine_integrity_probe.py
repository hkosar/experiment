#!/usr/bin/env python3
from __future__ import annotations

import errno
import importlib.util
import json
import os
import shutil
import stat
import tempfile
import uuid
from typing import Any

TARGET = os.path.abspath(os.sys.argv[1])


def load(label: str, data: str | None = None):
    spec = importlib.util.spec_from_file_location("r6ind_" + uuid.uuid4().hex, TARGET)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.SECRETS = mod.SecretIndex()
    mod.DESCRIPTOR_KEY = os.urandom(32)
    mod.STORE = mod.Store(candidate=label)
    mod.STORE.base_url = "http://127.0.0.1:9"
    data = data or tempfile.mkdtemp(prefix="chatgpt-r6-independent-")
    mod.Handler.data_dir = data
    return mod, data


def records(data: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for root, _dirs, names in os.walk(data):
        for name in sorted(names):
            path = os.path.join(root, name)
            doc: Any = {}
            try:
                with open(path, encoding="utf-8") as fh:
                    doc = json.load(fh)
            except Exception:
                doc = {}
            fields = doc.get("fields", {}) if isinstance(doc, dict) else {}
            out.append({
                "path": os.path.relpath(path, data),
                "step": doc.get("step") if isinstance(doc, dict) else None,
                "phase": fields.get("phase") if isinstance(fields, dict) else None,
                "outcome": fields.get("outcome") if isinstance(fields, dict) else None,
                "final_status": fields.get("final_status") if isinstance(fields, dict) else None,
                "size": os.path.getsize(path),
            })
    return sorted(out, key=lambda x: x["path"])


def register(mod, task: str):
    return mod.dispatch(
        "POST", "/owner/artifact/register",
        {"source_digest": "a" * 64, "size_bytes": 1, "file_count": 1,
         "task_id": task, "transition": "R", "target_role": "verifier"},
        {"owner_key": mod.STORE.owner_key},
    )


def scenario_post_durable_non_oserror():
    """Committed directory fsync succeeds, then close raises KeyboardInterrupt.

    Because R6 catches BaseException outside the published flag, this can still
    become ordinary CaptureError even though the committed record is durable.
    """
    mod, data = load("postdurable")
    real_close = mod.os.close
    calls = {"directory_closes": 0, "forced": 0}

    def close(fd):
        try:
            isdir = stat.S_ISDIR(mod.os.fstat(fd).st_mode)
        except OSError:
            isdir = False
        if isdir:
            calls["directory_closes"] += 1
            if calls["directory_closes"] == 2:  # committed record, after prepared
                real_close(fd)
                calls["forced"] += 1
                raise KeyboardInterrupt("forced interruption after durable committed fsync")
        return real_close(fd)

    mod.os.close = close
    try:
        status, body = register(mod, "POST-DURABLE")
    finally:
        mod.os.close = real_close
    try:
        recs = records(data)
        return {
            "status": status, "body": body, "fault_calls": calls,
            "registrations": len(mod.STORE.registrations),
            "identity_index": len(mod.STORE.reg_by_identity),
            "transitions": list(mod.STORE.transitions),
            "quarantine": list(mod.STORE.storage_quarantine),
            "pools": dict(mod.STORE.captures), "records": recs,
            "contradiction": (
                status == 500 and body.get("outcome") == "capture-failed"
                and not mod.STORE.registrations
                and any((r.get("step") or "").startswith("committed-artifact-register")
                        and r.get("phase") == "committed" for r in recs)
                and not mod.STORE.storage_quarantine
            ),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def scenario_preartifact_makedirs_failure():
    """No temp or final name is ever created; quarantine should be unnecessary."""
    mod, data = load("premkdir")
    real_makedirs = mod.os.makedirs
    calls = {"makedirs_faults": 0}

    def makedirs(path, *args, **kwargs):
        calls["makedirs_faults"] += 1
        raise OSError(errno.EACCES, "forced pre-artifact directory creation failure")

    mod.os.makedirs = makedirs
    try:
        status, body = register(mod, "PRE-MKDIR")
    finally:
        mod.os.makedirs = real_makedirs
    try:
        recs = records(data)
        return {
            "status": status, "body": body, "fault_calls": calls,
            "records": recs, "pools": dict(mod.STORE.captures),
            "quarantine": list(mod.STORE.storage_quarantine),
            "registrations": len(mod.STORE.registrations),
            "spurious_quarantine": (
                status == 503 and body.get("outcome") == "refused-storage-quarantine"
                and not recs and bool(mod.STORE.storage_quarantine)
            ),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def scenario_rollback_close_after_fsync():
    """Rollback deletion is directory-fsynced, then close reports an error."""
    mod, data = load("rbclose")
    real_fsync, real_close = mod.os.fsync, mod.os.close
    calls = {"fsyncs": 0, "directory_closes": 0, "rollback_close_faults": 0,
             "rollback_directory_fsync_succeeded": False}

    def fsync(fd):
        calls["fsyncs"] += 1
        if calls["fsyncs"] == 2:  # publication directory fsync
            raise OSError(errno.EIO, "forced publication directory fsync failure")
        out = real_fsync(fd)
        if calls["fsyncs"] == 3:
            calls["rollback_directory_fsync_succeeded"] = True
        return out

    def close(fd):
        try:
            isdir = stat.S_ISDIR(mod.os.fstat(fd).st_mode)
        except OSError:
            isdir = False
        if isdir:
            calls["directory_closes"] += 1
            if calls["directory_closes"] == 2:  # rollback dir close
                real_close(fd)
                calls["rollback_close_faults"] += 1
                raise OSError(errno.EIO, "forced close failure after rollback fsync")
        return real_close(fd)

    mod.os.fsync, mod.os.close = fsync, close
    err = None
    try:
        try:
            mod.write_capture("/poc1/receipt", "POC1", "rbclose",
                              {"outcome": "x"}, data_dir=data)
        except BaseException as exc:
            err = {"type": type(exc).__name__, "text": str(exc)}
    finally:
        mod.os.fsync, mod.os.close = real_fsync, real_close
    try:
        recs = records(data)
        return {
            "error": err, "fault_calls": calls, "records": recs,
            "pools": dict(mod.STORE.captures),
            "quarantine": list(mod.STORE.storage_quarantine),
            "spurious_quarantine": (
                calls["rollback_directory_fsync_succeeded"]
                and not recs
                and err is not None and err.get("type") == "CaptureQuarantine"
            ),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def induce_true_quarantine(mod):
    real_open, real_unlink = mod.os.open, mod.os.unlink
    root = os.path.abspath(os.path.join(mod.Handler.data_dir, "captures", mod.STORE.candidate, "POC1"))
    dir_open_count = 0

    def op(path, flags, *args, **kwargs):
        nonlocal dir_open_count
        if os.path.abspath(os.fspath(path)) == root and flags == os.O_RDONLY:
            dir_open_count += 1
            if dir_open_count == 2:  # prepared succeeds; committed publication fails
                raise OSError(errno.EIO, "forced committed publication directory-open failure")
        return real_open(path, flags, *args, **kwargs)

    def unlink(path, *args, **kwargs):
        name = os.path.basename(os.fspath(path))
        if name.startswith("committed-artifact-register-") and name.endswith(".json"):
            raise OSError(errno.EIO, "forced committed final-link rollback failure")
        return real_unlink(path, *args, **kwargs)

    mod.os.open, mod.os.unlink = op, unlink
    try:
        return register(mod, "TRUE-QUAR")
    finally:
        mod.os.open, mod.os.unlink = real_open, real_unlink


def scenario_fail_closed_and_restart():
    mod, data = load("restart")
    try:
        status, body = induce_true_quarantine(mod)
        before_records = records(data)
        before_state = {
            "registrations": len(mod.STORE.registrations),
            "pools": dict(mod.STORE.captures),
            "quarantine": len(mod.STORE.storage_quarantine),
        }
        health = mod.dispatch("GET", "/health", {}, {})
        owner_after = mod.dispatch("POST", "/owner/cases", {},
                                   {"owner_key": mod.STORE.owner_key})
        provider_after = mod.dispatch("POST", "/poc1/receipt", {},
                                      {"provider_key": mod.STORE.provider_key})
        after_records = records(data)
        after_state = {
            "registrations": len(mod.STORE.registrations),
            "pools": dict(mod.STORE.captures),
            "quarantine": len(mod.STORE.storage_quarantine),
        }

        mod2, _ = load("restart", data=data)
        restart_health = mod2.dispatch("GET", "/health", {}, {})
        restart_register = register(mod2, "AFTER-RESTART")
        restart_records = records(data)

        return {
            "initial": {"status": status, "body": body},
            "before_state": before_state,
            "health": health,
            "owner_after": owner_after,
            "provider_after": provider_after,
            "after_state": after_state,
            "records_unchanged_while_quarantined": before_records == after_records,
            "current_process_fail_closed": (
                status == 503
                and health[0] == 200 and health[1].get("storage_quarantined") is True
                and owner_after[0] == 503 and provider_after[0] == 503
                and before_state == after_state and before_records == after_records
            ),
            "restart": {
                "health": restart_health,
                "register": restart_register,
                "records": restart_records,
                "quarantine_count": len(mod2.STORE.storage_quarantine),
                "accepted_without_explicit_recovery": (
                    restart_health[1].get("storage_quarantined") is False
                    and restart_register[0] == 200
                    and len(mod2.STORE.storage_quarantine) == 0
                ),
            },
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def main():
    result = {
        "target": TARGET,
        "post_durable_non_oserror": scenario_post_durable_non_oserror(),
        "preartifact_makedirs_failure": scenario_preartifact_makedirs_failure(),
        "rollback_close_after_fsync": scenario_rollback_close_after_fsync(),
        "fail_closed_and_restart": scenario_fail_closed_and_restart(),
    }
    result["summary"] = {
        "ordinary_failure_with_durable_committed_evidence": result["post_durable_non_oserror"]["contradiction"],
        "preartifact_spurious_quarantine": result["preartifact_makedirs_failure"]["spurious_quarantine"],
        "post_rollback_fsync_spurious_quarantine": result["rollback_close_after_fsync"]["spurious_quarantine"],
        "current_process_fail_closed": result["fail_closed_and_restart"]["current_process_fail_closed"],
        "restart_bypasses_explicit_recovery": result["fail_closed_and_restart"]["restart"]["accepted_without_explicit_recovery"],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

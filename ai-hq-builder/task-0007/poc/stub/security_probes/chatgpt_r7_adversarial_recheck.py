#!/usr/bin/env python3
from __future__ import annotations

import builtins
import errno
import importlib.util
import json
import os
import shutil
import stat
import tempfile
import uuid
from pathlib import Path
from typing import Any

R7 = os.path.abspath('/mnt/data/r7_recheck3_work/pkg/poc/stub/stub_server.py')
R6 = os.path.abspath('/mnt/data/r7_recheck3_work/pkg/poc/stub/r6_reference/stub_server_r6.py')


def load(target: str, label: str, data: str | None = None):
    spec = importlib.util.spec_from_file_location('r7adv_' + uuid.uuid4().hex, target)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.SECRETS = mod.SecretIndex()
    mod.DESCRIPTOR_KEY = os.urandom(32)
    mod.STORE = mod.Store(candidate=label)
    mod.STORE.base_url = 'http://127.0.0.1:9'
    data = data or tempfile.mkdtemp(prefix='chatgpt-r7-adv-')
    mod.Handler.data_dir = data
    return mod, data


def register(mod, task: str):
    return mod.dispatch(
        'POST', '/owner/artifact/register',
        {'source_digest': 'a' * 64, 'size_bytes': 1, 'file_count': 1,
         'task_id': task, 'transition': 'R', 'target_role': 'verifier'},
        {'owner_key': mod.STORE.owner_key},
    )


def files(data: str):
    rows = []
    for root, _dirs, names in os.walk(data):
        for name in sorted(names):
            p = os.path.join(root, name)
            rows.append({'path': os.path.relpath(p, data), 'size': os.path.getsize(p)})
    return rows


def induce_true_quarantine_with_marker_failure(failure: str):
    """Create a real ambiguous final record, then fail marker persistence before a marker file exists."""
    mod, data = load(R7, 'markerfail-' + failure)
    real_os_open = mod.os.open
    real_unlink = mod.os.unlink
    real_makedirs = mod.os.makedirs
    real_builtin_open = builtins.open
    capture_root = os.path.abspath(os.path.join(data, 'captures', mod.STORE.candidate, 'POC1'))
    marker_root = os.path.abspath(os.path.join(data, 'storage_quarantine', mod.STORE.candidate))
    calls = {'capture_dir_opens': 0, 'final_unlink_faults': 0,
             'marker_makedirs_faults': 0, 'marker_open_faults': 0}

    def os_open(path, flags, *args, **kwargs):
        p = os.path.abspath(os.fspath(path))
        if p == capture_root and flags == os.O_RDONLY:
            calls['capture_dir_opens'] += 1
            if calls['capture_dir_opens'] == 2:  # prepared succeeds; committed publication fails
                raise OSError(errno.EIO, 'forced committed publication directory-open failure')
        return real_os_open(path, flags, *args, **kwargs)

    def unlink(path, *args, **kwargs):
        name = os.path.basename(os.fspath(path))
        if name.startswith('committed-artifact-register-') and name.endswith('.json'):
            calls['final_unlink_faults'] += 1
            raise OSError(errno.EIO, 'forced committed final-link rollback failure')
        return real_unlink(path, *args, **kwargs)

    def makedirs(path, *args, **kwargs):
        p = os.path.abspath(os.fspath(path))
        if failure == 'makedirs' and p == marker_root:
            calls['marker_makedirs_faults'] += 1
            raise OSError(errno.EROFS, 'forced marker-directory creation failure')
        return real_makedirs(path, *args, **kwargs)

    def builtin_open(path, mode='r', *args, **kwargs):
        try:
            p = os.path.abspath(os.fspath(path))
        except TypeError:
            p = ''
        if failure == 'open' and p.startswith(marker_root + os.sep) and 'w' in mode:
            calls['marker_open_faults'] += 1
            raise PermissionError(errno.EACCES, 'forced marker-file open failure', p)
        return real_builtin_open(path, mode, *args, **kwargs)

    mod.os.open, mod.os.unlink, mod.os.makedirs = os_open, unlink, makedirs
    builtins.open = builtin_open
    try:
        initial = register(mod, 'MARKER-' + failure.upper())
    finally:
        mod.os.open, mod.os.unlink, mod.os.makedirs = real_os_open, real_unlink, real_makedirs
        builtins.open = real_builtin_open

    try:
        current_health = mod.dispatch('GET', '/health', {}, {})
        before_restart_files = files(data)
        mod2, _ = load(R7, 'markerfail-' + failure, data=data)
        restart_health = mod2.dispatch('GET', '/health', {}, {})
        restart_register = register(mod2, 'AFTER-RESTART-' + failure.upper())
        return {
            'failure': failure,
            'fault_calls': calls,
            'initial': initial,
            'current_health': current_health,
            'before_restart_files': before_restart_files,
            'restart_health': restart_health,
            'restart_register': restart_register,
            'restart_quarantine_count': len(mod2.STORE.storage_quarantine),
            'restart_bypassed': (
                initial[0] == 503
                and (initial[1].get('detail') or {}).get('marker_persisted') is False
                and restart_health[1].get('storage_quarantined') is False
                and restart_register[0] == 200
                and len(mod2.STORE.storage_quarantine) == 0
            ),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def item3_created_temp_but_untracked(target: str):
    """mkstemp creates a name, then faults before returning it; rollback directory proof also fails."""
    mod, data = load(target, 'item3-untracked')
    real_mkstemp = mod.tempfile.mkstemp
    real_os_open = mod.os.open
    state: dict[str, Any] = {'created_path': None, 'mkstemp_faults': 0, 'rollback_open_faults': 0}
    root = os.path.abspath(os.path.join(data, 'captures', mod.STORE.candidate, 'POC1'))

    def mkstemp(*args, **kwargs):
        fd, path = real_mkstemp(*args, **kwargs)
        os.close(fd)
        state['created_path'] = path
        state['mkstemp_faults'] += 1
        # The caller never receives fd/path, so its local tmp remains None.
        raise RuntimeError('forced after real temp creation, before mkstemp returned')

    def os_open(path, flags, *args, **kwargs):
        p = os.path.abspath(os.fspath(path))
        if state['created_path'] and p == root and flags == os.O_RDONLY:
            state['rollback_open_faults'] += 1
            raise OSError(errno.EIO, 'forced rollback directory-open failure')
        return real_os_open(path, flags, *args, **kwargs)

    mod.tempfile.mkstemp = mkstemp
    mod.os.open = os_open
    err = None
    try:
        try:
            mod.write_capture('/poc1/receipt', 'POC1', 'item3', {'outcome': 'x'}, data_dir=data)
        except BaseException as exc:
            err = {'type': type(exc).__name__, 'text': str(exc)}
    finally:
        mod.tempfile.mkstemp = real_mkstemp
        mod.os.open = real_os_open
    try:
        created = state['created_path']
        return {
            'target': os.path.basename(target),
            'fault_calls': state,
            'error': err,
            'created_temp_survives': bool(created and os.path.exists(created)),
            'files': files(data),
            'pools': dict(mod.STORE.captures),
            'quarantine': list(mod.STORE.storage_quarantine),
            'ordinary_release_with_existing_temp': (
                bool(created and os.path.exists(created))
                and err is not None and err.get('type') == 'CaptureError'
                and not mod.STORE.storage_quarantine
                and all(v == 0 for v in mod.STORE.captures.values())
            ),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def item4_non_oserror_after_rollback_fsync(target: str):
    """Rollback deletion and directory fsync succeed; real close then raises RuntimeError."""
    mod, data = load(target, 'item4-runtime')
    real_fsync, real_close = mod.os.fsync, mod.os.close
    calls = {'fsyncs': 0, 'directory_closes': 0, 'rollback_fsync_succeeded': False,
             'runtime_close_faults': 0}

    def fsync(fd):
        calls['fsyncs'] += 1
        if calls['fsyncs'] == 2:  # publication directory fsync
            raise OSError(errno.EIO, 'forced publication directory-fsync failure')
        out = real_fsync(fd)
        if calls['fsyncs'] == 3:
            calls['rollback_fsync_succeeded'] = True
        return out

    def close(fd):
        try:
            isdir = stat.S_ISDIR(mod.os.fstat(fd).st_mode)
        except OSError:
            isdir = False
        if isdir:
            calls['directory_closes'] += 1
            if calls['directory_closes'] == 2:
                real_close(fd)
                calls['runtime_close_faults'] += 1
                raise RuntimeError('forced non-OSError after real rollback directory close')
        return real_close(fd)

    mod.os.fsync, mod.os.close = fsync, close
    err = None
    try:
        try:
            mod.write_capture('/poc1/receipt', 'POC1', 'item4', {'outcome': 'x'}, data_dir=data)
        except BaseException as exc:
            err = {'type': type(exc).__name__, 'text': str(exc)}
    finally:
        mod.os.fsync, mod.os.close = real_fsync, real_close
    try:
        return {
            'target': os.path.basename(target),
            'fault_calls': calls,
            'error': err,
            'files': files(data),
            'pools': dict(mod.STORE.captures),
            'quarantine': list(mod.STORE.storage_quarantine),
            'anomalies': list(mod.STORE.storage_anomalies),
            'violates_item4': (
                calls['rollback_fsync_succeeded']
                and calls['runtime_close_faults'] == 1
                and not files(data)
                and not mod.STORE.storage_quarantine
                and sum(mod.STORE.captures.values()) == 1
                and not mod.STORE.storage_anomalies
                and err is not None and err.get('type') == 'RuntimeError'
            ),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def main():
    result = {
        'marker_write_failures': [
            induce_true_quarantine_with_marker_failure('makedirs'),
            induce_true_quarantine_with_marker_failure('open'),
        ],
        'item3_untracked_temp_compare': [
            item3_created_temp_but_untracked(R6),
            item3_created_temp_but_untracked(R7),
        ],
        'item4_non_oserror_compare': [
            item4_non_oserror_after_rollback_fsync(R6),
            item4_non_oserror_after_rollback_fsync(R7),
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()

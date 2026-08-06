#!/usr/bin/env python3
"""Independent R8 adversarial checks beyond the shipped acceptance cases."""
from __future__ import annotations
import builtins
import errno
import glob
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import sys
import tempfile
import uuid

DEFAULT_TARGET = '/mnt/data/R8_exec/poc/stub/stub_server.py'
TARGET = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                         os.environ.get('R8_TARGET', DEFAULT_TARGET))
DIGEST = 'a' * 64


def load(target: str, candidate: str, data: str | None = None):
    spec = importlib.util.spec_from_file_location('r8adv_' + uuid.uuid4().hex, target)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    mod.SECRETS = mod.SecretIndex()
    mod.DESCRIPTOR_KEY = os.urandom(32)
    mod.STORE = mod.Store(candidate=candidate)
    mod.STORE.base_url = 'http://127.0.0.1:9'
    data = data or tempfile.mkdtemp(prefix='chatgpt-r8-adv-')
    os.makedirs(data, exist_ok=True)
    mod.Handler.data_dir = data
    return mod, data


def register(mod, task='ADV'):
    return mod.dispatch(
        'POST', '/owner/artifact/register',
        {'source_digest': DIGEST, 'size_bytes': 1, 'file_count': 1,
         'task_id': task, 'transition': 'R', 'target_role': 'verifier'},
        {'owner_key': mod.STORE.owner_key})


def health(mod):
    return mod.dispatch('GET', '/health', {}, {})


def marker_paths(mod, data):
    primary = sorted(glob.glob(os.path.join(
        data, mod.QUARANTINE_DIRNAME, mod.STORE.candidate,
        mod.QUARANTINE_PREFIX + '*.json')))
    fallback = sorted(glob.glob(os.path.join(
        data, f'{mod.QUARANTINE_FALLBACK_PREFIX}{mod.STORE.candidate}-*.json')))
    return primary, fallback


def fd_path(fd: int) -> str | None:
    try:
        return os.path.abspath(os.readlink(f'/proc/self/fd/{fd}'))
    except OSError:
        return None


def induce_true_quarantine(mod, data, close_fault: str | None = None):
    """Create the accepted ambiguous committed-record condition.

    close_fault: None, 'primary', or 'both'. When selected, the marker file and
    parent directory are really fsynced and the real directory close completes,
    then RuntimeError is raised from the marker writer's close tail.
    """
    real_open, real_unlink = mod.os.open, mod.os.unlink
    real_close, real_fsync = mod.os.close, mod.os.fsync
    poc_root = os.path.abspath(os.path.join(
        data, 'captures', mod.STORE.candidate, 'POC1'))
    primary_parent = os.path.abspath(mod._quarantine_root(data))
    fallback_parent = os.path.abspath(mod._quarantine_fallback_dir(data))
    close_targets = set()
    if close_fault in ('primary', 'both'):
        close_targets.add(primary_parent)
    if close_fault == 'both':
        close_targets.add(fallback_parent)
    hits = {
        'capture_dir_opens': 0,
        'publication_open_faults': 0,
        'final_unlink_faults': 0,
        'marker_close_fault_paths': [],
        'marker_file_fsync_paths': [],
        'marker_dir_fsync_paths': [],
    }

    def patched_open(path, flags, *args, **kwargs):
        try:
            p = os.path.abspath(os.fspath(path))
        except TypeError:
            p = ''
        if p == poc_root and flags == os.O_RDONLY:
            hits['capture_dir_opens'] += 1
            if hits['capture_dir_opens'] == 2:
                hits['publication_open_faults'] += 1
                raise OSError(errno.EIO, 'forced committed publication dir-open failure')
        return real_open(path, flags, *args, **kwargs)

    def patched_unlink(path, *args, **kwargs):
        name = os.path.basename(os.fspath(path))
        if name.startswith('committed-') and name.endswith('.json'):
            hits['final_unlink_faults'] += 1
            raise OSError(errno.EIO, 'forced final-link rollback failure')
        return real_unlink(path, *args, **kwargs)

    def observed_fsync(fd):
        p = fd_path(fd)
        if p:
            base = os.path.basename(p)
            if (base.startswith(mod.QUARANTINE_PREFIX)
                    or base.startswith(mod.QUARANTINE_FALLBACK_PREFIX)):
                hits['marker_file_fsync_paths'].append(p)
            if p in (primary_parent, fallback_parent):
                hits['marker_dir_fsync_paths'].append(p)
        return real_fsync(fd)

    def close_after_real_close(fd):
        p = fd_path(fd)
        if p in close_targets:
            real_close(fd)
            hits['marker_close_fault_paths'].append(p)
            raise RuntimeError('forced marker directory-close tail failure after real close')
        return real_close(fd)

    mod.os.open, mod.os.unlink = patched_open, patched_unlink
    mod.os.fsync, mod.os.close = observed_fsync, close_after_real_close
    try:
        status, body = register(mod, 'QUARANTINE')
    finally:
        mod.os.open, mod.os.unlink = real_open, real_unlink
        mod.os.fsync, mod.os.close = real_fsync, real_close
    primary, fallback = marker_paths(mod, data)
    docs = {}
    for p in primary + fallback:
        try:
            docs[p] = json.load(open(p, encoding='utf-8')).get('kind')
        except Exception as exc:
            docs[p] = f'UNREADABLE:{type(exc).__name__}'
    return status, body, hits, primary, fallback, docs


def scenario_post_durable_marker_close_misclassified():
    mod, data = load(TARGET, 'marker-close-both')
    try:
        status, body, hits, primary, fallback, docs = induce_true_quarantine(
            mod, data, close_fault='both')
        current_health = health(mod)
        fresh, _ = load(TARGET, mod.STORE.candidate, data=data)
        restart_health = health(fresh)
        restart_register = register(fresh, 'AFTER-RESTART')
        detail = body.get('detail') or {}
        return {
            'status': status,
            'body_restart_fields': {k: body.get(k) for k in (
                'restart_protection', 'survives_restart', 'WARNING',
                'durable_records', 'reconcile_by')},
            'detail_marker_fields': {k: detail.get(k) for k in (
                'marker_persisted', 'marker_path', 'marker_paths',
                'marker_error', 'marker_attempts', 'restart_protection')},
            'faults': hits,
            'primary_markers': primary,
            'fallback_markers': fallback,
            'marker_docs': docs,
            'current_health': current_health,
            'restart_health': restart_health,
            'restart_register': restart_register,
            'false_none_claim': (
                status == 503
                and body.get('restart_protection') == 'none'
                and body.get('survives_restart') is False
                and len(primary) == 1 and len(fallback) == 1
                and len(hits['marker_close_fault_paths']) == 2
                and len(hits['marker_file_fsync_paths']) == 2
                and len(hits['marker_dir_fsync_paths']) == 2
                and restart_health[1].get('storage_quarantined') is True
                and restart_register[0] == 503),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def scenario_failed_primary_is_unlisted_durable_record():
    mod, data = load(TARGET, 'marker-close-primary')
    try:
        status, body, hits, primary, fallback, docs = induce_true_quarantine(
            mod, data, close_fault='primary')
        listed = list(body.get('durable_records') or [])
        for p in listed:
            try:
                os.unlink(p)
            except FileNotFoundError:
                pass
        remaining_before_restart = [p for p in primary + fallback if os.path.exists(p)]
        fresh, _ = load(TARGET, mod.STORE.candidate, data=data)
        restart_health = health(fresh)
        restart_register = register(fresh, 'AFTER-LISTED-DELETION')
        return {
            'status': status,
            'restart_fields': {k: body.get(k) for k in (
                'restart_protection', 'survives_restart', 'durable_records',
                'reconcile_by')},
            'detail_marker_attempts': (body.get('detail') or {}).get('marker_attempts'),
            'faults': hits,
            'primary_markers': primary,
            'fallback_markers': fallback,
            'marker_docs': docs,
            'listed_deleted': listed,
            'remaining_before_restart': remaining_before_restart,
            'restart_health': restart_health,
            'restart_register': restart_register,
            'reconciliation_inventory_incomplete': (
                status == 503
                and body.get('restart_protection') == 'durable'
                and len(primary) == 1 and len(fallback) == 1
                and primary[0] not in listed and fallback[0] in listed
                and os.path.exists(primary[0])
                and restart_health[1].get('storage_quarantined') is True
                and restart_register[0] == 503),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def scenario_restart_inventory_loses_sibling_marker():
    mod, data = load(TARGET, 'restart-inventory')
    try:
        status, body, hits, primary, fallback, docs = induce_true_quarantine(
            mod, data, close_fault=None)
        initial_records = list(body.get('durable_records') or [])
        fresh, _ = load(TARGET, mod.STORE.candidate, data=data)
        restart_health = health(fresh)
        block = restart_health[1].get('storage_quarantine') or {}
        recovered_records = list(block.get('durable_records') or [])
        for p in recovered_records:
            try:
                os.unlink(p)
            except FileNotFoundError:
                pass
        second, _ = load(TARGET, mod.STORE.candidate, data=data)
        second_health = health(second)
        return {
            'status': status,
            'initial_durable_records': initial_records,
            'primary_markers': primary,
            'fallback_markers': fallback,
            'restart_incidents': block.get('incidents'),
            'restart_durable_records': recovered_records,
            'restart_recovered_from_marker': block.get('recovered_from_marker'),
            'second_restart_health_after_deleting_every_reported_record': second_health,
            'sibling_relationship_lost': (
                len(initial_records) == 2
                and block.get('incidents') == 2
                and len(recovered_records) == 1
                and second_health[1].get('storage_quarantined') is True),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def scenario_scan_once_two_process_bypass():
    a, data = load(TARGET, 'scan-once')
    try:
        a_initial = health(a)
        b, _ = load(TARGET, a.STORE.candidate, data=data)
        b_status, b_body, b_hits, primary, fallback, _ = induce_true_quarantine(
            b, data, close_fault=None)
        marker_requires = None
        if primary:
            marker_requires = json.load(open(primary[0], encoding='utf-8')).get('requires')
        a_register = register(a, 'A-AFTER-B-QUARANTINE')
        a_after_health = health(a)
        c, _ = load(TARGET, a.STORE.candidate, data=data)
        c_health = health(c)
        c_register = register(c, 'C-AFTER-B-QUARANTINE')
        return {
            'a_initial_health': a_initial,
            'b_quarantine_status': b_status,
            'b_restart_fields': {k: b_body.get(k) for k in (
                'restart_protection', 'survives_restart', 'durable_records')},
            'b_faults': b_hits,
            'marker_requires': marker_requires,
            'a_register_after_marker_created': a_register,
            'a_health_after_marker_created': a_after_health,
            'fresh_c_health': c_health,
            'fresh_c_register': c_register,
            'already_scanned_process_bypasses': (
                a_initial[1].get('storage_quarantined') is False
                and b_status == 503
                and len(primary) == 1 and len(fallback) == 1
                and a_register[0] == 200
                and a_after_health[1].get('storage_quarantined') is False
                and c_health[1].get('storage_quarantined') is True
                and c_register[0] == 503),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def scenario_transient_scan_error_mislabelled_durable():
    mod, data = load(TARGET, 'transient-scan')
    primary = os.path.abspath(mod._quarantine_root(data))
    real_listdir = mod.os.listdir
    calls = {'primary_faults': 0}

    def transient(path):
        p = os.path.abspath(os.fspath(path))
        if p == primary and calls['primary_faults'] == 0:
            calls['primary_faults'] += 1
            raise OSError(errno.EIO, 'one-shot primary directory listing fault')
        return real_listdir(path)

    mod.os.listdir = transient
    try:
        first_health = health(mod)
    finally:
        mod.os.listdir = real_listdir
    fresh, _ = load(TARGET, mod.STORE.candidate, data=data)
    restart_health = health(fresh)
    restart_register = register(fresh, 'AFTER-TRANSIENT-SCAN')
    block = first_health[1].get('storage_quarantine') or {}
    result = {
        'faults': calls,
        'first_health': first_health,
        'reported_durable_records_exist': [
            (p, os.path.exists(p)) for p in (block.get('durable_records') or [])],
        'restart_health': restart_health,
        'restart_register': restart_register,
        'false_durable_claim': (
            calls['primary_faults'] == 1
            and first_health[1].get('storage_quarantined') is True
            and block.get('restart_protection') == 'durable'
            and block.get('survives_restart') is True
            and restart_health[1].get('storage_quarantined') is False
            and restart_register[0] == 200),
    }
    shutil.rmtree(data, ignore_errors=True)
    return result



def _marker_write_blocker(mod, data, hits):
    """Return a builtins.open replacement that rejects both marker locations."""
    real_builtin = builtins.open
    primary = os.path.abspath(mod._quarantine_root(data))
    fallback_prefix = f'{mod.QUARANTINE_FALLBACK_PREFIX}{mod.STORE.candidate}-'

    def blocked(path, mode='r', *args, **kwargs):
        try:
            full = os.path.abspath(os.fspath(path))
        except TypeError:
            full = ''
        marker_write = (
            full.startswith(primary + os.sep)
            or (os.path.dirname(full) == os.path.abspath(data)
                and os.path.basename(full).startswith(fallback_prefix))
        )
        if marker_write and 'w' in mode:
            hits['marker_open_fault_paths'].append(full)
            raise PermissionError(errno.EACCES, 'forced marker write failure at both locations', full)
        return real_builtin(path, mode, *args, **kwargs)
    return real_builtin, blocked


def scenario_both_marker_writes_fail_truthfully_without_disk_fact():
    """Control: no marker and no temp means the explicit unprotected warning is true."""
    mod, data = load(TARGET, 'both-marker-fail-control')
    try:
        real_open, real_unlink = mod.os.open, mod.os.unlink
        poc_root = os.path.abspath(os.path.join(data, 'captures', mod.STORE.candidate, 'POC1'))
        hits = {'capture_dir_opens': 0, 'publication_open_faults': 0,
                'final_unlink_faults': 0, 'marker_open_fault_paths': []}

        def blocked_open(path, flags, *args, **kwargs):
            try:
                full = os.path.abspath(os.fspath(path))
            except TypeError:
                full = ''
            if full == poc_root and flags == os.O_RDONLY:
                hits['capture_dir_opens'] += 1
                if hits['capture_dir_opens'] == 2:
                    hits['publication_open_faults'] += 1
                    raise OSError(errno.EIO, 'forced committed publication dir-open failure')
            return real_open(path, flags, *args, **kwargs)

        def blocked_unlink(path, *args, **kwargs):
            name = os.path.basename(os.fspath(path))
            if name.startswith('committed-') and name.endswith('.json'):
                hits['final_unlink_faults'] += 1
                raise OSError(errno.EIO, 'forced final-link rollback failure')
            return real_unlink(path, *args, **kwargs)

        real_builtin, blocked_builtin = _marker_write_blocker(mod, data, hits)
        mod.os.open, mod.os.unlink = blocked_open, blocked_unlink
        builtins.open = blocked_builtin
        try:
            status, body = register(mod, 'BOTH-MARKERS-NO-TEMP')
        finally:
            mod.os.open, mod.os.unlink = real_open, real_unlink
            builtins.open = real_builtin

        primary, fallback = marker_paths(mod, data)
        current_health = health(mod)
        fresh, _ = load(TARGET, mod.STORE.candidate, data=data)
        restart_health = health(fresh)
        restart_register = register(fresh, 'AFTER-TRUE-NONE')
        serialized = json.dumps(body, sort_keys=True)
        return {
            'status': status,
            'body': body,
            'faults': hits,
            'primary_markers': primary,
            'fallback_markers': fallback,
            'current_health': current_health,
            'restart_health': restart_health,
            'restart_register': restart_register,
            'truthful_none_control': (
                status == 503
                and len(hits['marker_open_fault_paths']) == 2
                and not primary and not fallback
                and body.get('restart_protection') == 'none'
                and body.get('survives_restart') is False
                and 'does not clear it' not in serialized
                and restart_health[1].get('storage_quarantined') is False
                and restart_register[0] == 200),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def scenario_writefree_temp_exists_but_live_response_claims_none():
    """Both markers fail while a temp survives; live posture must count the disk fact."""
    mod, data = load(TARGET, 'writefree-live-posture')
    try:
        real_mkstemp = mod.tempfile.mkstemp
        real_unlink = mod.os.unlink
        real_close = mod.os.close
        hits = {'created_temp': None, 'mkstemp_faults': 0,
                'temp_unlink_faults': 0, 'marker_open_fault_paths': []}

        def mkstemp_then_raise(*args, **kwargs):
            fd, path = real_mkstemp(*args, **kwargs)
            real_close(fd)
            hits['created_temp'] = path
            hits['mkstemp_faults'] += 1
            raise RuntimeError('forced after real temp create, before path return')

        def keep_temp(path, *args, **kwargs):
            full = os.path.abspath(os.fspath(path))
            if hits['created_temp'] and full == os.path.abspath(hits['created_temp']):
                hits['temp_unlink_faults'] += 1
                raise OSError(errno.EIO, 'forced surviving temp unlink failure')
            return real_unlink(path, *args, **kwargs)

        real_builtin, blocked_builtin = _marker_write_blocker(mod, data, hits)
        mod.tempfile.mkstemp = mkstemp_then_raise
        mod.os.unlink = keep_temp
        builtins.open = blocked_builtin
        try:
            status, body = register(mod, 'WRITEFREE-TEMP')
        finally:
            mod.tempfile.mkstemp = real_mkstemp
            mod.os.unlink = real_unlink
            builtins.open = real_builtin

        temp_path = hits['created_temp']
        temp_exists = bool(temp_path and os.path.isfile(temp_path))
        primary, fallback = marker_paths(mod, data)
        current_health = health(mod)
        fresh, _ = load(TARGET, mod.STORE.candidate, data=data)
        restart_health = health(fresh)
        restart_register = register(fresh, 'AFTER-WRITEFREE-TEMP')
        fresh_block = restart_health[1].get('storage_quarantine') or {}
        detail = body.get('detail') or {}
        return {
            'status': status,
            'body_restart_fields': {k: body.get(k) for k in (
                'restart_protection', 'survives_restart', 'WARNING',
                'durable_records', 'reconcile_by')},
            'detail': detail,
            'faults': hits,
            'temp_exists': temp_exists,
            'primary_markers': primary,
            'fallback_markers': fallback,
            'current_health': current_health,
            'restart_health': restart_health,
            'restart_register': restart_register,
            'fresh_durable_records': fresh_block.get('durable_records'),
            'false_none_despite_writefree_disk_fact': (
                status == 503
                and hits['mkstemp_faults'] == 1
                and hits['temp_unlink_faults'] >= 1
                and len(hits['marker_open_fault_paths']) == 2
                and temp_exists
                and not primary and not fallback
                and detail.get('surviving_temp_path') == temp_path
                and body.get('restart_protection') == 'none'
                and body.get('survives_restart') is False
                and restart_health[1].get('storage_quarantined') is True
                and temp_path in (fresh_block.get('durable_records') or [])
                and restart_register[0] == 503),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def scenario_partial_marker_files_exist_but_live_response_claims_none():
    """A failed write after file creation leaves marker presence, which restart honors."""
    mod, data = load(TARGET, 'partial-marker-live-posture')
    try:
        real_open, real_unlink = mod.os.open, mod.os.unlink
        real_dump = mod.json.dump
        poc_root = os.path.abspath(os.path.join(data, 'captures', mod.STORE.candidate, 'POC1'))
        primary_root = os.path.abspath(mod._quarantine_root(data))
        fallback_prefix = f'{mod.QUARANTINE_FALLBACK_PREFIX}{mod.STORE.candidate}-'
        hits = {'capture_dir_opens': 0, 'publication_open_faults': 0,
                'final_unlink_faults': 0, 'partial_dump_fault_paths': []}

        def blocked_open(path, flags, *args, **kwargs):
            try:
                full = os.path.abspath(os.fspath(path))
            except TypeError:
                full = ''
            if full == poc_root and flags == os.O_RDONLY:
                hits['capture_dir_opens'] += 1
                if hits['capture_dir_opens'] == 2:
                    hits['publication_open_faults'] += 1
                    raise OSError(errno.EIO, 'forced committed publication dir-open failure')
            return real_open(path, flags, *args, **kwargs)

        def blocked_unlink(path, *args, **kwargs):
            name = os.path.basename(os.fspath(path))
            if name.startswith('committed-') and name.endswith('.json'):
                hits['final_unlink_faults'] += 1
                raise OSError(errno.EIO, 'forced final-link rollback failure')
            return real_unlink(path, *args, **kwargs)

        def partial_dump(obj, fh, *args, **kwargs):
            try:
                full = os.path.abspath(os.fspath(fh.name))
            except (AttributeError, TypeError):
                full = ''
            marker_target = (
                full.startswith(primary_root + os.sep)
                or (os.path.dirname(full) == os.path.abspath(data)
                    and os.path.basename(full).startswith(fallback_prefix))
            )
            if marker_target:
                fh.write('{"kind":"storage-quarantine"')
                fh.flush()
                hits['partial_dump_fault_paths'].append(full)
                raise OSError(errno.ENOSPC, 'forced marker JSON write failure after path creation')
            return real_dump(obj, fh, *args, **kwargs)

        mod.os.open, mod.os.unlink = blocked_open, blocked_unlink
        mod.json.dump = partial_dump
        try:
            status, body = register(mod, 'PARTIAL-MARKERS')
        finally:
            mod.os.open, mod.os.unlink = real_open, real_unlink
            mod.json.dump = real_dump

        primary, fallback = marker_paths(mod, data)
        marker_sizes = {p: os.path.getsize(p) for p in primary + fallback}
        current_health = health(mod)
        fresh, _ = load(TARGET, mod.STORE.candidate, data=data)
        restart_health = health(fresh)
        restart_register = register(fresh, 'AFTER-PARTIAL-MARKERS')
        return {
            'status': status,
            'body_restart_fields': {k: body.get(k) for k in (
                'restart_protection', 'survives_restart', 'WARNING',
                'durable_records', 'reconcile_by')},
            'detail': body.get('detail'),
            'faults': hits,
            'primary_markers': primary,
            'fallback_markers': fallback,
            'marker_sizes': marker_sizes,
            'current_health': current_health,
            'restart_health': restart_health,
            'restart_register': restart_register,
            'false_none_despite_partial_marker_presence': (
                status == 503
                and len(hits['partial_dump_fault_paths']) == 2
                and len(primary) == 1 and len(fallback) == 1
                and all(marker_sizes[p] > 0 for p in marker_sizes)
                and body.get('restart_protection') == 'none'
                and body.get('survives_restart') is False
                and restart_health[1].get('storage_quarantined') is True
                and restart_register[0] == 503),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)


def scenario_fallback_scan_error_reports_data_directory_as_record():
    """A transient fallback-list failure is neither durable nor a marker path."""
    mod, data = load(TARGET, 'fallback-scan-error')
    try:
        sentinel = os.path.join(data, 'unrelated-owner-data.txt')
        with open(sentinel, 'w', encoding='utf-8') as fh:
            fh.write('must not be described as a quarantine marker\n')
        os.makedirs(mod._quarantine_root(data), exist_ok=True)
        real_listdir = mod.os.listdir
        hits = {'fallback_list_faults': 0}

        def one_shot(path):
            full = os.path.abspath(os.fspath(path))
            if full == os.path.abspath(data) and hits['fallback_list_faults'] == 0:
                hits['fallback_list_faults'] += 1
                raise OSError(errno.EIO, 'forced one-shot fallback data-dir listing failure')
            return real_listdir(path)

        mod.os.listdir = one_shot
        try:
            first_health = health(mod)
        finally:
            mod.os.listdir = real_listdir
        block = first_health[1].get('storage_quarantine') or {}
        fresh, _ = load(TARGET, mod.STORE.candidate, data=data)
        restart_health = health(fresh)
        restart_register = register(fresh, 'AFTER-FALLBACK-SCAN-ERROR')
        return {
            'faults': hits,
            'sentinel': sentinel,
            'sentinel_exists': os.path.isfile(sentinel),
            'first_health': first_health,
            'reported_durable_records': block.get('durable_records'),
            'reported_record_types': [
                {'path': p, 'is_directory': os.path.isdir(p), 'is_file': os.path.isfile(p)}
                for p in (block.get('durable_records') or [])],
            'restart_health': restart_health,
            'restart_register': restart_register,
            'dangerous_false_inventory': (
                hits['fallback_list_faults'] == 1
                and block.get('restart_protection') == 'durable'
                and block.get('survives_restart') is True
                and os.path.abspath(data) in (block.get('durable_records') or [])
                and os.path.isdir(data)
                and os.path.isfile(sentinel)
                and restart_health[1].get('storage_quarantined') is False
                and restart_register[0] == 200),
        }
    finally:
        shutil.rmtree(data, ignore_errors=True)

def scenario_realpath_fix_edges():
    # The planted candidate symlink is refused, but the reservation is leaked.
    mod, data = load(TARGET, 'realpath-candidate')
    outside = tempfile.mkdtemp(prefix='chatgpt-r8-outside-')
    os.makedirs(os.path.join(data, 'captures'), exist_ok=True)
    os.symlink(outside, os.path.join(data, 'captures', mod.STORE.candidate))
    before = dict(mod.STORE.captures)
    err = None
    try:
        mod.write_capture('/poc1/receipt', 'POC1', 'symlink', {'outcome': 'x'},
                          data_dir=data)
    except BaseException as exc:
        err = f'{type(exc).__name__}: {exc}'
    after = dict(mod.STORE.captures)
    outside_files = sorted(glob.glob(os.path.join(outside, '**', '*'), recursive=True))
    candidate_case = {
        'error': err,
        'before_pools': before,
        'after_pools': after,
        'outside_files': outside_files,
        'refused': bool(err and 'escapes the captures directory' in err),
        'quota_leaked': sum(after.values()) == sum(before.values()) + 1,
    }
    shutil.rmtree(data, ignore_errors=True)
    shutil.rmtree(outside, ignore_errors=True)

    # A symlink at the captures root is accepted because both sides are realpath'd.
    mod2, data2 = load(TARGET, 'realpath-root')
    outside2 = tempfile.mkdtemp(prefix='chatgpt-r8-outside-root-')
    os.symlink(outside2, os.path.join(data2, 'captures'))
    ret = err2 = None
    try:
        ret = mod2.write_capture('/poc1/receipt', 'POC1', 'rootlink',
                                 {'outcome': 'x'}, data_dir=data2)
    except BaseException as exc:
        err2 = f'{type(exc).__name__}: {exc}'
    physical = sorted(glob.glob(os.path.join(outside2, '**', '*.json'), recursive=True))
    root_case = {
        'returned': ret,
        'error': err2,
        'physical_files_outside_data_dir': physical,
        'accepted_root_symlink': bool(ret and physical),
    }
    shutil.rmtree(data2, ignore_errors=True)
    shutil.rmtree(outside2, ignore_errors=True)
    return {'candidate_symlink': candidate_case, 'captures_root_symlink': root_case}


def main():
    out = {
        'target': TARGET,
        'target_sha256': hashlib.sha256(open(TARGET, 'rb').read()).hexdigest(),
        'post_durable_marker_close_misclassified': scenario_post_durable_marker_close_misclassified(),
        'failed_primary_is_unlisted_durable_record': scenario_failed_primary_is_unlisted_durable_record(),
        'restart_inventory_loses_sibling_marker': scenario_restart_inventory_loses_sibling_marker(),
        'scan_once_two_process_bypass': scenario_scan_once_two_process_bypass(),
        'transient_scan_error_mislabelled_durable': scenario_transient_scan_error_mislabelled_durable(),
        'both_marker_writes_fail_truthfully_without_disk_fact': scenario_both_marker_writes_fail_truthfully_without_disk_fact(),
        'writefree_temp_exists_but_live_response_claims_none': scenario_writefree_temp_exists_but_live_response_claims_none(),
        'partial_marker_files_exist_but_live_response_claims_none': scenario_partial_marker_files_exist_but_live_response_claims_none(),
        'fallback_scan_error_reports_data_directory_as_record': scenario_fallback_scan_error_reports_data_directory_as_record(),
        'realpath_fix_edges': scenario_realpath_fix_edges(),
    }
    out['summary'] = {
        'post_durable_marker_close_false_none_claim': out['post_durable_marker_close_misclassified']['false_none_claim'],
        'failed_primary_reconciliation_inventory_incomplete': out['failed_primary_is_unlisted_durable_record']['reconciliation_inventory_incomplete'],
        'restart_inventory_loses_sibling_marker': out['restart_inventory_loses_sibling_marker']['sibling_relationship_lost'],
        'scan_once_two_process_bypass': out['scan_once_two_process_bypass']['already_scanned_process_bypasses'],
        'transient_scan_error_false_durable_claim': out['transient_scan_error_mislabelled_durable']['false_durable_claim'],
        'both_marker_fail_truthful_none_control': out['both_marker_writes_fail_truthfully_without_disk_fact']['truthful_none_control'],
        'writefree_temp_live_false_none_claim': out['writefree_temp_exists_but_live_response_claims_none']['false_none_despite_writefree_disk_fact'],
        'partial_marker_live_false_none_claim': out['partial_marker_files_exist_but_live_response_claims_none']['false_none_despite_partial_marker_presence'],
        'fallback_scan_error_dangerous_false_inventory': out['fallback_scan_error_reports_data_directory_as_record']['dangerous_false_inventory'],
        'candidate_symlink_quota_leak': out['realpath_fix_edges']['candidate_symlink']['quota_leaked'],
        'captures_root_symlink_accepted': out['realpath_fix_edges']['captures_root_symlink']['accepted_root_symlink'],
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()

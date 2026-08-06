#!/usr/bin/env python3
"""Independent R4 post-link cleanup fault probes.

Usage: python chatgpt_capture_postlink_cleanup_probe.py PATH_TO_STUB

Exercises failures after the tempfile has been fully written, including the
new final hard link, temp unlink, and directory-open boundary.
"""
from __future__ import annotations
import errno, glob, importlib.util, json, os, shutil, sys, tempfile, uuid

def load(target,label):
    spec=importlib.util.spec_from_file_location('cleanup_'+uuid.uuid4().hex,target)
    m=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(m)
    m.SECRETS=m.SecretIndex(); m.DESCRIPTOR_KEY=os.urandom(32); m.STORE=m.Store(candidate=label)
    d=tempfile.mkdtemp(prefix='chatgpt-cleanup-'); m.Handler.data_dir=d
    return m,d

def files(d):
    out=[]
    for p in sorted(glob.glob(d+'/**',recursive=True)):
        if os.path.isfile(p): out.append({'path':os.path.relpath(p,d),'size':os.path.getsize(p)})
    return out

def invoke(m,d):
    ret=None; err=None
    try: ret=m.write_capture('/poc1/receipt','POC1','cleanup-fault',{'outcome':'x'},data_dir=d)
    except BaseException as e: err={'type':type(e).__name__,'text':str(e)}
    return {'returned':ret,'error':err,'files':files(d),'pools':dict(m.STORE.captures)}

def link_failure(target):
    m,d=load(target,'linkfail'); real=m.os.link
    m.os.link=lambda *a,**kw: (_ for _ in ()).throw(OSError(errno.EIO,'forced link failure'))
    try: return invoke(m,d)
    finally: m.os.link=real; shutil.rmtree(d,ignore_errors=True)

def temp_unlink_failure(target):
    m,d=load(target,'unlinkfail'); real=m.os.unlink; calls=[]
    def unlink(path,*a,**kw):
        calls.append(str(path))
        if len(calls)==1: raise OSError(errno.EIO,'forced first temp unlink failure after link')
        return real(path,*a,**kw)
    m.os.unlink=unlink
    try:
        out=invoke(m,d); out['unlink_calls']=len(calls); return out
    finally: m.os.unlink=real; shutil.rmtree(d,ignore_errors=True)

def directory_open_failure(target):
    m,d=load(target,'diropen'); real=m.os.open; root=os.path.abspath(os.path.join(d,'captures','diropen','POC1'))
    def op(path,flags,*a,**kw):
        if os.path.abspath(os.fspath(path))==root and flags==os.O_RDONLY:
            raise OSError(errno.EIO,'forced directory open failure after link')
        return real(path,flags,*a,**kw)
    m.os.open=op
    try: return invoke(m,d)
    finally: m.os.open=real; shutil.rmtree(d,ignore_errors=True)

def main(target):
    return {'target':os.path.abspath(target),'link_failure_control':link_failure(target),
            'temp_unlink_after_link_failure':temp_unlink_failure(target),
            'directory_open_after_link_failure':directory_open_failure(target)}

if __name__=='__main__': print(json.dumps(main(os.path.abspath(sys.argv[1])),indent=2,sort_keys=True))

#!/usr/bin/env python3
"""Independent post-publication capture fault probe.

Usage: python chatgpt_capture_publication_fault_probe.py PATH_TO_STUB

Forces EIO on the directory fsync immediately after publication, both for a
standalone capture and for the committed evidence of artifact registration.
The safe result is: no success-named final evidence for an ineffective
transition, no state delta, and no consumed capture quota.
"""
from __future__ import annotations
import errno, glob, importlib.util, json, os, shutil, sys, tempfile, uuid

def load(target,label):
    spec=importlib.util.spec_from_file_location('postpub_'+uuid.uuid4().hex,target)
    m=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(m)
    m.SECRETS=m.SecretIndex(); m.DESCRIPTOR_KEY=os.urandom(32); m.STORE=m.Store(candidate=label)
    d=tempfile.mkdtemp(prefix='chatgpt-postpub-'); m.Handler.data_dir=d
    return m,d

def records(d):
    out=[]
    for p in sorted(glob.glob(d+'/**/*.json',recursive=True)):
        try: doc=json.load(open(p,encoding='utf-8'))
        except Exception: doc={}
        f=doc.get('fields',{}) if isinstance(doc,dict) else {}
        out.append({'file':os.path.relpath(p,d),'size':os.path.getsize(p),
                    'step':doc.get('step') if isinstance(doc,dict) else None,
                    'phase':f.get('phase'),'outcome':f.get('outcome'),
                    'final_status':f.get('final_status')})
    return out

def standalone(target):
    m,d=load(target,'standalone')
    real=m.os.fsync; calls=[]
    def fsync(fd):
        calls.append(fd)
        if len(calls)==2: raise OSError(errno.EIO,'forced publication-directory-fsync failure')
        return real(fd)
    m.os.fsync=fsync; err=None; ret=None
    try:
        try: ret=m.write_capture('/poc1/receipt','POC1','postpub-fault',{'outcome':'x'},data_dir=d)
        except BaseException as e: err={'type':type(e).__name__,'text':str(e)}
        return {'returned':ret,'error':err,'fsync_calls':len(calls),
                'records':records(d),'pools':dict(m.STORE.captures)}
    finally:
        m.os.fsync=real; shutil.rmtree(d,ignore_errors=True)

def committed(target):
    m,d=load(target,'falsecommit')
    real=m.os.fsync; calls=[]
    def fsync(fd):
        calls.append(fd)
        if len(calls)==4: raise OSError(errno.EIO,'forced committed-publication-directory-fsync failure')
        return real(fd)
    m.os.fsync=fsync
    try:
        status,body=m.dispatch('POST','/owner/artifact/register',{
          'source_digest':'a'*64,'size_bytes':1,'file_count':1,
          'task_id':'POSTPUB','transition':'R','target_role':'verifier'
        },{'owner_key':m.STORE.owner_key})
        return {'status':status,'body':body,'fsync_calls':len(calls),
                'registrations':len(m.STORE.registrations),
                'identity_index':len(m.STORE.reg_by_identity),
                'transition_mirror':list(m.STORE.transitions),
                'records':records(d),'pools':dict(m.STORE.captures)}
    finally:
        m.os.fsync=real; shutil.rmtree(d,ignore_errors=True)

def main(target):
    return {'target':os.path.abspath(target),'standalone_directory_fsync':standalone(target),
            'committed_registration_directory_fsync':committed(target)}

if __name__=='__main__':
    print(json.dumps(main(os.path.abspath(sys.argv[1])),indent=2,sort_keys=True))

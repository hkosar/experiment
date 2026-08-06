#!/usr/bin/env python3
import importlib.util, os, tempfile, shutil, stat, json, uuid, sys

def load(target,label):
 s=importlib.util.spec_from_file_location('cmp_'+uuid.uuid4().hex,target); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
 m.SECRETS=m.SecretIndex(); m.DESCRIPTOR_KEY=os.urandom(32); m.STORE=m.Store(candidate=label); m.STORE.base_url='http://127.0.0.1:9'; d=tempfile.mkdtemp(prefix='r6-intcmp-'); m.Handler.data_dir=d; return m,d

def recs(d):
 out=[]
 for root,_,names in os.walk(d):
  for n in names:
   p=os.path.join(root,n)
   try: doc=json.load(open(p)); f=doc.get('fields',{})
   except Exception: doc={}; f={}
   out.append({'file':os.path.relpath(p,d),'step':doc.get('step'),'phase':f.get('phase'),'outcome':f.get('outcome')})
 return sorted(out,key=lambda x:x['file'])

def run(target):
 m,d=load(target,os.path.basename(target)); real=m.os.close; c={'dir':0,'forced':0}
 def close(fd):
  try: isdir=stat.S_ISDIR(m.os.fstat(fd).st_mode)
  except OSError: isdir=False
  if isdir:
   c['dir']+=1
   if c['dir']==2:
    real(fd); c['forced']+=1; raise KeyboardInterrupt('forced after committed dir fsync/close')
  return real(fd)
 m.os.close=close
 try:
  st,b=m.dispatch('POST','/owner/artifact/register',{'source_digest':'a'*64,'size_bytes':1,'file_count':1,'task_id':'CMP','transition':'R','target_role':'verifier'},{'owner_key':m.STORE.owner_key})
 finally: m.os.close=real
 try:
  return {'target':target,'status':st,'body':b,'calls':c,'records':recs(d),'registrations':len(m.STORE.registrations),'identity_index':len(m.STORE.reg_by_identity),'pools':dict(m.STORE.captures),'quarantine':len(getattr(m.STORE,'storage_quarantine',[]))}
 finally: shutil.rmtree(d,ignore_errors=True)

print(json.dumps([run(x) for x in sys.argv[1:]],indent=2,sort_keys=True))

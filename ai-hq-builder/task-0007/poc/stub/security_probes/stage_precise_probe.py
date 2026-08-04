import os,tempfile,importlib.util,shutil,json
SRC='/mnt/data/r2r3_review/pkg/poc/stub/stub_server.py'
s=importlib.util.spec_from_file_location('stg',SRC);S=importlib.util.module_from_spec(s);s.loader.exec_module(S)
S.SECRETS=S.SecretIndex();S.DESCRIPTOR_KEY=os.urandom(32);S.STORE=S.Store(candidate='stg');S.STORE.base_url='http://x';d=tempfile.mkdtemp();S.Handler.data_dir=d
h={'provider_key':S.STORE.provider_key}
st,o=S.dispatch('POST','/poc3/run-started',{'schedule_id':'S','occurrence':'O'},h);rid=o['run_id']
real=S.write_capture
def fail(*a,**kw):
 if len(a)>=3 and a[2]=='stage-delivered': raise S.CaptureError('forced stage capture failure')
 return real(*a,**kw)
S.write_capture=fail
s1,o1=S.dispatch('POST','/stage/deliver',{'run_id':rid},h);after1=S.STORE.stage_attempts.get(rid)
S.write_capture=real
s2,o2=S.dispatch('POST','/stage/deliver',{'run_id':rid},h);after2=S.STORE.stage_attempts.get(rid)
print(json.dumps({'first':{'status':s1,'outcome':o1.get('outcome'),'attempt_counter_after':after1},'second':{'status':s2,'outcome':o2.get('outcome'),'reported_attempt':o2.get('stage_attempt'),'attempt_counter_after':after2}},indent=2))
shutil.rmtree(d,ignore_errors=True)

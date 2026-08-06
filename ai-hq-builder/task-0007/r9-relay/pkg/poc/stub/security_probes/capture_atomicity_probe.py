import os,tempfile,importlib.util,shutil,json,builtins,glob
SRC='/mnt/data/r2r3_review/pkg/poc/stub/stub_server.py'
s=importlib.util.spec_from_file_location('capatomic',SRC);S=importlib.util.module_from_spec(s);s.loader.exec_module(S)
S.SECRETS=S.SecretIndex();S.DESCRIPTOR_KEY=os.urandom(32);S.STORE=S.Store(candidate='capatomic');d=tempfile.mkdtemp();S.Handler.data_dir=d
real_open=builtins.open
def fail_open(path,*a,**kw):
 if str(path).endswith('.tmp'): raise OSError(5,'forced after final placeholder allocation')
 return real_open(path,*a,**kw)
builtins.open=fail_open
err=None
try:
 S.write_capture('/poc1/receipt','POC1','atomic-test',{'outcome':'x'})
except Exception as e: err=repr(e)
finally: builtins.open=real_open
files=[]
for p in glob.glob(d+'/**',recursive=True):
 if os.path.isfile(p): files.append({'path':os.path.relpath(p,d),'size':os.path.getsize(p)})
print(json.dumps({'error':err,'files_left':files,'pool_count':S.STORE.captures},indent=2,sort_keys=True))
shutil.rmtree(d,ignore_errors=True)

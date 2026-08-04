import os,json,tempfile,threading,importlib.util,shutil
SRC='/mnt/data/r2r3_review/pkg/poc/stub/stub_server.py'
def load(name):
 s=importlib.util.spec_from_file_location(name,SRC); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
 m.SECRETS=m.SecretIndex(); m.DESCRIPTOR_KEY=os.urandom(32); m.STORE=m.Store(candidate=name); m.STORE.base_url='http://x'
 d=tempfile.mkdtemp(); m.Handler.data_dir=d; return m,d
def h(m,w): return {'owner_key':m.STORE.owner_key} if w=='o' else {'provider_key':m.STORE.provider_key}
out={}
# registration same identity
m,d=load('reg-race'); bar=threading.Barrier(2); real=m.Transition.prepare
def prep(self):
 if self.name=='artifact-register': bar.wait(timeout=5)
 return real(self)
m.Transition.prepare=prep
p={'source_digest':'a'*64,'size_bytes':1,'file_count':1,'task_id':'T','transition':'R','target_role':'verifier'}
rs=[]; ts=[threading.Thread(target=lambda:rs.append(m.dispatch('POST','/owner/artifact/register',dict(p),h(m,'o')))) for _ in range(2)]
[t.start() for t in ts]; [t.join() for t in ts]
out['registration_race']={'statuses':[x[0] for x in rs], 'outcomes':[x[1].get('outcome') for x in rs], 'refs':[x[1].get('registration_ref') for x in rs], 'registrations':len(m.STORE.registrations), 'identity_index':len(m.STORE.reg_by_identity)}
shutil.rmtree(d)
# run declaration race
m,d=load('run-race'); bar=threading.Barrier(2); real=m.Transition.prepare
def prep2(self):
 if self.name=='run-started': bar.wait(timeout=5)
 return real(self)
m.Transition.prepare=prep2
p={'schedule_id':'S','occurrence':'O'}
rs=[]; ts=[threading.Thread(target=lambda:rs.append(m.dispatch('POST','/poc3/run-started',dict(p),h(m,'p')))) for _ in range(2)]
[t.start() for t in ts]; [t.join() for t in ts]
out['run_declaration_race']={'statuses':[x[0] for x in rs], 'outcomes':[x[1].get('outcome') for x in rs], 'run_ids':[x[1].get('run_id') for x in rs], 'runs':len(m.STORE.runs), 'declaration_index':len(m.STORE.runs_by_declaration)}
shutil.rmtree(d)
print(json.dumps(out,indent=2,sort_keys=True))

import os,json,tempfile,threading,importlib.util,http.client,shutil
SRC='/mnt/data/r2r3_review/pkg/poc/stub/stub_server.py'
def load(name):
 s=importlib.util.spec_from_file_location(name,SRC); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
 m.SECRETS=m.SecretIndex(); m.DESCRIPTOR_KEY=os.urandom(32); m.STORE=m.Store(candidate=name)
 td=tempfile.mkdtemp(prefix=name+'-'); m.Handler.data_dir=td
 srv=m.ThreadingHTTPServer(('127.0.0.1',0),m.Handler); port=srv.server_address[1]; m.STORE.base_url=f'http://127.0.0.1:{port}'
 threading.Thread(target=srv.serve_forever,daemon=True).start()
 return m,td,srv,port
def post(m,port,path,payload,who='provider'):
 c=http.client.HTTPConnection('127.0.0.1',port,timeout=10); h={'Content-Type':'application/json'}
 h['X-Owner-Key' if who=='owner' else 'X-Provider-Key']=m.STORE.owner_key if who=='owner' else m.STORE.provider_key
 c.request('POST',path,json.dumps(payload),h); r=c.getresponse(); b=r.read(); c.close(); return r.status,json.loads(b)
def setup_to_decided(m,port):
 _,r=post(m,port,'/owner/artifact/register',{'source_digest':'a'*64,'size_bytes':1,'file_count':1,'task_id':'T','transition':'R','target_role':'verifier'},'owner')
 _,c=post(m,port,'/poc1/review-case',{'registration_ref':r['registration_ref'],'task_id':'T','transition':'R','artifact_digest':'a'*64,'target_role':'verifier','submission_epoch':1,'envelope':{'trust':'external-untrusted','partition':'business'}},'provider')
 tok=c['resume_token']; rec,_=m.STORE.find_token(tok); cid=rec['case_id']; post(m,port,'/owner/decide',{'case_id':cid,'decision':'accept'},'owner'); return tok,cid
def setup_cap(m,port):
 tok,cid=setup_to_decided(m,port); _,v=post(m,port,'/poc1/verify-decision',{'token':tok},'provider'); return cid,v['execution_capability'],v['action_request']
out={}
# token spend race
m,td,srv,port=load('token-http'); tok,cid=setup_to_decided(m,port)
bar=threading.Barrier(2); real=m.Transition.prepare
def prep(self):
 if self.name=='capability-mint': bar.wait(timeout=5)
 return real(self)
m.Transition.prepare=prep
rs=[]; ts=[threading.Thread(target=lambda:rs.append(post(m,port,'/poc1/verify-decision',{'token':tok},'provider'))) for _ in range(2)]
[t.start() for t in ts]; [t.join() for t in ts]
out['token_spend']={'statuses':[x[0] for x in rs],'authorized':[x[1].get('authorized') for x in rs],'capabilities':[x[1].get('execution_capability') for x in rs],'action_ids':[x[1].get('action_request',{}).get('id') for x in rs],'store_capability_count':len(m.STORE.capabilities)}
srv.shutdown();srv.server_close();shutil.rmtree(td,ignore_errors=True)
# capability spend race
m,td,srv,port=load('cap-http'); cid,cap,ar=setup_cap(m,port)
bar=threading.Barrier(2); real=m.Transition.prepare
def prep2(self):
 if self.name=='attempt-start': bar.wait(timeout=5)
 return real(self)
m.Transition.prepare=prep2
payload={'capability':cap,'action_request_id':ar['id'],'case_id':cid,'payload':ar['payload'],'destination_digest_claimed':'b'*64}
rs=[]; ts=[threading.Thread(target=lambda:rs.append(post(m,port,'/relay/deliver',payload,'provider'))) for _ in range(2)]
[t.start() for t in ts]; [t.join() for t in ts]
out['capability_spend']={'statuses':[x[0] for x in rs],'delivered':[x[1].get('delivered') for x in rs],'replayed':[x[1].get('replayed') for x in rs],'receipt_ids':[x[1].get('receipt',{}).get('receipt_id') for x in rs],'store_receipt':m.STORE.relay_receipts.get(ar['id'])}
srv.shutdown();srv.server_close();shutil.rmtree(td,ignore_errors=True)
print(json.dumps(out,indent=2,sort_keys=True))

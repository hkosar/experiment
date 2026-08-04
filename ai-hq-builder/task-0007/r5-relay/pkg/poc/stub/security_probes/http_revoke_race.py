import os,json,tempfile,threading,importlib.util,http.client,shutil
SRC='/mnt/data/r2r3_review/pkg/poc/stub/stub_server.py'
s=importlib.util.spec_from_file_location('rv',SRC);S=importlib.util.module_from_spec(s);s.loader.exec_module(S)
S.SECRETS=S.SecretIndex();S.DESCRIPTOR_KEY=os.urandom(32);S.STORE=S.Store(candidate='rv');td=tempfile.mkdtemp();S.Handler.data_dir=td
srv=S.ThreadingHTTPServer(('127.0.0.1',0),S.Handler);port=srv.server_address[1];S.STORE.base_url=f'http://127.0.0.1:{port}';threading.Thread(target=srv.serve_forever,daemon=True).start()
def post(path,p,who):
 c=http.client.HTTPConnection('127.0.0.1',port,timeout=10);h={'Content-Type':'application/json',('X-Owner-Key' if who=='o' else 'X-Provider-Key'):(S.STORE.owner_key if who=='o' else S.STORE.provider_key)};c.request('POST',path,json.dumps(p),h);r=c.getresponse();b=json.loads(r.read());c.close();return r.status,b
_,r=post('/owner/artifact/register',{'source_digest':'a'*64,'size_bytes':1,'file_count':1,'task_id':'T','transition':'R','target_role':'verifier'},'o')
_,c=post('/poc1/review-case',{'registration_ref':r['registration_ref'],'task_id':'T','transition':'R','artifact_digest':'a'*64,'target_role':'verifier','submission_epoch':1,'envelope':{'trust':'external-untrusted','partition':'business'}},'p')
tok=c['resume_token'];rec,_=S.STORE.find_token(tok);cid=rec['case_id'];post('/owner/decide',{'case_id':cid,'decision':'accept'},'o');_,a=post('/poc1/verify-decision',{'token':tok},'p');cap=a['execution_capability'];ar=a['action_request']
entered=threading.Event();release=threading.Event();real=S.Transition.prepare
def prep(self):
 if self.name=='attempt-start':
  z=real(self);entered.set();release.wait(5);return z
 return real(self)
S.Transition.prepare=prep
relay=[];t=threading.Thread(target=lambda:relay.append(post('/relay/deliver',{'capability':cap,'action_request_id':ar['id'],'case_id':cid,'payload':ar['payload']},'p')));t.start();entered.wait(5);rev=post('/owner/revoke',{'capability':cap,'reason':'stop'},'o');release.set();t.join()
print(json.dumps({'revoke':rev,'relay':relay[0],'final_status':S.STORE.capabilities[cap]['status'],'receipt':S.STORE.relay_receipts.get(ar['id'])},indent=2,sort_keys=True))
srv.shutdown();srv.server_close();shutil.rmtree(td,ignore_errors=True)

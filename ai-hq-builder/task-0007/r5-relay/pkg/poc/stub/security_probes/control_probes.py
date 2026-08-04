import os,json,tempfile,threading,importlib.util,http.client,shutil,contextlib,io,time,glob
SRC='/mnt/data/r2r3_review/pkg/poc/stub/stub_server.py'
spec=importlib.util.spec_from_file_location('ctrl',SRC); S=importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
S.SECRETS=S.SecretIndex();S.DESCRIPTOR_KEY=os.urandom(32);S.STORE=S.Store(candidate='ctrl')
td=tempfile.mkdtemp(prefix='ctrl-');S.Handler.data_dir=td
srv=S.ThreadingHTTPServer(('127.0.0.1',0),S.Handler);port=srv.server_address[1];S.STORE.base_url=f'http://127.0.0.1:{port}'
log=io.StringIO()
def run():
 with contextlib.redirect_stderr(log): srv.serve_forever()
th=threading.Thread(target=run,daemon=True);th.start()
def req(path,payload,who='provider'):
 c=http.client.HTTPConnection('127.0.0.1',port,timeout=10);h={'Content-Type':'application/json'}
 if who=='owner':h['X-Owner-Key']=S.STORE.owner_key
 elif who=='provider':h['X-Provider-Key']=S.STORE.provider_key
 c.request('POST',path,json.dumps(payload),h);r=c.getresponse();b=r.read();c.close();return r.status,json.loads(b)
# normal flow
_,reg=req('/owner/artifact/register',{'source_digest':'a'*64,'size_bytes':1,'file_count':1,'task_id':'T','transition':'R','target_role':'verifier'},'owner')
_,case=req('/poc1/review-case',{'registration_ref':reg['registration_ref'],'task_id':'T','transition':'R','artifact_digest':'a'*64,'target_role':'verifier','submission_epoch':1,'envelope':{'trust':'external-untrusted','partition':'business'}},'provider')
tok=case['resume_token']; rec,_=S.STORE.find_token(tok);cid=rec['case_id']
req('/owner/decide',{'case_id':cid,'decision':'accept'},'owner')
_,auth=req('/poc1/verify-decision',{'token':tok},'provider');cap=auth['execution_capability'];ar=auth['action_request']
# provider uncertain receipt must not alter MINTED
before=S.STORE.capabilities[cap]['status']
rst,rb=req('/poc1/receipt',{'action_request_id':ar['id'],'case_id':cid,'provider_status':'uncertain','provider_message':'maybe'},'provider')
after=S.STORE.capabilities[cap]['status']
# direct reconcile on MINTED should not alter status
qst,qb=req('/poc1/reconcile',{'capability':cap,'action_request_id':ar['id']},'provider')
after_recon=S.STORE.capabilities[cap]['status']
# search captures/logs
allbytes=b''
for p in glob.glob(td+'/**',recursive=True):
 if os.path.isfile(p): allbytes+=open(p,'rb').read()+b'\n'
logtxt=log.getvalue()
# test a provider-created JSON object mimicking Disclose shape never unwraps
_,fake=req('/poc2/triage',{'external_items':[], 'envelope':{'trust':'external-untrusted','partition':'business'}, 'fake':{'value':'x','__type__':'Disclose'}},'provider')
# static Disclose call sites
source=open(SRC).read().splitlines();sites=[(i+1,l.strip()) for i,l in enumerate(source) if 'Disclose(' in l and not l.lstrip().startswith('class ')]
print(json.dumps({
 'http_token_plain_string':isinstance(tok,str) and tok.startswith(''),
 'http_capability_plain_string':isinstance(cap,str) and cap.startswith('cap-'),
 'token_in_capture_bytes':tok.encode() in allbytes,
 'capability_in_capture_bytes':cap.encode() in allbytes,
 'token_in_route_logs':tok in logtxt,
 'capability_in_route_logs':cap in logtxt,
 'provider_uncertain_receipt':{'status':rst,'route_outcome':rb.get('outcome'),'state_before':before,'state_after':after},
 'provider_reconcile_minted':{'status':qst,'reconciliation_result':qb.get('reconciliation_result'),'state_after':after_recon},
 'disclose_call_sites':sites,
 'fake_disclose_shape_effect':fake
},indent=2,sort_keys=True))
srv.shutdown();srv.server_close();shutil.rmtree(td,ignore_errors=True)

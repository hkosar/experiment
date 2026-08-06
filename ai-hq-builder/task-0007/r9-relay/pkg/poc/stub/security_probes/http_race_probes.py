import os, json, tempfile, threading, importlib.util, http.client, shutil, time
SRC='/mnt/data/r2r3_review/pkg/poc/stub/stub_server.py'
spec=importlib.util.spec_from_file_location('shttp',SRC); S=importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
S.SECRETS=S.SecretIndex(); S.DESCRIPTOR_KEY=os.urandom(32); S.STORE=S.Store(candidate='http-probe')
td=tempfile.mkdtemp(prefix='http-probe-'); S.Handler.data_dir=td
srv=S.ThreadingHTTPServer(('127.0.0.1',0),S.Handler); port=srv.server_address[1]; S.STORE.base_url=f'http://127.0.0.1:{port}'
th=threading.Thread(target=srv.serve_forever,daemon=True); th.start()

def post(path,payload,who='provider'):
    c=http.client.HTTPConnection('127.0.0.1',port,timeout=10)
    h={'Content-Type':'application/json'}
    h['X-Owner-Key' if who=='owner' else 'X-Provider-Key']=S.STORE.owner_key if who=='owner' else S.STORE.provider_key
    raw=json.dumps(payload)
    c.request('POST',path,raw,h); r=c.getresponse(); b=r.read(); c.close()
    return r.status,json.loads(b)

def register():
    return post('/owner/artifact/register',{'source_digest':'a'*64,'size_bytes':1,'file_count':1,'task_id':'T','transition':'R','target_role':'verifier'},'owner')[1]['registration_ref']
def review(ref):
    return post('/poc1/review-case',{'registration_ref':ref,'task_id':'T','transition':'R','artifact_digest':'a'*64,'target_role':'verifier','submission_epoch':1,'envelope':{'trust':'external-untrusted','partition':'business'}})

out={}
# review race actual HTTP, barrier in capture after pre-check
ref=register(); bar=threading.Barrier(2); real=S.write_capture
def wc(*a,**kw):
    if len(a)>=3 and a[2]=='review-case': bar.wait(timeout=5)
    return real(*a,**kw)
S.write_capture=wc
rs=[]; ts=[threading.Thread(target=lambda:rs.append(review(ref))) for _ in range(2)]
[t.start() for t in ts]; [t.join() for t in ts]
S.write_capture=real
out['http_review_race']={'statuses':[x[0] for x in rs],'outcomes':[x[1].get('outcome') for x in rs],'case_count':len(S.STORE.cases),'token_count':len(S.STORE.tokens)}
# choose one case/token; reset fresh for token race easier
srv.shutdown(); srv.server_close(); shutil.rmtree(td,ignore_errors=True)
print(json.dumps(out,indent=2))

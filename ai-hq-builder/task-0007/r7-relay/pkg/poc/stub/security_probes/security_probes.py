import os, sys, json, tempfile, shutil, threading, importlib.util, time, hashlib
SRC='/mnt/data/r2r3_review/pkg/poc/stub/stub_server.py'

def loadmod(name='stubprobe'):
    spec=importlib.util.spec_from_file_location(name,SRC)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    # reset globals cleanly
    m.SECRETS=m.SecretIndex()
    m.DESCRIPTOR_KEY=os.urandom(32)
    m.STORE=m.Store(candidate='probe')
    m.STORE.base_url='http://127.0.0.1:9999'
    d=tempfile.mkdtemp(prefix='r2r3-probe-')
    m.Handler.data_dir=d
    return m,d

def hdr(m, who):
    return {'owner_key':m.STORE.owner_key} if who=='owner' else {'provider_key':m.STORE.provider_key}

def reveal(v):
    return v.value if hasattr(v,'value') else v

def setup_registration(m, task='TASK-1', transition='review', role='verifier', digest='a'*64):
    st,o=m.dispatch('POST','/owner/artifact/register',{
      'source_digest':digest,'size_bytes':123,'file_count':2,'task_id':task,
      'transition':transition,'target_role':role},hdr(m,'owner'))
    assert st==200,(st,o)
    return o['registration_ref']

def review_payload(ref, task='TASK-1', transition='review', role='verifier', digest='a'*64, epoch=1):
    return {'registration_ref':ref,'task_id':task,'transition':transition,
      'artifact_digest':digest,'target_role':role,'submission_epoch':epoch,
      'envelope':{'trust':'external-untrusted','partition':'business'}}

def setup_case(m):
    ref=setup_registration(m)
    st,o=m.dispatch('POST','/poc1/review-case',review_payload(ref),hdr(m,'provider'))
    assert st==200,(st,o)
    tok=reveal(o['resume_token'])
    # locate case via token
    rec,_=m.STORE.find_token(tok); cid=rec['case_id']
    st,o=m.dispatch('POST','/owner/decide',{'case_id':cid,'decision':'accept'},hdr(m,'owner'))
    assert st==200,(st,o)
    st,o=m.dispatch('POST','/poc1/verify-decision',{'token':tok},hdr(m,'provider'))
    assert st==200 and o.get('authorized'),(st,o)
    cap=reveal(o['execution_capability'])
    return cid,cap,o['action_request']

results={}

# 1 concurrent duplicate review case
m,d=loadmod('probe_review_race')
try:
    ref=setup_registration(m)
    payload=review_payload(ref)
    barrier=threading.Barrier(2)
    real=m.write_capture
    def wc(*a,**kw):
        if len(a)>=3 and a[2]=='review-case':
            barrier.wait(timeout=5)
        return real(*a,**kw)
    m.write_capture=wc
    outs=[]
    def worker(): outs.append(m.dispatch('POST','/poc1/review-case',dict(payload),hdr(m,'provider')))
    ts=[threading.Thread(target=worker) for _ in range(2)]
    [t.start() for t in ts]; [t.join() for t in ts]
    results['concurrent_review_case']={
      'statuses':[x[0] for x in outs], 'outcomes':[x[1].get('outcome') for x in outs],
      'case_count':len(m.STORE.cases),'identity_count':len(m.STORE.by_identity),
      'token_count':len(m.STORE.tokens),
      'case_ids':list(m.STORE.cases),
      'tokens_case_ids':[v['case_id'] for v in m.STORE.tokens.values()]}
finally: shutil.rmtree(d,ignore_errors=True)

# 2 concurrent same resume token verify -> multiple capabilities
m,d=loadmod('probe_token_race')
try:
    ref=setup_registration(m)
    st,o=m.dispatch('POST','/poc1/review-case',review_payload(ref),hdr(m,'provider'))
    tok=reveal(o['resume_token']); rec,_=m.STORE.find_token(tok); cid=rec['case_id']
    m.dispatch('POST','/owner/decide',{'case_id':cid,'decision':'accept'},hdr(m,'owner'))
    barrier=threading.Barrier(2)
    realprep=m.Transition.prepare
    def prep(self):
        if self.name=='capability-mint': barrier.wait(timeout=5)
        return realprep(self)
    m.Transition.prepare=prep
    outs=[]
    def worker(): outs.append(m.dispatch('POST','/poc1/verify-decision',{'token':tok},hdr(m,'provider')))
    ts=[threading.Thread(target=worker) for _ in range(2)]
    [t.start() for t in ts]; [t.join() for t in ts]
    results['concurrent_token_spend']={
      'statuses':[x[0] for x in outs], 'authorized':[x[1].get('authorized') for x in outs],
      'capability_count':len(m.STORE.capabilities), 'action_request_ids':[x[1].get('action_request',{}).get('id') for x in outs],
      'token_consumed':m.STORE.tokens[m.STORE.digest(tok)]['consumed']}
finally: shutil.rmtree(d,ignore_errors=True)

# 3 concurrent deliver same capability -> multiple delivered responses/receipts
m,d=loadmod('probe_deliver_race')
try:
    cid,cap,ar=setup_case(m)
    payload={'capability':cap,'action_request_id':ar['id'],'case_id':cid,'payload':ar['payload'],'destination_digest_claimed':'b'*64}
    barrier=threading.Barrier(2)
    realprep=m.Transition.prepare
    def prep(self):
        if self.name=='attempt-start': barrier.wait(timeout=5)
        return realprep(self)
    m.Transition.prepare=prep
    outs=[]
    def worker(): outs.append(m.dispatch('POST','/relay/deliver',dict(payload),hdr(m,'provider')))
    ts=[threading.Thread(target=worker) for _ in range(2)]
    [t.start() for t in ts]; [t.join() for t in ts]
    results['concurrent_capability_spend']={
      'statuses':[x[0] for x in outs], 'delivered':[x[1].get('delivered') for x in outs],
      'replayed':[x[1].get('replayed') for x in outs],
      'receipt_ids':[x[1].get('receipt',{}).get('receipt_id') for x in outs],
      'attempts':[x[1].get('attempt') for x in outs],
      'stored_receipt':m.STORE.relay_receipts.get(ar['id']),
      'relay_attempts':m.STORE.relay_attempts.get(ar['id']),
      'status':m.STORE.capabilities[cap]['status']}
finally: shutil.rmtree(d,ignore_errors=True)

# 4 revoke race: owner revoke during attempt-start prepare, relay still delivers
m,d=loadmod('probe_revoke_race')
try:
    cid,cap,ar=setup_case(m)
    payload={'capability':cap,'action_request_id':ar['id'],'case_id':cid,'payload':ar['payload'],'destination_digest_claimed':'b'*64}
    entered=threading.Event(); release=threading.Event()
    realprep=m.Transition.prepare
    def prep(self):
        if self.name=='attempt-start':
            # write prepared then pause before caller reads prior_status/mutates
            r=realprep(self); entered.set(); release.wait(5); return r
        return realprep(self)
    m.Transition.prepare=prep
    out=[]
    t=threading.Thread(target=lambda: out.append(m.dispatch('POST','/relay/deliver',dict(payload),hdr(m,'provider'))))
    t.start(); entered.wait(5)
    revoke=m.dispatch('POST','/owner/revoke',{'capability':cap,'reason':'owner stop'},hdr(m,'owner'))
    release.set(); t.join()
    results['revoke_vs_delivery_race']={
      'revoke_status':revoke[0], 'revoke_outcome':revoke[1].get('outcome'),
      'relay_status':out[0][0], 'relay_delivered':out[0][1].get('delivered'),
      'final_capability_status':m.STORE.capabilities[cap]['status'],
      'receipt_present':ar['id'] in m.STORE.relay_receipts}
finally: shutil.rmtree(d,ignore_errors=True)

# 5 review case false case-opened capture if token mint fails after capture
m,d=loadmod('probe_review_false_capture')
try:
    ref=setup_registration(m)
    # force mint_token quota failure
    realmint=m.STORE.mint_token
    def badmint(case_id): raise m.QuotaError('forced token ceiling',429)
    m.STORE.mint_token=badmint
    st,o=m.dispatch('POST','/poc1/review-case',review_payload(ref),hdr(m,'provider'))
    caps=[]
    for root,_,files in os.walk(d):
      for f in files:
        if f.endswith('.json'):
          try:
            doc=json.load(open(os.path.join(root,f)))
            if doc.get('step') in ('review-case','review-quota'): caps.append({'step':doc.get('step'),'fields':doc.get('fields')})
          except: pass
    results['false_case_opened_capture_on_token_failure']={'status':st,'outcome':o.get('outcome'),'case_count':len(m.STORE.cases),'captures':caps}
finally: shutil.rmtree(d,ignore_errors=True)

# 6 capability committed evidence persists if secret-index add fails after commit
m,d=loadmod('probe_cap_false_commit')
try:
    ref=setup_registration(m)
    st,o=m.dispatch('POST','/poc1/review-case',review_payload(ref),hdr(m,'provider'))
    tok=reveal(o['resume_token']); rec,_=m.STORE.find_token(tok); cid=rec['case_id']
    m.dispatch('POST','/owner/decide',{'case_id':cid,'decision':'accept'},hdr(m,'owner'))
    realadd=m.SECRETS.add
    def add(v):
      if isinstance(v,str) and v.startswith('cap-'): return False
      return realadd(v)
    m.SECRETS.add=add
    st,o=m.dispatch('POST','/poc1/verify-decision',{'token':tok},hdr(m,'provider'))
    commits=[]
    for root,_,files in os.walk(d):
      for f in files:
        if f.startswith('committed-capability-mint'):
          commits.append(json.load(open(os.path.join(root,f))))
    results['false_capability_commit_on_secret_index_failure']={'status':st,'outcome':o.get('outcome'),'capability_count':len(m.STORE.capabilities),'token_consumed':m.STORE.tokens[m.STORE.digest(tok)]['consumed'],'commit_count':len(commits),'commit_fields':[x.get('fields') for x in commits]}
finally: shutil.rmtree(d,ignore_errors=True)

# 7 expiry transition no prepared/committed evidence
m,d=loadmod('probe_expiry_evidence')
try:
    cid,cap,ar=setup_case(m)
    m.STORE.capabilities[cap]['expires_at']=time.time()-1
    before=len(m.STORE.transitions)
    st,o=m.dispatch('POST','/relay/deliver',{'capability':cap,'action_request_id':ar['id'],'case_id':cid,'payload':ar['payload']},hdr(m,'provider'))
    expiration_caps=[]
    for root,_,files in os.walk(d):
      for f in files:
        if 'expir' in f.lower(): expiration_caps.append(f)
    results['expiry_without_transition_evidence']={'status':st,'outcome':o.get('outcome'),'final_status':m.STORE.capabilities[cap]['status'],'transition_count_delta':len(m.STORE.transitions)-before,'expiration_named_captures':expiration_caps}
finally: shutil.rmtree(d,ignore_errors=True)

# 8 stage attempt increments on capture failure
m,d=loadmod('probe_stage_capture_failure')
try:
    # start run
    st,o=m.dispatch('POST','/poc3/run-started',{'schedule_id':'s','occurrence':'o'},hdr(m,'provider'))
    rid=o['run_id']
    real=m.write_capture
    def wc(*a,**kw):
      if len(a)>=3 and a[2]=='stage-delivered': raise m.CaptureError('forced')
      return real(*a,**kw)
    m.write_capture=wc
    st1,o1=m.dispatch('POST','/stage/deliver',{'run_id':rid},hdr(m,'provider'))
    m.write_capture=real
    st2,o2=m.dispatch('POST','/stage/deliver',{'run_id':rid},hdr(m,'provider'))
    results['stage_attempt_mutates_without_capture']={'first_status':st1,'first_outcome':o1.get('outcome'),'attempt_after_failure':m.STORE.stage_attempts.get(rid),'second_status':st2,'second_attempt':o2.get('stage_attempt')}
finally: shutil.rmtree(d,ignore_errors=True)

print(json.dumps(results,indent=2,sort_keys=True))

#!/usr/bin/env python3
"""Independent N-way live-HTTP serialization probe for TASK-0007 R4.

Installs an external release gate at route-handler entry. The gate does not
raise inside the transition; it records how many handlers can enter before the
first is released. This proves whether the outer transition mutex generalizes
beyond the two-request acceptance cases.
"""
from __future__ import annotations
import json, os, threading, time
from chatgpt_r4_prelock_probe import Live, DIGEST, reg_body, review_body, to_decided, to_capability

N = 8

def gated_many(s, route, body, who='provider', n=N):
    key=('POST',route); real=s.m.HANDLERS[key]
    guard=threading.Lock(); first=threading.Event(); release=threading.Event()
    entered=0; responses=[None]*n
    def wrapped(payload):
        nonlocal entered
        with guard:
            entered += 1
            first.set()
        if not release.wait(15):
            raise RuntimeError('nway release timeout')
        return real(payload)
    s.m.HANDLERS[key]=wrapped
    def go(i):
        try: responses[i]=s.post(route,dict(body),who)
        except Exception as e: responses[i]=('EXC',{'error':type(e).__name__,'detail':str(e)})
    threads=[threading.Thread(target=go,args=(i,)) for i in range(n)]
    threads[0].start()
    if not first.wait(5): raise RuntimeError('first handler did not enter')
    for t in threads[1:]: t.start()
    time.sleep(2)
    with guard: before=entered
    release.set()
    for t in threads: t.join(40)
    s.m.HANDLERS[key]=real
    return before,responses

def summarize(responses):
    return {
      'statuses':[r[0] for r in responses],
      'outcomes':[r[1].get('outcome') if isinstance(r,tuple) and isinstance(r[1],dict) else None for r in responses],
    }

def run(target):
    out={}
    s=Live(target,'nway-reg')
    try:
      before,r=gated_many(s,'/owner/artifact/register',reg_body('NREG'),'owner')
      out['registration']={'handler_entries_before_release':before,**summarize(r),
                           'registrations':len(s.m.STORE.registrations),'identity_index':len(s.m.STORE.reg_by_identity)}
    finally:s.close()

    s=Live(target,'nway-case')
    try:
      reg=s.post('/owner/artifact/register',reg_body('NCASE'),'owner')[1]
      before,r=gated_many(s,'/poc1/review-case',review_body(reg['registration_ref'],'NCASE'))
      out['review_case']={'handler_entries_before_release':before,**summarize(r),
                          'cases':len(s.m.STORE.cases),'tokens':len(s.m.STORE.tokens)}
    finally:s.close()

    s=Live(target,'nway-token')
    try:
      _,tok=to_decided(s,'NTOK')
      before,r=gated_many(s,'/poc1/verify-decision',{'token':tok})
      out['token_spend']={'handler_entries_before_release':before,**summarize(r),
                          'capabilities':len(s.m.STORE.capabilities),'action_requests':len(s.m.STORE.cap_by_ar)}
    finally:s.close()

    s=Live(target,'nway-cap')
    try:
      cid,cap,ar=to_capability(s,'NCAP')
      body={'capability':cap,'action_request_id':ar['id'],'case_id':cid,
            'payload':ar['payload'],'destination_digest_claimed':DIGEST}
      before,r=gated_many(s,'/relay/deliver',body)
      out['capability_spend']={'handler_entries_before_release':before,**summarize(r),
                              'receipts':len(s.m.STORE.relay_receipts),
                              'final_status':s.m.STORE.capabilities[cap]['status']}
    finally:s.close()

    s=Live(target,'nway-run')
    try:
      before,r=gated_many(s,'/poc3/run-started',{'schedule_id':'NS','occurrence':'NO','provider_correlation_id':'x'})
      out['run_declaration']={'handler_entries_before_release':before,**summarize(r),
                              'runs':len(s.m.STORE.runs),'declarations':len(s.m.STORE.runs_by_declaration)}
    finally:s.close()
    return out

if __name__=='__main__':
    import sys
    print(json.dumps(run(os.path.abspath(sys.argv[1])),indent=2,sort_keys=True))

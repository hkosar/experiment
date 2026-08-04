#!/usr/bin/env python3
from __future__ import annotations
import os, json, threading, time
from chatgpt_r4_prelock_probe import Live, to_capability, DIGEST

def run(target):
    s=Live(target,'epoch-probe')
    try:
        cid,cap,ar=to_capability(s,'EPOCH')
        entered=threading.Event(); release=threading.Event(); real=s.m.Transition.prepare
        def prep(self):
            if self.name=='attempt-start':
                z=real(self)
                entered.set()
                if not release.wait(10):
                    raise RuntimeError('release timeout')
                return z
            return real(self)
        s.m.Transition.prepare=prep
        dl=[]; rv=[]
        body={'capability':cap,'action_request_id':ar['id'],'case_id':cid,
              'payload':ar['payload'],'destination_digest_claimed':DIGEST}
        td=threading.Thread(target=lambda: dl.append(s.post('/relay/deliver',body)))
        tr=threading.Thread(target=lambda: rv.append(s.post('/owner/revoke',{'capability':cap,'reason':'stop'},'owner')))
        td.start()
        if not entered.wait(5): raise RuntimeError('delivery never reached attempt-start prepare')
        tr.start()
        revoke_returned_while_delivery_paused=False
        deadline=time.time()+2
        while time.time()<deadline:
            if rv:
                revoke_returned_while_delivery_paused=True
                break
            time.sleep(.01)
        release.set()
        td.join(30);tr.join(30)
        return {'revoke_returned_while_delivery_paused':revoke_returned_while_delivery_paused,
                'revoke':rv[0] if rv else None,'delivery':dl[0] if dl else None,
                'final_status':s.m.STORE.capabilities[cap]['status'],
                'receipt_present':ar['id'] in s.m.STORE.relay_receipts}
    finally:
        s.close()

if __name__=='__main__':
    import sys
    print(json.dumps(run(os.path.abspath(sys.argv[1])),indent=2,sort_keys=True))

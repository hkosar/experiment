import os,tempfile,importlib.util,shutil,json
SRC='/mnt/data/r2r3_review/pkg/poc/stub/stub_server.py'
s=importlib.util.spec_from_file_location('quota',SRC);S=importlib.util.module_from_spec(s);s.loader.exec_module(S)
S.SECRETS=S.SecretIndex();S.DESCRIPTOR_KEY=os.urandom(32);S.STORE=S.Store(candidate='quota');S.STORE.base_url='http://x';d=tempfile.mkdtemp();S.Handler.data_dir=d
h={'provider_key':S.STORE.provider_key}
# force quota already reached
S.STORE.receipt_count=S.MAX_RECEIPTS
p1=S.dispatch('POST','/poc1/refusal',{'action_request_id':'ar-x','case_id':'case-x','refusal_code':'X','refusal_message':'x'},h)
p3=S.dispatch('POST','/poc3/receipt',{'run_id':'none','occurrence':'o','provider_status':'ok'},h)
# fill owner ideas quota; provider Case B doesn't create STORE.ideas and route doesn't check
for i in range(S.MAX_IDEAS): S.STORE.ideas[str(i)]={'provisional':False}
p2=S.dispatch('POST','/poc2/triage',{'external_items':[],'envelope':{'trust':'external-untrusted','partition':'business'}},h)
print(json.dumps({'receipt_count_pre':S.MAX_RECEIPTS,'poc1_refusal':{'status':p1[0],'outcome':p1[1].get('outcome')},'poc3_receipt':{'status':p3[0],'outcome':p3[1].get('outcome')},'ideas_count_pre':S.MAX_IDEAS,'poc2_triage':{'status':p2[0],'outcome':p2[1].get('outcome')}},indent=2))
shutil.rmtree(d,ignore_errors=True)

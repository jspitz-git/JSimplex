"""Exclusive offline synthetic GREEN original/portable binding tests."""
from common_final import *
import copy,subprocess
h=H/'green';ph='0'*64
hashes={str(h/n):ph for n in ('audit.json','pins.json','postcheck.json','review.md')}
audit=dict(all_passed=True,checks={'synthetic':True},raw_sha256={n:ph for n in GREEN_RAW},invocation_sha256={str(h/n):ph for n in ('guard-invocation.json','guard-output.log','attempt-reserved.json')})
post=dict(all_passed=True,checks={'synthetic':True},sha256={str(h/n):ph for n in ('audit.json','pins.json')})
for n in GREEN_RAW:
 for p in (out('green')/n,h/'portable'/n):hashes[str(p)]=ph
hashes.update(audit['invocation_sha256']);records={str(h/'audit.json'):audit,str(h/'postcheck.json'):post}
def check(hashes,records,review='ACCEPTED. Unresolved findings: []'):
 return green_evidence(hashfn=lambda p:hashes[str(p)],readfn=lambda p:records[str(p)],textfn=lambda p:review)
paths=check(hashes,records);c={'synthetic_valid_all23_paths':len(paths)==23,'all_original_portable_included':all(str(p) in paths for n in GREEN_RAW for p in (out('green')/n,h/'portable'/n))};cases=[]
for name,mutate in [('missing_original',lambda a,b:a.pop(str(out('green')/'raw/case.toml'))),('changed_original',lambda a,b:a.__setitem__(str(out('green')/'raw/case.toml'),'1'*64)),('missing_portable',lambda a,b:a.pop(str(h/'portable/raw/case.toml'))),('changed_portable',lambda a,b:a.__setitem__(str(h/'portable/process.json'),'1'*64)),('missing_invocation',lambda a,b:a.pop(str(h/'guard-invocation.json'))),('changed_invocation',lambda a,b:a.__setitem__(str(h/'guard-output.log'),'1'*64)),('incomplete_raw_schema',lambda a,b:b[str(h/'audit.json')]['raw_sha256'].pop('run.log')),('failed_post',lambda a,b:b[str(h/'postcheck.json')].__setitem__('all_passed',False)),('changed_stage_pins',lambda a,b:a.__setitem__(str(h/'pins.json'),'1'*64))]:
 a=copy.deepcopy(hashes);b=copy.deepcopy(records);mutate(a,b)
 try:check(a,b);rejected=False
 except (AssertionError,KeyError):rejected=True
 c[name]=rejected;cases.append(dict(name=name,rejected=rejected))
c['master_required_all_evidence']='req.update(green_evidence())' in (H/'common_final.py').read_text();c['stage_requires_all_evidence']="set(evidence).issubset(a['sha256'])" in (H/'common_final.py').read_text()
f=H/'final-failure-cases';f.mkdir()
for name,contents in [('missing',None),('malformed','{'),('incomplete','{}')]:
 d=f/name;d.mkdir()
 if contents is not None:(d/'process.json').write_text(contents)
 dest=f/(name+'-audit.json');cmd=[sys.executable,str(H/'audit-final.py'),'green',str(d),str(dest)];p=subprocess.run(cmd,capture_output=True,text=True);dump(f/(name+'-process.json'),dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));x=read(dest);c['durable_'+name]=p.returncode==1 and x['all_passed'] is False
result=dict(checks=c,all_passed=all(c.values()),cases=cases,scope='Synthetic hashes/metadata and new Python auditor only, no numerical call.',sha256={str(H/n):sha(H/n) for n in ('common_final.py','launcher-final.py','audit-final.py','review_fix_2.py','final_failure_tests.py')});dump(H/'final-failure-tests.json',result);print(json.dumps(c));assert result['all_passed']

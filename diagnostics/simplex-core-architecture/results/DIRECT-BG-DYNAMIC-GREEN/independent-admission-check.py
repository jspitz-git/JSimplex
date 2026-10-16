"""New independent read/hash-only GREEN check. Never imports existing controls or Julia."""
import hashlib,json
from pathlib import Path
E=Path(__file__).resolve().parent
D=E.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION'
R=E.parents[3]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
checks=[]
def check(v,n):
 assert v,n
 checks.append(n)
def p(n):return Path(n) if Path(n).is_absolute() else R/n
prep=rd(D/'preparation-pins.json')
check(set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']),'exact preparation membership')
check(all(sha(p(n))==h for n,h in prep['sha256'].items()),'all preparation digests')
rev=rd(D/'review.json')
check(rev['accepted'] is True and rev['findings']==[],'accepted preparation review')
check(all(sha(p(n))==h for n,h in rev['sha256'].items()),'preparation review bindings')
for mode,s in rd(D/'stages.json').items():
 root=Path(s['path'])
 check({str(x.relative_to(root)) for x in root.rglob('*') if x.is_file()}==set(s['sha256']),mode+' stage membership')
 check(all(sha(root/n)==h for n,h in s['sha256'].items()),mode+' stage digests')
check(len(rd(D/'stages.json')['green']['sha256'])==81,'81 green files')
red=D/'runs/red300'; rev=rd(red/'result-review.json')
check(rev['accepted'] is True and rev['findings']==[] and rev['scope']=='dynamic BG RED result','accepted RED result')
check(set(rev['sha256'])=={str(x) for x in red.rglob('*') if x.is_file() and x!=red/'result-review.json'},'RED review membership')
check(all(sha(n)==h for n,h in rev['sha256'].items()),'RED result bindings')
check('Detected access to binding `Main.run_dynamic_bg_red`' in (red/'output/run.log').read_text(),'RED world-age warning retained')
expected=rd(D/'expected-tests.json')['green']
check([g[1] for g in expected['groups']]==[51,154,56,53,13,7634,115,461,239] and sum(g[1] for g in expected['groups'])==expected['assertions']==8776,'exact nine leaves / 8776')
ledger=rd(D/'work-ledger.json')['totals']
check([ledger[k] for k in ['backend_construction_attempts','valid_solve_entries','replace_entries']]==[194,936,212],'bounded source-derived API entries')
run=D/'runs/green300';s=rd(run/'sealed.json')
check(s['phase']=='green300' and s['head']=='93409174b90fbc8de6b26ed1db902f8ad8b3f743' and s['master']=='26e2291745999f485a74f643298ca997d65c7205','exact phase and refs')
check(s['config']==rd(run/'config.json') and s['config']['seconds']==300 and s['config']['expected_exit']==0,'300 second correctness configuration')
check(set(s['files'])==set(s['inventory']),'seal inventory exact membership')
check(all(str(Path(n).resolve())==v['resolved'] and sha(n)==v['sha256'] for n,v in s['inventory'].items()),'all sealed resolved paths and digests')
check(not (run/'reservation.json').exists() and not (run/'output').exists(),'not launched before review')
check(all(sha(n)==h for n,h in rd(E/'world-age-sources.json')['sha256'].items()),'world-age source bindings')
host=rd(run/'host.json');check(host['matches']==[] and set(s['groups'])==set(host['groups']),'sealed clean host scan')
record={'passed':True,'checks':checks,'count':len(checks),'sealed_sha256':sha(run/'sealed.json'),'scope':'Independent fresh Python-only exact-stage checks; no Julia or existing executable invoked'}
with (E/'independent-admission-check.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record))

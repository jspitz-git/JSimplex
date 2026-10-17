"""Fresh independent saved-result checks; no numerical process or auditor invocation."""
from pathlib import Path
import json,hashlib,sys,tomllib,re,math
E=Path(__file__).resolve().parent;R=E.parents[3];D=E.parent/'DIRECT-BG-BLOCK-DRIVER-PREPARATION';run=D/'runs/red300';out=run/'output'
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
checks=[]
def ck(n,v):checks.append({'name':n,'passed':bool(v)})
def inventory(j):
 paths=set(j['files'])|{str(p) for t in j['trees'] for p in Path(t).rglob('*') if p.is_file()}
 return {p:{'resolved':str(Path(p).resolve(strict=True)),'sha256':sha(p)} for p in sorted(paths)}
s=rd(run/'sealed.json');pins=rd(run/'launch-pins.json');a=rd(run/'admission.json');inv=rd(run/'invocation.json');res=rd(run/'reservation.json');p=rd(out/'process.json');cur=rd(out/'current.json');audit=rd(run/'audit.json');sup=inv['supervisor']
expected={'host.json','config.json','sealed.json','admission.json','prehost.json','launch-pins.json','reservation.json','launcher.log','invocation.json','posthost.json','audit.json','output/process.json','output/raw.toml','output/pins.json','output/run.log','output/resources.jsonl','output/current.json'}
ck('exact single-phase run file membership',set(str(x.relative_to(run)) for x in run.rglob('*') if x.is_file())==expected and {x.name for x in run.parent.iterdir()}=={'red300'})
ck('no run symlinks',not any(x.is_symlink() for x in run.rglob('*')))
ck('seal inventory unchanged',inventory(s)==s['inventory'])
ck('launch inventory unchanged',inventory(pins)==pins['inventory'])
ck('launch exact file/tree membership',set(pins['files'])==set(s['files'])|{str(run/'sealed.json'),str(run/'admission.json'),str(run/'prehost.json')} and len(pins['files'])==1872 and pins['trees']==s['trees'] and pins['inputs']==[])
ck('output launchpins exact',rd(out/'pins.json')==pins)
ck('admission exact hashes scope',a['accepted'] is True and a['findings']==[] and a['scope']=='block BG exact-stage admission' and a['phase']=='red300' and a['pins_sha256']==sha(run/'sealed.json') and set(a['sha256'])==set(s['files'])|{str(run/'sealed.json')} and all(sha(n)==h for n,h in a['sha256'].items()) and all(sha(n)==h for n,h in a['evidence_sha256'].items()))
sys.path.insert(0,str(D));import control
control.validate_sources();control.validate_environment();control.preparation();ck('current sources runtime environment refs preparation',True)
cfg=control.config('red300');ck('exact config commands',cfg==s['config']==rd(run/'config.json') and p['command']==cur['command']==inv['command']==cfg['command'] and p['cwd']==str(R))
ck('guard exact292 deadline',inv['guard_command']==control.guard_command(cfg,run/'launch-pins.json',inv['monotonic_start']) and Path(inv['python']).resolve()==Path(sys.executable).resolve())
ck('reservation exclusive oneattempt300',res==dict(one_attempt=True,phase='red300',command=cfg['command'],pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=300))
ck('invocation reservation review linkage',inv['reservation_sha256']==sha(run/'reservation.json') and inv['review_sha256']==sha(run/'admission.json'))
ck('process pins linkage',p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(run/'launch-pins.json') and p['pins_unchanged'] is True)
ck('identities exact linkage',p['runner']==cur['runner']==sup['guard_identity'] and p['child']==cur['child'])
ck('boot start command PGID SID identity',all(x['boot_id']==s['boot_id'] and x['start_ticks']>0 and x['pid']==x['pgid']==x['sid'] and x['command'] for x in [p['runner'],p['child']]) and p['runner']['command']==' '.join(inv['guard_command'])+' ' and p['child']['command']==' '.join(cfg['command'])+' ')
ck('exit1 expected no timeout or cleanup',p['returncode']==1 and p['reason']=='exit1' and 'error' not in p and sup['returncode']==0 and sup['accepted'] is True and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup)
ck('inclusive bounds',all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=300 for v in [inv['elapsed_seconds'],sup['elapsed_seconds']]) and 0<=p['elapsed_including_launch']<=292)
hosts=[rd(run/n) for n in ['host.json','prehost.json','posthost.json']];post=hosts[-1]
ck('host closure all identities',all(h['matches']==[] and all(h[k]==s[k] for k in ['head','master','boot_id']) for h in hosts))
ck('historical and new group session coverage',set(s['groups'])<=set(hosts[1]['groups'])<=set(post['groups']) and len(post['groups'])==236 and all(p[r][k] in post['groups'] for r in ['runner','child'] for k in ['pgid','sid']))
fresh=control.full_host(post['groups']);ck('fresh no Julia/group/session leftovers',fresh['matches']==[] and fresh['boot_id']==s['boot_id'])
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];ck('five samples and terminal memory pass',len(resources)==5 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]))
ck('RSS recorded',type(p['child_maxrss_kib']) is int and p['child_maxrss_kib']==427716)
raw=tomllib.loads((out/'raw.toml').read_text());root=raw['tests'];leaf=root['children'][0]
ck('raw complete schema phase threads',set(raw)=={'phase','complete','fatal','loaded','threads','blas_threads','tests'} and raw['phase']=='red300' and raw['complete'] is True and raw['fatal']=='' and type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1)
ck('loaded exact six including Test',raw['loaded']==control.loaded_for(cfg) and len(raw['loaded'])==6 and 'Test' in raw['loaded'])
keys={'name','pass','fail','error','broken','failures','children'}
ck('root exact empty counters',set(root)==keys and root['name']=='root' and all(type(root[k]) is int and root[k]==0 for k in ['pass','fail','error','broken']) and root['failures']==[] and len(root['children'])==1)
ck('leaf exact eight failures zero others',set(leaf)==keys and leaf['name']=='Missing block BG U contracts (eight expected failures)' and all(type(leaf[k]) is int and leaf[k]==v for k,v in [('pass',0),('fail',8),('error',0),('broken',0)]) and leaf['children']==[])
symbols=re.findall(r'@test isdefined\(JSimplex,:([^\)]+)\)',(D/'red.jl').read_text());failures=[f'Test Failed at {D}/red.jl:{i+4}\n  Expression: isdefined(JSimplex, :{x})\n   Evaluated: isdefined(JSimplex, {x})' for i,x in enumerate(symbols)]
ck('each exact source-bound failure string',len(symbols)==8 and leaf['failures']==failures)
log=(out/'run.log').read_text();ck('full log exact expected only no warnings/errors',log=='BEGIN block BG driver red300\n'+''.join('TEST FAILURE: '+f+'\n' for f in failures))
ck('launcher log exact process JSON',json.loads((run/'launcher.log').read_text())==p)
ck('saved audit acceptance and exact preaudit hashes',audit['all_passed'] is True and audit['pure_timeout'] is False and audit['error']=='' and audit['phase']=='red300' and set(audit['sha256'])=={str(run/n) for n in expected-{'audit.json'}} and all(sha(n)==h for n,h in audit['sha256'].items()))
ck('supplementary postcheck not in launch pins',str(E/'postcheck.py') not in pins['files'] and str(E/'postcheck.json') not in pins['files'])
r={'all_passed':all(x['passed'] for x in checks),'checks':checks,'findings':[x['name'] for x in checks if not x['passed']],'fresh_host':fresh,'counts':{'checks':len(checks),'run_files':len(expected),'sealed_files':len(s['files']),'launch_files':len(pins['files']),'resource_samples':len(resources),'assertions':8,'pass':0,'fail':8,'error':0,'broken':0},'inclusive_seconds':inv['elapsed_seconds'],'child_maxrss_kib':p['child_maxrss_kib'],'no_numerical_or_audit_rerun':True}
with (E/'independent-result-check.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({k:r[k] for k in ['all_passed','findings','counts']}))

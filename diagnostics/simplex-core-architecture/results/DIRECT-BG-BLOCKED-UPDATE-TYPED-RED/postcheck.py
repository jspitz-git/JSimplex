"""Supplemental saved-prefix check, no Julia or admitted auditor execution."""
from pathlib import Path
import sys,json,tomllib,hashlib,math
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS');sys.path.insert(0,str(D));import control as c
from oracle import unit,metrics
run=D/'runs/red300';o=D/'outers/red300';out=run/'output';payload=run/'payload'
checks={}
def check(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
def rd(p):return json.loads(p.read_text())
a=rd(run/'audit.json');p=rd(out/'process.json');inv=rd(run/'invocation.json');sup=inv['supervisor'];s=rd(run/'sealed.json');closure=rd(run/'outer-closure.json')
check('failed_admitted_audit_preserved',a['all_passed'] is False and a['pure_timeout'] is False and a['error']=="RuntimeError('Exact payload membership')")
check('audit_bindings',c.bindings(a))
c.verify_review(rd(run/'admission.json'),run/'sealed.json',s['files']+[str(run/'sealed.json')],'BG blocked typed exact-run admission','red300');check('admission_bindings',True)
c.verify_seal(c.config('red300'),s);check('sealed_inventory_unchanged',True)
check('launch_inventory_unchanged',c.guard.pins_match(rd(run/'launch-pins.json')) and rd(out/'pins.json')==rd(run/'launch-pins.json') and p['pins_unchanged'] is True)
check('wall_time_killed_not_success',p['reason']=='wall_time' and p['returncode']==-9 and sup['accepted'] is False and sup['returncode']==1 and rd(o/'outer-outcome.json')['returncode']==2)
check('supervisor_below300',0<=inv['elapsed_seconds']<=300 and 0<=sup['elapsed_seconds']<=300)
check('guard_deadline_observed',292<=p['elapsed_including_launch']<=300 and sup['soft_timeout'] is True and sup['hard_timeout'] is False and sup['guard_term'] is True)
check('external_closure',c.validate_result_closure('red300',closure))
h=closure['host'];check('full289_closed',len(h['groups'])==289 and c.host_safe(h) and all(p[r][k] in h['groups'] for r in ['runner','child'] for k in ['pgid','sid']))
expected={f'unit-{i}.toml' for i in range(1,11)}|{f'cost-{i}.toml' for i in range(1,11)}|{'load.toml','panel-load.toml','tests-load.toml'}
check('exact23_payload_prefix',{f.name for f in payload.iterdir()}==expected and all(f.is_file() and not f.is_symlink() for f in payload.iterdir()))
data={f.name:tomllib.loads(f.read_text()) for f in payload.iterdir()};schedule=rd(D/'schedule.json');totals=[0]*4;failures=[];rows=[]
for i in range(1,11):
 u=data[f'unit-{i}.toml'];t=unit(u,i,schedule,'red');totals=[x+y for x,y in zip(totals,t)];failures.extend(dict(unit=u['name'],**f) for f in u['records']['failures']);rows.append(dict(index=i,name=u['name'],totals=t))
check('source_bound_saved_prefix',True)
check('two_expectedN026_only',len(failures)==2 and {f['unit'] for f in failures}=={'dense96/native','dense96/markowitz'} and all(f['site']=='N026' and f['kind']=='fail' for f in failures))
check('P011_zero_and_preservation_assertions_pass',rows[0]['totals']==[11768,0,0,0] and data['unit-1.toml']['records']['sites']['P011']==1 and all(data['unit-1.toml']['records']['sites'][f'P{i:03d}']==1 for i in range(95,103)))
costs={n:metrics(v) for n,v in data.items() if not n.startswith('unit-')};check('13_partial_costs_valid',len(costs)==13)
log=(out/'run.log').read_text();check('interrupted_unit11_no_end',log.count('UNIT BEGIN 11 sparse256/native\n')==1 and 'UNIT END 11' not in log and 'UNIT BEGIN 12' not in log)
check('no_full_raw_or_newREDacceptance',not (payload/'raw.toml').exists() and not (run/'result-review.json').exists())
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
check('all_resource_samples_within_limits',len(resources)>0 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]))
files=sorted([f for root in [run,o] for f in root.rglob('*') if f.is_file()]+[E/n for n in ['postcheck.py','host-entry.json','entry-check.json','request.txt','outer.log']])
result=dict(all_passed=True,qualification_accepted=False,pure_timeout_qualification_proven=False,checks=checks,completed_units=rows,saved_prefix_totals=totals,failures=failures,preparation=costs,group_count=len(h['groups']),identities=dict(outer=s['outer_identity'],runner=p['runner'],child=p['child']),process_seconds=p['elapsed_including_launch'],supervisor_seconds=sup['elapsed_seconds'],outer_seconds=rd(o/'outer-outcome.json')['elapsed_with_checks_seconds'],resource_summary=dict(samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_used_kib=max(x['swap_used_kib'] for x in resources),terminal=p['terminal_memory'],child_maxrss_kib=p['child_maxrss_kib']),sha256={str(f):c.sha(f) for f in files},scope='Faithful timeout diagnostic and completed prefix only. Interrupted unit has no saved state/assertion totals. Full RED remains rejected; no auditor/numerical rerun.')
c.save(E/'postcheck.json',result)
print(json.dumps({k:result[k] for k in ['all_passed','qualification_accepted','saved_prefix_totals','group_count','resource_summary','process_seconds','supervisor_seconds']}))

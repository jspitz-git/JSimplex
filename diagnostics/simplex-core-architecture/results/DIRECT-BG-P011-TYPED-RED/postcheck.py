"""New read-only saved-result check; never reruns the admitted auditor or Julia."""
from pathlib import Path
import sys,json,tomllib,hashlib
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-P011-TYPED-HARNESS');sys.path.insert(0,str(D));import control as c
phase='p011-red300';run=D/'runs'/phase;out=run/'output';payload=run/'payload';outer=D/'outers'/phase
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
checks={}
def check(k,v):checks[k]=bool(v)
audit=rd(run/'audit.json');check('admitted_audit_pass',audit['all_passed'] is True)
check('audit_bindings',all(sha(n)==h for n,h in audit['sha256'].items()))
p=rd(out/'process.json');inv=rd(run/'invocation.json');sup=inv['supervisor']
check('red_child_exit1_guard_success',type(p['returncode']) is int and p['returncode']==1 and p['reason']=='exit1' and sup['returncode']==0 and sup['accepted'] is True)
check('300_and_292_bounds',0<=inv['elapsed_seconds']<=300 and 0<=sup['elapsed_seconds']<=300 and 0<=p['elapsed_including_launch']<=292)
check('no_timeout_or_termination',all(sup.get(k) is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']))
check('pins_preserved',p['pins_unchanged'] is True)
data={f.name:tomllib.loads(f.read_text()) for f in payload.iterdir() if f.is_file()}
raw=data.get('raw.toml',{});u=data.get('unit-1.toml',{});probe=data.get('probe.toml',{})
check('red_exact_totals',raw.get('totals')==[11759,1,0,0])
failures=u.get('records',{}).get('failures',[])
check('sole_P011',len(failures)==1 and failures[0].get('site')=='P011' and failures[0].get('kind')=='fail')
check('four_zero_counters',all(type(probe.get(k)) is int and probe[k]==0 for k in ['bytes','events','consumed_bytes','consumed_events']))
check('value_owner_preservation',probe.get('values_unchanged') is True and probe.get('owners_unchanged') is True)
check('independent_external_closure',c.validate_result_closure(phase,rd(run/'outer-closure.json')) is True)
check('outer_success',rd(outer/'outer-outcome.json')['returncode']==0)
resources=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()]
metrics={n:v for n,v in data.items() if n not in ['raw.toml','unit-1.toml','probe.toml']}
files=sorted([p for root in [run,outer] for p in root.rglob('*') if p.is_file()]+[E/'host-entry.json',E/'entry-check.json',E/'request.txt',E/'outer.log',Path(__file__).resolve()])
result=dict(all_passed=all(checks.values()),checks=checks,totals=raw.get('totals'),failures=failures,probe=probe,preparation=metrics,
 resource_summary=dict(samples=len(resources),min_available_kib=min(s['available_kib'] for s in resources),max_swap_used_kib=max(s['swap_used_kib'] for s in resources),terminal=p['terminal_memory'],child_maxrss_kib=p['child_maxrss_kib']),
 process_seconds=p['elapsed_including_launch'],supervisor_seconds=sup['elapsed_seconds'],sha256={str(p):sha(p) for p in files},scope='New saved-evidence check only; no auditor rerun, compilation or numerical calls; partial cost records overlap, no speedup')
with (E/'postcheck.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['all_passed','totals','resource_summary','process_seconds']}))
if not result['all_passed']:raise RuntimeError('Saved RED result did not qualify; preserve')

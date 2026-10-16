"""Supplementary one-shot RED result binding; never reruns Julia or admitted auditor."""
from pathlib import Path
import sys,json
E=Path(__file__).resolve().parent;R=E.parents[3];D=E.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION'
sys.path.insert(0,str(D));import control as c
import tomllib
run=D/'runs/red300';out=run/'output';checks={}
def check(n,v):
 checks[n]=bool(v);c.require(v,n)
a=c.rd(run/'audit.json');check('original_admitted_audit_pass',a['all_passed'] is True and a['pure_timeout'] is False and a['phase']=='red300')
check('original_audit_evidence_unchanged',c.bindings(a))
c.preparation();c.validate_environment();c.validate_sources();check('all_preparation_runtime_sources',True)
s=c.rd(run/'sealed.json');pins=c.rd(run/'launch-pins.json');check('all_launch_pins_unchanged',c.guard.pins_match(s) and c.guard.pins_match(pins))
c.verify_review(c.rd(run/'admission.json'),run/'sealed.json',s['files']+[str(run/'sealed.json')],'dynamic BG exact-stage admission','red300');check('exact_admission_binding',True)
p=c.rd(out/'process.json');raw=tomllib.loads((out/'raw.toml').read_text());t=raw['tests'];children=t['children'];e=c.rd(D/'expected-tests.json')['red']['groups'][0]
check('single_expected_group',len(children)==1 and children[0]['name']==e[0])
leaf=children[0];check('eight_expected_only',(leaf['pass'],leaf['fail'],leaf['error'],leaf['broken'])==(0,8,0,0) and len(leaf['failures'])==8)
check('complete_no_fatal',raw['complete'] is True and raw['fatal']=='' and raw['phase']=='red300')
check('exact_child_exit_one',p['returncode']==1 and p['reason']=='exit1' and p['pins_unchanged'] is True)
inv=c.rd(run/'invocation.json');check('inclusive_limit',0<=inv['elapsed_seconds']<=300 and inv['supervisor']['accepted'] is True)
groups=c.rd(run/'posthost.json')['groups'];h=c.full_host(groups);check('fresh_full_groups_sessions_nojulia',not h['matches'] and set(groups)<=set(h['groups']) and all(h[k]==s[k] for k in ['boot_id','head','master']))
check('no_green_attempt',not (D/'runs/green300').exists() and not (D/'runs/green600').exists())
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
check('resource_samples_and_terminal',bool(resources) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]))
c.save(E/'posthost.json',h)
files=[x for x in run.rglob('*') if x.is_file()]+[E/'postcheck.py',E/'posthost.json',E/'authorization.json',E/'entry.json']
c.save(E/'postcheck.json',dict(all_passed=True,checks=checks,summary=dict(assertions=8,expected_failures=8,errors=0,broken=0,exit=1,elapsed_seconds=inv['elapsed_seconds'],resource_samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_used_kib=max(x['swap_used_kib'] for x in resources),api_factor_solve_update_calls=0,scope='RED missing-contract assertions only; no numerical equivalence or performance result'),sha256={str(x):c.sha(x) for x in sorted(files)}))
print('RED supplementary checks PASS',len(checks),'eight expected failures; no GREEN')

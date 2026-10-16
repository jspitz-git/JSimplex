"""New saved GREEN evidence check; no repeated auditor, Julia, or numerical work."""
from pathlib import Path
import sys,json,tomllib
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION';sys.path.insert(0,str(D));import control as c
run=D/'runs/green300';out=run/'output';checks={}
def check(n,v):
 checks[n]=bool(v);c.require(v,n)
a=c.rd(run/'audit.json');check('original_admitted_audit_pass',a['all_passed'] is True and a['pure_timeout'] is False and a['phase']=='green300');check('original_audit_evidence_unchanged',c.bindings(a))
c.preparation();c.validate_environment();c.validate_sources();c.predecessor('green300');check('preparation_runtime_source_red_lineage',True)
s=c.rd(run/'sealed.json');pins=c.rd(run/'launch-pins.json');check('launch_inputs_unchanged',c.guard.pins_match(s) and c.guard.pins_match(pins))
c.verify_review(c.rd(run/'admission.json'),run/'sealed.json',s['files']+[str(run/'sealed.json')],'dynamic BG exact-stage admission','green300');check('exact_admission_worldage_evidence',True)
raw=tomllib.loads((out/'raw.toml').read_text());root=raw['tests'];groups=[[x[k] for k in ['name','pass','fail','error','broken']] for x in root['children']];expected=c.rd(D/'expected-tests.json')['green'];check('nine_exact_leaf_groups',groups==expected['groups'] and len(groups)==9 and all(x['children']==[] for x in root['children']))
check('all8776_pass_no_error_fail_broken',sum(x[1] for x in groups)==8776 and all(x[2:]==[0,0,0] for x in groups) and all(root[k]==0 for k in ['pass','fail','error','broken']))
check('complete_correct_source_threads',raw['complete'] is True and raw['fatal']=='' and raw['phase']=='green300' and raw['loaded']==c.loaded_for(c.config('green300')) and raw['threads']==raw['blas_threads']==1)
p=c.rd(out/'process.json');inv=c.rd(run/'invocation.json');check('exact_exit_zero',p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] is True and inv['supervisor']['accepted'] is True)
check('inclusive_limit',0<=inv['elapsed_seconds']<=300)
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];check('resources_and_terminal',bool(resources) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]))
h=c.full_host(c.rd(run/'posthost.json')['groups']);check('fresh_full_groups_sessions_nojulia',not h['matches'] and all(h[k]==s[k] for k in ['head','master','boot_id']))
log=(out/'run.log').read_text();warnings=[x for x in log.splitlines() if x.startswith('WARNING:')];targets=['Main.DynamicBGSlotTests','DynamicBGSlotTests.run_slots','Main.DynamicBGTests','DynamicBGTests.lifecycles','DynamicBGTests.rejection_and_aliases','DynamicBGTests.export_modes','DynamicBGTests.focused_updates'];check('retained_worldage_warnings_exact',warnings==['WARNING: Detected access to binding `'+n+'` in a world prior to its definition world.' for n in targets])
check('all_suites_entered_completed',all(log.count('BEGIN '+n+'\n')==log.count('END '+n+'\n')==1 for n in ['slots','lifecycles','rejection_and_aliases','export_modes','focused_updates']))
check('no_other_attempts',{x.name for x in (D/'runs').iterdir()}=={'red300','green300'})
c.save(E/'posthost.json',h)
files=sorted([x for x in run.rglob('*') if x.is_file()]+[E/'postcheck.py',E/'posthost.json',E/'authorization.json',E/'entry.json'])
c.save(E/'postcheck.json',dict(all_passed=True,checks=checks,summary=dict(assertions=8776,groups=groups,failures=0,errors=0,broken=0,exit=0,elapsed_seconds=inv['elapsed_seconds'],resource_samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_used_kib=max(x['swap_used_kib'] for x in resources),warnings=warnings,scope='Correctness only; API ledger source-derived not runtime counters; no performance acceptance'),sha256={str(x):c.sha(x) for x in files}))
print('GREEN supplementary checks PASS',len(checks),'8776passing,7warnings retained')

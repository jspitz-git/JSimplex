"""New supplemental post-exit checks. Not a launch pin. Never reruns auditor/Julia."""
from pathlib import Path
import sys,json,tomllib,hashlib
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-BLOCK-DRIVER-PREPARATION';sys.path.insert(0,str(D))
import control as c
run=D/'runs/red300';out=run/'output';checks={}
def ok(v,n):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
a=c.rd(run/'audit.json');p=c.rd(out/'process.json');s=c.rd(run/'sealed.json');lp=c.rd(run/'launch-pins.json');inv=c.rd(run/'invocation.json');raw=tomllib.loads((out/'raw.toml').read_text());log=(out/'run.log').read_text(errors='replace')
ok(a['all_passed'] is True and a['pure_timeout'] is False,'saved_audit_accepted')
ok(p['returncode']==1 and p['reason']=='exit1' and p['pins_unchanged'] is True,'expected_RED_exit')
ok(raw['complete'] is True and raw['fatal']=='','complete_raw')
t=raw['tests'];children=t['children']
ok(t['name']=='root' and all(t[k]==0 for k in ('pass','fail','error','broken')) and not t['failures'],'empty_root')
ok(len(children)==1,'one_group');z=children[0]
ok(z['name']=='Missing block BG U contracts (eight expected failures)' and [z[k] for k in ('pass','fail','error','broken')]==[0,8,0,0] and not z['children'],'exact_eight_failures')
ok(len(z['failures'])==8 and log.count('TEST FAILURE:')==8,'all_failure_records')
for name in ('BGBlockUpper','_bgu_build','_bgu_insert_at!','_bgu_swap_rows!','_bgu_rotate_rows!','BlockBGFactor','_block_bg_factor','_block_bg_replace!'):
 ok(any(name in f for f in z['failures']),'missing_contract_'+name)
ok(raw['loaded']==c.loaded_for(c.config('red300')),'actual_loaded_paths')
ok(raw['threads']==raw['blas_threads']==1,'thread_settings')
ok(c.guard.pins_match(s) and c.guard.pins_match(lp),'fresh_all_sealed_and_launch_pins')
ok(set(lp['files'])==set(s['files'])|{str(run/'sealed.json'),str(run/'admission.json'),str(run/'prehost.json')},'launch_membership')
ok(inv['supervisor']['accepted'] is True and inv['elapsed_seconds']<=300,'bounded_supervision')
samples=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
ok(bool(samples) and all(not c.guard.pressure(x) for x in samples+[p['terminal_memory']]),'resources_including_terminal')
groups=c.rd(run/'posthost.json')['groups'];h=c.full_host(groups);c.save(E/'posthost.json',h)
ok(not h['matches'],'fresh_no_Julia_and_full_groups_sessions')
ok(all(p[role][key] in h['groups'] for role in ('runner','child') for key in ('pgid','sid')),'new_groups_included')
ok(h['head']==s['head'] and h['master']==s['master'] and h['boot_id']==s['boot_id'],'refs_boot_unchanged')
ok(not any(x in log for x in ('world age','world-age','WARNING:','Warning:','FATAL DRIVER:','LoadError')),'no_selected_warning_or_fatal_tokens')
files=[q for q in run.rglob('*') if q.is_file()]+[Path(__file__),E/'posthost.json',E/'authorization.json']
c.save(E/'postcheck.json',dict(all_passed=True,checks=checks,sha256={str(q):c.sha(q) for q in sorted(files)},resources=dict(samples=len(samples),minimum_available_kib=min(x['available_kib'] for x in samples),maximum_swap_used_kib=max(x['swap_used_kib'] for x in samples),elapsed_inclusive=inv['elapsed_seconds']),scope='Supplemental postexit verification; no auditor/Julia rerun or performance inference'))
print('Postcheck PASS',len(checks),'checks;',len(lp['inventory']),'launch pins')

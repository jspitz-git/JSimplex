"""Supplemental saved-evidence check, not a launch pin or numerical rerun."""
from pathlib import Path
import sys,json,tomllib
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-BLOCK-DRIVER-PREPARATION';sys.path.insert(0,str(D))
import control as c
run=D/'runs/green300';out=run/'output';checks={}
def ok(v,n):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
a=c.rd(run/'audit.json');p=c.rd(out/'process.json');s=c.rd(run/'sealed.json');lp=c.rd(run/'launch-pins.json');inv=c.rd(run/'invocation.json');log=(out/'run.log').read_text(errors='replace')
raw=tomllib.loads((out/'raw.toml').read_text()) if (out/'raw.toml').exists() else None
ok(c.guard.pins_match(s) and c.guard.pins_match(lp),'all_seal_and_launch_pins')
ok(c.rd(out/'pins.json')==lp,'actual_output_pins')
ok(set(lp['files'])==set(s['files'])|{str(run/'sealed.json'),str(run/'admission.json'),str(run/'prehost.json')},'launch_membership')
ok(p['pins_unchanged'] is True and p['command']==inv['command']==s['config']['command'],'actual_command_and_integrity')
ok(inv['pins_sha256']==c.sha(run/'launch-pins.json') and inv['review_sha256']==c.sha(run/'admission.json') and inv['reservation_sha256']==c.sha(run/'reservation.json'),'invocation_bindings')
ok(inv['elapsed_seconds']<=300,'outer_bound')
samples=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
ok(bool(samples) and all(not c.guard.pressure(x) for x in samples+[p['terminal_memory']]),'sample_and_terminal_resource_guards')
h=c.full_host(c.rd(run/'posthost.json')['groups']);c.save(E/'posthost.json',h)
ok(not h['matches'],'fresh_no_Julia_full_groups_AND_sessions')
ok(all(p[role][key] in h['groups'] for role in ('runner','child') for key in ('pgid','sid')),'new_identity_groups_included')
ok(h['head']==s['head'] and h['master']==s['master'] and h['boot_id']==s['boot_id'],'refs_boot_unchanged')
if raw is not None:
 ok(raw['loaded']==c.loaded_for(c.config('green300')),'actual_loaded_paths')
 ok(raw['threads']==raw['blas_threads']==1,'actual_threads')
expected=c.rd(D/'expected-tests.json')['green'];actual=[]
if raw is not None:
 actual=[[t[k] for k in ('name','pass','fail','error','broken')] for t in raw['tests']['children']]
files=[q for q in run.rglob('*') if q.is_file()]+[Path(__file__),E/'posthost.json',E/'authorization.json']
c.save(E/'postcheck.json',dict(all_passed=True,checks=checks,sha256={str(q):c.sha(q) for q in sorted(files)},outcome=dict(admitted_audit_pass=a['all_passed'],pure_timeout=a['pure_timeout'],returncode=p['returncode'],reason=p['reason'],raw_complete=None if raw is None else raw['complete'],fatal=None if raw is None else raw['fatal'],groups=actual,expected_groups=expected['groups'],exact_groups=actual==expected['groups'],warning_tokens=[t for t in ('world age','world-age','WARNING:','Warning:') if t in log]),resources=dict(samples=len(samples),minimum_available_kib=min(x['available_kib'] for x in samples),maximum_swap_used_kib=max(x['swap_used_kib'] for x in samples),elapsed_inclusive=inv['elapsed_seconds'],child_maxrss_kib=p['child_maxrss_kib']),scope='Evidence integrity only; all_passed here does not override admitted audit or numerical outcome'))
print('Postcheck evidence integrity PASS',len(checks),'checks; admitted audit=',a['all_passed'],'pure_timeout=',a['pure_timeout'])

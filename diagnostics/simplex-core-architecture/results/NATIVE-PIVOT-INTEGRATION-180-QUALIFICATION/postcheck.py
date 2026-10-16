"""Post-exit supplemental integrity summary, never reruns the stage audit."""
from pathlib import Path
import json,hashlib,sys,tomllib
T=Path(__file__).resolve().parent;N=T.parent/'NATIVE-PIVOT-INTEGRATION-180-PREPARATION';sys.path.insert(0,str(N))
from control import *
import guard
run=N/'runs/integration';out=run/'output';a=rd(run/'audit.json');p=rd(out/'process.json');inv=rd(run/'invocation.json');sealed=rd(run/'sealed.json');pins=rd(run/'launch-pins.json')
groups=rd(run/'posthost.json')['groups'];h=full_host(groups);verify_host(h);save(T/'host.json',h)
checks={}
def check(k,v):checks[k]=bool(v);require(v,k)
check('closed_processes',not h['matches'] and set(groups)<=set(h['groups']))
check('all_pins',guard.pins_match(sealed) and guard.pins_match(pins) and rd(out/'pins.json')==pins)
check('audit_bindings',bindings(a))
check('command',p['command']==inv['command']==config('integration')['command'])
check('new_allowance',rd(run/'reservation.json')['max_seconds']==180 and inv['elapsed_seconds']<=180)
check('identity',all(p[x]['boot_id']==h['boot_id'] and p[x]['start_ticks']>0 and p[x]['command'] and p[x]['pgid'] in groups and p[x]['sid'] in groups for x in ('runner','child')))
resources=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()]
check('resource_guards',bool(resources) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]))
check('actual_baseline',bindings(rd(N.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT/actual-baseline.json')))
raw=tomllib.loads((out/'raw.toml').read_text()) if (out/'raw.toml').exists() else None
summary=dict(qualification_accepted=a['all_passed'],audit_error=a['error'],reason=p['reason'],returncode=p['returncode'],inner_elapsed_before_cleanup=p['elapsed_including_launch'],inclusive_seconds=inv['elapsed_seconds'],resources=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_kib=max(x['swap_used_kib'] for x in resources),maxrss_kib=p['child_maxrss_kib'],groups=len(groups),raw_exists=raw is not None,audit_result=a['result'],allowance_consumed=True)
if raw is not None:summary.update(raw_complete=raw.get('complete'),fatal=raw.get('fatal'),started=raw.get('started'),active=raw.get('active'),tests=raw.get('tests'),cases=raw.get('cases'))
paths=[run/'audit.json',run/'invocation.json',run/'posthost.json',out/'process.json',out/'run.log',out/'resources.jsonl',T/'host.json',T/'postcheck.py']
if raw is not None:paths.append(out/'raw.toml')
save(T/'postcheck.json',dict(all_passed=all(checks.values()),checks=checks,summary=summary,sha256={str(x):sha(x) for x in paths},scope='Supplemental integrity only; numerical qualification follows unchanged original audit'))
print({k:v for k,v in summary.items() if k not in ('audit_result','tests','cases','fatal')})

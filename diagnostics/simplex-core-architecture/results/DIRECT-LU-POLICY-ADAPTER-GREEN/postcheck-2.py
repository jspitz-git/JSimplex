"""New saved GREEN output summary. Never reruns numerical test or original auditor."""
from pathlib import Path
import sys,json,tomllib
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-LU-POLICY-ADAPTER-DRIVER-PREPARATION';sys.path.insert(0,str(D))
from control import rd,save,require,sha,full_host
run=D/'runs/green300';out=run/'output';p=rd(out/'process.json');inv=rd(run/'invocation.json');a=rd(run/'audit.json');log=(out/'run.log').read_text();raw=tomllib.loads((out/'raw.toml').read_text()) if (out/'raw.toml').exists() else None
h=full_host(rd(run/'posthost.json')['groups']);save(E/'postcheck-2-host.json',h)
checks=dict(auditor_accepted=a['all_passed'] is True and a['pure_timeout'] is False,expected_exit=p['returncode']==0 and p['reason']=='exit0' and inv['supervisor']['returncode']==0,pins_unchanged=p['pins_unchanged'] is True,inclusive_limit=0<inv['elapsed_seconds']<=300,fresh_groups_sessions_no_Julia=not h['matches'],no_extra_run=not (D/'runs/green600').exists())
if raw is not None:
 children=raw['tests']['children'];expected=rd(D/'expected-tests.json')['green']['groups']
 checks.update(raw_complete=raw.get('complete') is True and raw.get('fatal')=='',exact_groups=len(children)==9 and all((c['name'],c['pass'],c['fail'],c['error'],c['broken'])==tuple(e) for c,e in zip(children,expected)),expected_total=sum(c['pass'] for c in children)==30455,no_test_failure_log=not any(x in log for x in ['TEST FAILURE:','BROKEN TEST:','FATAL DRIVER:','GROUP/COUNT MISMATCH']))
 summary=dict(groups=[{k:c[k] for k in ['name','pass','fail','error','broken']} for c in children],complete=raw.get('complete'),fatal=raw.get('fatal'))
else:checks['raw_present']=False;summary={}
files=sorted(p for p in run.rglob('*') if p.is_file())+[Path(__file__)]
save(E/'postcheck-2.json',dict(all_passed=all(checks.values()),checks=checks,result=summary,warnings=[s for s in log.splitlines() if s.startswith('WARNING:')],sha256={str(p):sha(p) for p in files},scope='New saved-output summary, not auditor/numerical rerun'))
print('Saved-output postcheck',sum(checks.values()),'/',len(checks),json.dumps(summary))

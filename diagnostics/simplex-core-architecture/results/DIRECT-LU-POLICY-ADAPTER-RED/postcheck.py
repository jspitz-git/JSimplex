"""New saved-output checks; not a test/auditor rerun."""
from pathlib import Path
import sys,json,tomllib
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-LU-POLICY-ADAPTER-DRIVER-PREPARATION';sys.path.insert(0,str(D))
from control import rd,save,require,sha,full_host
run=D/'runs/red300';out=run/'output';raw=tomllib.loads((out/'raw.toml').read_text());leaf=raw['tests']['children'][0];failures=leaf['failures'];p=rd(out/'process.json');inv=rd(run/'invocation.json');a=rd(run/'audit.json');log=(out/'run.log').read_text()
checks=dict(expected_counts=[leaf[k] for k in ['pass','fail','error','broken']]==[0,7,0,0],exact_six_applicability=len(failures)==7 and all('applicable(' in f and manager in f and 'Val{:'+backend+'}' in f for f,(manager,backend) in zip(failures[:6],[(m,b) for m in ['ForrestTomlinFactorization','SuhlSuhlFactorization','BartelsGolubFactorization'] for b in ['native','markowitz']])),field_failure='pivot_policy in fieldnames(JSimplex.DirectLowerBackend)' in failures[6],raw_complete=raw['complete'] and raw['fatal']=='',expected_exit=p['returncode']==1 and p['reason']=='exit1' and inv['supervisor']['returncode']==0,auditor_accepted=a['all_passed'] is True and a['pure_timeout'] is False,pins_unchanged=p['pins_unchanged'] is True,seven_immediate_failures=log.count('TEST FAILURE:')==7,warning_preserved=log.count('WARNING: Detected access to binding')==1 and 'Main.run_direct_lu_policy_red' in log,inclusive_limit=0<inv['elapsed_seconds']<300,no_green=not (D/'runs/green300').exists())
h=full_host(rd(run/'posthost.json')['groups']);checks['fresh_groups_sessions_no_Julia']=not h['matches'];require(all(checks.values()),'Postcheck failed')
save(E/'postcheck-host.json',h)
files=[out/'raw.toml',out/'run.log',out/'process.json',run/'audit.json',run/'invocation.json',Path(__file__),E/'close.py',E/'publication.py']
save(E/'postcheck.json',dict(all_passed=True,checks=checks,sha256={str(p):sha(p) for p in files},scope='Saved RED result/source checks only; no auditor or Julia rerun'))
print('Saved-output postcheck',len(checks),'PASS')

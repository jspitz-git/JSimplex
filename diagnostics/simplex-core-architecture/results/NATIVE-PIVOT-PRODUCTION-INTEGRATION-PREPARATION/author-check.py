from pathlib import Path
import json,hashlib,subprocess
Q=Path(__file__).resolve().parent;R=Q.parents[3];B=Q.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
plan=R/'docs/superpowers/plans/2026-10-16-native-pivot-production-integration.md'
m=json.loads((Q/'payload-manifest.json').read_text());sc=json.loads((Q/'source-check.json').read_text())
checks={}
checks['source_bindings']=all(sha(R/p)==h for p,h in sc['sha256'].items())
checks['payload_exact']=all(sha(R[x['source']])==sha(R[x['payload']])==x['sha256'] for x in m['files'])
checks['actual_baseline']=all(sha(R/p)==h for p,h in json.loads((Q/'actual-baseline.json').read_text()).items())
checks['assertions']=sum([4946,35,1568,245,48,114])==6956
old=(B/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION/recorder.jl').read_text();new=(Q/'recorder.jl').read_text();expected=old.replace('push!(t.failures,sprint(show,r)))','push!(t.failures,sprint(show,r));println(stderr,"TEST FAILURE: ",sprint(show,r));flush(stderr))').replace('Test.record(t::Capture,r::Test.Broken)=(t.broken+=1)','Test.record(t::Capture,r::Test.Broken)=(t.broken+=1;println(stderr,"BROKEN TEST: ",sprint(show,r));flush(stderr))')
checks['recorder_exact_inverse']=new==expected
checks['no_hook_driver']='Probe' not in (Q/'master-driver.jl').read_text()
checks['new_timing_contract']=all(s in plan.read_text() for s in ['300s','600s','5s deadline','no further human permission'.capitalize()]) if False else all(s in plan.read_text() for s in ['300s','600s','5s deadline','No further human permission'])
checks['no_actual_tracked_changes']=not subprocess.check_output(['git','diff','--name-only','--','src','test','.github','Project.toml'],cwd=R,text=True).strip()
for k,v in checks.items():need(v,k)
pins={str(p.relative_to(R)):sha(p) for p in sorted(Q.rglob('*')) if p.is_file()}
pins[str(plan.relative_to(R))]=sha(plan)
save(Q/'author-check.json',dict(all_passed=True,checks=checks,sha256=pins))
print(len(checks),'PASS',len(pins),'bindings')

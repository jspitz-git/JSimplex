from pathlib import Path
import json,hashlib,sys,importlib.util
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parents[2];checks=[]
def read(p):return json.loads(p.read_text())
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(v,m):
 checks.append(dict(check=m,passed=bool(v)))
 if not v:raise ValueError(m)
s=importlib.util.spec_from_file_location('task2closuredefinitions',D/'run.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
p=read(D/'green-pins.json');check(len(p['files'])==149 and L.G.pins_match(p),'149 actual unchanged launch pins')
a=read(D/'green-admission.json');check(a['accepted'] is True and a['pins_sha256']==sha(D/'green-pins.json'),'bound independent source/numerical admission')
a=read(D/'result-review.json');check(a['accepted'] is True and a['pins_sha256']==sha(D/'green-pins.json'),'independent result/code/work/memory review bound to actual launch manifest')
for n,h in a['bindings'].items():check(sha(n)==h,'actual result-review artifact binding: '+n)
q=read(D/'postcheck.json');check(q['accepted'] is True and len(q['checks'])==498 and all(x['passed'] for x in q['checks']),'498 postexit checks accepted')
check(q['runs']['green']['assertions']==371 and sum(q['runs']['green']['testsets'].values())==371,'371 ordinary Test passes')
check(read(D/'red-run/result.json')['accepted'] is True and read(D/'red-run/result.json')['exit']==1,'expected six-interface RED failures preserved')
check(read(D/'green-run/result.json')['accepted'] is True and read(D/'green-run/result.json')['exit']==0,'one accepted GREEN process')
check(read(D/'before-coverage-review/admission.json')['accepted'] is False,'initial rejected review preserved')
for n,v in read(D/'qualified-sources.json').items():check(sha(n)==v['sha256']==sha(v['preserved']),'exact qualified current and preserved source: '+n)
for n,v in read(D/'continuation-map.json').items():
 check(sha(v['preserved'])==v['sha256'],'previous continuation bytes preserved: '+n)
 check(read(W/'diagnostics/dual-step-experiment/task1/closure.json')['bindings'][n]==v['sha256'],'exact Task1 closure README mapping')
h=L.host();check(h['no_julia'] is True and not h['conflicts'] and len(h['checked_groups'])==792,'fresh792groupsANDsessions/noJulia/current refs')
with (D/'closure-host.json').open('x') as f:json.dump(h,f,indent=2)
check(not L.H.H.git(W,'diff','--name-only','--','src','test','Project.toml','.github'),'production source/test/env/CI unchanged')
check(not L.H.H.git(W,'diff','--name-only','--','diagnostics/dual-step-experiment/task1','docs/superpowers/plans/2026-10-31-experimental-dual-engine.md','docs/superpowers/specs/2026-10-31-experimental-dual-engine-design.md'),'Task1 evidence and accepted plan/design frozen')
report=(D/'REPORT.md').read_text();check('48m' in report and 'retained full row residual' in report and 'no speedup' in report.lower(),'explicit work/memory/coverage limits')
check('Tasks3–6 remain open' in report,'remaining plan not marked complete')
files=sorted(p for p in D.rglob('*') if p.is_file())+sorted((W/'experimental/dual_engine').rglob('*.jl'))+[W/'diagnostics/dual-step-experiment/README.md']
bindings={str(p):sha(p) for p in files}
with (D/'closure.json').open('x') as f:json.dump(dict(accepted=True,checks=checks,bindings=bindings,scope='Task2 postexit closure; no production promotion, no retroactive launch pins'),f,indent=2)
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(bindings))))

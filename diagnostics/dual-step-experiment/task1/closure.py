from pathlib import Path
import json,hashlib,sys,importlib.util
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parents[2];checks=[]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(v,m):
 checks.append(dict(check=m,passed=bool(v)))
 if not v:raise ValueError(m)
s=importlib.util.spec_from_file_location('finaldefinitions',D/'run-green-final.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
p=read(D/'green-final-pins.json');check(L.G.pins_match(p) and len(p['files'])==174,'174 actual unchanged launchpins')
check(read(D/'green-admission.json')['accepted'] is True and read(D/'green-admission.json')['pins_sha256']==sha(D/'green-final-pins.json'),'bound independent source/numerical admission')
check(read(D/'result-review.json')['accepted'] is True,'independent resultreview accepted')
q=read(D/'postcheck.json');check(q['accepted'] is True and all(x['passed'] for x in q['checks']),'34postchecks accepted')
check(sum(q['runs']['testsets'].values())==106,'106ordinary Test passes')
check(read(D/'red-run/result.json')['exit']==1 and read(D/'ownership-red-run/result.json')['exit']==1,'both exact expected RED failures preserved')
check(read(D/'green-run/result.json')['exit']==0,'corrected GREEN exit0')
h=L.host();check(h['no_julia'] is True and not h['conflicts'] and len(h['checked_groups'])==788,'fresh788groupsANDsessions/noJulia and refs')
with (D/'closure-host.json').open('x') as f:json.dump(h,f,indent=2)
check(not L.H.H.git(W,'diff','--name-only','--','src','test','Project.toml','.github'),'production source/test/env/CI unchanged')
check('redundant cold N-entry' in (D/'REPORT.md').read_text(),'deferredcoldwork disclosed')
files=sorted(p for p in D.rglob('*') if p.is_file())+sorted((W/'experimental/dual_engine').rglob('*.jl'))+[W/'diagnostics/dual-step-experiment/OWNERSHIP.md',W/'diagnostics/dual-step-experiment/README.md']
bindings={str(p):sha(p) for p in files}
with (D/'closure.json').open('x') as f:json.dump(dict(accepted=True,checks=checks,bindings=bindings,scope='postexit Task1 diagnostic closure; not retroactive launch pins; no production promotion'),f,indent=2)
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(bindings))))

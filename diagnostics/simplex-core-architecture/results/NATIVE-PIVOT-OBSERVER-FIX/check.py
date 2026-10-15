"""New offline source/inverse checks only; no Julia parser or old checker import."""
from pathlib import Path
import json,hashlib,subprocess,ast
D=Path(__file__).resolve().parent;R=D.parents[3];Q=D.parent/'NATIVE-PIVOT-QUALIFICATION';G=D.parent/'NATIVE-PIVOT-GREEN';P=D.parent/'NATIVE-PIVOT-PREPARATION'
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
def require(v,m):
 if not v:raise RuntimeError(m)
s=(D/'test-support-fixed.jl').read_text();i=rd(D/'inverse.json');old=(Q/'test-support.jl').read_text();undo=s.replace(i['helper'],'')
for a,b in i['support_changes']:undo=undo.replace(b,a)
t=(D/'test-driver-fixed.jl').read_text();u=t
for a,b in i['driver_routes']:u=u.replace(b,a)
reg=(D/'regression.jl').read_text();budget=rd(Q/'budget.json')
checks=dict(support_inverse=undo==old and s.count(i['helper'])==1,four_sites=len(i['support_changes'])==4 and all(s.count(b)==1 and a not in s for a,b in i['support_changes']),dense_storage='Vector{String}(undef,length(values))' in i['helper'] and 'enumerate(values)' in i['helper'] and '.(' not in i['helper'],driver_inverse=u==(Q/'test-driver-reviewed.jl').read_text() and len(i['driver_routes'])==4,source_RED=i['source_red']['missing_dense_helper'] is True and len(i['source_red']['unsafe_sites'])==4,regression_count=12*9+4*2+1+2==i['regression_assertions']==119,regression_contract=all(x in reg for x in ['@test_throws MethodError scalar.(sparse_special)','out isa Vector{String}','TOML.parse(text)','owners(v)==owner_before','snapshot(v),before','precision(BigFloat)==oldprecision','rounding(BigFloat)==oldrounding','0x7ff8000000000042']),old_budget=budget['green_assertions']==6858 and sum(budget['main'].values())+sum(budget['neighbors'].values())==792,failed_green=rd(Q/'runs/green/audit.json')['all_passed'] is False and rd(Q/'runs/green/result-review.json')['qualification_accepted'] is False,candidate_unchanged=all(sha(e['source'])==e['sha256'] for arm in ['candidate','reference'] for e in rd(P/'overlay-manifest.json')[arm]),actual_unchanged=not subprocess.check_output(['git','diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce'],cwd=R,text=True).strip(),no_new_stage={p.name for p in (R/'.superpowers/native-pivot-qualification').iterdir()}=={'red','green'},no_new_run={p.name for p in (Q/'runs').iterdir()}=={'red','green'})
paths=[Path(__file__),D/'test-support-fixed.jl',D/'test-driver-fixed.jl',D/'regression.jl',D/'inverse.json',D/'REPORT.md',Q/'test-support.jl',Q/'test-driver-reviewed.jl',Q/'tests-observed.jl',Q/'neighbors-observed.jl',Q/'cost-driver.jl',Q/'budget.json',P/'overlay-manifest.json',Q/'runs/green/output/raw.toml',Q/'runs/green/audit.json',Q/'runs/green/result-review.json',G/'REPORT.md']
runtime=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src')
paths += [runtime/n for n in ['SparseArrays.jl','sparsevector.jl','higherorderfns.jl']]
save(D/'check.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in paths},scope='Source-level RED/inverse only; Julia regression and all new code UNEXECUTED'))
require(all(checks.values()),'Offline check failed; preserve');print(dict(checks=len(checks),bindings=len(paths),all_passed=True))

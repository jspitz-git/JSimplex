from pathlib import Path
import json,hashlib,difflib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S-LOAD';S=E.with_name('MA-S');A=E.with_name('MA-R')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,o):
 with (E/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
def require(v,m):
 if not v:raise SystemExit(m)
old=(S/'driver.jl').read_text()
pairs=[('records[]=TST.qualification()','records[]=Base.invokelatest(TST.qualification)'),('raw["costs"]=costs(index)','raw["costs"]=Base.invokelatest(costs,index)')]
def boundary_checks(s):return {'qualification_latest':s.count(pairs[0][1])==1,'cost_phase_latest':s.count(pairs[1][1])==1}
# Source contract RED precedes writing the separate candidate. This is not Julia RED.
red=boundary_checks(old)
require(not any(red.values()),'Expected exactly two missing boundary markers in original')
save('source-red.json',dict(checks=red,expected_missing=2,scope='Python text assertions only; runtime failure already preserved in MA-S/run-1. No Julia execution.',sha256={str(S/'driver.jl'):sha(S/'driver.jl'),str(E/'prepare.py'):sha(E/'prepare.py')}))
new=old
for a,b in pairs:
 require(new.count(a)==1,'Nonunique original edit');new=new.replace(a,b)
with (E/'driver.jl').open('x') as f:f.write(new)
inverse=new
for a,b in pairs:inverse=inverse.replace(b,a)
source=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base/Base_compiler.jl')
checks=boundary_checks(new)|{'whole_driver_inverse':inverse.encode()==(S/'driver.jl').read_bytes(),'exactly_two_boundaries':new.count('Base.invokelatest(')==2,'all_helpers_and_timed_windows_identical':new.split('function main()')[0]==old.split('function main()')[0],'load_before_boundaries':new.index('Base.include(P,joinpath(RD,"instrumented.jl"))')<new.index(pairs[0][1])<new.index(pairs[1][1]),'raw_finally_and_acceptance_identical':new.split('        all(w["compile_seconds"]')[1]==old.split('        all(w["compile_seconds"]')[1],'smoke_and_RED_before_include_identical':new.split('        started=time_ns()')[0]==old.split('        started=time_ns()')[0],'Base_alias_Core_latest':'const invokelatest = Core.invokelatest' in source.read_text(),'driver_path_depth_same':E.parent==S.parent and (E/'../MA-R').resolve()==A.resolve(),'no_new_method_definitions':new.count('function ')==old.count('function ')}
with (E/'driver.diff').open('x') as f:f.writelines(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='MA-S/driver.jl (frozen failed)',tofile='MA-S-LOAD/driver.jl (unexecuted)'))
paths=[E/'prepare.py',E/'driver.jl',E/'driver.diff',E/'source-red.json',source,S/'driver.jl',S/'audit_reviewed.py',S/'admission-reviewed.md',A/'candidate.jl',A/'instrumented.jl',A/'reference.jl',A/'tests.jl',A/'fixtures.toml']
save('source-green.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in paths},scope='Offline source/inverse checks only. No parser/import/compile/numerical verification or runtime qualification.',edits=pairs))
print(json.dumps({'red_missing':sum(not x for x in red.values()),'green_checks':checks,'bindings':len(paths)}))
require(all(checks.values()),'Source contract failure')

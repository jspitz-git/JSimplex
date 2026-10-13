"""MA-I new offline preparation. No Julia, no old control execution."""
from pathlib import Path
import json,hashlib,shutil,tomllib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-I';H=D.parent/'MA-H';F=D.parent/'MA-F-repair';E=D.parent/'MA-E'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,s):
 p=D/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:f.write(s)
def save(n,x):put(n,json.dumps(x,indent=2)+'\n')
def changed(s,a,b):
 if s.count(a)!=1:raise ValueError(('unique replacement',a,s.count(a)))
 return s.replace(a,b)
if (E/'overlays/reference/src/markowitz_factorization.jl').read_bytes()!=(R/'src/markowitz_factorization.jl').read_bytes():raise ValueError('reference differs')
shutil.copytree(E/'overlays',D/'overlays')
for a,b in [('candidate-markowitz.jl','src/markowitz_factorization.jl'),('candidate-JSimplex.jl','src/JSimplex.jl'),('candidate-Project.toml','Project.toml')]:
 (D/'overlays/candidate'/b).write_bytes((H/a).read_bytes())
for n in ('kernels.jl','reference-upper.jl','test-collector.jl','tests-instrumented.jl','fixtures.toml','finite_oracle.py','guard-reviewed.py','launcher-reviewed.py'):
 put(n,(F/n).read_text())
put('reference-forward.jl',(H/'reference-forward.jl').read_text())
r=(H/'route-tests.jl').read_text()
reps=[('const Old = Main.MarkowitzMAUpperTests\n','const Old = Main.MarkowitzMAUpperTests\nconst ENTRY = Dict("constructors"=>0,"copies"=>0,"reference"=>0,"candidate"=>0,"throws"=>0,"successes"=>0)\n'),('    b = J.MarkowitzBackend(A)','    ENTRY["constructors"] += 1\n    b = J.MarkowitzBackend(A)'),('    c = J._copy_backend(b)','    ENTRY["copies"] += 1\n    c = J._copy_backend(b)'),('    er = outcome(reference_forward!,expected,b,rhs)','    ENTRY["reference"] += 1\n    er = outcome(reference_forward!,expected,b,rhs)'),('    ec = outcome(J._backend_forward_solve!,actual,c,rhs)','    ENTRY["candidate"] += 1\n    ec = outcome(J._backend_forward_solve!,actual,c,rhs)\n    ENTRY["throws"] += Int(er !== nothing) + Int(ec !== nothing)\n    ENTRY["successes"] += Int(er === nothing) + Int(ec === nothing)')]
for a,b in reps:r=changed(r,a,b)
back=r
for a,b in reversed(reps):back=changed(back,b,a)
if back!=(H/'route-tests.jl').read_text():raise ValueError('route inverse')
put('route-tests-instrumented.jl',r);save('route-instrumentation.json',dict(replacements=reps,inverse=True,original_sha256=sha(H/'route-tests.jl'),instrumented_sha256=hashlib.sha256(r.encode()).hexdigest(),expected=dict(constructors=28,copies=28,reference=28,candidate=28,throws=6,successes=50),scope='Cold driver entries before calls, outcomes after catches; no instrumentation of candidate or kernel timings.'))
s=(F/'driver.jl').read_text();dreps=[('                Base.include(Main,joinpath(@__DIR__,"tests-instrumented.jl"))','                Base.include(Main,joinpath(@__DIR__,"tests-instrumented.jl"))\n                if cfg["stage"] == "qualification"\n                    Base.include(Main,joinpath(@__DIR__,"route-tests-instrumented.jl"))\n                end'),('            raw["tests"]=snapshot(ts);raw["counts"]=total(ts)','            raw["context_restored"]=Test.get_testset()===parent_testset && Test.get_testset_depth()==parent_depth\n            raw["tests"]=snapshot(ts);raw["counts"]=total(ts)\n            if isdefined(Main,:MarkowitzMARoutingTests)\n                raw["route_entries"]=copy(Main.MarkowitzMARoutingTests.ENTRY)\n            end')]
for a,b in dreps:s=changed(s,a,b)
put('driver.jl',s);save('driver-instrumentation.json',dict(replacements=dreps,original_sha256=sha(F/'driver.jl')))
counts=json.loads((F/'test-counts.json').read_text());counts.update({'MA route complete forward':126,'MA route exceptional forward':54,'MA route scoped rounding forward':86});save('test-counts.json',counts)
s=(F/'auditor.py').read_text().replace("D.parent/'MA-E/overlays'","D/'overlays'")
s=changed(s," if stage in ('red','qualification'):\n  tree=raw['tests']"," if stage in ('red','qualification'):\n  require(raw['context_restored'] is True,'test context restoration')\n  if stage=='qualification':require(raw['route_entries']==dict(constructors=28,copies=28,reference=28,candidate=28,throws=6,successes=50),'route entries/outcomes')\n  else:require('route_entries' not in raw,'RED must not run route tests')\n  tree=raw['tests']")
put('auditor.py',s)
for n in ('control_reviewed.py','seal-reviewed.py'):
 s=(F/n).read_text().replace('MA-F/attempt-2','MA-I/attempt-1').replace('MA-F-attempt-2','MA-I-attempt-1').replace("D.parent/'MA-E/overlays'","D/'overlays'")
 put(n,s)
for p in sorted((F/'configs').glob('*.toml')):
 s=p.read_text().replace('/results/MA-E/overlays/','/results/MA-I/overlays/').replace('/MA-F/attempt-2/','/MA-I/attempt-1/')
 c=tomllib.loads(s);s=s.replace(c['source_sha256'],sha(D/'overlays'/c['side']/'src/markowitz_factorization.jl'))
 put('configs/'+p.name,s)
# New synthetic tests import only NEW pure modules. Historical test source remains untouched.
s=(E/'synthetic-final.py').read_text().replace('from control import','from control_reviewed import').replace('[381,0,0,0]','[647,0,0,0]').replace("for name in ('guard.py','launcher.py','seal.py','control.py','auditor.py'):","for name in ('guard-reviewed.py','launcher-reviewed.py','seal-reviewed.py','control_reviewed.py','auditor.py'):")
s=changed(s," if stage=='red':return raw"," if stage in ('red','qualification'):raw['context_restored']=True\n if stage=='qualification':raw['route_entries']=dict(constructors=28,copies=28,reference=28,candidate=28,throws=6,successes=50)\n if stage=='red':return raw")
put('synthetic.py',s.replace('synthetic-final.json','synthetic.json'))
s=(E/'synthetic-admission-reviewed.py').read_text().replace('MA-F-attempt-1','MA-I-attempt-1').replace('synthetic-admission-reviewed.json','synthetic-admission.json')
put('synthetic-admission.py',s)
save('overlay-hashes.json',{side:{str(p.relative_to(D/'overlays'/side)):sha(p) for p in sorted((D/'overlays'/side).rglob('*')) if p.is_file()} for side in ('reference','candidate')})
put('progress.md','# MA-I progress\n\nNew host preflight passed: 90 old PGIDs AND sessions absent, no Julia, refs and protected files unchanged. MA-H bound continuation bytes preserved before new work.\n\nNew ordinary overlays and controls prepared offline. Historical scripts were read/copied, never executed/imported. Candidate only MA-H exact source. No Julia, seal or reservation yet. New driver adds untimed pre-entry counters and outcome counts with exact inverse to H route tests; original381 tests/cold timings and cost kernel unchanged.\n\nApplicable executing-plans/worktree/TDD/review/verification skills retained. Existing isolated checkout reused; scoped plan forbids full-suite and old reruns. Independent exact admission is mandatory before numerical work.\n')
print('prepared',sum(counts.values()),'assertions',len(list((D/'configs').glob('*.toml'))),'configs')

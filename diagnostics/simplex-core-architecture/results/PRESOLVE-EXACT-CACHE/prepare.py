from pathlib import Path
import shutil,json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/PRESOLVE-EXACT-CACHE'; O=R/'.superpowers/presolve-exact-cache'
def write(p,s):
 with p.open('x') as f:f.write(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=(R/'src/presolve_dependencies.jl').read_text();prefix='function reduce_dependent_rows(problem::LinearProblem{T}) where {T}'
body=source[source.index(prefix):];assert body.count(prefix)==1
candidate=body.replace(prefix,'function reduce_dependent_rows(problem::LinearProblem{Float64})').replace('    entries = _row_entries(problem.A)','    exact_cache = Dict{Float64,ExactValue}()\n    entries = _row_entries(problem.A)',1).replace('_exact_rational(value)\n                            for (column, value) in terms)','get!(() -> _exact_rational(value), exact_cache, value)\n                            for (column, value) in terms)',1)
write(D/'candidate-append.jl','\n# Experimental per-call coefficient conversion cache; Float64 only.\n'+candidate)
write(D/'reference-function.jl',body)
imports='using JSimplex: LinearProblem, ExactValue, identity_presolve, _row_entries, _exact_rational, _subtract_scaled!, _implied_interval, _bound_rational, _interval_disjoint, _interval_subset, PresolveFailure, INFEASIBLE, _row_result\n'
write(D/'cores.jl','module CacheExperiment\n'+imports+body.replace('reduce_dependent_rows','reference_reduce',1)+'\ncandidate_reduce(p::LinearProblem)=reference_reduce(p)\n'+candidate.replace('reduce_dependent_rows','candidate_reduce',1)+'\nend\n')
O.mkdir(parents=True,exist_ok=False)
for side in ('reference','candidate'):
 q=O/side;q.mkdir();shutil.copytree(R/'src',q/'src')
 for n in ('Project.toml','Manifest.toml','LocalPreferences.toml'):shutil.copyfile(R/n,q/n)
 if side=='candidate':
  with (q/'src/presolve_dependencies.jl').open('ab') as f:f.write((D/'candidate-append.jl').read_bytes())
for n in ('guard.py','supervisor.py'):shutil.copyfile(R/'diagnostics/simplex-core-architecture/results/MA-X'/n,D/n)
shutil.copyfile(R/'diagnostics/simplex-core-architecture/results/MASTER-PROFILE/cases.toml',D/'cases.toml')
checks={'generic_source_preserved':(O/'candidate/src/presolve_dependencies.jl').read_bytes()==source.encode()+(D/'candidate-append.jl').read_bytes(),'exact_reference_function':body.encode()==(D/'reference-function.jl').read_bytes(),'three_edits':candidate.replace('function reduce_dependent_rows(problem::LinearProblem{Float64})',prefix).replace('    exact_cache = Dict{Float64,ExactValue}()\n','',1).replace('get!(() -> _exact_rational(value), exact_cache, value)','_exact_rational(value)',1)==body,'reference_overlay':all((O/'reference'/p.relative_to(R)).read_bytes()==p.read_bytes() for p in (R/'src').rglob('*') if p.is_file()),'candidate_other_sources':all((O/'candidate'/p.relative_to(R)).read_bytes()==p.read_bytes() for p in (R/'src').rglob('*') if p.is_file() and p.name!='presolve_dependencies.jl')}
assert all(checks.values());shutil.copyfile(__file__,D/'prepare.py');write(D/'preparation.json',json.dumps(dict(checks=checks,all_passed=True,overlay=str(O),candidate_sha256=sha(D/'candidate-append.jl')),indent=2)+'\n')
print('Separate ordinary overlays prepared; exact three-edit inverse PASS; no Julia.')

from control import *
import guard,ast
P=D.with_name('PRESOLVE-EXACT-CACHE-PIPELINE');old=rd(P/'pins.json');O=R/'.superpowers/presolve-exact-cache/reference'
entry=rd(D/'host.json');prior=rd(P.with_name('PRESOLVE-EXACT-CACHE')/'host.json')
req(all(sha(R/p)==h for p,h in prior['master_identity'].items()),'master source/test identity');req(all(sha(p)==h for p,h in prior['protected'].items()),'protected bytes')
inputs=[Path('/home/jspitz/mps')/(n+'.mps') for n in ('runtime','medium','test')];forbidden=[Path('/home/jspitz/mps')/(n+'.mps') for n in ('big','largo','AnyMOD')]
# Different byte lengths exclude exact-content aliases without reading forbidden LPs.
req(all(p.resolve().name.lower() not in guard.FORBIDDEN_NAMES and all(p.stat().st_size!=q.stat().st_size for q in forbidden) for p in inputs),'forbidden names/content aliases')
save(D/'input-identity.json',dict(inputs={str(p):dict(bytes=p.stat().st_size,sha256=sha(p),resolved=str(p.resolve())) for p in inputs},forbidden_lengths={str(p):p.stat().st_size for p in forbidden}))
commands={str(i):['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(O),str(D/'driver.jl'),name,str(D/f'run-{i}')] for i,name in enumerate(('runtime','medium','test'),1)};save(D/'commands.json',commands)
orig=(D/'original-controller.jl').read_text();cl=(D/'controller.jl').read_text();inverse=cl.replace('function profile_large_presolve(problem::LinearProblem{T}, observer) where {T}','function presolve_problem(problem::LinearProblem{T}) where {T}').replace('for round in 1:12','for _ in 1:12').replace('next = profile_large_dispatch(current, steps, propagation_trace, index, round, observer)','next = _dispatch_presolve_pass!(current, steps, propagation_trace, index)')
tests={'controller_inverse':inverse==orig and orig in (R/'src/presolve.jl').read_text(),'guard_exact':sha(D/'guard.py')==sha(P/'guard.py'),'supervisor_inverse':(D/'supervisor.py').read_text().replace('started+114','started+64').replace('started+118','started+68').replace('started+120','started+70').replace('<=120','<=70')==(P/'supervisor.py').read_text(),'reference_source':all(sha(p)==sha(R/'src'/p.relative_to(O/'src')) for p in (O/'src').rglob('*.jl'))}
for p in D.glob('*.py'):ast.parse(p.read_text())
tests['python_syntax']=True
for n,delta in [('rejected',{'accepted':False}),('findings',{'findings':['x']}),('wrong_pins',{'pins_sha256':'x'}),('missing_bindings',{'sha256':{}})]:
 good=dict(accepted=True,findings=[],pins_sha256='ok',sha256={str(D/'driver.jl'):sha(D/'driver.jl')})
 try:validate_review(good|delta,'ok',[D/'driver.jl']);tests[n]=False
 except ValueError:tests[n]=True
save(D/'offline-checks.json',dict(all_passed=all(tests.values()),checks=tests));req(all(tests.values()),'offline checks')
required=sorted(str(p) for p in D.iterdir() if p.is_file());save(D/'required.json',required)
# Reuse known dependency paths, freshly hash. Do not carry unrelated old diagnostics.
files=[p for p in old['files'] if not p.startswith(str(R))]
files += [str(R/p) for p in prior['master_identity']]+list(prior['protected'])+required+[str(D/'required.json')]+[str(p) for p in inputs]
trees=[p for p in old['trees'] if not p.startswith(str(R))]+[str(R/'src'),str(O)]
files=sorted(set(files));pins=dict(files=files,trees=trees,inventory=guard.inventory(files,trees),inputs=[str(p) for p in inputs],created=time.time());save(D/'pins.json',pins)
print('Offline checks',len(tests),'PASS; fresh pins',len(pins['inventory']))

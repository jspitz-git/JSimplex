from pathlib import Path
import json,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');O=D.parents[1]/'generic-residual-pivot-crash/2026-10-28'
p=D/'fixtures.jl';s=p.read_text()
s=s.replace('if w==1;@test old[2]==c*c;end','if T<:Rational&&w==1;@test old[2]==c*c;end')
s=s.replace('initial_perturbed=w.perturbed)','initial_perturbed=w.perturbed,initial_phase=w.scratch.phase_generation)')
s=s.replace('w.perturbed=v.initial_perturbed;w.scratch.perturbations=nothing','w.perturbed=v.initial_perturbed;w.scratch.perturbations=nothing;w.scratch.phase_generation=v.initial_phase')
s=s.replace('w.scratch.perturbations===j)','w.scratch.perturbations===j,w.scratch.phase_generation,isempty(w.scratch.checkpoints),isempty(w.scratch.recovery_rejections))')
s=s.replace('sameowners(owners(x[2].values[length(a.w.problem.objective)+1:end]),owners(x[2].primal))==sameowners(owners(y[2].values[length(b.w.problem.objective)+1:end]),owners(y[2].primal))','sharing(x[2])==sharing(y[2])')
s=s.replace('function outowners(x)','function sharing(x)\n fields=(x.values,x.multipliers,x.primal,x.dual)\n [[sameowners(owners(v),owners(w)) for v in a,w in b] for a in fields,b in fields]\nend\nfunction outowners(x)')
s=s.replace('same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a))','same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a))')
# Matrix of nested arrays: same handles recursively. Small comparison fixtures, outside measurements.
p.write_text(s)
# Recorded plan dimensions are bounded m=min(8,n/2), not m=n/2 for n64.
for name in ['PLAN.md','DESIGN.md']:
 p=D/name;s=p.read_text().replace('m=8/32','m=min(8,n/2)').replace('m=8/32','m=min(8,n/2)');p.write_text(s)
# Driver is simple ordinary Test and warmed alternating pairs; all prep recorded separately.
s=(O/'driver-final.jl').read_text().replace('fixtures-final.jl','fixtures.jl').replace('Residual pivot crash whole-function comparison','Unit perturb residual whole-function comparison').replace('RESIDUAL_PIVOT_CRASH_COMPLETE','UNIT_PERTURB_RESIDUAL_COMPLETE')
s=s.replace(',recycled=spec["recycled"],cap=spec["cap"]','')
(D/'driver.jl').write_text(s)
contexts=[f'BF{bits}_{mode}' for bits in (64,128,256) for mode in ['Nearest','Down','Up','ToZero','FromZero']]+['Float32','Float64','Rational{BigInt}','Rational{Int64}']
grid=[]
def add(c,a,n,d,h,s,m):grid.append(dict(id=f'C{len(grid)+1:04}',context=c,variant=a,n=n,m=min(8,n//2),density=d,shape=h,scope=s,mode=m))
for c in contexts:
 # Weighted pricing: meaningful Rational target, unchanged controls for all contexts.
 for n in (16,64):
  for scope in ('devex','steepest'):
   for mode in ('unit','mixed','nonunit'):
    for shape in (('positive','negative','mixed','wide') if c=='Rational{BigInt}' else ('mixed',)):
     add(c,'A',n,'sparse',shape,scope,mode)
 for n in (16,64):
  for density in ('sparse','dense'):
   for scope in ('dual','primal'):
    for shape in (('positive','negative','mixed') if c.startswith('BF') else ('mixed',)):
     add(c,'B',n,density,shape,scope,'unit')
   for scope in ('residual','outer'):
    for shape in ('positive','negative','mixed'):add(c,'C',n,density,shape,scope,'unit')
(D/'expected-cases.json').write_text(json.dumps(grid,indent=2)+'\n')
(D/'grid.toml').write_text(''.join('[[cells]]\n'+''.join(f'{k} = {json.dumps(v)}\n' for k,v in row.items())+'\n' for row in grid))
s=(O/'audit-final.py').read_text().replace('from common_final import','from common import').replace('contract-final.json','contract.json').replace('pins-final.json','pins.json').replace('audit-final.py','audit.py').replace('Residual pivot crash whole-function comparison','Unit perturb residual whole-function comparison').replace('RESIDUAL_PIVOT_CRASH_COMPLETE','UNIT_PERTURB_RESIDUAL_COMPLETE').replace("spec['scope']=='crash'","spec['scope'] in ['dual','primal']")
(D/'audit.py').write_text(s)
(D/'fixture-preparation.json').write_text(json.dumps(dict(cases=len(grid),contexts=len(contexts),measured_windows=18*len(grid),preparation=38+len(grid),numerics_executed=False),indent=2)+'\n')
print(len(grid),'cells')

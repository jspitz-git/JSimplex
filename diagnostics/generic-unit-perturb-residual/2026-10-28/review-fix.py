from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');sys.path.insert(0,str(D));import common as c
s=(D/'fixtures.jl').read_text()
s=s.replace('for v in (a,b);J.observe_progress!', 'for v in (a,b),_ in 1:2;J.observe_progress!')
s=s.replace('@test same(outputstate(a),outputstate(b))\n    for tag', '@test same(outputstate(a),outputstate(b))\n    @test scope===:dual ? a.journal.level==b.journal.level==2 : a.journal.bounds.level==b.journal.bounds.level==2\n    for tag')
s=s.replace('for tag in (Val(:original),Val(:B))\n     v=', 'for tag in (Val(:original),Val(:B)),throw_at in (1,2)\n     calls=Ref(0)\n     v=')
s=s.replace('stop_requested=()->throw(sentinel)','stop_requested=()->(calls[]+=1;calls[]==throw_at ? throw(sentinel) : false)')
s=s.replace('   z=setprecision(BigFloat,512) do;1+ldexp(BigFloat(1),-400);end\n   a.values[2]=z;b.values[2]=deepcopy(z);@test checkpair(a,b,:C)[1]===:value','''   z=setprecision(BigFloat,512) do;1+ldexp(BigFloat(1),-400);end
   a.values[2]=z;b.values[2]=deepcopy(z);@test checkpair(a,b,:C)[1]===:value
   a=fixture(T,16,:dense,:mixed,:residual);b=fixture(T,16,:dense,:mixed,:residual)
   a.values[2]=z;b.values[2]=deepcopy(z);@test checkpair(a,b,:C)[1]===:value''')
needle='  # Hand-derived lifted residual:'
extra='''  # Overlapping input arrays must still produce independently copied working scalars.
  p0=LinearProblem(spzeros(T,1,0),T[]);w0=J._initialize_workspace_state(p0,SolverOptions(T;verbose=false));v0=T[3//2]
  ra=UPRReference._lp_residual_values(T,w0,v0,v0);rb=UPRC._lp_residual_values(T,w0,v0,v0)
  @test same(resultvalue(ra),resultvalue(rb));@test sharing(ra)==sharing(rb)
  @test ra.values!==v0&&rb.values!==v0&&ra.multipliers!==v0&&rb.multipliers!==v0
  if T===BigFloat||T===Rational{BigInt}
   for r in (ra,rb)
    @test !sameowners(owners(v0[1]),owners(r.values[1]))
    @test !sameowners(owners(v0[1]),owners(r.multipliers[1]))
    @test !sameowners(owners(r.values[1]),owners(r.multipliers[1]))
    @test sameowners(owners(r.values[1]),owners(r.primal[1]))
    @test sameowners(owners(r.multipliers[1]),owners(r.dual[1]))
   end
  end
'''
s=s.replace(needle,extra+needle)
(D/'fixtures-reviewed.jl').write_text(s)
(D/'driver-reviewed.jl').write_text((D/'driver.jl').read_text().replace('fixtures.jl','fixtures-reviewed.jl'))
(D/'common_reviewed.py').write_text((D/'common.py').read_text().replace('contract.json','contract-reviewed.json').replace('pins.json','pins-reviewed.json'))
(D/'launch-reviewed.py').write_text((D/'launch.py').read_text().replace('from common import','from common_reviewed import').replace('contract.json','contract-reviewed.json').replace('pins.json','pins-reviewed.json').replace('admission.json','admission-reviewed.json'))
(D/'audit-reviewed.py').write_text((D/'audit.py').read_text().replace('from common import','from common_reviewed import').replace('contract.json','contract-reviewed.json').replace('pins.json','pins-reviewed.json').replace('audit.py','audit-reviewed.py'))
for name in ['WORK-MEMORY.md','PLAN.md']:
 old=D/(name+'.before-review');shutil.copyfile(D/name,old)
 s=(D/name).read_text().replace('LP refinement setup only','LP refinement initial setup, each accepted auxiliary candidate and each certificate-projection candidate that reaches the residual call').replace('callbackprecision','callbackprecision (source-preserved; existing regressions, not a new runtime cross-product)')
 (D/name).write_text(s)
# Correct nonexistent name in unsealed phase draft, preserving its original.
p=D/'prepare-phase.py';shutil.copyfile(p,D/'prepare-phase.py.before-review');p.write_text(p.read_text().replace("'lp_refinement_integration_tests.jl'", "'simplex_perturbation_integration_tests.jl','lp_refinement_diagnostic_tests.jl','lp_refinement_entry_tests.jl','lp_refinement_factor_tests.jl','lp_refinement_limit_tests.jl','lp_refinement_precision_tests.jl','lp_refinement_projection_tests.jl','lp_refinement_recovery_tests.jl','lp_refinement_state_tests.jl','lp_refinement_terminal_tests.jl'"))
con=c.read('contract.json');con['command'][-2]=str(D/'driver-reviewed.jl');c.put('contract-reviewed.json',con)
shutil.copyfile(__file__,D/'review-fix.py')
paths=set(c.read('pins.json')['inventory']);paths.update(str(p) for p in D.iterdir() if p.is_file() and p.name not in ['pins-reviewed.json'])
c.put('pins-reviewed.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=c.read('pins.json')['inputs'],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
# Initial inventory doc bindings resolve only to exact before-review copies.
c.put('review-fix.json',dict(accepted=True,numerics=False,checks=dict(two_observations='for v in (a,b),_ in 1:2' in s if False else 'for v in (a,b),_ in 1:2' in (D/'fixtures-reviewed.jl').read_text(),second_level='level==b.journal.level==2' in (D/'fixtures-reviewed.jl').read_text(),throw_after_work='throw_at in (1,2)' in (D/'fixtures-reviewed.jl').read_text(),fresh_mutable_scalars='!sameowners(owners(v0[1])' in (D/'fixtures-reviewed.jl').read_text()),historical_maps={str(D/name):dict(before=str(D/(name+'.before-review')),sha256=c.sha(D/(name+'.before-review'))) for name in ['WORK-MEMORY.md','PLAN.md']},bindings={str(D/n):c.sha(D/n) for n in ['fixtures-reviewed.jl','driver-reviewed.jl','contract-reviewed.json','common_reviewed.py','launch-reviewed.py','audit-reviewed.py','pins-reviewed.json']}))
print('separate reviewed revision',len(paths),'pins; noJulia')

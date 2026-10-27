from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');sys.path.insert(0,str(D));import common as c
for src,n in [('/tmp/vfp-admission-review-20261027.json','admission-initial.json'),('/tmp/vfp-admission-host-review-20261027.json','admission-initial-host.json')]:shutil.copyfile(src,D/n)
s=(D/'extra-tests.jl').read_text();where='  # A real quality-scratch overlap'
extra='''  # One real >128 pool rebuild with a hand-computed tie winner, independent
  # of the original price pattern used to create its now-invalid cache.
  for mod in (VFPReference,VFPB)
   v=fixture(T,128,4,:partial_rebuild,:sparse,:positive)
   for i in eachindex(v.w.reduced_costs);v.w.basis.states[i]==J.BASIC||(v.w.reduced_costs[i]=T(1//4));end
   J._invalidate_pricing_pool!(v.w;basis=false,costs=true)
   before=routebefore(v);z=mod._primal_entering(v.w,T(1//8))
   @test same(z,(5,-one(T)));checkroute(v,before)
  end
  for mod in (VFPReference,VFPC)
   v=fixture(T,8,4,:pivot,:sparse,:positive);pol=J.NumericalPolicy(T;recovery=true,pivot_validation=true)
   J._sync_recovery_rejections!(v.w);push!(v.w.scratch.recovery_rejections,(1,5))
   before=snapshot(v);cache=v.w.scratch.pivot_quality_cache
   @test mod.validate_pivot!(v.w,v.proposal,pol)===:reject_candidate
   @test v.w.scratch.pivot_quality_cache===cache&&intact(v,before)
  end
'''
c.need(s.count(where)==1,'extra insertion');s=s.replace(where,extra+where)
# Include explicit error-bound nonfinite checks in addition to nonfinite pivots.
s=s.replace('@test !VFPC._pivot_agrees(x,T(1),zero(T))','@test !VFPC._pivot_agrees(x,T(1),zero(T))\n    @test !VFPReference._pivot_agrees(T(1),T(1),x)\n    @test !VFPC._pivot_agrees(T(1),T(1),x)')
where='   # The first virtual coefficient'
extra='''   # A reliable tiny pivot must still fail the finite reciprocal gate.
   a=fixture(BigFloat,2,1,:pivot,:sparse,:positive);b=fixture(BigFloat,2,1,:pivot,:sparse,:positive)
   for side in (:a,:b)
    v=side===:a ? a : b;c=v.proposal;p=floatmin(BigFloat)
    v.w.problem.A[1,2]=BigFloat(2)*p
    v=merge(v,(proposal=J.PivotCandidate(2,1,p,[p],[BigFloat(1//2)]),))
    side===:a ? (a=v) : (b=v)
   end
   z=checkpair(a,b);@test z[1]===:value&&z[2]===:reject_candidate
'''
s=s.replace(where,extra+where)
# Full expected reliability cannot be forced for near-range dyadics with zero
# rhs; independence asserted via direct product oracle and unsafe flag.
s=s.replace('@test old==new','@test old==new\n    product=coefficient*factor\n    @test old==(!iszero(coefficient)&&!iszero(factor)&&abs(product)<floatmin(BigFloat))')
s=s.replace('@test same(qo,qn)&&same(qualityout(sr),qualityout(sn))','@test same(qo,qn)&&same(qualityout(sr),qualityout(sn))\n    @test !qo.reliable\n    (!isfinite(product)||old)&&@test !qo.finite')
(D/'extra-tests-final.jl').write_text(s)
s=(D/'driver-reviewed.jl').read_text().replace('"extra-tests.jl"','"extra-tests-final.jl"')
s=s.replace('reset!(v);push!(cold,timed(method,s,v))','rt=@timed reset!(v);push!(cold,merge(timed(method,s,v),Dict("preparation_reset"=>cost(rt))))').replace('reset!(v);push!(warm,timed(method,s,v))','rt=@timed reset!(v);push!(warm,merge(timed(method,s,v),Dict("preparation_reset"=>cost(rt))))')
(D/'driver-final.jl').write_text(s)
co=c.read('contract-reviewed.json');co['command']=[v.replace('/driver-reviewed.jl','/driver-final.jl') for v in co['command']];c.put('contract-final.json',co)
for src,dst in [('common_reviewed.py','common_final.py'),('launch-reviewed.py','launch-final.py'),('audit-reviewed.py','audit-final.py')]:
 s=(D/src).read_text().replace('contract-reviewed.json','contract-final.json').replace('pins-reviewed.json','pins-final.json').replace('common_reviewed','common_final').replace('audit-reviewed.py','audit-final.py')
 if dst=='audit-final.py':s=s.replace("resources=[json.loads", "  c.need(all(validcost(x['preparation_reset']) for k in ['cold','warm'] for x in v[k]),'cold/warm reset prep costs')\nresources=[json.loads")
 (D/dst).write_text(s)
(D/'PREPARATION-SCOPE.md').write_text('''Pre-execution admission amendments: initial four findings retained, sources unchanged. Final driver adds explicit boundary oracles, genuine partial tie/rebuild, real quality-buffer alias, recovery early rejection, reciprocal rejection, and reset cost records inside cold/warm metadata. Whole measured windows, grid and numerical expectations unchanged. Julia loading/includes and process initialization are bounded in inclusive launch wall time, not individually allocation-profiled. Each fixture, validation/snapshots, context correctness/GC, cold/warm calls and their resets, and measured-call resets/route checks have separate cost records. Native fallback controls call unchanged production compensation; no custom callback-neutrality or full recovery crossproduct claim. C's division-range guard remains source-preserved; any earlier reliable-quality or inverse gate may short circuit a range-invalid complete-call fixture. Broader regression test files cover unchanged recovery/observer machinery. No general trajectory/native-memory claim.\n''')
shutil.copyfile(__file__,D/'final-prepare.py')
pins=c.read('pins-reviewed.json');paths=set(pins['inventory']);paths.update(str(D/n) for n in ['admission-initial.json','admission-initial-host.json','extra-tests-final.jl','driver-final.jl','contract-final.json','common_final.py','launch-final.py','audit-final.py','PREPARATION-SCOPE.md','final-prepare.py','pins-reviewed.json'])
c.put('pins-final.json',dict(files=sorted(paths),trees=pins['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
import common_final as f;f.unchanged();f.put('final-author-host.json',f.host());print(len(paths),'finalpins; noJulia')

function boundary_correctness(::Type{T}) where T
 @testset "Cross-call owners and real dual cost rebase $T" begin
  if T===BigFloat
   for mod in (SSUReference,SSUA)
    v=fixture(T,4,2,:values,:sparse,:unbounded)
    fill!(v.w.costs,zero(T));fill!(v.w.reduced_costs,zero(T))
    x=mod._workspace_stagnation_values(v.w,v.state,:primal)
    y=mod._workspace_stagnation_values(v.w,v.state,:primal)
    @test all(iszero,x)&&all(iszero,y)
    @test all(x[i]!==y[i] for i in 1:3)
    @test x[1]!==x[2]&&x[1]!==x[3]&&x[2]!==x[3]
   end
  end
  for mod in (SSUReference,SSUB,SSUC,SSUBC)
   v=fixture(T,4,2,:init,:sparse,:slack)
   reset!(v);mod._primal_initialize_steepest!(v.w);first_owner=v.w.pricing_weights[5]
   reset!(v);mod._primal_initialize_steepest!(v.w);second_owner=v.w.pricing_weights[5]
   if T in (BigFloat,Rational{BigInt})
    @test first_owner!==second_owner
    @test v.w.pricing_weights[5]===v.w.pricing_weights[6]
   end
   @test same(first_owner,second_owner)
  end
  # Actual dual observation: retain the same history object after a cost-only
  # context change, emit exactly one cost-rebase event, then observe again.
  counts=[Ref(0),Ref(0)]
  observer(counter)=(reason,w)->begin;reason===:stagnation_cost_rebase&&(counter[]+=1);nothing;end
  a=fixture(T,4,2,:observe_dual,:sparse,:free;observer=observer(counts[1]))
  b=fixture(T,4,2,:observe_dual,:sparse,:free;observer=observer(counts[2]))
  olda=a.w.scratch.stagnation;oldb=b.w.scratch.stagnation
  old_observations=olda.monitor.observations
  a.w.costs[1]+=one(T);b.w.costs[1]+=one(T)
  reset!(a);reset!(b)
  x=capture(()->SSUReference._observe_stagnation!(a.w,:dual,a.steps...))
  y=capture(()->SSUA._observe_stagnation!(b.w,:dual,b.steps...))
  @test same(x,y)&&x[1]===:value&&same(outputs(a),outputs(b))
  @test a.w.scratch.stagnation===olda&&b.w.scratch.stagnation===oldb
  @test counts[1][]==counts[2][]==1
  @test olda.monitor.observations==oldb.monitor.observations==old_observations+1
 end
end

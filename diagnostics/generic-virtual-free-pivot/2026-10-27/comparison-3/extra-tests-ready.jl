# Additional independent boundary oracles. Ordinary Test only; outside timing.
function extra_correctness(::Type{T}) where T
 @testset "Explicit free/virtual/pivot boundaries $T" begin
  for price in (T(1//4),-T(1//4),zero(T)),tol in (T(1//4),T(1//8),-T(1//8))
   a=fixture(T,8,4,:enter_dantzig,:sparse,:positive);b=fixture(T,8,4,:enter_dantzig,:sparse,:positive)
   for (mod,v) in ((VFPReference,a),(VFPB,b))
    for i in eachindex(v.w.reduced_costs);v.w.basis.states[i]==J.BASIC||(v.w.reduced_costs[i]=copy(price));end
    eligible=abs(price)>tol;expected=eligible ? (5,price<0 ? one(T) : -one(T)) : (0,zero(T))
    before=snapshot(v)
    @test same(mod._primal_entering(v.w,tol),expected)
    @test mod._pool_primal_eligible(v.w,5,tol)==eligible
    @test intact(v,before)
    # Summary uses the unchanged, valid options tolerance; all eight free
    # variables contribute the same independently known magnitude.
    active=abs(price)>v.w.options.dual_tolerance
    @test same(mod.dual_infeasibility_summary(v.w),(active ? T(8)*abs(price) : zero(T),active ? 8 : 0))
   end
  end
  triples=((T(1),T(1),zero(T),true),(T(1),T(1),T(1),false),(T(1),T(5//4),T(1//4),true),(T(1),T(5//4),T(1//8),false),(T(1),-T(1),T(1//4),false),(zero(T),zero(T),zero(T),false),(T(1),T(1),-T(1),false))
  for (x,y,e,expected) in triples
   @test VFPReference._pivot_agrees(x,y,e)==expected
   @test VFPC._pivot_agrees(x,y,e)==expected
  end
  if T<:AbstractFloat
   for x in (T(NaN),T(Inf),-T(Inf))
    @test !VFPReference._pivot_agrees(x,T(1),zero(T))
    @test !VFPC._pivot_agrees(x,T(1),zero(T))
    @test !VFPReference._pivot_agrees(T(1),T(1),x)
    @test !VFPC._pivot_agrees(T(1),T(1),x)
   end
  end
  # One real >128 pool rebuild with a hand-computed tie winner, independent
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
  # A real quality-scratch overlap must still be rejected, before any
  # proposal values can be certified. Recreate separately owned arms.
  a=fixture(T,8,4,:pivot,:dense,:mixed);b=fixture(T,8,4,:pivot,:dense,:mixed)
  for side in (:a,:b)
   v=side===:a ? a : b;c=v.proposal;q=J._pivot_quality_buffers(v.w)
   copyto!(q.column.residual,c.column)
   v=merge(v,(proposal=J.PivotCandidate(c.entering,c.leaving_row,c.row_pivot,q.column.residual,c.rho),))
   side===:a ? (a=v) : (b=v)
  end
  z=checkpair(a,b;protect=false);@test z[1]===:error&&z[2]===ArgumentError
  if T===BigFloat
   for value in (BigFloat(0),-BigFloat(0),floatmin(BigFloat),-floatmin(BigFloat),floatmax(BigFloat),-floatmax(BigFloat))
    for scope in (:virtual,:virtual_transposed,:enter_dantzig,:summary,:pivot)
     a=fixture(T,8,4,scope,:dense,:positive);b=fixture(T,8,4,scope,:dense,:positive)
     for v in (a,b)
      if scope in (:virtual,:virtual_transposed);v.x[1]=copy(value)
      elseif scope===:pivot;v.proposal.column[1]=copy(value)
      else;v.w.reduced_costs[5]=copy(value)
      end
     end
     checkpair(a,b)
    end
   end
   # A reliable tiny pivot crosses the reciprocal range boundary. Directed
   # rounding may cap overflow at floatmax; require the original decision.
   a=fixture(BigFloat,2,1,:pivot,:sparse,:positive);b=fixture(BigFloat,2,1,:pivot,:sparse,:positive)
   for side in (:a,:b)
    v=side===:a ? a : b;c=v.proposal;p=floatmin(BigFloat)
    v.w.problem.A[1,2]=BigFloat(2)*p
    v=merge(v,(proposal=J.PivotCandidate(2,1,p,[p],[BigFloat(1//2)]),))
    side===:a ? (a=v) : (b=v)
   end
   for v in (a,b)
    B=J._basis_matrix!(v.w);p=v.proposal.column[1];pol=v.w.progress.numerical_policy
    @test J.solve_quality!(J.SolveQualityScratch(BigFloat,1),B,v.proposal.column,[BigFloat(2)*p],pol).reliable
    @test J.solve_quality!(J.SolveQualityScratch(BigFloat,1),B,v.proposal.rho,[BigFloat(1)],pol;transposed=true).reliable
   end
   z=checkpair(a,b);@test z[1]===:value
   !isfinite(inv(a.proposal.column[1]))&&@test z[2]===:reject_candidate
   # The first virtual coefficient times 1/2 exercises underflow; times 2
   # exercises overflow. Compare the internal unsafe flag and full quality,
   # never accepting a nonfinite result as a usable certificate.
   for coefficient in (floatmin(BigFloat),floatmax(BigFloat)),factor in (BigFloat(1//2),BigFloat(2)),transposed in (false,true)
    B=J._PriceAuditMatrix(sparse(reshape([coefficient],1,1)))
    x=fill(factor,transposed ? 2 : 3);rhs=zeros(BigFloat,transposed ? 3 : 2)
    sr=J.SolveQualityScratch(BigFloat,length(rhs));sn=J.SolveQualityScratch(BigFloat,length(rhs))
    old=VFPReference._quality_components!(sr.work_residual,sr.work_scale,sr.terms,B,x,rhs,transposed)
    new=VFPA._quality_components!(sn.work_residual,sn.work_scale,sn.terms,B,x,rhs,transposed)
    @test old==new
    product=coefficient*factor
    @test old==(!iszero(coefficient)&&!iszero(factor)&&abs(product)<floatmin(BigFloat))
    @test same(qualityout(sr),qualityout(sn))
    qo=VFPReference.solve_quality!(sr,B,x,rhs,J.NumericalPolicy(BigFloat);transposed)
    qn=VFPA.solve_quality!(sn,B,x,rhs,J.NumericalPolicy(BigFloat);transposed)
    @test same(qo,qn)&&same(qualityout(sr),qualityout(sn))
    @test !qo.reliable
    (!isfinite(product)||old)&&@test !qo.finite
   end
  end
 end
end

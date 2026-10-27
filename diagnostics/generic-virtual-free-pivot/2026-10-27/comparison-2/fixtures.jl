using Test,JSimplex,SparseArrays,LinearAlgebra
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a,b))
same(a::J.Bound,b::J.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
same(a::J.SolveQuality,b::J.SolveQuality)=same(a.absolute_error,b.absolute_error)&&same(a.relative_error,b.relative_error)&&a.finite==b.finite&&a.reliable==b.reliable
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
patternvalue(::Type{T},i,pattern) where T = T(pattern===:zero ? 0 : (pattern===:negative||pattern===:mixed&&iseven(i) ? -1 : 1)*((i%3+1)//8))
function makeworkspace(::Type{T},n,m,density,pattern;pricing=:dantzig,partial=false) where T
 A=zeros(T,m,n)
 for j in 1:n,i in 1:m
  if j<=m
   if i==j;A[i,j]=T(2)
   elseif i<j&&(density===:dense||j==i+1);A[i,j]=one(T)
   end
  elseif i==1||density===:dense||(i+j)%4==0
   A[i,j]=T(((i+j)%5+1)//32)
  end
 end
 # A literal dyadic direction gives an independent pivot oracle. Upper
 # triangular 2I+integer U keeps all control-type solves representable.
 wanted=T[patternvalue(T,i,pattern) for i in 1:m]
 n>m&&(A[:,m+1]=A[:,1:m]*wanted)
 rho=T[patternvalue(T,i,pattern) for i in 1:m]
 objective=transpose(A)*rho
 p=LinearProblem(sparse(A),objective;column_lower=zeros(T,n),column_upper=fill(T(4),n),row_lower=fill(-T(1024),m),row_upper=fill(T(1024),m))
 opt=SolverOptions(T;algorithm=:primal,pricing=pricing,partial_pricing=partial,verbose=false)
 pol=J.NumericalPolicy(T;pivot_validation=true,recovery=false,solve_refinement=false,partial_pricing=partial,refactor_timing=false)
 w=J.initialize_workspace(p,opt;progress=J.SimplexProgressContext(p;numerical_policy=pol))
 fill!(w.basis.states,J.AT_LOWER);copyto!(w.basis.basic_indices,collect(1:m));fill!(w.scratch.basic_mask,false)
 for i in 1:m;w.basis.states[i]=J.BASIC;w.scratch.basic_mask[i]=true;end
 J.recompute!(w;refactorize=true)
 return w,rho,wanted
end
poolstate(p)=isnothing(p) ? nothing : Tuple(getfield(p,k) isa AbstractArray ? copy(getfield(p,k)) : getfield(p,k) for k in fieldnames(typeof(p)))
function restorepool!(p,seed)
 for (i,k) in enumerate(fieldnames(typeof(p)))
  if k===:indices;resize!(p.indices,length(seed[i]));copyto!(p.indices,seed[i])
  else;setfield!(p,k,seed[i])
  end
 end
 nothing
end
function fixture(::Type{T},n,m,scope,density,pattern) where T
 pricing=scope===:enter_devex ? :devex : :dantzig
 partial=scope in (:partial_hit,:partial_rebuild)
 w,rho,wanted=makeworkspace(T,n,m,density,pattern;pricing,partial)
 if scope in (:audit,:virtual,:virtual_transposed)
  copyto!(w.scratch.rho,rho)
  predicted=vcat(w.costs[1:n]-transpose(w.problem.A)*rho,rho)
  if scope===:audit;return (scope=scope,w=w,predicted=predicted);end
  B=J._PriceAuditMatrix(w.problem.A)
  x=scope===:virtual ? vcat(rho,predicted) : T[patternvalue(T,i,pattern) for i in 1:size(B,1)]
  rhs=scope===:virtual ? copy(w.costs) : vcat(w.problem.A*x[1:n]-x[n+1:n+m],x)
  return (scope=scope,w=w,B=B,x=x,rhs=rhs,scratch=J.SolveQualityScratch(T,length(rhs)),policy=w.progress.numerical_policy)
 elseif scope===:pivot
  enter=m+1;rhs=Vector(w.problem.A[:,enter]);column=similar(rhs);J.forward_solve!(column,w.factorization,rhs)
  unit=zeros(T,m);unit[1]=one(T);row=similar(unit);J.transpose_solve!(row,w.factorization,unit)
  proposal=J.PivotCandidate(enter,1,dot(row,rhs),column,row)
  return (scope=scope,w=w,proposal=proposal,wanted=wanted)
 end
 for i in eachindex(w.basis.states)
  w.basis.states[i]==J.BASIC&&(w.reduced_costs[i]=zero(T);continue)
  w.reduced_costs[i]=patternvalue(T,i,pattern===:bound ? :positive : pattern)
  w.pricing_weights[i]=T(2)
  w.basis.states[i]=pattern===:bound ? J.AT_UPPER : J.FREE_NONBASIC
  if pattern!==:bound;w.lower[i]=J.Bound{T}(nothing);w.upper[i]=J.Bound{T}(nothing);end
 end
 seed=nothing
 if partial
  pool=J._pricing_pool!(w,:primal)
  J.select_pricing_candidate!(w,pool,w.progress.numerical_policy)
  seed=poolstate(pool)
 end
 return (scope=scope,w=w,poolseed=seed)
end
function reset!(v)
 if v.scope in (:partial_hit,:partial_rebuild)
  restorepool!(v.w.scratch.pricing_pool,v.poolseed)
  if v.scope===:partial_rebuild;J._invalidate_pricing_pool!(v.w;basis=false,costs=true);end
 end
 nothing
end
function qualityout(s)
 (s.residual,s.work_residual,s.work_scale,s.terms,s.compensation,s.error_sum)
end
function outputs(v)
 w=v.w
 if v.scope in (:virtual,:virtual_transposed);return qualityout(v.scratch)
 elseif v.scope===:pivot
  b=w.scratch.pivot_quality_cache;bm=w.scratch.basis_matrix
  return (isnothing(b) ? nothing : (b.rhs,b.unit,b.correction,b.trial,b.singletons,qualityout(b.column),qualityout(b.row)),isnothing(bm) ? nothing : (bm.colptr,bm.rowval,bm.nzval))
 end
 state=w.scratch.pricing
 (w.primal,w.reduced_costs,w.pricing_weights,w.scratch.steepest_valid,w.scratch.steepest_initialized,poolstate(w.scratch.pricing_pool),isnothing(state) ? nothing : Tuple(getfield(state,k) for k in fieldnames(typeof(state))))
end
function inputs(v)
 w=v.w;common=(w.problem.A.nzval,w.problem.A.rowval,w.problem.A.colptr,w.costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states)
 if v.scope===:audit;return (common...,w.scratch.rho,v.predicted)
 elseif v.scope in (:virtual,:virtual_transposed);return (common...,v.x,v.rhs)
 elseif v.scope===:pivot;return (common...,v.proposal.column,v.proposal.rho)
 end
 return (common...,w.reduced_costs,w.primal)
end
snapshot(v)=(inputs(v),map(copy,inputs(v)),deepcopy(inputs(v)))
function intact(v,s)
 all(inputs(v)[i]===s[1][i]&&same(inputs(v)[i],s[3][i])&&all(inputs(v)[i][j]===s[2][i][j] for j in eachindex(s[2][i])) for i in eachindex(s[1]))
end
@noinline function whole(::Val{arm},::Val{scope},v) where {arm,scope}
 mod=arm===:original ? VFPReference : arm===:A ? VFPA : arm===:B ? VFPB : VFPC
 if scope===:audit;return mod._primal_price_prediction_reliable(v.w,v.predicted)
 elseif scope in (:virtual,:virtual_transposed);return mod.solve_quality!(v.scratch,v.B,v.x,v.rhs,v.policy;transposed=scope===:virtual_transposed)
 elseif scope===:pivot;return mod.validate_pivot!(v.w,v.proposal,v.w.progress.numerical_policy)
 elseif scope===:summary;return mod.dual_infeasibility_summary(v.w)
 end
 return mod._primal_entering(v.w,v.w.options.dual_tolerance)
end
sink(x::Bool)=Int(x)
sink(x::Symbol)=x===:accept ? 1 : x===:refresh ? 2 : 3
sink(x::J.SolveQuality)=Int(x.finite)+2Int(x.reliable)+Int(iszero(x.absolute_error))
sink(x::Tuple{Int,<:Real})=x[1]+Int(signbit(x[2]))
sink(x::Tuple{<:Real,Int})=x[2]+Int(iszero(x[1]))
@noinline runwhole(m,s,v)=sink(whole(m,s,v))
function timed(m::M,s::S,v::V) where {M,S,V}
 t=@timed runwhole(m,s,v);merge(cost(t),Dict("sink"=>t.value))
end
armfor(scope)=scope in (:audit,:virtual,:virtual_transposed) ? :A : scope===:pivot ? :C : :B
function checkpair(a,b;protect=true)
 arm=armfor(a.scope);reset!(a);reset!(b);sa=snapshot(a);sb=snapshot(b);ctx=(precision(BigFloat),rounding(BigFloat))
 x=capture(()->whole(Val(:original),Val(a.scope),a));y=capture(()->whole(Val(arm),Val(b.scope),b))
 @test same(x,y)
 @test same(outputs(a),outputs(b))
 @test ctx==(precision(BigFloat),rounding(BigFloat))
 protect&&@test intact(a,sa)&&intact(b,sb)
 x
end
function checkroute(v,before)
 if v.scope in (:partial_hit,:partial_rebuild)
  p=v.w.scratch.pricing_pool;actual=length(v.w.basis.states)>128
  @test J._partial_pricing_enabled(v.w,:primal)==actual
  if actual
   @test p.passes==before.passes+1
   @test v.scope===:partial_hit ? p.scanned_entries==before.scanned_entries : p.full_scans==before.full_scans+1&&p.scanned_entries==before.scanned_entries+length(v.w.basis.states)
  else
   @test poolstate(p)==before.state
  end
 end
end
function routebefore(v)
 if v.scope in (:partial_hit,:partial_rebuild)
  p=v.w.scratch.pricing_pool
  @test v.scope===:partial_hit ? p.valid&&!isempty(p.indices) : !p.valid&&isempty(p.indices)
  return (passes=p.passes,scanned_entries=p.scanned_entries,full_scans=p.full_scans,state=poolstate(p))
 end
 nothing
end
function correctness(::Type{T}) where T
 @testset "Virtual/free/pivot correctness $T" begin
  for scope in (:audit,:virtual,:virtual_transposed,:enter_dantzig,:enter_devex,:partial_hit,:partial_rebuild,:summary,:pivot),density in (:sparse,:dense),pattern in (:positive,:negative,:mixed,:zero)
   # A zero candidate pool cannot have a cached hit; zero exhaustion uses rebuild.
   scope===:partial_hit&&pattern===:zero&&continue
   a=fixture(T,8,4,scope,density,pattern);b=fixture(T,8,4,scope,density,pattern)
   z=checkpair(a,b)
   @test z[1]===:value
   scope===:audit&&@test z[2]===true
   scope===:pivot&&@test z[2]===(pattern===:zero ? :reject_candidate : :accept)
   if scope===:pivot;@test pattern===:zero ? all(iszero,a.proposal.column)&&all(iszero,b.proposal.column) : same(a.proposal.column,a.wanted)&&same(b.proposal.column,b.wanted);end
  end
  # Independently exercise both genuine >128 partial routes and small fallback.
  for n in (8,128),scope in (:partial_hit,:partial_rebuild)
   a=fixture(T,n,4,scope,:sparse,:positive);b=fixture(T,n,4,scope,:sparse,:positive)
   for (arm,v) in ((:original,a),(:B,b))
    reset!(v);before=routebefore(v);z=whole(Val(arm),Val(scope),v);@test z[1]>0;checkroute(v,before)
   end
  end
  for scope in (:audit,:virtual,:virtual_transposed,:enter_dantzig,:summary,:pivot),edge in (:nonfinite,:mixed_precision,:dimension,:alias,:perturbed)
   a=fixture(T,8,4,scope,:dense,:mixed);b=fixture(T,8,4,scope,:dense,:mixed)
   for side in (:a,:b)
    v=side===:a ? a : b
    if scope===:audit
     if edge===:nonfinite&&T<:AbstractFloat;v.w.scratch.rho[1]=T(NaN)
     elseif edge===:mixed_precision&&T===BigFloat;v.w.scratch.rho[1]=setprecision(()->BigFloat(v.w.scratch.rho[1]),BigFloat,512)
     elseif edge===:dimension;v=merge(v,(predicted=v.predicted[1:end-1],))
     elseif edge===:alias;v=merge(v,(predicted=v.w.costs,))
     elseif edge===:perturbed;v.predicted[v.w.basis.basic_indices[1]]=one(T)
     end
    elseif scope in (:virtual,:virtual_transposed)
     if edge===:nonfinite&&T<:AbstractFloat;v.x[1]=T(Inf)
     elseif edge===:mixed_precision&&T===BigFloat;v.x[1]=setprecision(()->BigFloat(3//7),BigFloat,512)
     elseif edge===:dimension;v=merge(v,(x=v.x[1:end-1],))
     elseif edge===:alias
      q=v.scratch;v=merge(v,(rhs=q.residual,))
     elseif edge===:perturbed;v.rhs[1]+=one(T)
     end
    elseif scope===:pivot
     c=v.proposal
     if edge===:nonfinite&&T<:AbstractFloat;c.column[1]=T(Inf)
     elseif edge===:mixed_precision&&T===BigFloat;c.column[1]=setprecision(()->BigFloat(c.column[1]),BigFloat,512)
     elseif edge===:dimension;v=merge(v,(proposal=J.PivotCandidate(c.entering,c.leaving_row,c.row_pivot,c.column[1:end-1],c.rho),))
     elseif edge===:alias;v=merge(v,(proposal=J.PivotCandidate(c.entering,c.leaving_row,c.row_pivot,c.column,c.column),))
     elseif edge===:perturbed;v=merge(v,(proposal=J.PivotCandidate(c.entering,c.leaving_row,-c.row_pivot,c.column,c.rho),))
     end
    else
     if edge===:nonfinite&&T<:AbstractFloat;v.w.reduced_costs[end]=T(NaN)
     elseif edge===:mixed_precision&&T===BigFloat;v.w.reduced_costs[end]=setprecision(()->BigFloat(3//7),BigFloat,512)
     elseif edge===:dimension;resize!(v.w.reduced_costs,1)
     elseif edge===:perturbed;fill!(v.w.reduced_costs,zero(T))
     end
    end
    side===:a ? (a=v) : (b=v)
   end
   z=checkpair(a,b;protect=edge!==:alias)
   if edge===:dimension&&scope in (:virtual,:virtual_transposed,:pivot);@test z[1]===:error&&z[2]===DimensionMismatch;end
   edge===:alias&&scope in (:virtual,:virtual_transposed)&&@test z[1]===:error&&z[2]===ArgumentError
   edge===:perturbed&&scope===:audit&&@test z[1]===:value&&z[2]===false
  end
  # Empty implicit system and views retain generic dispatch and guards.
  for transposed in (false,true)
   B=J._PriceAuditMatrix(spzeros(T,0,0));scope=transposed ? :virtual_transposed : :virtual
   a=(scope=scope,w=fixture(T,8,4,:audit,:sparse,:positive).w,B=B,x=T[],rhs=T[],scratch=J.SolveQualityScratch(T,0),policy=J.NumericalPolicy(T));b=merge(a,(x=T[],rhs=T[],scratch=J.SolveQualityScratch(T,0)))
   z=checkpair(a,b);@test z[1]===:value&&z[2].reliable
   a=fixture(T,8,4,scope,:sparse,:positive);b=fixture(T,8,4,scope,:sparse,:positive);a=merge(a,(x=view(a.x,:),));b=merge(b,(x=view(b.x,:),));checkpair(a,b)
  end
  # Steepest pricing may solve weights between candidates: no reuse is made
  # across those calls. Exercise the real cold weight route separately.
  a=fixture(T,8,4,:enter_dantzig,:sparse,:positive);b=fixture(T,8,4,:enter_dantzig,:sparse,:positive)
  for v in (a,b)
   v.w.options=SolverOptions(T;algorithm=:primal,pricing=:steepest_edge,verbose=false)
   fill!(v.w.scratch.steepest_valid,false)
  end
  checkpair(a,b)
 end
end

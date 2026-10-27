using Test,JSimplex,SparseArrays,LinearAlgebra
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a,b))
same(a::J.SolveQuality,b::J.SolveQuality)=same(a.absolute_error,b.absolute_error)&&same(a.relative_error,b.relative_error)&&a.finite==b.finite&&a.reliable==b.reliable
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
struct PlainWrapper{T} <: AbstractMatrix{T};data::Matrix{T};end
Base.size(B::PlainWrapper)=size(B.data)
Base.getindex(B::PlainWrapper,i::Int,j::Int)=B.data[i,j]
function fixture(::Type{T},n,scope,density,pattern,m=4) where T
 if scope===:finish
  r=T[(pattern===:zero ? 0 : pattern===:negative||pattern===:mixed&&isodd(i) ? -1 : 1)*((i%5+1)//64) for i in 1:n]
  scale=fill(T(2),n);terms=fill(5,n)
  return (scope=scope,r=r,scale=scale,terms=terms,scratch=J.SolveQualityScratch(T,n),policy=J.NumericalPolicy(T))
 elseif scope in (:quality,:quality_transposed)
  B=zeros(T,n,n)
  for j in 1:n,i in 1:n
   if i==j;B[i,j]=T(2)
   elseif density===:dense||(i+j)%8==0;B[i,j]=T(1//32);end
  end
  density===:sparse&&(B=sparse(B))
  x=T[(pattern===:zero ? 0 : pattern===:negative||pattern===:mixed&&isodd(i) ? -1 : 1)*((i%5+1)//8) for i in 1:n]
  rhs=scope===:quality ? B*x : transpose(B)*x
  return (scope=scope,B=B,x=x,rhs=rhs,scratch=J.SolveQualityScratch(T,n),policy=J.NumericalPolicy(T))
 end
 A=zeros(T,m,n)
 for j in 1:n,i in 1:m
  if density===:dense||(i+j)%4==0;A[i,j]=T(((i+j)%5+1)//32);end
 end
 lo=T[(pattern===:zero ? 0 : pattern===:negative||pattern===:mixed&&isodd(i) ? -1 : 1)*((i%3+1)//4) for i in 1:n]
 p=LinearProblem(sparse(A),T[(i%3+1)//8 for i in 1:n];column_lower=lo,column_upper=lo.+T(4),row_lower=fill(-T(1024),m),row_upper=fill(T(1024),m))
 opt=SolverOptions(T;algorithm=:primal,pricing=:dantzig,verbose=false)
 pol=J.NumericalPolicy(T;refactor_timing=false)
 w=J.initialize_workspace(p,opt;progress=J.SimplexProgressContext(p;numerical_policy=pol))
 (scope=scope,w=w,primal=copy(w.primal),prices=copy(w.reduced_costs))
end
function reset!(v)
 if v.scope===:audit;copyto!(v.w.primal,v.primal);copyto!(v.w.reduced_costs,v.prices);end
 nothing
end
function inputs(v)
 if v.scope===:finish;return (v.r,v.scale,v.terms);end
 if v.scope!==:audit
  B=v.B
  if B isa J._PriceAuditMatrix;B=B.matrix;end
  return B isa SparseMatrixCSC ? (B.nzval,B.rowval,B.colptr,v.x,v.rhs) : (B,v.x,v.rhs)
 end
 w=v.w
 (w.problem.A.nzval,w.problem.A.rowval,w.problem.A.colptr,w.problem.objective,w.costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states)
end
function outputs(v)
 if v.scope!==:audit
  s=v.scratch;return (s.residual,s.work_residual,s.work_scale,s.terms,s.compensation,s.error_sum)
 end
 w=v.w
 (w.primal,w.reduced_costs,w.pricing_weights,w.scratch.rho,w.scratch.row_rhs,w.scratch.row_solution,w.scratch.tableau_row,w.iterations,w.refactorizations)
end
snapshot(v)=(inputs(v),map(copy,inputs(v)),deepcopy(inputs(v)))
function intact(v,s)
 all(inputs(v)[i]===s[1][i]&&same(inputs(v)[i],s[3][i])&&all(inputs(v)[i][j]===s[2][i][j] for j in eachindex(s[2][i])) for i in eachindex(s[1]))
end
@noinline function whole(::Val{arm},::Val{scope},v) where {arm,scope}
 mod=arm===:original ? LocalReference : arm===:A ? LocalCandidateA : arm===:B ? LocalCandidateB : arm===:AB ? LocalCandidateAB : LocalCandidateC
 if scope===:audit;return mod._audit_primal_values!(v.w)
 elseif scope===:finish;return mod._floating_quality!(v.scratch,v.r,v.scale,v.terms,v.policy)
 else;return mod.solve_quality!(v.scratch,v.B,v.x,v.rhs,v.policy;transposed=scope===:quality_transposed)
 end
end
sink(x::Symbol)=x===:accurate ? 1 : x===:corrected ? 2 : 3
sink(x::J.SolveQuality)=Int(x.finite)+2Int(x.reliable)+Int(iszero(x.absolute_error))
@noinline runwhole(m,s,v)=sink(whole(m,s,v))
function timed(m::M,s::S,v::V) where {M,S,V}
 t=@timed runwhole(m,s,v);merge(cost(t),Dict("sink"=>t.value))
end
function checkpair(a,b,arm;protect=true)
 reset!(a);reset!(b);sa=snapshot(a);sb=snapshot(b);ctx=(precision(BigFloat),rounding(BigFloat))
 x=capture(()->whole(Val(:original),Val(a.scope),a));y=capture(()->whole(Val(arm),Val(b.scope),b))
 @test same(x,y)
 @test same(outputs(a),outputs(b))
 @test ctx==(precision(BigFloat),rounding(BigFloat))
 protect&&@test intact(a,sa)&&intact(b,sb)
 x
end
variants(scope)=scope===:audit ? (:C,) : scope===:finish ? (:B,) : (:A,:B,:AB)
scopes(::Type{T}) where T=T<:AbstractFloat ? (:quality,:quality_transposed,:finish,:audit) : (:quality,:quality_transposed,:audit)
function correctness(::Type{T}) where T
 @testset "Local quality correctness $T" begin
  for scope in scopes(T),arm in variants(scope),pattern in (:positive,:negative,:mixed,:zero)
   for density in (scope===:finish ? (:vector,) : (:sparse,:dense))
    a=fixture(T,8,scope,density,pattern);b=fixture(T,8,scope,density,pattern)
    z=checkpair(a,b,arm)
    @test z[1]===:value
    scope===:audit&&@test z[2]===:accurate
   end
  end
  for scope in scopes(T),arm in variants(scope),edge in (:empty,:short,:nonfinite,:mixed_precision,:view,:alias,:perturbed)
   a=fixture(T,8,scope,:dense,:mixed);b=fixture(T,8,scope,:dense,:mixed)
   if edge===:empty&&scope!==:audit;a=fixture(T,0,scope,:dense,:zero);b=fixture(T,0,scope,:dense,:zero);end
   for side in (:a,:b)
    v=side===:a ? a : b
    if scope===:finish
     if edge===:short;v=merge(v,(scale=v.scale[1:end-1],))
     elseif edge===:nonfinite&&T<:AbstractFloat;v.r[1]=T(NaN)
     elseif edge===:mixed_precision&&T===BigFloat;v.r[1]=setprecision(()->BigFloat(3//7),BigFloat,512)
     elseif edge===:view;v=merge(v,(r=view(v.r,:),))
     elseif edge===:alias;v=merge(v,(r=v.scratch.residual,))
     elseif edge===:perturbed;v.scale[1]=-one(T)
     end
    elseif scope===:audit
     if edge===:nonfinite&&T<:AbstractFloat;v.primal[1]=T(NaN)
     elseif edge===:mixed_precision&&T===BigFloat;v.primal[1]=setprecision(()->BigFloat(v.primal[1]),BigFloat,512)
     elseif edge===:perturbed;v.primal[1]+=one(T)
     end
    else
     if edge===:short;v=merge(v,(x=v.x[1:end-1],))
     elseif edge===:nonfinite&&T<:AbstractFloat;v.x[1]=T(Inf)
     elseif edge===:mixed_precision&&T===BigFloat;v.x[1]=setprecision(()->BigFloat(3//7),BigFloat,512)
     elseif edge===:view;v=merge(v,(x=view(v.x,:),))
     elseif edge===:alias
      s=v.scratch;v=merge(v,(scratch=J.SolveQualityScratch(v.x,s.work_residual,s.work_scale,s.terms,s.compensation,s.error_sum),))
     elseif edge===:perturbed;v.rhs[1]+=one(T)
     end
    end
    side===:a ? (a=v) : (b=v)
   end
   # Alias correctness permits the original explicitly mutable scratch overlap.
   z=checkpair(a,b,arm;protect=edge!==:alias)
   edge===:short&&scope!==:audit&&@test z[1]===:error&&z[2]===DimensionMismatch
   edge===:alias&&scope in (:quality,:quality_transposed)&&@test z[1]===:error&&z[2]===ArgumentError
   edge===:nonfinite&&scope===:audit&&@test z[1]===:value&&z[2]===:corrected
   edge===:perturbed&&scope===:audit&&@test z[1]===:value&&z[2]===:corrected
  end
  for transposed in (false,true),arm in (:A,:B,:AB)
   B=J._PriceAuditMatrix(sparse(T[1 0;0 2]));x=ones(T,transposed ? size(B,1) : size(B,2));rhs=transposed ? transpose(B)*x : B*x
   scope=transposed ? :quality_transposed : :quality
   a=(scope=scope,B=B,x=x,rhs=rhs,scratch=J.SolveQualityScratch(T,length(rhs)),policy=J.NumericalPolicy(T));b=merge(a,(x=copy(x),rhs=copy(rhs),scratch=J.SolveQualityScratch(T,length(rhs))))
   z=checkpair(a,b,arm);@test z[1]===:value&&z[2].reliable
  end
  if T===BigFloat
   for modeval in (BigFloat(0),-BigFloat(0),BigFloat(1),BigFloat(-1),BigFloat(Inf),BigFloat(-Inf),BigFloat(NaN),floatmin(BigFloat),floatmax(BigFloat))
    for arm in (:A,:B,:AB),scope in (:quality,:quality_transposed,:finish)
     a=fixture(T,2,scope,:dense,:positive);b=fixture(T,2,scope,:dense,:positive)
     for v in (a,b)
      if scope===:finish;v.r[1]=copy(modeval)
      else;v.x[1]=copy(modeval);end
     end
     checkpair(a,b,arm)
    end
   end
  elseif T<:AbstractFloat
   for scope in (:quality,:quality_transposed),arm in (:B,:AB)
    a=fixture(T,2,scope,:dense,:positive);b=fixture(T,2,scope,:dense,:positive)
    for v in (a,b);v.B[1,1]=T(2);v.x[1]=floatmax(T);v.rhs[1]=floatmax(T);end
    checkpair(a,b,arm)
   end
  end
 end
end

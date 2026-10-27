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
struct PlainWrapper{T} <: AbstractMatrix{T}; data::Matrix{T}; end
Base.size(B::PlainWrapper)=size(B.data)
Base.getindex(B::PlainWrapper,i::Int,j::Int)=B.data[i,j]
isquality(s)=s in (:quality,:quality_transposed)
isdevex(s)=s in (:devex_shared,:devex_solved)
scopes(::Type{T}) where T=T<:AbstractFloat ? (:direction,:row,:quality,:quality_transposed,:devex_shared,:devex_solved) : (:quality,:quality_transposed,:devex_shared,:devex_solved)
function fixture(::Type{T},n,scope,density,pattern) where T
 if isquality(scope)
  B=zeros(T,n,n)
  for j in 1:n,i in 1:n
   if i==j;B[i,j]=T(2)
   elseif density===:dense||(i+j)%8==0;B[i,j]=T(1//32);end
  end
  density===:sparse&&(B=sparse(B))
  x=T[(pattern===:negative||pattern===:mixed&&isodd(i) ? -1 : 1)*((i%5+1)//8) for i in 1:n]
  rhs=scope===:quality ? B*x : transpose(B)*x
  return (scope=scope,B=B,x=x,rhs=rhs,scratch=J.SolveQualityScratch(T,n),policy=J.NumericalPolicy(T))
 end
 m=isdevex(scope) ? 4 : n;columns=n;A=zeros(T,m,columns)
 for j in 1:columns,i in 1:m
  if isdevex(scope)
   if j==1;A[i,j]=i==1 ? one(T) : zero(T)
   elseif density===:dense||j%4==0
    neg=pattern===:negative||pattern===:mixed&&isodd(j)
    A[i,j]=i==1 ? T((neg ? 1 : -1)*((i+j)%5+1)//2) : T(((i+j)%3)//8)
   end
  elseif i==j;A[i,j]=T(2)
  elseif density===:dense||(i+j)%8==0;A[i,j]=T(1//32)
  end
 end
 p=LinearProblem(sparse(A),zeros(T,columns);row_lower=fill(-T(8),m),row_upper=fill(T(8),m),column_lower=fill(-T(8),columns),column_upper=fill(T(8),columns))
 opt=SolverOptions(T;algorithm=isdevex(scope) ? :primal : :dual,pricing=:devex,verbose=false)
 pol=J.NumericalPolicy(T;refactor_timing=false)
 w=isdevex(scope) ? J.initialize_workspace(p,opt;progress=J.SimplexProgressContext(p;numerical_policy=pol)) : J._initialize_workspace_state(p,opt;progress=J.SimplexProgressContext(p;numerical_policy=pol))
 vector=T[(pattern===:negative||pattern===:mixed&&isodd(i) ? -1 : 1)*((i%5+1)//8) for i in 1:m];rhs=zeros(T,m)
 if isdevex(scope)
  fill!(w.pricing_weights,T(4));fill!(w.scratch.rho,zero(T));w.scratch.rho[1]=-one(T)
  J.price!(w.scratch.tableau_row,w,w.scratch.rho)
 else
  for i in 1:m;w.basis.basic_indices[i]=isodd(i) ? i : columns+i;end
  for (j,k) in enumerate(w.basis.basic_indices)
   if k<=columns
    for q in nzrange(w.problem.A,k);rhs[w.problem.A.rowval[q]]+=w.problem.A.nzval[q]*vector[j];end
   else;rhs[k-columns]-=vector[j];end
  end
  scope===:direction&&J._hypersparse_workspace!(w)
 end
 (scope=scope,w=w,vector=vector,rhs=rhs,pivot=one(T),weights=copy(w.pricing_weights))
end
function reset!(v)
 if v.scope===:direction
  copyto!(v.w.scratch.row_rhs,v.rhs);fill!(v.w.scratch.hypersparse.valid,true)
 elseif isdevex(v.scope);copyto!(v.w.pricing_weights,v.weights)
 end
 nothing
end
function inputs(v)
 if isquality(v.scope)
  B=v.B
  return B isa SparseMatrixCSC ? (B.nzval,B.rowval,B.colptr,v.x,v.rhs) : (B,v.x,v.rhs)
 end
 w=v.w
 (w.problem.A.nzval,w.problem.A.rowval,w.problem.A.colptr,w.problem.objective,w.primal,w.costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states,v.vector,v.rhs)
end
function outputs(v)
 if isquality(v.scope);s=v.scratch;return (s.residual,s.work_residual,s.work_scale,s.terms,s.compensation,s.error_sum);end
 w=v.w
 isdevex(v.scope) ? (w.pricing_weights,w.scratch.rho,w.scratch.tableau_row) : (w.scratch.tau,w.scratch.row_rhs,isnothing(w.scratch.hypersparse) ? () : w.scratch.hypersparse.valid)
end
snapshot(v)=(inputs(v),map(copy,inputs(v)),deepcopy(inputs(v)))
function intact(v,s)
 all(inputs(v)[i]===s[1][i]&&same(inputs(v)[i],s[3][i])&&all(inputs(v)[i][j]===s[2][i][j] for j in eachindex(s[2][i])) for i in eachindex(s[1]))
end
for (method,module_) in [(:original,:SavingsReference),(:candidate,:SavingsCandidate)]
 @eval begin
  @noinline whole(::Val{$(QuoteNode(method))},::Val{:direction},v)=$module_._dual_direction_residual_ok!(v.w,v.vector,v.pivot)
  @noinline whole(::Val{$(QuoteNode(method))},::Val{:row},v)=$module_._dual_row_residual_ratio(v.w,v.vector,1)
  @noinline whole(::Val{$(QuoteNode(method))},::Val{:quality},v)=$module_.solve_quality!(v.scratch,v.B,v.x,v.rhs,v.policy)
  @noinline whole(::Val{$(QuoteNode(method))},::Val{:quality_transposed},v)=$module_.solve_quality!(v.scratch,v.B,v.x,v.rhs,v.policy;transposed=true)
  @noinline whole(::Val{$(QuoteNode(method))},::Val{:devex_shared},v)=$module_._primal_update_devex!(v.w,1,1,v.pivot;shared_row=true)
  @noinline whole(::Val{$(QuoteNode(method))},::Val{:devex_solved},v)=$module_._primal_update_devex!(v.w,1,1,v.pivot;shared_row=false)
 end
end
sink(x::Bool)=Int(x)
sink(x::Nothing)=0
sink(x::J.SolveQuality)=Int(x.finite)+2Int(x.reliable)+Int(iszero(x.absolute_error))
sink(x::AbstractFloat)=isfinite(x) ? (x>1 ? 2 : iszero(x) ? 0 : 1) : -1
@noinline runwhole(m,s,v)=sink(whole(m,s,v))
function timed(m::M,s::S,v::V) where {M,S,V}
 t=@timed runwhole(m,s,v);merge(cost(t),Dict("sink"=>t.value))
end
function checkpair(a,b;protect=true)
 reset!(a);reset!(b);sa=snapshot(a);sb=snapshot(b)
 x=capture(()->whole(Val(:original),Val(a.scope),a));y=capture(()->whole(Val(:candidate),Val(b.scope),b))
 @test same(x,y)
 @test same(outputs(a),outputs(b))
 if protect;@test intact(a,sa)&&intact(b,sb);end
 x
end
function correctness(::Type{T}) where T
 @testset "Whole-function correctness $T" begin
  for scope in scopes(T),density in (:sparse,:dense),pattern in (:positive,:negative,:mixed)
   a=fixture(T,8,scope,density,pattern);b=fixture(T,8,scope,density,pattern);checkpair(a,b)
  end
  for scope in scopes(T)
   if !isdevex(scope)
    a=fixture(T,0,scope,:dense,:positive);b=fixture(T,0,scope,:dense,:positive)
    z=checkpair(a,b);@test z[1]===:value
   else
    a=fixture(T,8,scope,:dense,:positive);b=fixture(T,8,scope,:dense,:positive)
    for v in (a,b);fill!(v.w.basis.states,J.BASIC);end
    checkpair(a,b)
   end
  end
  for scope in scopes(T),edge in (:zero,:short,:nonfinite,:mixed_precision,:alias,:bad_basis,:view)
   a=fixture(T,8,scope,:dense,:mixed);b=fixture(T,8,scope,:dense,:mixed)
   for side in (:a,:b)
    v=side===:a ? a : b
    if isquality(scope)
     if edge===:zero;fill!(v.B,zero(T));fill!(v.x,zero(T));fill!(v.rhs,zero(T))
     elseif edge===:short;v=merge(v,(x=v.x[1:end-1],))
     elseif edge===:nonfinite&&T<:AbstractFloat;v.x[1]=T(Inf)
     elseif edge===:mixed_precision&&T===BigFloat;v.x[1]=setprecision(()->BigFloat(3//7),BigFloat,512)
     elseif edge===:alias
      s=v.scratch;v=merge(v,(scratch=J.SolveQualityScratch(v.x,s.work_residual,s.work_scale,s.terms,s.compensation,s.error_sum),))
     elseif edge===:bad_basis;v=merge(v,(B=PlainWrapper(Matrix(v.B)),))
     elseif edge===:view;v=merge(v,(x=view(v.x,:),))
     end
    else
     if edge===:zero;fill!(v.vector,zero(T));isdevex(scope)&&fill!(v.w.scratch.tableau_row,zero(T))
     elseif edge===:short&&!isdevex(scope);v=merge(v,(vector=T[],))
     elseif edge===:nonfinite&&T<:AbstractFloat
      if isdevex(scope);v.w.scratch.tableau_row[2]=T(Inf);else;v.vector[1]=T(Inf);end
     elseif edge===:mixed_precision&&T===BigFloat
      v.vector[1]=setprecision(()->BigFloat(3//7),BigFloat,512)
      if isdevex(scope)
       v.w.scratch.tableau_row[2]=setprecision(()->BigFloat(3//7),BigFloat,512)
       v.w.pricing_weights[1]=setprecision(()->BigFloat(7//3),BigFloat,512)
       v=merge(v,(weights=copy(v.w.pricing_weights),pivot=setprecision(()->BigFloat(3//7),BigFloat,512)))
      end
     elseif edge===:alias&&scope===:direction;v.w.scratch.tau=v.w.scratch.row_rhs
     elseif edge===:bad_basis&&!isdevex(scope);v.w.basis.basic_indices[end]=length(v.w.primal)+1
     end
    end
    side===:a ? (a=v) : (b=v)
   end
   x=checkpair(a,b;protect=edge!==:alias)
   edge===:short&&!isdevex(scope)&&@test x[1]===:error&&x[2]===DimensionMismatch
   edge===:alias&&isquality(scope)&&@test x[1]===:error&&x[2]===ArgumentError
  end
  if T===BigFloat
   vals=BigFloat[0,-0.0,1,-1,Inf,-Inf,NaN,floatmax(BigFloat),floatmin(BigFloat)]
   push!(vals,setprecision(()->BigFloat(3//7),BigFloat,512))
   for x in vals,y in vals
    before=deepcopy((x,y));u=SavingsReference._primal_devex_candidate_weight(x,y);v=SavingsCandidate._primal_devex_candidate_weight(x,y)
    @test same(u,v);@test same((x,y),before)
    @test v!==x&&v!==y
   end
   a=SavingsCandidate._primal_devex_candidate_weight(BigFloat(Inf),BigFloat(1));b=SavingsCandidate._primal_devex_candidate_weight(BigFloat(Inf),BigFloat(1));@test a!==b&&same(a,b)
   for tr in (false,true),dense in (false,true)
    s=tr ? :quality_transposed : :quality;a=fixture(T,2,s,dense ? :dense : :sparse,:positive);b=fixture(T,2,s,dense ? :dense : :sparse,:positive)
    for v in (a,b);fill!(v.B,BigFloat(0));v.B[1,1]=floatmin(BigFloat);v.x[1]=BigFloat(1//2);fill!(v.rhs,BigFloat(0));end
    z=checkpair(a,b)
    unsafe_expected=setprecision(BigFloat,2*precision(BigFloat)+18) do
     floatmin(BigFloat)*BigFloat(1//2)<floatmin(BigFloat)
    end
    @test z[1]===:value&&z[2].finite===!unsafe_expected
   end
  end
 end
end

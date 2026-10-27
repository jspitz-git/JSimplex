using Test,JSimplex,SparseArrays,LinearAlgebra,Statistics
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a))
same(a::J.Bound,b::J.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
modof(::Val{:original})=BNIReference
modof(::Val{:A})=BNIA
modof(::Val{:B})=BNIB
modof(::Val{:C})=BNIC
isresidual(scope)=scope in (:direction_residual,:row_residual)
function ratio_fixture(::Type{T},n,scope,density,pattern) where T
 m=scope===:harris ? 4 : n;columns=isresidual(scope) ? n : scope===:harris ? n : 1
 A=zeros(T,m,columns)
 for j in 1:columns,i in 1:m
  if isresidual(scope)
   if i==j;A[i,j]=T(2)
   elseif i>1&&j>1&&(density===:dense||(i+j)%8==0);A[i,j]=T(1//32);end
  elseif density===:dense||(i+j)%4==0;A[i,j]=T(((i+j)%5+1)//8)
  end
 end
 p=LinearProblem(sparse(A),zeros(T,columns);row_lower=fill(-T(8),m),row_upper=fill(T(8),m),column_lower=fill(-T(8),columns),column_upper=fill(T(8),columns))
 opt=SolverOptions(T;algorithm=scope===:primal_ratio ? :primal : :dual,pricing=:dantzig,verbose=false)
 policy=J.NumericalPolicy(T;refactor_timing=false)
 w=J._initialize_workspace_state(p,opt;progress=J.SimplexProgressContext(p;numerical_policy=policy))
 vector=zeros(T,scope===:harris ? length(w.basis.states) : m);rhs=zeros(T,m)
 if isresidual(scope)
  for i in 1:m;w.basis.basic_indices[i]=isodd(i) ? i : columns+i;end
  if scope===:row_residual
   if m>0;vector[1]=T(1//2);end
   if m>0&&pattern===:perturbed;vector[end]=T(1//1024);end
  else
   for i in 1:m;vector[i]=T((isodd(i) ? 1 : -1)//8);end
   for (j,k) in enumerate(w.basis.basic_indices)
    if k<=columns
     for q in w.problem.A.colptr[k]:w.problem.A.colptr[k+1]-1;rhs[w.problem.A.rowval[q]]+=w.problem.A.nzval[q]*vector[j];end
    else;rhs[k-columns]-=vector[j];end
   end
   if pattern===:perturbed;rhs[end]+=T(1//1024);end
  end
 elseif scope===:primal_ratio
  for i in 1:m
   active=density===:dense||i%4==0;ordinal=density===:dense ? i : i÷4
   negative=pattern===:negative||pattern===:mixed&&isodd(ordinal)
   vector[i]=active ? (negative ? -T((i+1)//8) : T((i+1)//8)) : zero(T)
   magnitude=T((i+1)//8);step=pattern===:unique ? T((i+64)//64) : one(T)
   w.lower[columns+i]=Bound(-magnitude*step);w.upper[columns+i]=Bound(magnitude*step)
  end
 else
  for i in 1:columns
   active=density===:dense||i%4==0;negative=pattern===:negative||pattern===:mixed&&isodd(i÷(density===:dense ? 1 : 4))
   w.basis.states[i]=negative ? J.AT_UPPER : J.AT_LOWER
   vector[i]=active ? (negative ? -T((i+1)//8) : T((i+1)//8)) : zero(T)
   step=pattern===:unique ? T((i+64)//64) : pattern===:ties ? zero(T) : one(T)
   w.reduced_costs[i]=vector[i]*step
  end
 end
 if scope===:direction_residual;J._hypersparse_workspace!(w);end
 (w=w,vector=vector,rhs=rhs,scope=scope,orientation=one(T),pivot=one(T))
end


function fixture(::Type{T},n,density,shape,scope;below=true,mode=:finite) where T
 if scope in (:snap,:step,:ratio)
  v=ratio_fixture(T,n,:primal_ratio,density,shape)
  if scope===:snap
   v.vector[1]=-one(T);v.w.upper[2]=J.Bound(one(T));v.w.primal[2]=T(17//16)
   v.w.lower[1]=J.Bound(zero(T));opts=v.w.options
   v.w.options=typeof(opts)((k===:primal_tolerance ? T(1//8) : getfield(opts,k) for k in fieldnames(typeof(opts)))...)
  end
  if scope!==:ratio
   for i in 2:n
    if i%3==0;v.w.lower[1+i]=J._unbounded_bound(T);v.w.upper[1+i]=J._unbounded_bound(T);end
   end
  end
  return merge(v,(scope=scope,step=T(1//32)))
 elseif scope===:norm
  vector=T[(density===:dense||i%4==0) ? (shape===:negative||shape===:mixed&&isodd(i) ? -1 : 1)*((i%7+1)//16) : 0 for i in 1:n]
  return (scope=scope,vector=vector)
 end
 m=min(8,n÷2);A=zeros(T,m,n)
 for j in 1:n,i in 1:m
  (density===:dense||(i+j)%5==0)&&(A[i,j]=T((shape===:negative||shape===:mixed&&isodd(i+j) ? -1 : 1)*((i+j)%7+1)//16))
 end
 p=LinearProblem(sparse(A),zeros(T,n);column_lower=zeros(T,n),column_upper=fill(T(4),n),row_lower=fill(-T(8),m),row_upper=fill(T(8),m))
 opt=SolverOptions(T;algorithm=:primal,pricing=:steepest_edge,verbose=false)
 pol=J.NumericalPolicy(T;refactor_timing=false,solve_refinement=false,recovery=false)
 progress=J.SimplexProgressContext(p;numerical_policy=pol)
 w=scope===:solve ? J.initialize_workspace(p,opt;progress) : J._initialize_workspace_state(p,opt;progress)
 if scope===:cert
  rho=fill(T(1//8),m);orientation=below ? one(T) : -one(T)
  for j in 1:n
   coefficient=sum((orientation*rho[i]*A[i,j] for i in 1:m);init=zero(T));value=coefficient<0 ? -T(2) : T(2)
   w.lower[j]=J.Bound(value);w.upper[j]=J.Bound(value)
   if mode===:one_sided&&!iszero(coefficient)
    if coefficient>0;w.upper[j]=J._unbounded_bound(T);else;w.lower[j]=J._unbounded_bound(T);end
   end
  end
  for j in n+1:n+m;w.lower[j]=J.Bound(zero(T));w.upper[j]=J.Bound(zero(T));end
  if mode===:zero_tol
   opts=w.options;w.options=typeof(opts)((k===:primal_tolerance ? zero(T) : getfield(opts,k) for k in fieldnames(typeof(opts)))...)
  end
  return (scope=scope,w=w,rho=rho,below=below)
 end
 (scope=scope,w=w,weights=copy(w.pricing_weights),valid=copy(w.scratch.steepest_valid))
end
function reset!(v)
 if v.scope in (:init,:solve)
  copyto!(v.w.pricing_weights,v.weights);copyto!(v.w.scratch.steepest_valid,v.valid);v.w.scratch.steepest_initialized=false
 end
 nothing
end
@noinline function whole(a::A,v::V) where {A,V}
 mod=modof(a)
 if v.scope===:snap;return mod._primal_bound_snap_feasible(v.w,1,v.orientation,v.vector,1)
 elseif v.scope===:step;return mod._primal_step_bounds_feasible(v.w,v.orientation,v.vector,v.step)
 elseif v.scope===:ratio;return mod._primal_ratio(v.w,1,v.orientation,v.vector)
 elseif v.scope===:norm;return mod._primal_direction_weight(v.vector)
 elseif v.scope===:init;return mod._primal_initialize_steepest!(v.w)
 elseif v.scope===:solve;return mod._primal_steepest_weight!(v.w,1)
 end
 mod._infeasibility_certified(v.w,v.rho,v.below)
end
sink(x::Bool)=Int(x)
sink(x::Rational)=Int(x>0)
sink(::Nothing)=1
sink(x::Tuple{<:Integer,<:AbstractFloat})=Int(isfinite(x[2]))
sink(x::Tuple{<:Tuple,<:AbstractFloat})=Int(isfinite(x[2]))
sink(x::Tuple{<:Rational,<:Rational})=Int(x[2]>0)
sink(x::Tuple{<:Union{Nothing,Real},Int,J.VariableState})=100*x[2]+Int(x[3])+(isnothing(x[1]) ? -10000 : 1)
@noinline runwhole(a::A,v::V) where {A,V}=sink(whole(a,v))
function timed(a::A,v::V) where {A,V}
 t=@timed runwhole(a,v);merge(cost(t),Dict("sink"=>t.value))
end
function inputs(v)
 v.scope===:norm&&return (v.vector,)
 w=v.w;A=w.problem.A
 q=(A.nzval,A.rowval,A.colptr,w.problem.objective,w.problem.column_lower,w.problem.column_upper,w.problem.row_lower,w.problem.row_upper,w.costs,w.reduced_costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states,w.primal)
 v.scope in (:snap,:step,:ratio) ? (q...,v.vector) : v.scope===:cert ? (q...,v.rho) : q
end
snapshot(v)=(inputs(v),map(copy,inputs(v)),deepcopy(inputs(v)))
function intact(v,s)
 a=inputs(v);all(a[k]===s[1][k]&&same(a[k],s[3][k])&&all(a[k][i]===s[2][k][i] for i in eachindex(a[k])) for k in eachindex(a))
end
outputs(v,z)=v.scope in (:init,:solve) ? (z,v.w.pricing_weights,v.w.scratch.steepest_valid,v.w.scratch.steepest_initialized,v.w.basis.basic_indices,v.w.basis.states,v.w.primal) : z
aliaspattern(q)=Bool[q[i]===q[j] for i in eachindex(q),j in eachindex(q)]
function checkpair(a,b,arm)
 reset!(a);reset!(b);sa=snapshot(a);sb=snapshot(b);ctx=(precision(BigFloat),rounding(BigFloat))
 x=capture(()->whole(Val(:original),a));y=capture(()->whole(Val(arm),b))
 @test x[1]===y[1]
 @test x[1]===:value ? same(outputs(a,x[2]),outputs(b,y[2])) : same(x,y)
 @test intact(a,sa)&&intact(b,sb)
 @test ctx==(precision(BigFloat),rounding(BigFloat))
 if x[1]===:value&&a.scope===:init;@test aliaspattern(a.w.pricing_weights)==aliaspattern(b.w.pricing_weights);end
 x
end
function correctness(::Type{T}) where T
 @testset "Bounds norm certificate $T" begin
  for scope in (:snap,:step,:ratio,:norm,:init,:solve),density in (:sparse,:dense),shape in (:positive,:negative,:mixed)
   arm=scope in (:snap,:step,:ratio) ? :A : :B
   a=fixture(T,8,density,shape,scope);b=fixture(T,8,density,shape,scope);x=checkpair(a,b,arm)
   if scope in (:snap,:step);@test x==(:value,true)
   elseif scope===:ratio;@test x[1]===:value&&x[2][2]>0&&x[2][1]==1
   end
  end
  for below in (true,false),density in (:sparse,:dense),shape in (:positive,:negative,:mixed),mode in (:finite,:one_sided,:zero_tol)
   a=fixture(T,16,density,shape,:cert;below,mode);b=fixture(T,16,density,shape,:cert;below,mode)
   @test checkpair(a,b,:C)==(:value,true)
   a.rho .*= -one(T);b.rho .*= -one(T);@test checkpair(a,b,:C)==(:value,false)
  end
  for scope in (:snap,:step,:ratio),variant in (:empty,:unbounded,:short,:nonfinite,:bad_point,:zero_tol,:negative_tol,:tol512,:alias)
   a=fixture(T,8,:dense,:mixed,scope);b=fixture(T,8,:dense,:mixed,scope)
   for v in (a,b)
    w=v.w
    if variant===:empty;empty!(w.basis.basic_indices)
    elseif variant===:unbounded
     for j in 3:length(w.lower);w.lower[j]=J._unbounded_bound(T);w.upper[j]=J._unbounded_bound(T);end
    elseif variant===:short;empty!(w.upper)
    elseif variant===:nonfinite&&T<:AbstractFloat;w.primal[end]=T(Inf)
    elseif variant===:bad_point;w.primal[end]=T(100)
    elseif variant in (:zero_tol,:negative_tol)||variant===:tol512&&T===BigFloat
     tol=variant===:zero_tol ? zero(T) : variant===:negative_tol ? -one(T) : setprecision(()->BigFloat(3//7),BigFloat,512)
     opts=w.options;w.options=typeof(opts)((k===:primal_tolerance ? tol : getfield(opts,k) for k in fieldnames(typeof(opts)))...)
    elseif variant===:alias;w.primal[w.basis.basic_indices[1]]=v.vector[1]
    end
   end
   checkpair(a,b,:A)
  end
  for variant in (:empty,:zeros,:views,:early_invalid),scope in (:norm,:init,:solve)
   a=fixture(T,8,:sparse,:positive,scope);b=fixture(T,8,:sparse,:positive,scope)
   if scope===:norm
    if variant===:empty;a=merge(a,(vector=T[],));b=merge(b,(vector=T[],))
    elseif variant===:zeros;fill!(a.vector,zero(T));fill!(b.vector,zero(T))
    elseif variant===:views;a=merge(a,(vector=@view(a.vector[1:2:end]),));b=merge(b,(vector=@view(b.vector[1:2:end]),))
    end
   elseif variant===:early_invalid
    a.w.basis.basic_indices[1]=1;b.w.basis.basic_indices[1]=1
   end
   checkpair(a,b,:B)
  end
  for variant in (:zero,:unbounded_bad,:short,:nonfinite,:tol512)
   a=fixture(T,16,:dense,:positive,:cert);b=fixture(T,16,:dense,:positive,:cert)
   for v in (a,b)
    if variant===:zero;fill!(v.rho,zero(T))
    elseif variant===:unbounded_bad;v.w.lower[1]=J._unbounded_bound(T)
    elseif variant===:short;resize!(v.rho,0)
    elseif variant===:nonfinite&&T<:AbstractFloat;v.rho[1]=T(NaN)
    elseif variant===:tol512&&T===BigFloat
     opts=v.w.options;v.w.options=typeof(opts)((k===:primal_tolerance ? setprecision(()->BigFloat(3//7),BigFloat,512) : getfield(opts,k) for k in fieldnames(typeof(opts)))...)
    end
   end
   x=checkpair(a,b,:C)
   variant in (:zero,:unbounded_bad)&&@test x==(:value,false)
  end
  if T===BigFloat
   values=(BigFloat(0),-BigFloat(0),BigFloat(1),BigFloat(-1),BigFloat(Inf),-BigFloat(Inf),BigFloat(NaN),floatmin(BigFloat),floatmax(BigFloat),setprecision(()->BigFloat(3//7),BigFloat,512),setprecision(()->BigFloat(-3//7),BigFloat,512))
   for x in values
    a=(scope=:norm,vector=[x]);b=(scope=:norm,vector=[deepcopy(x)]);r=checkpair(a,b,:B)
    if r[1]===:value
     result1=whole(Val(:B),b);result2=whole(Val(:B),b);@test result1[2]!==result2[2]
    end
   end
   for scope in (:snap,:step,:ratio,:cert)
    a=fixture(T,8,:dense,:mixed,scope);b=fixture(T,8,:dense,:mixed,scope)
    for v in (a,b)
     wide=setprecision(()->BigFloat(-3//7),BigFloat,512)
     v.w.primal[end]=wide;v.w.lower[end]=J.Bound(deepcopy(wide));v.w.upper[end]=J.Bound(setprecision(()->BigFloat(3//7),BigFloat,512))
    end
    checkpair(a,b,scope===:cert ? :C : :A)
   end
  end
 end
end

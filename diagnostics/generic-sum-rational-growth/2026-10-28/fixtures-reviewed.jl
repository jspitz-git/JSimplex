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
modof(::Val{:original})=SRGReference
modof(::Val{:A})=SRGA
modof(::Val{:B})=SRGB
modof(::Val{:C})=SRGC
statevalues(s)=Tuple(getfield(s,k) for k in fieldnames(typeof(s)))
function restorestate!(s,t)
 for (k,v) in zip(fieldnames(typeof(s)),t);setfield!(s,k,v);end
 nothing
end
function fixture(::Type{T},n,density,shape,scope;below=true,mode=:valid,chain=8) where T
 if scope in (:rows,:feasible)
  m=min(8,n);A=zeros(T,m,n)
  for j in 1:n,i in 1:m
   if density===:dense||(i+j)%5==0
    sign=shape===:negative||shape===:mixed&&isodd(j) ? -1 : 1
    A[i,j]=T(sign*((i+j)%7+1)//16)
   end
  end
  p=LinearProblem(sparse(A),zeros(T,n);row_lower=fill(-T(4096),m),row_upper=fill(T(4096),m),column_lower=fill(-T(4),n),column_upper=fill(T(4),n))
  x=fill(T(1//2),n)
  return (scope=scope,p=p,x=x,lower=zeros(T,m),upper=zeros(T,m),tol=zero(T))
 elseif scope===:cert
  m=min(8,n);A=zeros(T,m,n)
  for j in 1:n,i in 1:m
   if density===:dense||(i+j)%5==0||(i==1&&j==1)
    A[i,j]=shape===:wide && T===Rational{BigInt} ? T((big(1)<<127)+i+j,(big(1)<<63)+13) : T(((i+j)%7+1)//16)
   end
  end
  p=LinearProblem(sparse(A),zeros(T,n);column_lower=zeros(T,n),column_upper=fill(T(4),n),row_lower=fill(-T(8),m),row_upper=fill(T(8),m))
  o=SolverOptions(T;verbose=false,pricing=:dantzig,basis_update=:pfi)
  pol=J.NumericalPolicy(T;refactor_timing=false,solve_refinement=false,recovery=false)
  w=J._initialize_workspace_state(p,o;progress=J.SimplexProgressContext(p;numerical_policy=pol));rho=fill(T(1//8),m)
  endpoint=(below ? 1 : -1)*(mode===:invalid ? -1 : 1)*T(2)
  for j in 1:n
   w.lower[j]=Bound(endpoint);w.upper[j]=Bound(endpoint)
   if mode===:one_sided
    if below;w.upper[j]=J._unbounded_bound(T);else;w.lower[j]=J._unbounded_bound(T);end
   end
  end
  for j in n+1:n+m;w.lower[j]=Bound(zero(T));w.upper[j]=Bound(zero(T));end
  if mode===:zero_tol
   opts=w.options;w.options=typeof(opts)((k===:primal_tolerance ? zero(T) : getfield(opts,k) for k in fieldnames(typeof(opts)))...)
  end
  return (scope=scope,w=w,rho=rho,below=below,mode=mode)
 end
 # A real PFI and genuine replace_column! calls construct the packed update chain.
 p=LinearProblem(spdiagm(0=>ones(T,n)),zeros(T,n);row_lower=fill(-T(8),n),row_upper=fill(T(8),n))
 o=SolverOptions(T;verbose=false,basis_update=:pfi,refactorization_interval=20)
 pol=J.NumericalPolicy(T;simplex_strategy=:adaptive,refactor_timing=false,solve_refinement=false,recovery=false)
 w=J._initialize_workspace_state(p,o;progress=J.SimplexProgressContext(p;numerical_policy=pol))
 for k in 1:chain
  pivot=mod1(k,n);direction=zeros(T,n);pv=shape===:negative ? -T(1//2) : T(1//2);direction[pivot]=pv
  for i in 1:n
   i==pivot&&continue
   if density===:dense||mod(i+k,4)==0
    desired=shape===:negative||shape===:mixed&&isodd(i+k) ? -T((i%5+1)//8) : T((i%5+1)//8)
    direction[i]=-desired*pv
   end
  end
  J.replace_column!(w.factorization,direction,pivot;zero_tolerance=zero(T))
 end
 w.scratch.refactorization.metrics_update_count=-1
 return (scope=scope,w=w,initial=statevalues(w.scratch.refactorization),chain=chain)
end
function reset!(v)
 if v.scope in (:growth,:refresh,:scheduled);restorestate!(v.w.scratch.refactorization,v.initial);end
 nothing
end
@noinline function whole(tag::A,v::V) where {A,V}
 mod=modof(tag)
 if v.scope===:rows
  return eltype(v.x)<:Rational ? mod._primal_row_bounds(v.p.A,v.x,J._is_exact(eltype(v.x))) : mod._primal_row_bounds!(v.lower,v.upper,v.p.A,v.x)
 elseif v.scope===:feasible;return mod._original_primal_feasible(v.p,v.x,v.tol)
 elseif v.scope===:cert;return mod._infeasibility_certified(v.w,v.rho,v.below)
 elseif v.scope===:growth;return mod._factor_growth_measure(v.w.factorization)
 elseif v.scope===:refresh;return mod._refresh_refactor_metrics!(v.w;force=true)
 end
 mod._scheduled_refactor_reason(v.w,:dual)
end
function inputvalues(v)
 if v.scope in (:rows,:feasible)
  return (v.p.A.colptr,v.p.A.rowval,v.p.A.nzval,v.x,v.p.column_lower,v.p.column_upper,v.p.row_lower,v.p.row_upper,v.tol)
 end
 w=v.w
 arrays=((w.progress.start_ns,w.progress.iteration_offset,w.progress.refactorization_offset,w.progress.objective,w.progress.objective_constant),w.problem.A.colptr,w.problem.A.rowval,w.problem.A.nzval,w.costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states,w.primal,w.reduced_costs,w.pricing_weights,w.progress.scaling.row_factors,w.progress.scaling.column_factors)
 if v.scope===:cert;return (arrays,v.rho,statevalues(w.options),statevalues(w.progress.numerical_policy));end
 (arrays,Tuple((e.indices,e.values,e.pivot_row) for e in w.factorization.updates),w.factorization.work,Tuple(getfield(w.factorization.base.factorization,k) for k in fieldnames(typeof(w.factorization.base.factorization)) if getfield(w.factorization.base.factorization,k) isa AbstractArray{<:Real}),statevalues(w.options),statevalues(w.progress.numerical_policy))
end
function owners(x)
 if x isa BigFloat;return (x,)
 elseif x isa Rational{BigInt};return (numerator(x),denominator(x))
 elseif x isa J.Bound;return owners(x.value)
 elseif x isa AbstractArray;return (x,Tuple(owners(y) for y in x))
 elseif x isa Tuple;return Tuple(owners(y) for y in x)
 end
 nothing
end
sameowners(a,b)=a===b
sameowners(a::Tuple,b::Tuple)=length(a)==length(b)&&all(sameowners(x,y) for (x,y) in zip(a,b))
function checkpair(a,b,arm)
 va=deepcopy(inputvalues(a));vb=deepcopy(inputvalues(b));oa=owners(inputvalues(a));ob=owners(inputvalues(b));reset!(a);reset!(b)
 ambient=(precision(BigFloat),rounding(BigFloat));x=capture(()->whole(Val(:original),a));y=capture(()->whole(Val(arm),b));@test same(x,y);@test ambient==(precision(BigFloat),rounding(BigFloat))
 @test same(va,inputvalues(a));@test same(vb,inputvalues(b));@test sameowners(oa,owners(inputvalues(a)));@test sameowners(ob,owners(inputvalues(b)))
 if a.scope in (:growth,:refresh,:scheduled);@test same(statevalues(a.w.scratch.refactorization),statevalues(b.w.scratch.refactorization));end
 if a.scope===:rows && x[1]===:value && y[1]===:value
  if eltype(a.x)<:Rational
   @test x[2][1]===x[2][2];@test y[2][1]===y[2][2]
  else
   @test x[2][1]===a.lower&&x[2][2]===a.upper;@test y[2][1]===b.lower&&y[2][2]===b.upper
  end
 end
 x
end
resultkey(x::Bool)=Int(x)
resultkey(::Nothing)=0
resultkey(x::Symbol)=String(x)
resultkey(x::Real)=Float64(x)
resultkey(x::Tuple{<:AbstractArray,<:AbstractArray})=sum(Float64.(x[1]))+sum(Float64.(x[2]))
@noinline function timed(tag::A,v::V) where {A,V}
 t=@timed whole(tag,v);k=@timed resultkey(t.value)
 merge(cost(t),Dict("result"=>k.value,"capture_preparation"=>cost(k)))
end
function aliaspattern(x,a,b)
 x[1]===:value||return ()
 out=x[2]
 out isa Tuple||return ()
 Tuple((y===a,y===b, y isa BigFloat ? precision(y) : 0) for y in out)
end
function correctness(::Type{T}) where T
 @testset "ordinary whole functions $(T)" begin
  for shape in (:positive,:negative,:mixed),density in (:sparse,:dense),scope in (:rows,:feasible)
   a=fixture(T,16,density,shape,scope);b=fixture(T,16,density,shape,scope);out=checkpair(a,b,:A);@test out[1]===:value
   if scope===:feasible
    @test out[2]===true
    a.p.row_lower[1]=Bound(T(8192));b.p.row_lower[1]=Bound(T(8192));@test checkpair(a,b,:A)[2]===false
   else
    exact=Rational{BigInt}.(a.p.A)*Rational{BigInt}.(a.x)
    @test all(Rational{BigInt}(out[2][1][i])<=exact[i]<=Rational{BigInt}(out[2][2][i]) for i in eachindex(exact))
   end
  end
  for below in (true,false),mode in (:valid,:invalid,:one_sided,:zero_tol),shape in (T===Rational{BigInt} ? (:positive,:wide) : (:positive,))
   a=fixture(T,16,:sparse,shape,:cert;below,mode);b=fixture(T,16,:sparse,shape,:cert;below,mode)
   @test checkpair(a,b,:B)==(:value,mode!==:invalid)
  end
  for chain in (0,1,4,8,32),shape in (:positive,:negative,:mixed),scope in (:growth,:refresh,:scheduled)
   a=fixture(T,8,:sparse,shape,scope;chain);b=fixture(T,8,:sparse,shape,scope;chain)
   out=checkpair(a,b,:C);@test out[1]===:value
   if scope===:growth;@test out[2]==(chain==0 ? one(T) : T(2));end
   if scope!==:growth
    @test a.w.scratch.refactorization.nupdates==chain
   end
  end
  for aa in (T(1),-T(1),zero(T)),bb in (T(1),-T(1),zero(T))
   x=capture(()->SRGReference._primal_sum_bounds(aa,bb));y=capture(()->SRGA._primal_sum_bounds(aa,bb));@test same(x,y);@test aliaspattern(x,aa,bb)==aliaspattern(y,aa,bb)
   @test x[1]===:value&&x[2][1]<=aa+bb<=x[2][2]
  end
 end
end

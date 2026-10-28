using Test,JSimplex,SparseArrays,LinearAlgebra,Statistics
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
modof(::Val{:original})=EBAReference
modof(::Val{:A})=EBAA
modof(::Val{:B})=EBAB
modof(::Val{:C})=EBAC
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a))
same(a::J.Bound,b::J.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
statevalues(s)=Tuple(getfield(s,k) for k in fieldnames(typeof(s)))
function owners(x)
 x isa BigFloat&&return (x,)
 x isa Rational{BigInt}&&return (numerator(x),denominator(x))
 x isa J.Bound&&return owners(x.value)
 x isa AbstractArray&&return (x,Tuple(owners(y) for y in x))
 x isa Tuple&&return Tuple(owners(y) for y in x)
 nothing
end
sameowners(a,b)=a===b
sameowners(a::Tuple,b::Tuple)=length(a)==length(b)&&all(sameowners(x,y) for (x,y) in zip(a,b))
no_stop()=false
function fixture(::Type{T},n,density,shape,scope;mode=:good,observer=nothing) where T
 m=n==0 ? 0 : min(scope===:auxiliary ? 4 : 8,n÷2)
 native_bounds=scope===:errors&&startswith(String(mode),"native_");S=native_bounds ? Float64 : T
 actual_mode=Symbol(replace(String(mode),"native_"=>""));A=zeros(S,m,n)
 for j in 1:n,i in 1:m
  if i==j;A[i,j]=S(4)
  elseif density===:dense||i==mod1(j,m);A[i,j]=S(1//16);end
 end
 lo=fill(Bound(zero(S)),n+m);hi=[J._unbounded_bound(S) for _ in 1:n+m]
 if scope===:errors
  for j in 1:n+m
   which=actual_mode===:mixed ? (:free,:lower,:box,:upper)[mod1(j,4)] : actual_mode
   lo[j]=which===:free||which===:upper ? J._unbounded_bound(S) : Bound(zero(S))
   hi[j]=which===:box ? Bound(one(S)) : which in (:upper,:fixed) ? Bound(zero(S)) : J._unbounded_bound(S)
  end
 else
  for i in n+1:n+m;hi[i]=lo[i];end
 end
 p=LinearProblem(sparse(A),zeros(S,n);column_lower=lo[1:n],column_upper=hi[1:n],row_lower=lo[n+1:end],row_upper=hi[n+1:end])
 options=SolverOptions(S;verbose=false,presolve=false,scaling=:off,basis_update=:pfi,pricing=:dantzig,time_limit=Inf,iteration_limit=20,partial_pricing=false)
 policy=J.NumericalPolicy(S;lp_refinement=true,precision_boosting=false,crash=false,solve_refinement=false,recovery=false,refactor_timing=false,adaptive_pricing=false)
 diag=isnothing(observer) ? nothing : J.SimplexDiagnostics(;observer)
 w=J._initialize_workspace_state(p,options;progress=J.SimplexProgressContext(p;diagnostics=diag,numerical_policy=policy))
 if scope===:direction
  w.basis=J.Basis(collect(1:m),vcat(fill(J.BASIC,m),fill(J.AT_LOWER,n)))
  J.recompute!(w;refactorize=true)
  direction=T[(shape===:negative||shape===:mixed&&isodd(i) ? -1 : 1)*(i%5+1)//8 for i in 1:m]
  rhs=w.problem.A[:,1:m]*direction
  mode===:bad&&!isempty(rhs)&&(rhs[1]+=one(T))
  return (scope=scope,w=w,direction=direction,rhs=rhs,pivot=one(T))
 elseif scope===:errors
  N=n+m;prices=T[(shape===:negative ? -1 : shape===:mixed&&isodd(j) ? -1 : 1)//2 for j in 1:N]
  r=J.LPResiduals(zeros(T,N),zeros(T,m),fill(T(1//4),m),prices)
  return (scope=scope,w=w,r=r,mode=actual_mode)
 end
 J.recompute!(w)
 residuals=J._lp_residuals(w,w.primal,zeros(T,m));sp,sd=J._lp_correction_scales(w,residuals)
 problem,map=J.build_correction_problem(w,residuals,sp,sd)
 budget=Ref(J.SimplexRunBudget(w));stop=J._guard_stop_callback(no_stop)
 return (scope=scope,w=w,problem=problem,map=map,budget=budget,policy=policy,stop=stop)
end
function reset!(v)
 if v.scope===:direction;copyto!(v.w.scratch.row_rhs,v.rhs)
 elseif v.scope===:auxiliary;v.budget[]=J.SimplexRunBudget(v.w);end
 nothing
end
@noinline function whole(tag::A,v::V) where {A,V}
 m=modof(tag)
 v.scope===:direction&&return m._dual_direction_residual_ok!(v.w,v.direction,v.pivot)
 v.scope===:errors&&return m._lp_errors(v.w,v.r)
 m._lp_auxiliary_run_at_working_precision(v.w,v.problem,v.map,v.budget[],v.policy,v.stop)
end
function resultkey(x)
 x isa Bool&&return x
 if x isa Tuple&&length(x)==3&&x[1] isa Number;return sum(Float64,x);end
 aux,run,witness=x
 isnothing(run)&&return -1
 Int(run.status)
end
@noinline function timed(tag::A,v::V) where {A,V}
 t=@timed whole(tag,v);k=@timed resultkey(t.value)
 merge(cost(t),Dict("result"=>k.value,"capture_preparation"=>cost(k)))
end
function inputvalues(v)
 w=v.w
 base=(w.problem.A.colptr,w.problem.A.rowval,w.problem.A.nzval,w.problem.objective,w.problem.column_lower,w.problem.column_upper,w.problem.row_lower,w.problem.row_upper,w.basis.basic_indices,w.basis.states,w.costs,w.lower,w.upper,w.primal,w.reduced_costs,w.pricing_weights,w.progress.start_ns,w.progress.iteration_offset,w.progress.refactorization_offset,statevalues(w.options),statevalues(w.progress.numerical_policy))
 v.scope===:direction&&return (base,v.direction,v.rhs,v.pivot)
 v.scope===:errors&&return (base,v.r.values,v.r.multipliers,v.r.primal,v.r.dual)
 p=v.problem
 (base,p.A.colptr,p.A.rowval,p.A.nzval,p.objective,p.column_lower,p.column_upper,p.row_lower,p.row_upper,v.map.original_to_correction,v.map.correction_to_original,v.map.fixed_activities,v.map.primal_scale,v.map.dual_scale)
end
function outputstate(v)
 v.scope===:direction&&return (v.w.scratch.tau,v.w.scratch.row_rhs)
 v.scope===:auxiliary&&return (v.budget[].iterations,v.budget[].refactorizations,v.budget[].start_ns==v.w.progress.start_ns,v.budget[].time_limit_seconds,v.budget[].iteration_limit)
 nothing
end
function auxvalue(x)
 a,r,y=x
 isnothing(a)&&return x
 (a.basis.basic_indices,a.basis.states,a.primal,a.reduced_costs,a.costs,a.lower,a.upper,a.pricing_weights,a.iterations,a.refactorizations,statevalues(a.options),statevalues(a.progress.numerical_policy),r.status,r.objective_value,r.primal,r.iterations,r.refactorizations,r.message,isnothing(r.basis) ? nothing : (r.basis.basic_indices,r.basis.states),y)
end
scalarleaves(x::BigFloat)=(x,)
scalarleaves(x::Rational{BigInt})=(numerator(x),denominator(x))
scalarleaves(x)=()
function metricgraph(v,x)
 nodes=(v.r.values...,v.r.multipliers...,v.r.primal...,v.r.dual...)
 inputs=Tuple(leaf for node in nodes for leaf in scalarleaves(node))
 outputs=Tuple(leaf for node in x for leaf in scalarleaves(node))
 (Tuple(Tuple(a===b for b in inputs) for a in outputs),Tuple(a===b for a in outputs for b in outputs))
end
function auxowners(v,x)
 a,r,y=x
 isnothing(a)&&return false
 a.basis.basic_indices!==v.w.basis.basic_indices&&a.basis.states!==v.w.basis.states&&a.primal!==v.w.primal&&a.costs!==v.w.costs&&a.lower!==v.w.lower&&a.upper!==v.w.upper&&a.progress.start_ns==v.w.progress.start_ns
end
function checkpair(a,b,arm)
 reset!(a);reset!(b);va=deepcopy(inputvalues(a));vb=deepcopy(inputvalues(b));oa=owners(inputvalues(a));ob=owners(inputvalues(b));ambient=(precision(BigFloat),rounding(BigFloat))
 x=capture(()->whole(Val(:original),a));y=capture(()->whole(Val(arm),b))
 xx=x[1]===:value&&a.scope===:auxiliary ? (:value,auxvalue(x[2])) : x
 yy=y[1]===:value&&b.scope===:auxiliary ? (:value,auxvalue(y[2])) : y
 @test same(xx,yy)
 @test ambient==(precision(BigFloat),rounding(BigFloat))
 @test same(va,inputvalues(a));@test same(vb,inputvalues(b));@test sameowners(oa,owners(inputvalues(a)));@test sameowners(ob,owners(inputvalues(b)))
 @test same(outputstate(a),outputstate(b))
 if a.scope===:errors&&x[1]===:value;@test metricgraph(a,x[2])==metricgraph(b,y[2]);end
 if a.scope===:auxiliary&&x[1]===:value
  @test !isnothing(x[2][2])&&x[2][2].status==J.OPTIMAL&&y[2][2].status==J.OPTIMAL
  @test auxowners(a,x[2])&&auxowners(b,y[2])
  @test all(iszero,x[2][1].primal)&&all(iszero,y[2][1].primal)&&all(iszero,x[2][3])&&all(iszero,y[2][3])
 end
 x
end
function correctness(::Type{T}) where T
 @testset "Epsilon bound auxiliary $(T)" begin
  if T<:AbstractFloat
   for density in (:sparse,:dense),shape in (:positive,:negative,:mixed),mode in (:good,:bad)
    a=fixture(T,8,density,shape,:direction;mode);b=fixture(T,8,density,shape,:direction;mode);r=checkpair(a,b,:A)
    @test r[1]===:value;@test r[2]==(mode===:good)
   end
   a=fixture(T,8,:dense,:mixed,:direction);b=fixture(T,8,:dense,:mixed,:direction);a.direction[1]=T(Inf);b.direction[1]=T(Inf)
   @test checkpair(a,b,:A)[2]===false
   for tag in (Val(:original),Val(:A))
    a=fixture(T,8,:dense,:mixed,:direction);resize!(a.direction,1);@test_throws DimensionMismatch whole(tag,a)
    a=fixture(T,8,:sparse,:mixed,:direction);a.w.basis.basic_indices[1]=100;@test_throws BoundsError whole(tag,a)
   end
  end
  for mode in (:free,:lower,:upper,:box,:fixed,:mixed),shape in (:positive,:negative,:mixed)
   a=fixture(T,8,:sparse,shape,:errors;mode);b=fixture(T,8,:sparse,shape,:errors;mode);r=checkpair(a,b,:B)
   @test r[1]===:value
   @test r[2][1]==T(1//4)
   if mode===:fixed;@test r[2][2]==0&&r[2][3]==0;end
   if mode===:free;@test r[2][2]==T(1//2)&&r[2][3]==T(1//2);end
  end
  if T<:AbstractFloat
  for density in (:sparse,:dense)
   a=fixture(T,8,density,:positive,:auxiliary);b=fixture(T,8,density,:positive,:auxiliary);r=checkpair(a,b,:C)
   @test r[1]===:value
   reset!(a);r2=whole(Val(:original),a);@test r[2][1].basis.basic_indices!==r2[1].basis.basic_indices&&r[2][1].basis.states!==r2[1].basis.states
   reset!(b);s1=whole(Val(:C),b);reset!(b);s2=whole(Val(:C),b);@test s1[1].basis.basic_indices!==s2[1].basis.basic_indices&&s1[1].basis.states!==s2[1].basis.states
  end
  for tag in (Val(:original),Val(:C))
   a=fixture(T,8,:sparse,:positive,:auxiliary);before=deepcopy(inputvalues(a));stop=J._guard_stop_callback(()->true)
   out=modof(tag)._lp_auxiliary_run_at_working_precision(a.w,a.problem,a.map,a.budget[],a.policy,stop)
   @test out===(nothing,nothing,nothing);@test same(before,inputvalues(a))
  end
  else
   for tag in (Val(:original),Val(:C))
    a=fixture(T,8,:sparse,:positive,:auxiliary);before=deepcopy(inputvalues(a));own=owners(inputvalues(a));budget=outputstate(a)
    @test_throws MethodError whole(tag,a)
    @test same(before,inputvalues(a))
    @test sameowners(own,owners(inputvalues(a)))
    @test same(budget,outputstate(a))
   end
  end
  for scope in (:errors,:direction)
   scope===:direction&&!(T<:AbstractFloat)&&continue
   a=fixture(T,0,:sparse,:positive,scope;mode=scope===:errors ? :free : :good);b=fixture(T,0,:sparse,:positive,scope;mode=scope===:errors ? :free : :good)
   r=checkpair(a,b,scope===:direction ? :A : :B);@test r[1]===:value
   @test scope===:direction ? r[2]===true : all(iszero,r[2])
  end
  if T===Float64||T===BigFloat
   for tag in (Val(:original),Val(:C)),expired in (false,true)
    a=fixture(T,8,:sparse,:positive,:auxiliary);before=deepcopy(inputvalues(a));budget=a.budget[]
    budget.time_limit_seconds=expired ? 0.0 : 1e9
    expired&&(budget.start_ns=UInt64(0))
    initial=(budget.start_ns,budget.iterations,budget.refactorizations)
    stop=J._guard_stop_callback(()->J._budget_expired(budget))
    out=modof(tag)._lp_auxiliary_run_at_working_precision(a.w,a.problem,a.map,budget,a.policy,stop)
    @test expired ? out===(nothing,nothing,nothing) : !isnothing(out[2])&&out[2].status==J.OPTIMAL
    @test expired ? (budget.start_ns,budget.iterations,budget.refactorizations)==initial : out[1].options.time_limit==1e9&&out[1].progress.start_ns==budget.start_ns==initial[1]
    @test same(before,inputvalues(a))
   end
   for tag in (Val(:original),Val(:C))
    sentinel=ErrorException("EBA observer sentinel");held=Ref{Any}(nothing)
    observer=(reason,ws)->begin
     if reason===:refactor_other;held[]=ws;throw(sentinel);end
     nothing
    end
    a=fixture(T,8,:sparse,:positive,:auxiliary;observer);before=deepcopy(inputvalues(a));reset!(a)
    caught=try;whole(tag,a);nothing;catch e;e;end
    @test caught isa J.DiagnosticObserverFailure&&caught.cause===sentinel
    @test a.budget[].refactorizations>=1
    @test !isnothing(held[])&&held[].basis.basic_indices!==a.w.basis.basic_indices&&held[].basis.states!==a.w.basis.states
    @test same(before,inputvalues(a))
   end
  end
  if T===BigFloat
   a=fixture(T,8,:dense,:mixed,:direction);b=fixture(T,8,:dense,:mixed,:direction)
   z=setprecision(BigFloat,512) do;1+ldexp(BigFloat(1),-400);end
   a.direction[2]=z;b.direction[2]=deepcopy(z);@test checkpair(a,b,:A)[1]===:value
   for mode in (:native_free,:native_mixed)
    a=fixture(T,8,:sparse,:mixed,:errors;mode);b=fixture(T,8,:sparse,:mixed,:errors;mode);@test checkpair(a,b,:B)[1]===:value
   end
  end
 end
 nothing
end

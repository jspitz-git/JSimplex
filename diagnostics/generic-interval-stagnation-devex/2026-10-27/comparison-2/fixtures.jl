using Test,JSimplex,SparseArrays,LinearAlgebra
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
same(x,y)=isequal(x,y)
same(x::BigFloat,y::BigFloat)=isequal(x,y)&&precision(x)==precision(y)&&signbit(x)==signbit(y)
same(x::Tuple,y::Tuple)=length(x)==length(y)&&all(same(a,b) for (a,b) in zip(x,y))
same(x::AbstractArray,y::AbstractArray)=axes(x)==axes(y)&&all(same(x[i],y[i]) for i in eachindex(x,y))
same(x::J.Bound,y::J.Bound)=x.bounded==y.bounded&&same(x.value,y.value)
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
modof(arm)=arm===:original ? ISDReference : arm===:A ? ISDA : arm===:B ? ISDB : ISDC
function matrixof(::Type{T},n,m,density,shape) where T
 a=zeros(T,m,n)
 for j in 1:n,i in 1:m
  if density===:dense||(i+j)%5==0
   sign=shape===:negative||shape===:mixed&&iseven(i+j) ? -1 : 1
   a[i,j]=T(sign*((i+j)%7+2)//16)
  end
 end
 sparse(a)
end
function workof(::Type{T},n,m,density,shape;observer=nothing) where T
 A=matrixof(T,n,m,density,shape)
 p=LinearProblem(A,T[(i%5-2)//8 for i in 1:n];column_lower=zeros(T,n),column_upper=fill(T(4),n),row_lower=fill(-T(16),m),row_upper=fill(T(16),m))
 opt=SolverOptions(T;algorithm=:dual,pricing=:devex,partial_pricing=false,verbose=false)
 pol=J.NumericalPolicy(T;adaptive_stalling=true,stagnation_window=4,refactor_timing=false,solve_refinement=false,recovery=false)
 diag=isnothing(observer) ? nothing : J.SimplexDiagnostics(;observer)
 J.initialize_workspace(p,opt;progress=J.SimplexProgressContext(p;numerical_policy=pol,diagnostics=diag))
end
monitorseed(s)=(state=Tuple(getfield(s,k) for k in fieldnames(typeof(s))),monitor=Tuple(getfield(s.monitor,k) for k in fieldnames(typeof(s.monitor))))
function restoremonitor!(s,seed)
 for (i,k) in enumerate(fieldnames(typeof(s)));k===:monitor||setfield!(s,k,seed.state[i]);end
 for (i,k) in enumerate(fieldnames(typeof(s.monitor)));setfield!(s.monitor,k,seed.monitor[i]);end
 nothing
end
function fixture(::Type{T},n,m,scope,density,shape;observer=nothing) where T
 if scope in (:rows,:feasible,:reduced,:witness)
  A=matrixof(T,n,m,density,shape);x=T[(j%3+1)//8 for j in 1:n];y=T[(i%3+1)//16 for i in 1:m];c=transpose(A)*y;b=A*x
  p=LinearProblem(A,c;column_lower=zeros(T,n),column_upper=fill(T(2),n),row_lower=b,row_upper=copy(b))
  states=fill(J.AT_LOWER,n+m);states[1:m].=J.BASIC;basis=J.Basis(collect(1:m),states)
  opt=SolverOptions(T;verbose=false)
  return (scope=scope,p=p,x=x,y=y,basis=basis,opt=opt)
 elseif scope in (:new,:cold,:rebase)
  w=workof(T,n,m,density,shape;observer)
  for i in eachindex(w.primal)
   sign=shape===:negative||shape===:mixed&&iseven(i) ? -1 : 1
   w.primal[i]=T(sign*(i%3+1)//4);w.costs[i]=T(sign*(i%5+1)//8)
   w.lower[i]=J.Bound(T(sign===1 ? 1 : -4));w.upper[i]=J.Bound(T(sign===1 ? 4 : -1))
  end
  w.iterations=1;J._observe_stagnation!(w,:dual,zero(T),zero(T));s=w.scratch.stagnation
  scope===:rebase&&(w.costs[1]=w.costs[1]+T(1//32))
  return (scope=scope,w=w,state=s,seed=monitorseed(s),steps=zeros(T,2))
 elseif scope===:leaving
  return (scope=scope,weight=T(3//2),pivot=T(shape===:negative ? -3//4 : 3//4))
 else
  w=workof(T,n,m,density,shape)
  for j in eachindex(w.pricing_weights);w.pricing_weights[j]=T(2+j//32);end
  return (scope=scope,w=w,weights=copy(w.pricing_weights),pivot=T(shape===:negative ? -3//4 : 3//4))
 end
end
function reset!(v)
 if v.scope in (:new,:cold,:rebase)
  v.w.scratch.stagnation=v.scope===:cold ? nothing : v.state;restoremonitor!(v.state,v.seed);v.w.iterations=2
 elseif v.scope in (:devex_shared,:devex_solve)
  copyto!(v.w.pricing_weights,v.weights)
  # Same genuine BTRAN/price preparation for the shared consumer, outside window.
  if v.scope===:devex_shared
   unit=J._pipeline_unit_rhs!(v.w,1);rho=J._checked_basis_solve!(v.w.scratch.rho,v.w,unit;transposed=true,operation=:weight_btran,unit_row=1);J.price!(v.w.scratch.tableau_row,v.w,rho)
  end
 end
 nothing
end
@noinline function whole(::Val{arm},::Val{scope},v) where {arm,scope}
 mod=modof(arm)
 if scope===:rows;return mod._primal_row_bounds(v.p.A,v.x,J._is_exact(eltype(v.x)))
 elseif scope===:feasible;return mod._original_primal_feasible(v.p,v.x,v.opt.primal_tolerance)
 elseif scope===:reduced;return mod._original_reduced_cost_bounds(v.p,v.y)
 elseif scope===:witness;return mod._original_witness_certified(v.p,v.opt,v.basis,v.x,v.y)
 elseif scope===:new;return mod._new_workspace_stagnation(v.w,UInt(0),:dual)
 elseif scope in (:cold,:rebase);return mod._observe_stagnation!(v.w,:dual,v.steps[1],v.steps[2])
 elseif scope===:leaving;return mod._primal_devex_leaving_weight(v.weight,v.pivot)
 end
 mod._primal_update_devex!(v.w,1,1,v.pivot;shared_row=scope===:devex_shared)
end
sink(x::Bool)=Int(x)
sink(::Nothing)=1
sink(x::Symbol)=x===:progress ? 1 : x===:watch ? 2 : x===:stalled ? 3 : 4
sink(x::J.WorkspaceStagnation)=Int(x.monitor.window_count==0)
sink(x::Real)=Int(isfinite(x))
sink(x::Tuple{<:AbstractVector,<:AbstractVector})=Int(length(x[1])+length(x[2]))
@noinline runwhole(a,s,v)=sink(whole(a,s,v))
function timed(a::A,s::S,v::V) where {A,S,V}
 t=@timed runwhole(a,s,v);merge(cost(t),Dict("sink"=>t.value))
end
function inputs(v)
 if v.scope in (:rows,:feasible,:reduced,:witness)
  p=v.p;return (p.A.colptr,p.A.rowval,p.A.nzval,p.objective,p.column_lower,p.column_upper,p.row_lower,p.row_upper,v.x,v.y,v.basis.basic_indices,v.basis.states)
 elseif v.scope===:leaving;return ([v.weight,v.pivot],)
 end
 w=v.w;(w.problem.A.colptr,w.problem.A.rowval,w.problem.A.nzval,w.costs,w.primal,w.reduced_costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states)
end
snapshot(v)=(inputs(v),map(copy,inputs(v)),deepcopy(inputs(v)))
function intact(v,s)
 a=inputs(v);all((v.scope===:leaving||a[i]===s[1][i])&&same(a[i],s[3][i])&&all(a[i][j]===s[2][i][j] for j in eachindex(a[i])) for i in eachindex(a))
end
function monout(s)
 isnothing(s) ? nothing : (Tuple(getfield(s.monitor,k) for k in fieldnames(typeof(s.monitor))),s.last_iteration,s.cost_scale,s.value_scale)
end
function outputs(v,z)
 v.scope===:new&&return monout(z)
 v.scope in (:cold,:rebase)&&return monout(v.w.scratch.stagnation)
 v.scope in (:devex_shared,:devex_solve)&&return (v.w.pricing_weights,v.w.scratch.tableau_row,v.w.scratch.rho,v.w.iterations,v.w.refactorizations,v.w.basis.basic_indices,v.w.basis.states,v.w.scratch.steepest_valid)
 z
end
function checkpair(a,b,arm)
 reset!(a);reset!(b);sa=snapshot(a);sb=snapshot(b);ctx=(precision(BigFloat),rounding(BigFloat))
 x=capture(()->whole(Val(:original),Val(a.scope),a));y=capture(()->whole(Val(arm),Val(b.scope),b))
 @test same(x[1],y[1]);@test x[1]===:value
 if x[1]===:value;@test same(outputs(a,x[2]),outputs(b,y[2]));end
 @test intact(a,sa)&&intact(b,sb)
 @test ctx==(precision(BigFloat),rounding(BigFloat))
 x
end
function exact_enclosure(mod,a,b,op)
 out=op===:sum ? mod._primal_sum_bounds(a,b) : mod._primal_product_bounds(a,b)
 q=op===:sum ? Rational{BigInt}(a)+Rational{BigInt}(b) : Rational{BigInt}(a)*Rational{BigInt}(b)
 @test out[1]<=q<=out[2]
 out
end
function aliaspattern(out,a,b)
 (out[1]===a,out[1]===b,out[2]===a,out[2]===b,out[1]===out[2])
end
function correctness(::Type{T}) where T
 @testset "Interval setup Devex correctness $T" begin
  for scope in (:rows,:feasible,:reduced,:witness),shape in (:positive,:negative,:mixed),density in (:sparse,:dense)
   a=fixture(T,8,4,scope,density,shape);b=fixture(T,8,4,scope,density,shape);z=checkpair(a,b,:A)
   scope in (:feasible,:witness)&&@test z[2]===true
   if scope===:rows
    q=Rational{BigInt}.(a.p.A)*Rational{BigInt}.(a.x);@test all(z[2][1].<=q.<=z[2][2])
   elseif scope===:reduced
    q=Rational{BigInt}.(a.p.objective)-transpose(Rational{BigInt}.(a.p.A))*Rational{BigInt}.(a.y);@test all(z[2][1][1:8].<=q.<=z[2][2][1:8])
   elseif scope===:feasible
    a.x[1]=T(3);b.x[1]=T(3);@test !whole(Val(:original),Val(scope),a)&&!whole(Val(:A),Val(scope),b)
   elseif scope===:witness
    a.y[1]+=T(1);b.y[1]+=T(1);@test !whole(Val(:original),Val(scope),a)&&!whole(Val(:A),Val(scope),b)
   end
  end
  for op in (:sum,:product),(u,v) in ((0,1),(1,0),(1,-1),(-1,1),(3//8,5//16),(-3//8,5//16),(-3//8,-5//16),(3//8,-5//16))
   a,b=T(u),T(v);x=exact_enclosure(ISDReference,a,b,op);y=exact_enclosure(ISDA,a,b,op);@test same(x,y);T===BigFloat&&@test aliaspattern(x,a,b)==aliaspattern(y,a,b)
  end
  for scope in (:new,:cold,:rebase),shape in (:positive,:negative,:mixed),density in (:sparse,:dense)
   a=fixture(T,8,4,scope,density,shape);b=fixture(T,8,4,scope,density,shape);checkpair(a,b,:B)
  end
  for scope in (:devex_shared,:devex_solve,:leaving),shape in (:positive,:negative,:mixed),density in (:sparse,:dense)
   a=fixture(T,8,4,scope,density,shape);b=fixture(T,8,4,scope,density,shape);checkpair(a,b,:C)
  end
  for w in (T(0),T(1//2),T(2),T(-2)),p in (T(0),T(1),T(-1),T(3//4),T(-3//4))
   @test same(capture(()->ISDReference._primal_devex_leaving_weight(w,p)),capture(()->ISDC._primal_devex_leaving_weight(w,p)))
  end
  if T===BigFloat
   special=(BigFloat(0),-BigFloat(0),BigFloat(Inf),-BigFloat(Inf),BigFloat(NaN),floatmin(BigFloat),floatmax(BigFloat),ldexp(BigFloat(1),-300))
   for a in special,b in (BigFloat(0),-BigFloat(0),BigFloat(1),BigFloat(-1),BigFloat(3//4)),op in (:sum,:product)
    f=op===:sum ? :_primal_sum_bounds : :_primal_product_bounds
    x=capture(()->getfield(ISDReference,f)(a,b));y=capture(()->getfield(ISDA,f)(a,b));@test same(x,y)
   end
   for w in special,p in special
    @test same(capture(()->ISDReference._primal_devex_leaving_weight(w,p)),capture(()->ISDC._primal_devex_leaving_weight(w,p)))
   end
   high=setprecision(BigFloat,512) do;BigFloat(1)+ldexp(BigFloat(1),-300);end
   for a in (high,-high),b in (BigFloat(1),BigFloat(-1),BigFloat(3//8)),op in (:sum,:product)
    f=op===:sum ? :_primal_sum_bounds : :_primal_product_bounds;x=getfield(ISDReference,f)(a,b);y=getfield(ISDA,f)(a,b);@test same(x,y);@test aliaspattern(x,a,b)==aliaspattern(y,a,b)
    if all(isfinite,x);exact_enclosure(ISDReference,a,b,op);exact_enclosure(ISDA,a,b,op);end
   end
   # BigFloat outputs must remain invocation-owned, never cached mutable constants.
   for mod in (ISDReference,ISDC),w in (BigFloat(1//2),BigFloat(2),floatmax(BigFloat)),p in (BigFloat(1),BigFloat(-1),floatmin(BigFloat))
    a=mod._primal_devex_leaving_weight(w,p);b=mod._primal_devex_leaving_weight(w,p);@test a!==b&&a!==w&&a!==p
   end
  end
 end
end
function boundary_correctness(::Type{T}) where T
 @testset "Scale owners callbacks and empty bounds $T" begin
  for mod in (ISDReference,ISDB)
   v=fixture(T,4,2,:new,:sparse,:positive);v.w.costs[1]=T(7);v.w.primal[1]=T(9);v.w.upper[1]=J.Bound(T(11))
   a=mod._new_workspace_stagnation(v.w,UInt(0),:dual);b=mod._new_workspace_stagnation(v.w,UInt(0),:dual)
   @test a!==b&&a.monitor!==b.monitor
   @test same(a.cost_scale,T(7))&&same(a.value_scale,T(11))
   if T===BigFloat;@test a.cost_scale===v.w.costs[1]&&a.value_scale===v.w.upper[1].value;end
  end
  for action in (:mutate,:throw)
   sentinel=ErrorException("ISD rebase sentinel");counts=[Ref(0),Ref(0)]
   obs(k)=(reason,w)->begin
    if reason===:stagnation_cost_rebase
     counts[k][]+=1
     action===:throw&&throw(sentinel)
     w.primal[1]+=T(1//16)
    end
    nothing
   end
   a=fixture(T,4,2,:rebase,:dense,:mixed;observer=obs(1));b=fixture(T,4,2,:rebase,:dense,:mixed;observer=obs(2));olda=a.state;oldb=b.state
   reset!(a);reset!(b);ea=Ref{Any}(nothing);eb=Ref{Any}(nothing)
   x=try;ISDReference._observe_stagnation!(a.w,:dual,a.steps...);catch e;ea[]=e;nothing;end
   y=try;ISDB._observe_stagnation!(b.w,:dual,b.steps...);catch e;eb[]=e;nothing;end
   @test counts[1][]==counts[2][]==1
   @test a.w.scratch.stagnation===olda&&b.w.scratch.stagnation===oldb
   @test same(monout(olda),monout(oldb))&&same(a.w.primal,b.w.primal)
   if action===:throw
    @test ea[] isa J.DiagnosticObserverFailure&&eb[] isa J.DiagnosticObserverFailure
    @test ea[].cause===sentinel&&eb[].cause===sentinel
   else
    @test ea[]===eb[]===nothing&&x===y
   end
  end
  for n in (0,1),m in (0,1)
   m>n&&continue
   for scope in (:rows,:feasible,:reduced,:witness)
    a=fixture(T,n,m,scope,:sparse,:mixed);b=fixture(T,n,m,scope,:sparse,:mixed);checkpair(a,b,:A)
   end
  end
  if T===BigFloat
   for x in (BigFloat(Inf),-BigFloat(Inf),BigFloat(NaN),-BigFloat(0))
    a=fixture(T,4,2,:new,:sparse,:mixed);b=fixture(T,4,2,:new,:sparse,:mixed);a.w.costs[1]=x;b.w.costs[1]=copy(x)
    xa=capture(()->ISDReference._new_workspace_stagnation(a.w,UInt(0),:dual));xb=capture(()->ISDB._new_workspace_stagnation(b.w,UInt(0),:dual))
    @test xa[1]===xb[1]
    if xa[1]===:error;@test same(xa,xb)
    else;@test same(monout(xa[2]),monout(xb[2]))
    end
   end
  end
 end
end

function mixed_precision_correctness(::Type{T}) where T
 T===BigFloat||return nothing
 @testset "Actual stored-512 workspace and Devex boundaries" begin
  high(k,sg)=setprecision(BigFloat,512) do;sg*(BigFloat(k)+ldexp(BigFloat(1),-300));end
  for sg in (1,-1),scope in (:new,:cold,:rebase)
   a=fixture(T,4,2,scope,:dense,:mixed);b=fixture(T,4,2,scope,:dense,:mixed)
   for v in (a,b)
    w=v.w;w.costs[1]=high(6,sg);w.primal[1]=high(9,sg);w.lower[1]=J.Bound(high(11,-1));w.upper[1]=J.Bound(high(11,1))
    w.scratch.stagnation=nothing;w.iterations=1;J._observe_stagnation!(w,:dual,v.steps...)
   end
   a=merge(a,(state=a.w.scratch.stagnation,seed=monitorseed(a.w.scratch.stagnation)));b=merge(b,(state=b.w.scratch.stagnation,seed=monitorseed(b.w.scratch.stagnation)))
   if scope===:rebase;a.w.costs[1]=high(7,sg);b.w.costs[1]=high(7,sg);end
   sa=snapshot(a);sb=snapshot(b);x=checkpair(a,b,:B)
   sx=scope===:new ? x[2] : a.w.scratch.stagnation
   sy=scope===:new ? whole(Val(:B),Val(:new),b) : b.w.scratch.stagnation
   @test precision(sx.cost_scale)==precision(sy.cost_scale)==precision(BigFloat)
   @test precision(sx.value_scale)==precision(sy.value_scale)==precision(BigFloat)
   for (v,s) in ((a,sx),(b,sy))
    @test s.cost_scale!==v.w.costs[1]
    @test s.value_scale!==v.w.primal[1]&&s.value_scale!==v.w.upper[1].value&&s.value_scale!==v.w.lower[1].value
   end
   @test intact(a,sa)&&intact(b,sb)
   if scope===:new
    xx=ISDReference._new_workspace_stagnation(a.w,UInt(0),:dual);yy=ISDB._new_workspace_stagnation(b.w,UInt(0),:dual)
    @test sx!==xx&&sy!==yy&&sx.monitor!==xx.monitor&&sy.monitor!==yy.monitor
    @test sx.cost_scale!==xx.cost_scale&&sy.cost_scale!==yy.cost_scale
   end
  end
  for sg in (1,-1),weight in (high(2,sg),BigFloat(3//2)),pivot in (high(3,sg),BigFloat(3//4))
   before=(copy(weight),copy(pivot));x=ISDReference._primal_devex_leaving_weight(weight,pivot);y=ISDC._primal_devex_leaving_weight(weight,pivot)
   @test same(x,y)&&precision(x)==precision(y)==precision(BigFloat)
   @test x!==weight&&x!==pivot&&y!==weight&&y!==pivot
   @test x!==ISDReference._primal_devex_leaving_weight(weight,pivot)&&y!==ISDC._primal_devex_leaving_weight(weight,pivot)
   @test same(weight,before[1])&&same(pivot,before[2])
  end
  for scope in (:devex_shared,:devex_solve),sg in (1,-1)
   a=fixture(T,8,4,scope,:dense,:mixed);b=fixture(T,8,4,scope,:dense,:mixed)
   a=merge(a,(pivot=high(3,sg),));b=merge(b,(pivot=high(3,sg),))
   for v in (a,b);v.weights[1]=high(2,1);v.w.pricing_weights[1]=v.weights[1];end
   olda=a.weights[1];oldb=b.weights[1];checkpair(a,b,:C)
   @test a.w.pricing_weights[1]===olda&&b.w.pricing_weights[1]===oldb
   @test precision(a.w.pricing_weights[1])==precision(b.w.pricing_weights[1])==512
  end
 end
 nothing
end

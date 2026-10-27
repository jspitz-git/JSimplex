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
function workspace(::Type{T},n,m,density,shape;monitor=false,observer=nothing,algorithm=:primal) where T
 A=zeros(T,m,n)
 for j in 1:n,i in 1:m
  if density===:dense||(i+j)%5==0;A[i,j]=T(((i+j)%5+1)//16);end
 end
 if !monitor&&shape!==:slack
  for j in 1:min(m,n)
   fill!(view(A,:,j),zero(T));A[j,j]=shape===:negative||shape===:mixed&&iseven(j) ? -one(T) : one(T)
  end
 end
 p=LinearProblem(sparse(A),T[(i%5-2)//8 for i in 1:n];column_lower=zeros(T,n),column_upper=fill(T(4),n),row_lower=fill(-T(16),m),row_upper=fill(T(16),m))
 opt=SolverOptions(T;algorithm=algorithm,pricing=:steepest_edge,partial_pricing=false,verbose=false)
 pol=J.NumericalPolicy(T;adaptive_stalling=true,stagnation_window=4,refactor_timing=false,solve_refinement=false,recovery=false)
 diag=isnothing(observer) ? nothing : J.SimplexDiagnostics(;observer)
 w=J.initialize_workspace(p,opt;progress=J.SimplexProgressContext(p;numerical_policy=pol,diagnostics=diag))
 if monitor
  for i in eachindex(w.primal)
   w.primal[i]=i>n ? T(iseven(i) ? 20 : -20) : T((i%3-1)//4)
   w.reduced_costs[i]=i>n ? zero(T) : T((i%5-2)//8)
   if i<=n&&shape===:free;w.basis.states[i]=J.FREE_NONBASIC;w.lower[i]=J.Bound{T}(nothing);w.upper[i]=J.Bound{T}(nothing);end
   if i>n&&shape===:unbounded;w.lower[i]=J.Bound{T}(nothing);w.upper[i]=J.Bound{T}(nothing);end
  end
  w.iterations=1
  J._observe_stagnation!(w,algorithm,zero(T),zero(T))
 else
  fill!(w.basis.states,J.AT_LOWER);fill!(w.scratch.basic_mask,false)
  for i in 1:m
   index=shape!==:slack&&i<=n ? i : n+i
   w.basis.basic_indices[i]=index;w.basis.states[index]=J.BASIC;w.scratch.basic_mask[index]=true
  end
  # No solves occur in gate/initializer. The initially owned factor is -I;
  # these component fixtures do not claim a public basis trajectory.
  w.scratch.steepest_initialized=false;fill!(w.scratch.steepest_valid,false)
 end
 w
end
monitorseed(s)=isnothing(s) ? nothing : (state=Tuple(getfield(s,k) for k in fieldnames(typeof(s))),monitor=Tuple(getfield(s.monitor,k) for k in fieldnames(typeof(s.monitor))))
function restoremonitor!(s,seed)
 for (i,k) in enumerate(fieldnames(typeof(s)));k===:monitor||setfield!(s,k,seed.state[i]);end
 for (i,k) in enumerate(fieldnames(typeof(s.monitor)));setfield!(s.monitor,k,seed.monitor[i]);end
 nothing
end
function fixture(::Type{T},n,m,scope,density,shape;observer=nothing) where T
 monitoring=scope in (:values,:observe,:observe_dual,:observe_cold,:observe_same)
 w=workspace(T,n,m,density,shape;monitor=monitoring,observer,algorithm=scope===:observe_dual ? :dual : :primal)
 s=w.scratch.stagnation
 seed=monitorseed(s);weights=copy(w.pricing_weights);flags=copy(w.scratch.steepest_valid)
 if scope===:init_ready;w.scratch.steepest_initialized=true;end
 (scope=scope,w=w,state=s,seed=seed,weights=weights,flags=flags,shape=shape,steps=zeros(T,2))
end
function reset!(v)
 if v.scope in (:values,:observe,:observe_dual,:observe_same)
  v.w.scratch.stagnation=v.state;restoremonitor!(v.state,v.seed);v.w.iterations=v.scope===:observe_same ? 1 : 2
 elseif v.scope===:observe_cold
  v.w.scratch.stagnation=nothing;v.w.iterations=2
 else
  v.w.scratch.steepest_initialized=v.scope===:init_ready
  copyto!(v.w.pricing_weights,v.weights);copyto!(v.w.scratch.steepest_valid,v.flags)
 end
 nothing
end
modof(arm)=arm===:original ? SSUReference : arm===:A ? SSUA : arm===:B ? SSUB : arm===:C ? SSUC : SSUBC
@noinline function whole(::Val{arm},::Val{scope},v) where {arm,scope}
 mod=modof(arm);w=v.w
 if scope===:values;return mod._workspace_stagnation_values(w,w.scratch.stagnation,:primal)
 elseif scope in (:observe,:observe_dual,:observe_cold,:observe_same);return mod._observe_stagnation!(w,scope===:observe_dual ? :dual : :primal,v.steps[1],v.steps[2])
 elseif scope===:unit;return mod._primal_unit_basis(w)
 end
 return mod._primal_initialize_steepest!(w)
end
sink(x::Bool)=Int(x)
sink(::Nothing)=1
sink(x::Symbol)=x===:progress ? 1 : x===:watch ? 2 : x===:stalled ? 3 : 4
sink(x::Tuple{<:Real,<:Real,<:Real})=Int(isfinite(x[1]))+2Int(isfinite(x[2]))+4Int(isfinite(x[3]))
@noinline runwhole(a,s,v)=sink(whole(a,s,v))
function timed(a::A,s::S,v::V) where {A,S,V}
 t=@timed runwhole(a,s,v);merge(cost(t),Dict("sink"=>t.value))
end
function inputs(v)
 w=v.w
 (w.problem.A.colptr,w.problem.A.rowval,w.problem.A.nzval,w.costs,w.primal,w.reduced_costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states,v.steps)
end
snapshot(v)=(inputs(v),map(copy,inputs(v)),deepcopy(inputs(v)))
function intact(v,s)
 all(inputs(v)[i]===s[1][i]&&same(inputs(v)[i],s[3][i])&&all(inputs(v)[i][j]===s[2][i][j] for j in eachindex(s[2][i])) for i in eachindex(s[1]))
end
function outputs(v)
 s=v.w.scratch.stagnation
 mon=isnothing(s) ? nothing : (Tuple(getfield(s.monitor,k) for k in fieldnames(typeof(s.monitor))),s.last_iteration,s.cost_scale,s.value_scale)
 (v.w.pricing_weights,v.w.scratch.steepest_valid,v.w.scratch.steepest_initialized,mon)
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
function seed_oracle(v)
 w=v.w;T=eltype(w.pricing_weights);n=size(w.problem.A,2);m=size(w.problem.A,1)
 @test w.scratch.steepest_initialized
 if T===Rational{Int64};@test same(w.pricing_weights,v.weights);return;end
 @test all(w.scratch.steepest_valid)
 for j in 1:n
  q=Rational{BigInt}(1)
  for a in w.problem.A[:,j];q+=Rational{BigInt}(a)^2;end
  expected=T<:AbstractFloat ? sqrt(T(q)) : q
  @test same(w.pricing_weights[j],expected)
 end
 if m>0
  expected=T<:AbstractFloat ? sqrt(T(2)) : T(2)
  @test all(same(w.pricing_weights[j],expected) for j in n+1:n+m)
  T in (BigFloat,Rational{BigInt})&&@test all(w.pricing_weights[j]===w.pricing_weights[n+1] for j in n+1:n+m)
 end
end
function correctness(::Type{T}) where T
 @testset "Stagnation unit and seed correctness $T" begin
  for scope in (:values,:observe,:observe_dual,:observe_cold,:observe_same),shape in (:bounded,:unbounded,:free),density in (:sparse,:dense)
   a=fixture(T,8,4,scope,density,shape);b=fixture(T,8,4,scope,density,shape)
   z=checkpair(a,b,:A);@test z[1]===:value
  end
  for shape in (:positive,:negative,:mixed,:slack),density in (:sparse,:dense),scope in (:unit,:init,:init_ready),arm in (scope===:unit ? (:B,) : (:B,:C,:BC))
   a=fixture(T,8,4,scope,density,shape);b=fixture(T,8,4,scope,density,shape)
   z=checkpair(a,b,arm);@test z[1]===:value
   scope===:unit&&@test z[2]===true
   scope===:init&&(seed_oracle(a);seed_oracle(b))
  end
  for shape in (:positive,:negative,:mixed),bad in (:extra,:wrongrow,:nonunit,:badindex),scope in (:unit,:init),arm in (:B,:C,:BC)
   a=fixture(T,8,4,scope,:sparse,shape);b=fixture(T,8,4,scope,:sparse,shape)
   for v in (a,b)
    if bad===:extra;v.w.problem.A[2,1]=one(T)
    elseif bad===:wrongrow;v.w.problem.A[1,1]=zero(T);dropzeros!(v.w.problem.A);v.w.problem.A[2,1]=one(T)
    elseif bad===:nonunit;v.w.problem.A[1,1]=T(3//2)
    else;v.w.basis.basic_indices[1]=0
    end
   end
   z=checkpair(a,b,arm)
   if bad===:badindex&&(scope===:unit||T!==Rational{Int64});@test z[1]===:error&&z[2]===BoundsError
   else;@test z[1]===:value&&(scope!==:unit||z[2]===false)
   end
  end
  for n in (0,1),m in (0,1),arm in (:B,:C,:BC)
   a=fixture(T,n,m,:init,:sparse,:slack);b=fixture(T,n,m,:init,:sparse,:slack);checkpair(a,b,arm)
  end
  # Hand-derived metric: objective=2/2*4+3/2*5=23/2,
  # basic upper violation=5-4=1, free price=abs(-1/2/2)=1/4.
  a=fixture(T,1,1,:values,:sparse,:free);b=fixture(T,1,1,:values,:sparse,:free)
  for v in (a,b)
   v.w.costs.=[T(2),T(3)];v.w.primal.=[T(4),T(5)];v.w.reduced_costs.=[T(-1//2),zero(T)]
   v.w.lower[2]=J.Bound(zero(T));v.w.upper[2]=J.Bound(T(4))
   v.state.cost_scale=T(2);v.state.value_scale=one(T)
   v.state.monitor.objective_scale=one(T);v.state.monitor.primal_scale=one(T);v.state.monitor.dual_scale=one(T)
  end
  for mod in (SSUReference,SSUA)
   v=mod===SSUReference ? a : b
   @test same(mod._workspace_stagnation_values(v.w,v.state,:primal),(T(23//2),T(1),T(1//4)))
   @test same(mod._workspace_stagnation_values(v.w,v.state,:dual),(-T(23//2),T(1),T(1//4)))
  end
  if T===BigFloat
   for x in (BigFloat(0),-BigFloat(0),BigFloat(Inf),-BigFloat(Inf),BigFloat(NaN),floatmin(BigFloat),floatmax(BigFloat))
    for arm in (:B,:BC),scope in (:unit,:init)
     a=fixture(T,4,2,scope,:sparse,:positive);b=fixture(T,4,2,scope,:sparse,:positive)
     for v in (a,b);v.w.problem.A.nzval[v.w.problem.A.colptr[1]]=copy(x);end
     checkpair(a,b,arm)
    end
   end
   # Stored precision must not be lost by replacing abs with x==±1.
   x=setprecision(BigFloat,512) do;-(BigFloat(1)+ldexp(BigFloat(1),-300));end
   a=fixture(T,4,2,:unit,:sparse,:positive);b=fixture(T,4,2,:unit,:sparse,:positive)
   for v in (a,b);v.w.problem.A.nzval[v.w.problem.A.colptr[1]]=copy(x);end
   checkpair(a,b,:B)
   for scale in (BigFloat(0),BigFloat(-1),BigFloat(Inf),BigFloat(NaN))
    a=fixture(T,4,2,:values,:dense,:free);b=fixture(T,4,2,:values,:dense,:free)
    for v in (a,b);v.state.value_scale=copy(scale);end
    # Direct metric call deliberately retains malformed scale behavior.
    x=capture(()->SSUReference._workspace_stagnation_values(a.w,a.state,:primal));y=capture(()->SSUA._workspace_stagnation_values(b.w,b.state,:primal));@test same(x,y)
   end
  end
 end
end

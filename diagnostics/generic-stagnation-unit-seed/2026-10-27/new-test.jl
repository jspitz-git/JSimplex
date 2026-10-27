module GenericStagnationUnitSeedTests
using Test,JSimplex,SparseArrays,LinearAlgebra
module SSUReference
using JSimplex,SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,WorkspaceStagnation,StagnationMonitor,VariableState,
 BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,_is_fixed,bound_value,_primal_direction_magnitude,
 _finite_workspace,_with_recovery_precision,observe_progress!,reset_stagnation!,
 _simplex_event!,_primal_direction_weight,_primal_cacheable_weight
_stagnation_price_step(price,pivot) = price/pivot
_stagnation_price_step(price::Rational,pivot::Rational) =
    Rational{BigInt}(price)/Rational{BigInt}(pivot)

function _stagnation_context(ws,algorithm;include_costs=true)
    p = ws.progress.numerical_policy
    # Checkpoint/cache generations also change at ordinary refactorizations.
    # They are not phase changes and must not erase a watched window.
    key = hash((algorithm,objectid(ws.problem.A),size(ws.problem.A),ws.options.primal_tolerance,
        ws.options.dual_tolerance,p.solve_tolerance,p.stagnation_window))
    # Base's array hash samples sufficiently large arrays. Inspect every entry
    # so a change outside that sample still invalidates the affected history.
    for values in (ws.costs,ws.lower,ws.upper,ws.progress.scaling.row_factors,
                   ws.progress.scaling.column_factors)
        values === ws.costs && !include_costs && continue
        key = hash(length(values),key)
        for value in values
            key = hash(value,key)
        end
    end
    return key
end

function _new_workspace_stagnation(ws,key,algorithm)
    T = eltype(ws.costs)
    S = T <: Rational ? Rational{BigInt} : T
    cost_scale, value_scale = one(S),one(S)
    for value in ws.costs
        cost_scale = max(cost_scale,abs(S(value)))
    end
    for value in ws.primal
        value_scale = max(value_scale,abs(S(value)))
    end
    for bounds in (ws.lower,ws.upper), bound in bounds
        isfinite(bound) && (value_scale = max(value_scale,abs(S(bound_value(bound)))))
    end
    # Averaging prevents overflowing sums; these monitor scales cancel it so
    # the number of rows/columns does not alter the significance threshold.
    objective_scale = inv(2S(max(1,length(ws.costs))))
    primal_scale = inv(2S(max(1,length(ws.basis.basic_indices))))
    policy = ws.progress.numerical_policy
    monitor = StagnationMonitor{T}(policy.stagnation_window;objective_scale,
        primal_scale,dual_scale=objective_scale,tolerance=policy.solve_tolerance)
    return WorkspaceStagnation(monitor,key,
        _stagnation_context(ws,algorithm;include_costs=false),
        ws.iterations-1,cost_scale,value_scale)
end

function _workspace_stagnation_values(ws,state::WorkspaceStagnation{T,S},algorithm) where {T,S}
    m = state.monitor
    objective, primal, dual = zero(S),zero(S),zero(S)
    for j in eachindex(ws.costs)
        objective += ((S(ws.costs[j])/state.cost_scale)*
            (S(ws.primal[j])/state.value_scale))*m.objective_scale
        status = ws.basis.states[j]
        (status == BASIC || _is_fixed(ws.lower[j],ws.upper[j])) && continue
        price = S(ws.reduced_costs[j])/state.cost_scale
        violation = status == AT_LOWER ? -price : status == AT_UPPER ? price : abs(price)
        violation > S(ws.options.dual_tolerance)/state.cost_scale &&
            (dual += violation*m.dual_scale)
    end
    for j in ws.basis.basic_indices
        value = S(ws.primal[j])/state.value_scale
        lower = isfinite(ws.lower[j]) ? S(bound_value(ws.lower[j]))/state.value_scale-value : zero(S)
        upper = isfinite(ws.upper[j]) ? value-S(bound_value(ws.upper[j]))/state.value_scale : zero(S)
        violation = max(zero(S),lower,upper)
        violation > S(ws.options.primal_tolerance)/state.value_scale &&
            (primal += violation*m.primal_scale)
    end
    # The primal minimizes its working objective; the dual improves its lower
    # bound upward. Both orientations are decreases to the progress monitor.
    return algorithm == :dual ? -objective : objective, primal, dual
end

# Reuse private normalized BigFloat tolerances only within this observation.
# Evaluate each at its first comparison to preserve empty paths and error order;
# the generic method above deliberately retains the original arithmetic.
function _workspace_stagnation_values(ws,state::WorkspaceStagnation{BigFloat,BigFloat},algorithm)
    S = BigFloat
    m = state.monitor
    objective, primal, dual = zero(S),zero(S),zero(S)
    dual_threshold = nothing
    primal_threshold = nothing
    for j in eachindex(ws.costs)
        objective += ((S(ws.costs[j])/state.cost_scale)*
            (S(ws.primal[j])/state.value_scale))*m.objective_scale
        status = ws.basis.states[j]
        (status == BASIC || _is_fixed(ws.lower[j],ws.upper[j])) && continue
        price = S(ws.reduced_costs[j])/state.cost_scale
        violation = status == AT_LOWER ? -price : status == AT_UPPER ? price : abs(price)
        if isnothing(dual_threshold)
            dual_threshold = S(ws.options.dual_tolerance)/state.cost_scale
        end
        violation > dual_threshold &&
            (dual += violation*m.dual_scale)
    end
    for j in ws.basis.basic_indices
        value = S(ws.primal[j])/state.value_scale
        lower = isfinite(ws.lower[j]) ? S(bound_value(ws.lower[j]))/state.value_scale-value : zero(S)
        upper = isfinite(ws.upper[j]) ? value-S(bound_value(ws.upper[j]))/state.value_scale : zero(S)
        violation = max(zero(S),lower,upper)
        if isnothing(primal_threshold)
            primal_threshold = S(ws.options.primal_tolerance)/state.value_scale
        end
        violation > primal_threshold &&
            (primal += violation*m.primal_scale)
    end
    # The primal minimizes its working objective; the dual improves its lower
    # bound upward. Both orientations are decreases to the progress monitor.
    return algorithm == :dual ? -objective : objective, primal, dual
end

function _reset_workspace_stagnation!(ws)
    state = ws.scratch.stagnation
    isnothing(state) || reset_stagnation!(state.monitor)
    return nothing
end

function _observe_stagnation!(ws,algorithm::Symbol,primal_step,dual_step)::Symbol
    ws.progress.numerical_policy.adaptive_stalling || return :progress
    algorithm in (:primal,:dual) || throw(ArgumentError("Unknown stagnation algorithm"))
    ws.iterations > 0 || return :progress
    state = ws.scratch.stagnation
    !isnothing(state) && ws.iterations <= state.last_iteration && return state.monitor.state
    _finite_workspace(ws) || return :watch
    return _with_recovery_precision(ws,ws) do
        _observe_stagnation_precise!(ws,algorithm,primal_step,dual_step)
    end
end

function _observe_stagnation_precise!(ws,algorithm,primal_step,dual_step)
    key = _stagnation_context(ws,algorithm)
    state = ws.scratch.stagnation
    if !isnothing(state) && state.context_key != key && algorithm == :dual &&
       state.feasibility_context_key == _stagnation_context(ws,algorithm;include_costs=false)
        _rebase_dual_stagnation_costs!(ws,state,key)
    elseif isnothing(state) || state.context_key != key
        state = _new_workspace_stagnation(ws,key,algorithm)
        ws.scratch.stagnation = state
    end
    return _observe_workspace_stagnation!(ws,state,algorithm,primal_step,dual_step)
end

# Numerical price repairs change the working objective, but not the feasible
# region. Preserve its history and window cadence; never compare objectives or
# dual violations across different cost vectors. Explicit phase/perturbation
# resets still invalidate the monitor before the next observation.
function _rebase_dual_stagnation_costs!(ws,state::WorkspaceStagnation{T,S},key) where {T,S}
    state.cost_scale = maximum(x -> abs(S(x)),ws.costs;init=one(S))
    objective,_,dual = _workspace_stagnation_values(ws,state,:dual)
    m = state.monitor
    m.start_objective = m.minimum_objective = m.end_objective = m.best_objective = objective
    m.start_dual = m.minimum_dual = m.end_dual = m.best_dual = dual
    m.objective_improvement = m.dual_improvement = zero(S)
    state.context_key = key
    _simplex_event!(ws,:stagnation_cost_rebase)
    return nothing
end

function _observe_workspace_stagnation!(ws,state::WorkspaceStagnation{T,S},
                                       algorithm,primal_step,dual_step) where {T,S}
    m = state.monitor
    objective,primal_violation,dual_violation = _workspace_stagnation_values(ws,state,algorithm)
    result = observe_progress!(m;algorithm,objective,primal_violation,dual_violation,
        primal_step=(S(primal_step)/state.value_scale)*m.primal_scale,
        dual_step=(S(dual_step)/state.cost_scale)*m.dual_scale)
    state.last_iteration = ws.iterations
    if m.window_count == m.window
        result == :watch && _simplex_event!(ws,:stagnation_watch)
        result == :stalled && _simplex_event!(ws,:stagnation_stalled)

    end
    return result
end


function _primal_unit_basis(workspace::SimplexWorkspace{T}) where {T}
    A = workspace.problem.A
    column_count = size(A, 2)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        if index > column_count
            index - column_count == row || return false
        else
            start = A.colptr[index]
            A.colptr[index + 1] == start + 1 || return false
            A.rowval[start] == row || return false
            abs(A.nzval[start]) == one(T) || return false
        end
    end
    return true
end


function _primal_initialize_steepest!(workspace::SimplexWorkspace{T}) where {T}
    scratch = workspace.scratch
    scratch.steepest_initialized && return nothing
    scratch.steepest_initialized = true
    T <: Rational && T !== Rational{BigInt} && return nothing
    _primal_unit_basis(workspace) || return nothing
    A = workspace.problem.A
    row_count, column_count = size(A)
    for index in 1:column_count
        direction = @view A.nzval[A.colptr[index]:(A.colptr[index + 1] - 1)]
        _, weight = _primal_direction_weight(direction)
        workspace.pricing_weights[index] = weight
        scratch.steepest_valid[index] = _primal_cacheable_weight(weight)
    end
    _, row_weight = _primal_direction_weight(T[one(T)])
    for index in (column_count + 1):(column_count + row_count)
        workspace.pricing_weights[index] = row_weight
        scratch.steepest_valid[index] = _primal_cacheable_weight(row_weight)
    end
    return nothing
end


end

const SSUA=JSimplex
const SSUB=JSimplex
const SSUC=JSimplex
const SSUBC=JSimplex
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
function checkpair(a,b,arm;protect=true,reset_state=true)
 reset_state&&(reset!(a);reset!(b));sa=snapshot(a);sb=snapshot(b);ctx=(precision(BigFloat),rounding(BigFloat))
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
function extra_correctness(::Type{T}) where T
 @testset "Stagnation invalidation and seed ownership $T" begin
  for mod in (SSUReference,SSUA)
   @test mod._observe_stagnation!((progress=(numerical_policy=(adaptive_stalling=false,),),),:primal,0,0)===:progress
  end
  for scope in (:values,:observe,:observe_cold,:observe_same)
   a=fixture(T,0,0,scope,:sparse,:free);b=fixture(T,0,0,scope,:sparse,:free);checkpair(a,b,:A)
  end
  # Ordinary primal cost-context rebuild, bound invalidation, same-iteration and
  # nonfinite early return must retain the complete outer behavior.
  for change in (:cost,:bound,:nonfinite,:short_primal,:short_weights)
   a=fixture(T,8,4,:observe,:sparse,:free);b=fixture(T,8,4,:observe,:sparse,:free)
   for v in (a,b)
    if change===:cost;v.w.costs[1]+=one(T)
    elseif change===:bound;v.w.upper[end]=J.Bound(T(3))
    elseif change===:nonfinite&&T<:AbstractFloat;v.w.primal[1]=T(Inf)
    elseif change===:short_primal;resize!(v.w.primal,1)
    elseif change===:short_weights;resize!(v.w.pricing_weights,1)
    end
   end
   checkpair(a,b,:A)
  end
  for arm in (:B,:C,:BC),which in (:weights,:flags)
   a=fixture(T,8,4,:init,:sparse,:slack);b=fixture(T,8,4,:init,:sparse,:slack)
   for v in (a,b)
    if which===:weights;resize!(v.w.pricing_weights,9)
    else;resize!(v.w.scratch.steepest_valid,9)
    end
   end
   z=checkpair(a,b,arm;reset_state=false)
   @test T===Rational{Int64} ? z[1]===:value : z[1]===:error&&z[2]===BoundsError
  end
  if T===BigFloat
   for scope in (:values,:observe),whichfield in (:primal,:cost,:price,:bound)
    a=fixture(T,8,4,scope,:sparse,:free);b=fixture(T,8,4,scope,:sparse,:free)
    for v in (a,b)
     value=setprecision(BigFloat,512) do;BigFloat(3//7);end
     if whichfield===:primal;v.w.primal[end]=value
     elseif whichfield===:cost;v.w.costs[1]=value
     elseif whichfield===:price;v.w.reduced_costs[1]=value
     else;v.w.upper[end]=J.Bound(value)
     end
    end
    checkpair(a,b,:A)
   end
   # Real observer: a window event can mutate bounds or throw. Cache is
   # invocation-local, so the next context must be checked/rebuilt normally.
   for action in (:mutate,:throw)
    sentinel=ErrorException("SSU observer sentinel");counts=[Ref(0),Ref(0)];hits=[Ref(0),Ref(0)];threw=false
    function obs(counter,hit)
     (reason,w)->begin
      counter[]+=1
      if reason===:stagnation_watch
       hit[]+=1
       action===:throw&&throw(sentinel)
       w.upper[end]=J.Bound(BigFloat(7))
      end
      nothing
     end
    end
    a=fixture(T,4,2,:observe,:sparse,:free;observer=obs(counts[1],hits[1]));b=fixture(T,4,2,:observe,:sparse,:free;observer=obs(counts[2],hits[2]))
    for i in 2:6
     a.w.iterations=b.w.iterations=i
     x=try;(:value,SSUReference._observe_stagnation!(a.w,:primal,a.steps...));catch e;(:error,typeof(e),e isa J.DiagnosticObserverFailure&&e.cause===sentinel);end
     y=try;(:value,SSUA._observe_stagnation!(b.w,:primal,b.steps...));catch e;(:error,typeof(e),e isa J.DiagnosticObserverFailure&&e.cause===sentinel);end
     @test same(x,y)&&same(outputs(a),outputs(b))
     @test counts[1][]==counts[2][]
     if x[1]===:error;@test x[3]===true;threw=true;break;end
    end
    @test hits[1][]==hits[2][]&&hits[1][]>0
    @test threw==(action===:throw)
   end
  elseif T===Rational{BigInt}
   for pair in ((BigInt(1),BigInt(0)),(BigInt(2),BigInt(2)),(BigInt(-1),BigInt(-1)),(BigInt(-1),BigInt(1)))
    a=fixture(T,4,2,:unit,:sparse,:positive);b=fixture(T,4,2,:unit,:sparse,:positive)
    for v in (a,b);v.w.problem.A.nzval[v.w.problem.A.colptr[1]]=Base.unsafe_rational(copy(pair[1]),copy(pair[2]));end
    checkpair(a,b,:B)
   end
  end
 end
end
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

@testset "Stagnation unit and shared row-weight regressions" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;correctness(BigFloat);extra_correctness(BigFloat);boundary_correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);extra_correctness(T);boundary_correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   for (T,n,m,scope,shape,arm) in ((BigFloat,128,32,:values,:unbounded,:A),(BigFloat,128,32,:observe,:unbounded,:A),(BigFloat,32,32,:unit,:positive,:B),(Rational{BigInt},32,32,:unit,:positive,:B),(BigFloat,8,32,:init,:slack,:C))
    @testset "Whole-call allocation $T $scope" begin
     a=fixture(T,n,m,scope,:sparse,shape);b=fixture(T,n,m,scope,:sparse,shape);s=Val(scope)
     for k in 1:3,(method,v) in ((Val(:original),a),(Val(arm),b));reset!(v);timed(method,s,v);end
     pairs=Tuple{Dict{String,Any},Dict{String,Any}}[]
     for k in 1:3
      if isodd(k);reset!(a);old=timed(Val(:original),s,a);reset!(b);new=timed(Val(arm),s,b)
      else;reset!(b);new=timed(Val(arm),s,b);reset!(a);old=timed(Val(:original),s,a)
      end
      @test old["compile_seconds"]==old["recompile_seconds"]==new["compile_seconds"]==new["recompile_seconds"]==0
      push!(pairs,(old,new))
     end
     @test all(new["events"]<old["events"] for (old,new) in pairs)&&sort([new["bytes"] for (old,new) in pairs])[2]<sort([old["bytes"] for (old,new) in pairs])[2] # RED whole-call cost gate
    end
   end
  end
 end
end
end

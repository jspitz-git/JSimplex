module GenericRatioMonitorTests
using Test,JSimplex,SparseArrays,LinearAlgebra,Statistics
module RMReference
using JSimplex: SimplexWorkspace,StagnationMonitor,WorkspaceStagnation,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,bound_value,_lower_violation,_upper_violation,_primal_relaxed_step,_primal_bound_snap_feasible,_primal_step_bounds_feasible,_legacy_primal_row_validation_enabled,_primal_direction_magnitude,_finite_workspace,_with_recovery_precision,_stagnation_context,_new_workspace_stagnation,_rebase_dual_stagnation_costs!,_workspace_stagnation_values,_simplex_event!
function _primal_ratio(workspace::SimplexWorkspace{T}, entering::Int, direction::T,
                       tableau_column::Vector{T}) where {T}
    opposite = direction > zero(T) ? workspace.upper[entering] : workspace.lower[entering]
    # Keep optionality in flags so numeric loop accumulators stay concrete.
    has_step = isfinite(opposite)
    entering_step = has_step ?
        (bound_value(opposite) - workspace.primal[entering]) / direction : zero(T)
    strict_step = entering_step
    strict_row = 0
    strict_state = BASIC
    relaxed_limit = entering_step
    has_relaxed_limit = has_step
    tolerance = workspace.options.primal_tolerance
    for (row, index) in enumerate(workspace.basis.basic_indices)
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > zero(T) ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        raw_step = (bound_value(bound) - workspace.primal[index]) / movement
        isfinite(raw_step) || return nothing, -1, BASIC
        if raw_step < zero(T)
            violation = movement > zero(T) ?
                _upper_violation(bound, workspace.primal[index]) :
                _lower_violation(bound, workspace.primal[index])
            violation > tolerance && return nothing, -1, BASIC
        end
        candidate = max(zero(T), raw_step)
        if !has_step || candidate < strict_step ||
           (candidate == strict_step && strict_row == 0)
            strict_step = candidate
            strict_row = row
            strict_state = movement > zero(T) ? AT_UPPER : AT_LOWER
            has_step = true
        end
        relaxed = _primal_relaxed_step(raw_step, tolerance, movement)
        if isfinite(relaxed) && (!has_relaxed_limit || relaxed < relaxed_limit)
            relaxed_limit = max(zero(T), relaxed)
            has_relaxed_limit = true
        end
    end
    has_step || return nothing, strict_row, strict_state
    strict_row == 0 && return strict_step, strict_row, strict_state
    has_relaxed_limit || return strict_step, strict_row, strict_state

    strict_safe = !(strict_row in workspace.scratch.rejected_rows) &&
        _primal_bound_snap_feasible(
            workspace, entering, direction, tableau_column, strict_row)
    fallback = strict_safe ? (strict_step, strict_row, strict_state) : (nothing, -1, BASIC)
    leaving_row = 0
    leaving_step = strict_step
    leaving_state = strict_state
    largest_pivot = zero(T)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row in workspace.scratch.rejected_rows && continue
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > zero(T) ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        candidate = max(zero(T),
                        (bound_value(bound) - workspace.primal[index]) / movement)
        candidate <= relaxed_limit || continue
        pivot = abs(tableau_column[row])
        if pivot > largest_pivot
            !_primal_bound_snap_feasible(
                workspace, entering, direction, tableau_column, row) && continue
            leaving_row = row
            leaving_step = candidate
            leaving_state = movement > zero(T) ? AT_UPPER : AT_LOWER
            largest_pivot = pivot
        end
    end
    # Tolerated initial bound violations can create zero ratios on coefficients
    # too small to pivot on. A finite entering bound remains a valid Harris move
    # when the entire predicted step respects the same per-bound tolerance.
    if _legacy_primal_row_validation_enabled(workspace) &&
       largest_pivot <= workspace.options.zero_tolerance && isfinite(opposite) &&
       isfinite(entering_step) && entering_step > zero(T) && entering_step <= relaxed_limit &&
       _primal_step_bounds_feasible(workspace, direction, tableau_column, entering_step)
        return entering_step, 0, BASIC
    end
    if leaving_row == 0
        return fallback
    end
    _primal_step_bounds_feasible(workspace, direction, tableau_column, leaving_step) ||
        return fallback
    return leaving_step, leaving_row, leaving_state
end

function _primal_ratio(workspace::SimplexWorkspace{BigFloat}, entering::Int, direction::BigFloat,
                       tableau_column::Vector{BigFloat})
    T = BigFloat
    opposite = direction > 0 ? workspace.upper[entering] : workspace.lower[entering]
    # Keep optionality in flags so numeric loop accumulators stay concrete.
    has_step = isfinite(opposite)
    entering_step = has_step ?
        (bound_value(opposite) - workspace.primal[entering]) / direction : zero(T)
    strict_step = entering_step
    strict_row = 0
    strict_state = BASIC
    relaxed_limit = entering_step
    has_relaxed_limit = has_step
    tolerance = workspace.options.primal_tolerance
    for (row, index) in enumerate(workspace.basis.basic_indices)
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > 0 ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        raw_step = (bound_value(bound) - workspace.primal[index]) / movement
        isfinite(raw_step) || return nothing, -1, BASIC
        if raw_step < 0
            violation = movement > 0 ?
                _upper_violation(bound, workspace.primal[index]) :
                _lower_violation(bound, workspace.primal[index])
            violation > tolerance && return nothing, -1, BASIC
        end
        candidate = max(zero(T), raw_step)
        if !has_step || candidate < strict_step ||
           (candidate == strict_step && strict_row == 0)
            strict_step = candidate
            strict_row = row
            strict_state = movement > 0 ? AT_UPPER : AT_LOWER
            has_step = true
        end
        relaxed = _primal_relaxed_step(raw_step, tolerance, movement)
        if isfinite(relaxed) && (!has_relaxed_limit || relaxed < relaxed_limit)
            relaxed_limit = max(zero(T), relaxed)
            has_relaxed_limit = true
        end
    end
    has_step || return nothing, strict_row, strict_state
    strict_row == 0 && return strict_step, strict_row, strict_state
    has_relaxed_limit || return strict_step, strict_row, strict_state

    strict_safe = !(strict_row in workspace.scratch.rejected_rows) &&
        _primal_bound_snap_feasible(
            workspace, entering, direction, tableau_column, strict_row)
    fallback = strict_safe ? (strict_step, strict_row, strict_state) : (nothing, -1, BASIC)
    leaving_row = 0
    leaving_step = strict_step
    leaving_state = strict_state
    largest_pivot = zero(T)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row in workspace.scratch.rejected_rows && continue
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > 0 ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        candidate = max(zero(T),
                        (bound_value(bound) - workspace.primal[index]) / movement)
        candidate <= relaxed_limit || continue
        pivot = _primal_direction_magnitude(tableau_column[row])
        if pivot > largest_pivot
            !_primal_bound_snap_feasible(
                workspace, entering, direction, tableau_column, row) && continue
            leaving_row = row
            leaving_step = candidate
            leaving_state = movement > 0 ? AT_UPPER : AT_LOWER
            largest_pivot = pivot
        end
    end
    # Tolerated initial bound violations can create zero ratios on coefficients
    # too small to pivot on. A finite entering bound remains a valid Harris move
    # when the entire predicted step respects the same per-bound tolerance.
    if _legacy_primal_row_validation_enabled(workspace) &&
       largest_pivot <= workspace.options.zero_tolerance && isfinite(opposite) &&
       isfinite(entering_step) && entering_step > 0 && entering_step <= relaxed_limit &&
       _primal_step_bounds_feasible(workspace, direction, tableau_column, entering_step)
        return entering_step, 0, BASIC
    end
    if leaving_row == 0
        return fallback
    end
    _primal_step_bounds_feasible(workspace, direction, tableau_column, leaving_step) ||
        return fallback
    return leaving_step, leaving_row, leaving_state
end


_stagnation_improvement(anchor::Rational,current::Rational,scale::Rational) =
    (anchor-current)/scale

function _stagnation_improvement(anchor::T,current::T,scale::T) where {T<:AbstractFloat}
    anchor == current && return zero(T)
    # Normalize before subtracting, including opposite near-maximum values.
    reference = max(abs(anchor),abs(current),scale)
    change = anchor/reference-current/reference
    iszero(change) && return zero(T)
    return change*(reference/scale)
end

function observe_progress!(m::StagnationMonitor{T,S};objective,primal_violation,
                           dual_violation,primal_step,dual_step,
                           algorithm::Symbol=:all)::Symbol where {T,S}
    algorithm in (:all,:primal,:dual) || throw(ArgumentError("Unknown progress algorithm"))
    objective, primal, dual = S(objective), S(primal_violation), S(dual_violation)
    ps, ds = S(primal_step), S(dual_step)
    # A ratio of finite floating-point inputs can overflow. An infinite step
    # is not insignificant, but never establishes objective/feasibility progress.
    all(isfinite,(objective,primal,dual)) && !isnan(ps) && !isnan(ds) &&
        primal >= 0 && dual >= 0 ||
        throw(ArgumentError("Stagnation metrics must be finite, violations nonnegative, and steps not NaN"))
    if !m.initialized
        m.best_objective, m.best_primal, m.best_dual = objective, primal, dual
        m.initialized = true
    end
    if m.window_count == m.window
        m.window_count = 0
    end
    if m.window_count == 0
        m.start_objective = m.minimum_objective = objective
        m.start_primal = m.minimum_primal = primal
        m.start_dual = m.minimum_dual = dual
        m.insignificant_steps = 0
    end
    m.minimum_objective = min(m.minimum_objective,objective)
    m.minimum_primal = min(m.minimum_primal,primal)
    m.minimum_dual = min(m.minimum_dual,dual)
    m.end_objective, m.end_primal, m.end_dual = objective, primal, dual
    m.observations = min(typemax(Int)-1,m.observations)+1
    m.window_count += 1
    insignificant = T <: Rational ? iszero(ps) && iszero(ds) :
        abs(ps)/m.primal_scale <= m.tolerance && abs(ds)/m.dual_scale <= m.tolerance
    m.insignificant_steps += insignificant
    if m.window_count == m.window
        # A return to a previous low point is oscillation, not renewed progress.
        # Require a new endpoint improvement over the best earlier window.
        m.objective_improvement = _stagnation_improvement(m.best_objective,objective,m.objective_scale)
        m.primal_improvement = _stagnation_improvement(m.best_primal,primal,m.primal_scale)
        m.dual_improvement = _stagnation_improvement(m.best_dual,dual,m.dual_scale)
        # A primal pivot must improve the current (possibly auxiliary)
        # objective. Reduced-price changes at a fixed point are not progress.
        # Dual pivots can also make useful progress toward primal feasibility
        # at a constant objective. Retain all metrics for diagnostics.
        progress = m.objective_improvement > m.tolerance ||
            (algorithm != :primal && m.primal_improvement > m.tolerance) ||
            (algorithm == :all && m.dual_improvement > m.tolerance)
        # Retain the reference after a sub-tolerance change so that genuine
        # slow progress can accumulate across the two watched windows.
        m.objective_improvement > m.tolerance && (m.best_objective = min(m.best_objective,m.minimum_objective))
        m.primal_improvement > m.tolerance && (m.best_primal = min(m.best_primal,m.minimum_primal))
        m.dual_improvement > m.tolerance && (m.best_dual = min(m.best_dual,m.minimum_dual))
        m.stalled_windows = progress ? 0 : min(2,m.stalled_windows+1)
        m.state = m.stalled_windows == 0 ? :progress :
            m.stalled_windows == 1 ? :watch : :stalled
    end
    return m.state
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


end

const RMA=JSimplex
const RMB=JSimplex
const RMC=JSimplex
const RMBC=JSimplex
using Test,JSimplex,SparseArrays,LinearAlgebra,Statistics
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a))
same(a::J.Bound,b::J.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
fields(x)=Tuple(getfield(x,n) for n in fieldnames(typeof(x)))
function restore!(x,seed)
 for (i,n) in enumerate(fieldnames(typeof(x)));setfield!(x,n,seed[i]);end
 nothing
end
modof(::Val{:original})=RMReference
modof(::Val{:A})=RMA
modof(::Val{:B})=RMB
modof(::Val{:C})=RMC
modof(::Val{:BC})=RMBC
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
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

function monitorof(::Type{T},shape,phase) where T
 tol=T<:Rational ? zero(T) : T(1//128)
 m=J.StagnationMonitor{T}(4;tolerance=tol)
 objective=T(shape===:negative ? -2 : 2)
 ps=T(shape===:negative ? -1//1024 : 1//1024)
 ds=T(shape===:positive ? 1//1024 : -1//1024)
 m.initialized=phase!==:first;m.window_count=phase===:end ? 3 : phase===:ordinary ? 1 : 0
 m.best_objective=objective+one(T);m.best_primal=T(1//2);m.best_dual=T(1//4)
 m.start_objective=m.minimum_objective=objective+one(T)
 m.start_primal=m.minimum_primal=T(1//2);m.start_dual=m.minimum_dual=T(1//4)
 (m=m,seed=fields(m),values=(objective,T(1//4),T(1//8),ps,ds))
end
function fixture(::Type{T},n,density,shape,scope,phase=:end) where T
 if scope===:ratio
  v=ratio_fixture(T,n,:primal_ratio,density,shape)
  return merge(v,(scope=scope,))
 elseif scope===:progress
  return merge(monitorof(T,shape,phase),(scope=scope,))
 end
 A=zeros(T,n÷2,n)
 for j in 1:n,i in 1:n÷2
  (density===:dense||(i+j)%5==0)&&(A[i,j]=T((i+j)%7+1)/T(16))
 end
 p=LinearProblem(sparse(A),fill(T(1//8),n);column_lower=zeros(T,n),column_upper=fill(T(4),n),row_lower=fill(-T(8),n÷2),row_upper=fill(T(8),n÷2))
 opt=SolverOptions(T;algorithm=:dual,pricing=:devex,verbose=false)
 pol=J.NumericalPolicy(T;adaptive_stalling=true,stagnation_window=4,refactor_timing=false,solve_refinement=false,recovery=false)
 w=J.initialize_workspace(p,opt;progress=J.SimplexProgressContext(p;numerical_policy=pol))
 w.iterations=1;J._observe_stagnation!(w,:dual,zero(T),zero(T));state=w.scratch.stagnation
 mon=monitorof(T,shape,:end);restore!(state.monitor,mon.seed)
 state.last_iteration=1;w.iterations=2
 (scope=scope,w=w,state=state,seed=fields(state),monseed=fields(state.monitor),steps=mon.values[4:5])
end
function reset!(v)
 if v.scope===:progress;restore!(v.m,v.seed)
 elseif v.scope===:workspace
  restore!(v.state,v.seed);restore!(v.state.monitor,v.monseed);v.w.scratch.stagnation=v.state;v.w.iterations=2
 end
 nothing
end
@noinline function whole(a::A,v::V) where {A,V}
 mod=modof(a)
 if v.scope===:ratio;return mod._primal_ratio(v.w,1,v.orientation,v.vector)
 elseif v.scope===:progress
  q=v.values;return mod.observe_progress!(v.m;objective=q[1],primal_violation=q[2],dual_violation=q[3],primal_step=q[4],dual_step=q[5])
 end
 mod._observe_stagnation!(v.w,:dual,v.steps[1],v.steps[2])
end
sink(x::Symbol)=x===:progress ? 1 : x===:watch ? 2 : 3
sink(x::Tuple)=100*x[2]+Int(x[3])+(isnothing(x[1]) ? -10000 : 1)
@noinline function runwhole(a::A,v::V) where {A,V}
 sink(whole(a,v))
end
function timed(a::A,v::V) where {A,V}
 t=@timed runwhole(a,v);merge(cost(t),Dict("sink"=>t.value))
end
function arrays(v)
 v.scope===:progress&&return ()
 w=v.w;A=w.problem.A
 q=(A.nzval,A.rowval,A.colptr,w.problem.objective,w.problem.column_lower,w.problem.column_upper,w.problem.row_lower,w.problem.row_upper,w.costs,w.reduced_costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states,w.primal,w.pricing_weights)
 v.scope===:ratio ? (q...,v.vector) : q
end
snapshot(v)=(arrays(v),map(copy,arrays(v)),deepcopy(arrays(v)))
function intact(v,s)
 a=arrays(v);all(a[k]===s[1][k]&&same(a[k],s[3][k])&&all(a[k][i]===s[2][k][i] for i in eachindex(a[k])) for k in eachindex(a))
end
output(v,x)=v.scope===:ratio ? x : v.scope===:progress ? (x,fields(v.m)) : (x,fields(v.w.scratch.stagnation.monitor),v.w.scratch.stagnation.last_iteration,v.w.scratch.stagnation.cost_scale,v.w.scratch.stagnation.value_scale)
aliaspattern(q)=Bool[q[i]===q[j] for i in eachindex(q),j in eachindex(q)]
function checkpair(a,b,arm)
 reset!(a);reset!(b);sa=snapshot(a);sb=snapshot(b);ctx=(precision(BigFloat),rounding(BigFloat))
 scalar_a=a.scope===:progress ? deepcopy(a.values) : ();scalar_b=b.scope===:progress ? deepcopy(b.values) : ()
 x=capture(()->whole(Val(:original),a));y=capture(()->whole(Val(arm),b))
 @test x[1]===y[1]
 @test x[1]===:value ? same(output(a,x[2]),output(b,y[2])) : same(x,y)
 if a.scope===:progress
  @test same(a.values,scalar_a)&&same(b.values,scalar_b)
  @test aliaspattern((fields(a.m)...,a.values...))==aliaspattern((fields(b.m)...,b.values...))
 end
 @test intact(a,sa)&&intact(b,sb)
 @test ctx==(precision(BigFloat),rounding(BigFloat))
 if x[1]===:value&&a.scope===:ratio&&eltype(a.vector)===BigFloat&&!isnothing(x[2][1])
  z=whole(Val(arm),b);@test z[1]!==y[2][1]
 end
 x
end
function correctness(::Type{T}) where T
 @testset "Ratio and monitor parity $T" begin
  for density in (:sparse,:dense),shape in (:positive,:negative,:mixed,:ties,:unique)
   a=fixture(T,8,density,shape,:ratio);b=fixture(T,8,density,shape,:ratio)
   x=checkpair(a,b,:A);@test x[1]===:value&&x[2][2]>0&&x[2][1]>=0
  end
  for variant in (:zero,:negativezero,:short,:invalidbasis,:nan,:infinity,:rejected,:unbounded,:negative_step,:mixedprecision,:alias,:empty)
   a=fixture(T,8,:dense,:mixed,:ratio);b=fixture(T,8,:dense,:mixed,:ratio)
   for v in (a,b)
    w=v.w
    if variant===:empty;empty!(w.basis.basic_indices)
    elseif variant===:zero;fill!(v.vector,zero(T))
    elseif variant===:negativezero;v.vector[1]=-zero(T)
    elseif variant===:short;empty!(w.lower)
    elseif variant===:invalidbasis;w.basis.basic_indices[end]=length(w.primal)+1
    elseif variant===:nan&&T<:AbstractFloat;v.vector[1]=T(NaN)
    elseif variant===:infinity&&T<:AbstractFloat;v.vector[1]=T(Inf)
    elseif variant===:rejected;push!(w.scratch.rejected_rows,1)
    elseif variant===:unbounded;fill!(w.lower,J._unbounded_bound(T));fill!(w.upper,J._unbounded_bound(T))
    elseif variant===:negative_step;w.primal[w.basis.basic_indices[1]]=T(9)
    elseif variant===:mixedprecision&&T===BigFloat;v.vector[1]=setprecision(()->BigFloat(3//7),BigFloat,512)
    elseif variant===:alias;w.primal[w.basis.basic_indices[1]]=v.vector[1]
    end
   end
   checkpair(a,b,:A)
  end
  # Exact dyadic tolerated violation, both entering orientations and unsafe snap.
  for unsafe in (false,true),direction in (-one(T),one(T))
   a=fixture(T,2,:dense,:negative,:ratio);b=fixture(T,2,:dense,:negative,:ratio)
   for v in (a,b)
    w=v.w;opts=w.options;tol=T(1//8)
    w.options=typeof(opts)((n===:primal_tolerance ? tol : getfield(opts,n) for n in fieldnames(typeof(opts)))...)
    v.vector[1]=-one(T);v.vector[2]=unsafe ? T(10) : -T(2)
    if direction>0;w.lower[1]=J.Bound(zero(T));else;w.upper[1]=J.Bound(zero(T));end
    for i in eachindex(v.vector);v.vector[i]*=direction;end
    w.upper[2]=J.Bound(one(T));w.primal[2]=T(17//16)
    w.lower[3]=J.Bound(zero(T));w.upper[3]=J.Bound(unsafe ? zero(T) : T(2))
    push!(w.scratch.rejected_rows,2)
   end
   a=merge(a,(orientation=direction,));b=merge(b,(orientation=direction,))
   @test J._primal_bound_snap_feasible(a.w,1,direction,a.vector,1)===!unsafe
   @test !J._primal_step_bounds_feasible(a.w,direction,a.vector,one(T))
   x=checkpair(a,b,:A)
   @test x[1]===:value&&(unsafe ? isnothing(x[2][1])&&x[2][2]==-1 : iszero(x[2][1])&&x[2][2]==1)
  end
  # Independent known identity direction: positive step1, largest pivot wins the equal-ratio Harris pass.
  v=fixture(T,8,:dense,:positive,:ratio);x=whole(Val(:A),v)
  @test x[1]==1&&x[2]==8&&x[3]===J.AT_LOWER
  for arm in (:B,:C,:BC),shape in (:positive,:negative,:mixed),phase in (:first,:ordinary,:end)
   checkpair(fixture(T,8,:dense,shape,:progress,phase),fixture(T,8,:dense,shape,:progress,phase),arm)
   checkpair(fixture(T,8,:sparse,shape,:workspace),fixture(T,8,:sparse,shape,:workspace),arm)
  end
  for arm in (:B,:C,:BC),alg in (:all,:primal,:dual,:invalid),bad in (:none,:negative_primal,:nanstep,:infstep)
   a=monitorof(T,:positive,:end);b=monitorof(T,:positive,:end)
   q=a.values
   if bad===:negative_primal;q=(q[1],-one(T),q[3],q[4],q[5])
   elseif bad===:nanstep&&T<:AbstractFloat;q=(q[1],q[2],q[3],T(NaN),q[5])
   elseif bad===:infstep&&T<:AbstractFloat;q=(q[1],q[2],q[3],T(Inf),q[5])
   end
   ctx=(precision(BigFloat),rounding(BigFloat))
   call(mod,m)=mod.observe_progress!(m;algorithm=alg,objective=q[1],primal_violation=q[2],dual_violation=q[3],primal_step=q[4],dual_step=q[5])
   @test same(capture(()->call(RMReference,a.m)),capture(()->call(modof(Val(arm)),b.m)))
   @test same(fields(a.m),fields(b.m))
   @test ctx==(precision(BigFloat),rounding(BigFloat))
  end
  if T===BigFloat
   vals=(BigFloat(0),-BigFloat(0),BigFloat(1),BigFloat(-1),BigFloat(Inf),-BigFloat(Inf),BigFloat(NaN),floatmin(BigFloat),floatmax(BigFloat),setprecision(()->BigFloat(-3//7),BigFloat,512),setprecision(()->BigFloat(3//7),BigFloat,512))
   for x in vals
    old=deepcopy(x);z=max(zero(T),x);v=tested_nonnegative_step(x)
    @test same(z,v);@test (z===x)==(v===x);@test same(x,old)
    if !(z===x);@test v!==tested_nonnegative_step(x);end
   end
   for x in vals,y in vals,s in (BigFloat(1),BigFloat(3//8))
    old=(deepcopy(x),deepcopy(y),deepcopy(s));a=capture(()->RMReference._stagnation_improvement(x,y,s));b=capture(()->RMC._stagnation_improvement(x,y,s))
    @test same(a,b);@test same((x,y,s),old)
    if a[1]===:value;@test (a[2]===x,a[2]===y,a[2]===s)==(b[2]===x,b[2]===y,b[2]===s);end
   end
   for arm in (:B,:C,:BC),variant in (:positive512,:negative512,:signedzero,:infstep,:negativeinf)
    a=fixture(T,8,:dense,:mixed,:progress,:end);b=fixture(T,8,:dense,:mixed,:progress,:end)
    wide=setprecision(()->BigFloat(3//7),BigFloat,512)
    val=variant===:positive512 ? wide : variant===:negative512 ? setprecision(()->BigFloat(-3//7),BigFloat,512) : variant===:signedzero ? -zero(T) : variant===:infstep ? T(Inf) : -T(Inf)
    a=merge(a,(values=(a.values[1],a.values[2],a.values[3],val,val),));b=merge(b,(values=(b.values[1],b.values[2],b.values[3],deepcopy(val),deepcopy(val)),))
    # Shared step owners must be mirrored on both sides.
    b=merge(b,(values=(b.values[1],b.values[2],b.values[3],b.values[4],b.values[4]),))
    checkpair(a,b,arm)
   end
   widepositive=setprecision(BigFloat,512) do;BigFloat(1)+ldexp(BigFloat(1),-300);end
   widenegative=setprecision(()->-widepositive,BigFloat,512)
   @test precision(widepositive)==precision(widenegative)==512
   for arm in (:B,:C,:BC),wide in (widepositive,widenegative)
    a=fixture(T,8,:dense,:mixed,:progress,:end);b=fixture(T,8,:dense,:mixed,:progress,:end)
    for v in (a,b)
     v.m.best_objective=deepcopy(wide);v.m.best_primal=deepcopy(widepositive);v.m.best_dual=deepcopy(widepositive)
    end
    a=merge(a,(seed=fields(a.m),values=(wide,deepcopy(widepositive),deepcopy(widepositive),a.values[4],a.values[5]),))
    b=merge(b,(seed=fields(b.m),values=(deepcopy(wide),deepcopy(widepositive),deepcopy(widepositive),b.values[4],b.values[5]),))
    checkpair(a,b,arm)
    a=fixture(T,8,:dense,:mixed,:workspace);b=fixture(T,8,:dense,:mixed,:workspace)
    for v in (a,b)
     v.w.costs[1]=deepcopy(wide);v.w.lower[1]=J.Bound(deepcopy(widenegative));v.w.upper[1]=J.Bound(deepcopy(widepositive))
    end
    checkpair(a,b,arm)
   end
   for mod in (RMReference,RMC,RMBC),(a,b) in ((BigFloat(1),BigFloat(1)),(widepositive,BigFloat(1)))
    scale=BigFloat(1);z=mod._stagnation_improvement(a,b,scale);q=mod._stagnation_improvement(a,b,scale)
    @test (a==b ? iszero(z)&&iszero(q) : same(z,q))&&z!==q
    @test z!==a&&z!==b&&z!==scale
    @test precision(z)==precision(BigFloat)
   end
   # Unequal stored512 operands whose normalized divisions round equally in all modes.
   near1=setprecision(BigFloat,512) do;BigFloat(1)+ldexp(BigFloat(1),-300);end
   near2=setprecision(BigFloat,512) do;BigFloat(1)+ldexp(BigFloat(1),-299);end
   @test near1!=near2
   for mod in (RMReference,RMC,RMBC)
    scale=BigFloat(2);a=mod._stagnation_improvement(near1,near2,scale);b=mod._stagnation_improvement(near1,near2,scale)
    @test iszero(a)&&iszero(b)&&a!==b
    @test a!==near1&&a!==near2&&a!==scale&&precision(a)==precision(BigFloat)
   end
   # Multi-window independent state transitions and fresh result owners.
   for mod in (RMReference,RMB,RMC,RMBC)
    m=J.StagnationMonitor{T}(2;tolerance=BigFloat(1//128))
    seq=Symbol[]
    for k in 1:4
     push!(seq,mod.observe_progress!(m;objective=BigFloat(1),primal_violation=BigFloat(0),dual_violation=BigFloat(0),primal_step=BigFloat(0),dual_step=BigFloat(0)))
    end
    @test seq==[:progress,:watch,:watch,:stalled]
   end
  end
 end
end

tested_nonnegative_step(x::BigFloat)=isdefined(JSimplex,:_primal_nonnegative_step) ? JSimplex._primal_nonnegative_step(x) : max(zero(BigFloat),x)

@testset "BigFloat ratio zeros and stagnation magnitudes" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   for (scope,arm,phase) in ((:ratio,:A,:end),(:progress,:B,:ordinary),(:progress,:C,:end),(:workspace,:BC,:end))
    @testset "Whole-call allocation $scope/$arm/$phase" begin
     a=fixture(BigFloat,64,:dense,:positive,scope,phase);b=fixture(BigFloat,64,:dense,:positive,scope,phase)
     for k in 1:3,(tag,v) in ((Val(:original),a),(Val(arm),b));reset!(v);timed(tag,v);end
     pairs=Tuple{Dict{String,Any},Dict{String,Any}}[]
     for k in 1:3
      if isodd(k);reset!(a);old=timed(Val(:original),a);reset!(b);new=timed(Val(arm),b)
      else;reset!(b);new=timed(Val(arm),b);reset!(a);old=timed(Val(:original),a)
      end
      @test old["compile_seconds"]==old["recompile_seconds"]==new["compile_seconds"]==new["recompile_seconds"]==0
      push!(pairs,(old,new))
     end
     @test all(new["events"]<old["events"] for (old,new) in pairs)&&median([new["bytes"] for (old,new) in pairs])<median([old["bytes"] for (old,new) in pairs]) # RED whole-call allocation gate
    end
   end
  end
 end
end
end

"""Bounded progress history in working-LP units, with two-window hysteresis.

Exact observations are widened to rational BigInts, never floating point.
Objective observations must omit the model's additive objective constant.
"""
mutable struct StagnationMonitor{T<:Real,S<:Real}
    window::Int
    objective_scale::S
    primal_scale::S
    dual_scale::S
    tolerance::S
    observations::Int
    window_count::Int
    stalled_windows::Int
    insignificant_steps::Int
    state::Symbol
    initialized::Bool
    start_objective::S
    minimum_objective::S
    end_objective::S
    start_primal::S
    minimum_primal::S
    end_primal::S
    start_dual::S
    minimum_dual::S
    end_dual::S
    best_objective::S
    best_primal::S
    best_dual::S
    objective_improvement::S
    primal_improvement::S
    dual_improvement::S
end

mutable struct WorkspaceStagnation{T<:Real,S<:Real}
    monitor::StagnationMonitor{T,S}
    context_key::UInt
    last_iteration::Int
    cost_scale::S
    value_scale::S
end

_stagnation_price_step(price,pivot) = price/pivot
_stagnation_price_step(price::Rational,pivot::Rational) =
    Rational{BigInt}(price)/Rational{BigInt}(pivot)

function _stagnation_context(ws,algorithm)
    p = ws.progress.numerical_policy
    # Checkpoint/cache generations also change at ordinary refactorizations.
    # They are not phase changes and must not erase a watched window.
    key = hash((algorithm,objectid(ws.problem.A),size(ws.problem.A),ws.options.primal_tolerance,
        ws.options.dual_tolerance,p.solve_tolerance,p.stagnation_window))
    # Base's array hash samples sufficiently large arrays. Inspect every entry
    # so a cost or bound change outside that sample still resets the window.
    for values in (ws.costs,ws.lower,ws.upper,ws.progress.scaling.row_factors,
                   ws.progress.scaling.column_factors)
        key = hash(length(values),key)
        for value in values
            key = hash(value,key)
        end
    end
    return key
end

function _new_workspace_stagnation(ws,key)
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
    return WorkspaceStagnation(monitor,key,ws.iterations-1,cost_scale,value_scale)
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
    if isnothing(state) || state.context_key != key
        state = _new_workspace_stagnation(ws,key)
        ws.scratch.stagnation = state
    end
    return _observe_workspace_stagnation!(ws,state,algorithm,primal_step,dual_step)
end

function _observe_workspace_stagnation!(ws,state::WorkspaceStagnation{T,S},
                                       algorithm,primal_step,dual_step) where {T,S}
    m = state.monitor
    objective,primal_violation,dual_violation = _workspace_stagnation_values(ws,state,algorithm)
    result = observe_progress!(m;objective,primal_violation,dual_violation,
        primal_step=(S(primal_step)/state.value_scale)*m.primal_scale,
        dual_step=(S(dual_step)/state.cost_scale)*m.dual_scale)
    state.last_iteration = ws.iterations
    if m.window_count == m.window
        result == :watch && _simplex_event!(ws,:stagnation_watch)
        result == :stalled && _simplex_event!(ws,:stagnation_stalled)
        if result == :stalled && algorithm == :dual &&
           _is_exact(eltype(ws.costs)) === Val(false) &&
           ws.options.pricing == :steepest_edge && !ws.dual_pricing_fallback &&
           primal_infeasibility(ws) > ws.options.primal_tolerance
            ws.dual_pricing_fallback = true
            _simplex_event!(ws,:stagnation_fallback)
        end
    end
    return result
end

function StagnationMonitor{T}(window::Int;objective_scale=one(T),
    primal_scale=one(T),dual_scale=one(T),
    tolerance=T <: Rational ? zero(T) : T(256)*eps(T)) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("Unsupported stagnation type $T"))
    S = T <: Rational ? Rational{BigInt} : T
    scales = (S(objective_scale),S(primal_scale),S(dual_scale))
    limit = S(tolerance)
    window > 0 && all(x -> isfinite(x) && x > 0,scales) &&
        isfinite(limit) && 0 <= limit < 1 ||
        throw(ArgumentError("Invalid stagnation window, scale, or tolerance"))
    T <: Rational && !iszero(limit) &&
        throw(ArgumentError("Exact stagnation comparisons require zero tolerance"))
    z = zero(S)
    return StagnationMonitor{T,S}(window,scales...,limit,0,0,0,0,:progress,false,
        z,z,z,z,z,z,z,z,z,z,z,z,z,z,z)
end

function reset_stagnation!(monitor::StagnationMonitor)
    monitor.window_count = 0
    monitor.stalled_windows = 0
    monitor.insignificant_steps = 0
    monitor.initialized = false
    monitor.state = :progress
    return nothing
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
                           dual_violation,primal_step,dual_step)::Symbol where {T,S}
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
        progress = max(m.objective_improvement,m.primal_improvement,m.dual_improvement) > m.tolerance
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

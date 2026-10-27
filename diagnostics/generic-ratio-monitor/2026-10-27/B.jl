module RMB
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

_stagnation_step_magnitude(value) = abs(value)
_stagnation_step_magnitude(value::BigFloat) = _primal_direction_magnitude(value)

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
        _stagnation_step_magnitude(ps)/m.primal_scale <= m.tolerance && _stagnation_step_magnitude(ds)/m.dual_scale <= m.tolerance
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

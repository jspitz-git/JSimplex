module SSUBC
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


function _primal_unit_basis(workspace::SimplexWorkspace{BigFloat})
    A = workspace.problem.A
    column_count = size(A, 2)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        if index > column_count
            index - column_count == row || return false
        else
            start = A.colptr[index]
            A.colptr[index + 1] == start + 1 || return false
            A.rowval[start] == row || return false
            _primal_direction_magnitude(A.nzval[start]) == Clong(1) || return false
        end
    end
    return true
end


function _primal_unit_basis(workspace::SimplexWorkspace{Rational{BigInt}})
    A = workspace.problem.A
    column_count = size(A, 2)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        if index > column_count
            index - column_count == row || return false
        else
            start = A.colptr[index]
            A.colptr[index + 1] == start + 1 || return false
            A.rowval[start] == row || return false
            value = A.nzval[start]
            (value == 1 || value == -1) || return false
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


function _primal_initialize_steepest!(workspace::SimplexWorkspace{BigFloat})
    T = BigFloat
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
    row_cacheable = false
    row_ready = false
    for index in (column_count + 1):(column_count + row_count)
        workspace.pricing_weights[index] = row_weight
        if !row_ready
            row_cacheable = _primal_cacheable_weight(row_weight)
            row_ready = true
        end
        scratch.steepest_valid[index] = row_cacheable
    end
    return nothing
end


end

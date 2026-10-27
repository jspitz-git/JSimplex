module ISDReference
using JSimplex,SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,WorkspaceStagnation,StagnationMonitor,VariableState,
 BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,Bound,Basis,LinearProblem,SolverOptions,
 _is_fixed,bound_value,_primal_direction_magnitude,_finite_workspace,_with_recovery_precision,
 observe_progress!,reset_stagnation!,_simplex_event!,_is_exact,_primal_nearest_rounding,
 _refined_primal_rows_feasible,_native_basic_certificate_mode,_native_basic_column_interval,
 _native_basic_intersection,_pipeline_unit_rhs!,_checked_basis_solve!,price!
function _primal_sum_bounds(left::T, right::T) where {T<:Rational}
    value = left + right
    return value, value
end

function _primal_sum_bounds(left::T, right::T) where {T<:AbstractFloat}
    iszero(left) && return right, right
    iszero(right) && return left, left
    isfinite(left) && precision(right) == precision(T) && left == -right &&
        return zero(T), zero(T)
    value = left + right
    # FastTwoSum is exact when intermediate residuals cannot underflow.
    # Other rounding modes and mixed BigFloat precisions use the enclosure.
    if isfinite(value) && _primal_nearest_rounding(T) &&
       precision(left) == precision(right) == precision(T) &&
       min(abs(left), abs(right)) >= ldexp(nextfloat(zero(T)), precision(T))
        large, small = abs(left) >= abs(right) ? (left, right) : (right, left)
        error = (large - value) + small
        if isfinite(error)
            return error < zero(T) ? (prevfloat(value), value) :
                   error > zero(T) ? (value, nextfloat(value)) : (value, value)
        end
    end
    return prevfloat(value), nextfloat(value)
end

# Reuse invocation-local magnitudes only inside the original BigFloat guard.
function _primal_sum_bounds(left::BigFloat, right::BigFloat)
    T=BigFloat
    iszero(left) && return right, right
    iszero(right) && return left, left
    isfinite(left) && precision(right) == precision(T) && left == -right &&
        return zero(T), zero(T)
    value = left + right
    # FastTwoSum is exact when intermediate residuals cannot underflow.
    # Other rounding modes and mixed BigFloat precisions use the enclosure.
    if isfinite(value) && _primal_nearest_rounding(T) &&
       precision(left) == precision(right) == precision(T)
        left_magnitude, right_magnitude = abs(left), abs(right)
        if min(left_magnitude, right_magnitude) >= ldexp(nextfloat(zero(T)), precision(T))
            large, small = left_magnitude >= right_magnitude ? (left, right) : (right, left)
            error = (large - value) + small
            if isfinite(error)
                return error < 0 ? (prevfloat(value), value) :
                       error > 0 ? (value, nextfloat(value)) : (value, value)
            end
        end
    end
    return prevfloat(value), nextfloat(value)
end


_primal_difference_bounds(left::T, right::T) where {T<:Rational} =
    _primal_sum_bounds(left, -right)

function _primal_difference_bounds(left::T, right::T) where {T<:AbstractFloat}
    precision(right) == precision(T) && return _primal_sum_bounds(left, -right)
    # Negating an older, higher-precision tolerance can round before the sum.
    value = left - right
    return prevfloat(value), nextfloat(value)
end

# Integer comparison is exact and avoids temporary multiprecision constants.
_primal_positive_unit(value::T) where T = value == one(T)
_primal_positive_unit(value::BigFloat) = value == 1
_primal_negative_unit(value::T) where T = value == -one(T)
_primal_negative_unit(value::BigFloat) = value == -1

function _primal_product_bounds(left::T, right::T) where {T<:AbstractFloat}
    (iszero(left) || iszero(right)) && return zero(T), zero(T)
    _primal_positive_unit(left) && return right, right
    _primal_positive_unit(right) && return left, left
    _primal_negative_unit(left) && precision(right) == precision(T) && return -right, -right
    _primal_negative_unit(right) && precision(left) == precision(T) && return -left, -left
    value = left * right
    if isfinite(value) && _primal_nearest_rounding(T)
        error = fma(left, right, -value)
        # A nonzero fused residual has a conclusive sign. Zero only proves
        # exactness when the product's finest possible bit cannot underflow.
        if isfinite(error) && (!iszero(error) ||
           abs(value) >= ldexp(nextfloat(zero(T)), precision(left) + precision(right)))
            return error < zero(T) ? (prevfloat(value), value) :
                   error > zero(T) ? (value, nextfloat(value)) : (value, value)
        end
    end
    return prevfloat(value), nextfloat(value)
end

# Exact integer comparisons avoid temporary zeros; every enclosure guard remains.
function _primal_product_bounds(left::BigFloat, right::BigFloat)
    T=BigFloat
    (iszero(left) || iszero(right)) && return zero(T), zero(T)
    _primal_positive_unit(left) && return right, right
    _primal_positive_unit(right) && return left, left
    _primal_negative_unit(left) && precision(right) == precision(T) && return -right, -right
    _primal_negative_unit(right) && precision(left) == precision(T) && return -left, -left
    value = left * right
    if isfinite(value) && _primal_nearest_rounding(T)
        error = fma(left, right, -value)
        # A nonzero fused residual has a conclusive sign. Zero only proves
        # exactness when the product's finest possible bit cannot underflow.
        if isfinite(error) && (!iszero(error) ||
           abs(value) >= ldexp(nextfloat(zero(T)), precision(left) + precision(right)))
            return error < 0 ? (prevfloat(value), value) :
                   error > 0 ? (value, nextfloat(value)) : (value, value)
        end
    end
    return prevfloat(value), nextfloat(value)
end


function _primal_product_bounds(left::T, right::T) where {T<:Rational}
    value = left * right
    return value, value
end

function _primal_row_bounds(A::SparseMatrixCSC{T,Int}, primal::Vector{T},
                            ::Val{true}) where {T<:Rational}
    values = A * primal
    return values, values
end

function _primal_row_bounds(A::SparseMatrixCSC{T,Int}, primal::Vector{T},
                            ::Val{false}) where {T<:AbstractFloat}
    lower, upper = Vector{T}(undef, size(A, 1)), Vector{T}(undef, size(A, 1))
    return _primal_row_bounds!(lower, upper, A, primal)
end

# Keep the allocating and reusable paths in the same arithmetic order.
function _primal_row_bounds!(lower::Vector{T}, upper::Vector{T},
                             A::SparseMatrixCSC{T,Int}, primal::Vector{T}) where {T<:AbstractFloat}
    fill!(lower, zero(T))
    fill!(upper, zero(T))
    for column in axes(A, 2)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            row = A.rowval[position]
            product_lower, product_upper = _primal_product_bounds(A.nzval[position], primal[column])
            lower[row], _ = _primal_sum_bounds(lower[row], product_lower)
            _, upper[row] = _primal_sum_bounds(upper[row], product_upper)
        end
    end
    return lower, upper
end

function _primal_interval_within_bounds(value_lower::T, value_upper::T,
                                        lower::Bound{T}, upper::Bound{T},
                                        tolerance::T) where {T}
    isfinite(value_lower) && isfinite(value_upper) || return false
    if isfinite(lower) && value_lower < bound_value(lower)
        _, threshold = _primal_difference_bounds(bound_value(lower), tolerance)
        value_lower >= threshold || return false
    end
    if isfinite(upper) && value_upper > bound_value(upper)
        threshold, _ = _primal_sum_bounds(bound_value(upper), tolerance)
        value_upper <= threshold || return false
    end
    return true
end

function _within_primal_intervals(values_lower::AbstractVector{T}, values_upper::AbstractVector{T},
                                  lower::AbstractVector{Bound{T}}, upper::AbstractVector{Bound{T}},
                                  tolerance::T) where {T}
    for index in eachindex(values_lower)
        _primal_interval_within_bounds(values_lower[index], values_upper[index],
                                       lower[index], upper[index], tolerance) || return false
    end
    return true
end

_within_primal_bounds(values::AbstractVector{T}, lower::AbstractVector{Bound{T}},
                      upper::AbstractVector{Bound{T}}, tolerance::T) where {T} =
    _within_primal_intervals(values, values, lower, upper, tolerance)


function _primal_feasible_with_bounds(problem::LinearProblem{T}, primal::Vector{T},
                                      tolerance::T, column_lower, column_upper,
                                      row_bound_lower, row_bound_upper, row_bounds=nothing, buffers=nothing, share_native::Bool=false) where {T}
    _within_primal_bounds(primal, column_lower, column_upper, tolerance) || return false
    row_lower, row_upper = isnothing(row_bounds) ?
        _primal_row_bounds(problem.A, primal, _is_exact(T)) : row_bounds
    # Certify the entire activity interval in the requested absolute units.
    # Cancellation uncertainty must not enlarge the configured tolerance.
    if isnothing(buffers) || !(T <: Union{Float32,Float64})
        _within_primal_intervals(row_lower, row_upper, row_bound_lower,
                                 row_bound_upper, tolerance) && return true
    end
    # A long floating sum can have a wider enclosure than the absolute
    # tolerance, or overflow before cancellation, even when its exact
    # stored-coefficient activity is feasible. Exact fallback checks finite
    # coefficients independently and does not enlarge the user tolerance.
    T <: Union{Float32,Float64} || return false
    rows = isnothing(buffers) ? Int[] : empty!(buffers.rows)
    for row in eachindex(row_lower)
        _primal_interval_within_bounds(row_lower[row], row_upper[row],
                                       row_bound_lower[row], row_bound_upper[row],
                                       tolerance) || push!(rows, row)
    end
    isempty(rows) && return true
    return _refined_primal_rows_feasible(problem, primal, tolerance, rows,
                                          row_bound_lower, row_bound_upper, buffers, share_native)
end

function _original_primal_feasible(problem::LinearProblem{T}, primal::Vector{T}, tolerance::T) where {T}
    return _primal_feasible_with_bounds(problem, primal, tolerance,
        problem.column_lower, problem.column_upper, problem.row_lower, problem.row_upper)
end

_original_primal_feasible(workspace::SimplexWorkspace{T}, primal::Vector{T}) where {T} =
    _original_primal_feasible(workspace.problem, primal, workspace.options.primal_tolerance)

function _original_reduced_cost_bounds(problem::LinearProblem{T}, dual::Vector{T}) where {T}
    A = problem.A
    column_count = size(A, 2)
    lower = Vector{T}(undef, column_count + length(dual))
    upper = Vector{T}(undef, column_count + length(dual))
    copyto!(lower, column_count + 1, dual, 1, length(dual))
    copyto!(upper, column_count + 1, dual, 1, length(dual))
    for column in 1:column_count
        minimum_dot = maximum_dot = zero(T)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            product_lower, product_upper = _primal_product_bounds(A.nzval[position], dual[A.rowval[position]])
            minimum_dot, _ = _primal_sum_bounds(minimum_dot, product_lower)
            _, maximum_dot = _primal_sum_bounds(maximum_dot, product_upper)
        end
        lower[column], _ = _primal_difference_bounds(problem.objective[column], maximum_dot)
        _, upper[column] = _primal_difference_bounds(problem.objective[column], minimum_dot)
    end
    # Working row-activity columns are -I and have zero original cost.
    return lower, upper
end

function _primal_interval_at_bound(lower::T, upper::T, bound::Bound{T}, tolerance::T) where {T}
    isfinite(bound) && isfinite(lower) && isfinite(upper) || return false
    value = bound_value(bound)
    if lower < value
        _, threshold = _primal_difference_bounds(value, tolerance)
        lower >= threshold || return false
    end
    if upper > value
        threshold, _ = _primal_sum_bounds(value, tolerance)
        upper <= threshold || return false
    end
    return true
end

function _original_witness_certified(problem::LinearProblem{T}, options::SolverOptions{T},
                                     basis::Basis, primal::Vector{T}, dual::Vector{T}) where T
    row_count, column_count = size(problem.A)
    length(primal) == column_count && length(dual) == row_count &&
        length(basis.states) == column_count + row_count || return false
    all(isfinite, primal) && all(isfinite, dual) || return false
    reduced_lower, reduced_upper = _original_reduced_cost_bounds(problem, dual)
    all(isfinite, reduced_lower) && all(isfinite, reduced_upper) || return false
    row_lower, row_upper = _primal_row_bounds(problem.A, primal, _is_exact(T))
    _, negative_tolerance = _primal_difference_bounds(zero(T), options.dual_tolerance)
    uncertain_rows = nothing
    active_bounds = nothing
    native_basic_mode = UInt8(0) # Invocation-local: unknown/enabled/disabled.
    for index in eachindex(reduced_lower)
        stationary = reduced_lower[index] >= negative_tolerance &&
                     reduced_upper[index] <= options.dual_tolerance
        if basis.states[index] == BASIC && !stationary
            T <: Union{Float32,Float64} && index <= column_count || return false
            (reduced_upper[index] < negative_tolerance ||
             reduced_lower[index] > options.dual_tolerance) && return false
            if native_basic_mode == UInt8(0)
                native_basic_mode = _native_basic_certificate_mode(T) ? UInt8(1) : UInt8(2)
            end
            native_basic_mode == UInt8(1) || return false
            refined = _native_basic_column_interval(problem, dual, index)
            isnothing(refined) && return false
            intersection = _native_basic_intersection(
                (reduced_lower[index], reduced_upper[index]), refined)
            isnothing(intersection) && return false
            reduced_lower[index], reduced_upper[index] = intersection
            stationary = reduced_lower[index] >= negative_tolerance &&
                         reduced_upper[index] <= options.dual_tolerance
            stationary || return false
        end
        stationary && continue
        lower = index <= column_count ? problem.column_lower[index] : problem.row_lower[index - column_count]
        upper = index <= column_count ? problem.column_upper[index] : problem.row_upper[index - column_count]
        _is_fixed(lower, upper) && continue
        # Use actual structural values and certified original row activities,
        # not stored slack values or a possibly stale nonbasic bound label.
        value_lower = index <= column_count ? primal[index] : row_lower[index - column_count]
        value_upper = index <= column_count ? primal[index] : row_upper[index - column_count]
        at_lower = reduced_lower[index] >= negative_tolerance &&
                   _primal_interval_at_bound(value_lower, value_upper, lower,
                                             options.primal_tolerance)
        at_upper = reduced_upper[index] <= options.dual_tolerance &&
                   _primal_interval_at_bound(value_lower, value_upper, upper,
                                             options.primal_tolerance)
        at_lower || at_upper || begin
            # Cancellation can make the coarse activity interval inconclusive
            # even when native compensated feasibility has already succeeded.
            # Recheck distance to the priced bound, not just row feasibility.
            index > column_count && T <: Union{Float32,Float64} || return false
            active_bound = reduced_lower[index] >= negative_tolerance ? lower :
                           reduced_upper[index] <= options.dual_tolerance ? upper : nothing
            isnothing(active_bound) && return false
            isfinite(active_bound) || return false
            if isnothing(uncertain_rows)
                uncertain_rows = Int[]
                active_bounds = copy(problem.row_lower)
            end
            row = index - column_count
            push!(uncertain_rows, row)
            active_bounds[row] = active_bound
        end
    end
    isnothing(uncertain_rows) && return true
    return _refined_primal_rows_feasible(problem, primal, options.primal_tolerance,
                                         uncertain_rows, active_bounds, active_bounds)
end

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

function _workspace_stagnation_values(ws::SimplexWorkspace{BigFloat},state::WorkspaceStagnation{BigFloat,BigFloat},algorithm)
    S = BigFloat
    m = state.monitor
    objective, primal, dual = zero(S),zero(S),zero(S)
    comparison_zero = primal
    dual_threshold = nothing
    primal_threshold = nothing
    for j in eachindex(ws.costs)
        objective += ((S(ws.costs[j])/state.cost_scale)*
            (S(ws.primal[j])/state.value_scale))*m.objective_scale
        status = ws.basis.states[j]
        (status == BASIC || _is_fixed(ws.lower[j],ws.upper[j])) && continue
        price = S(ws.reduced_costs[j])/state.cost_scale
        violation = status == AT_LOWER ? -price : status == AT_UPPER ? price : _primal_direction_magnitude(price)
        if isnothing(dual_threshold)
            dual_threshold = S(ws.options.dual_tolerance)/state.cost_scale
        end
        violation > dual_threshold &&
            (dual += violation*m.dual_scale)
    end
    for j in ws.basis.basic_indices
        value = S(ws.primal[j])/state.value_scale
        lower = isfinite(ws.lower[j]) ? S(bound_value(ws.lower[j]))/state.value_scale-value : comparison_zero
        upper = isfinite(ws.upper[j]) ? value-S(bound_value(ws.upper[j]))/state.value_scale : comparison_zero
        violation = max(comparison_zero,lower,upper)
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

_primal_devex_leaving_weight(weight::T, pivot::T) where {T<:AbstractFloat} =
    max(one(T), min(floatmax(T), weight / abs(pivot)))
_primal_store_rational_weight(::Type{Rational{BigInt}}, weight::Rational{BigInt}) = weight
function _primal_store_rational_weight(::Type{Rational{I}},
                                       weight::Rational{BigInt}) where {I<:Integer}
    limit = BigInt(typemax(I))
    numerator_value, denominator_value = numerator(weight), denominator(weight)
    if numerator_value <= limit && denominator_value <= limit
        return convert(I, numerator_value) // convert(I, denominator_value)
    end
    # Devex is an estimate; retain a positive, representable integer weight.
    return convert(I, min(limit, div(numerator_value, denominator_value))) // one(I)
end
_primal_devex_leaving_weight(weight::T, pivot::T) where {T<:Rational} =
    _primal_store_rational_weight(T, max(one(Rational{BigInt}),
                                         big(weight) / big(pivot)^2))

_primal_devex_candidate_weight(coefficient::T, leaving_weight::T) where {T<:AbstractFloat} =
    min(floatmax(T), abs(coefficient) * leaving_weight)
_primal_devex_candidate_weight(coefficient::T, leaving_weight::T) where {T<:Rational} =
    _primal_store_rational_weight(T, big(coefficient)^2 * big(leaving_weight))

_primal_devex_candidate_weight(coefficient::BigFloat,leaving_weight::BigFloat) = begin
    product = _primal_direction_magnitude(coefficient) * leaving_weight
    isinf(product) && !signbit(product) ? floatmax(BigFloat) : product
end
function _primal_update_devex!(workspace::SimplexWorkspace{T}, entering::Int,
                               leaving_row::Int, pivot::T; shared_row::Bool=false) where {T}
    tableau_row = workspace.scratch.tableau_row
    if !shared_row
        unit = _pipeline_unit_rhs!(workspace,leaving_row)
        rho = _checked_basis_solve!(workspace.scratch.rho,workspace,unit;
                                    transposed=true,operation=:weight_btran,unit_row=leaving_row)
        price!(tableau_row, workspace, rho)
    end
    leaving = workspace.basis.basic_indices[leaving_row]
    leaving_weight = _primal_devex_leaving_weight(
        workspace.pricing_weights[entering], pivot,
    )
    for index in eachindex(workspace.basis.states)
        (index == entering || workspace.basis.states[index] == BASIC) && continue
        workspace.pricing_weights[index] = max(
            workspace.pricing_weights[index],
            _primal_devex_candidate_weight(tableau_row[index], leaving_weight),
        )
    end
    workspace.pricing_weights[leaving] = leaving_weight
    return nothing
end
end

module SRGB
import JSimplex
using JSimplex: SimplexWorkspace,LinearProblem,Bound,bound_value,PFIFactorization,_is_exact,_primal_nearest_rounding,_primal_direction_magnitude,_infeasibility_bound_allowance,_factor_storage_count,_with_recovery_precision,refactor_reason
using SparseArrays
_refined_primal_rows_feasible(args...) = JSimplex._refined_primal_rows_feasible(args...)
_infeasibility_certified(w::SimplexWorkspace{T},rho::Vector{T},b::Bool) where {T<:AbstractFloat} = JSimplex._infeasibility_certified(w,rho,b)
_factor_growth_measure(factor) = JSimplex._factor_growth_measure(factor)
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
        left_magnitude, right_magnitude = _primal_direction_magnitude(left), _primal_direction_magnitude(right)
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
           _primal_direction_magnitude(value) >= ldexp(nextfloat(zero(T)), precision(left) + precision(right)))
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


_refined_primal_rows_feasible(::LinearProblem, ::Vector, tolerance, rows) = false

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

function _infeasibility_certified(workspace::SimplexWorkspace{T},
                                  rho::Vector{T}, below::Bool) where {T<:Rational}
    try
        A = workspace.problem.A
        n = size(A,2)
        orientation = below ? one(T) : -one(T)
        minimum_value = zero(T)
        for index in eachindex(workspace.lower)
            coefficient = zero(T)
            if index <= n
                for position in nzrange(A,index)
                    coefficient += orientation*rho[A.rowval[position]]*A.nzval[position]
                end
            else
                coefficient = -orientation*rho[index-n]
            end
            iszero(coefficient) && continue
            bound = coefficient > zero(T) ? workspace.lower[index] : workspace.upper[index]
            isfinite(bound) || return false
            minimum_value += coefficient*bound_value(bound) -
                abs(coefficient)*_infeasibility_bound_allowance(workspace,index)
        end
        return minimum_value > zero(T)
    catch exception
        # Bounded rational intermediates may exceed their integer storage.
        # Failure to represent the proof is inconclusive, never infeasibility.
        exception isa OverflowError || rethrow()
        return false
    end
end

function _infeasibility_certified(workspace::SimplexWorkspace{Rational{BigInt}},
                                  rho::Vector{Rational{BigInt}}, below::Bool)
    T = Rational{BigInt}
    try
        A = workspace.problem.A
        n = size(A,2)
        minimum_value = zero(T)
        for index in eachindex(workspace.lower)
            coefficient = zero(T)
            if index <= n
                for position in nzrange(A,index)
                    coefficient += (below ? rho[A.rowval[position]] : -rho[A.rowval[position]])*A.nzval[position]
                end
            else
                coefficient = below ? -rho[index-n] : rho[index-n]
            end
            iszero(coefficient) && continue
            bound = coefficient > zero(T) ? workspace.lower[index] : workspace.upper[index]
            isfinite(bound) || return false
            minimum_value += coefficient*bound_value(bound) -
                abs(coefficient)*_infeasibility_bound_allowance(workspace,index)
        end
        return minimum_value > zero(T)
    catch exception
        # Bounded rational intermediates may exceed their integer storage.
        # Failure to represent the proof is inconclusive, never infeasibility.
        exception isa OverflowError || rethrow()
        return false
    end
end

_factor_growth_measure(factor::PFIFactorization{T}) where T =
    maximum(eta -> maximum(abs,eta.values;init=one(T)),factor.updates;init=one(T))

function _refresh_refactor_metrics!(ws;force::Bool=false)
    state = ws.scratch.refactorization
    age = state.nupdates = length(ws.factorization.updates)
    if !force
        age == state.metrics_update_count && return nothing
        age == 1 || iszero(age % 8) || age >= state.interval || return nothing
    end
    state.stored_elements = _factor_storage_count(ws.factorization)
    if !state.fixed
        state.growth_scale = _with_recovery_precision(ws,ws) do
            current = _factor_growth_measure(ws.factorization)
            baseline = state.base_growth_scale
            iszero(baseline) ? (iszero(current) ? 1.0 : Inf) : Float64(current/baseline)
        end
    end
    state.metrics_update_count = age
    return nothing
end

function _scheduled_refactor_reason(ws, algorithm::Symbol)
    if ws.progress.numerical_policy.adaptive_refactor
        state = ws.scratch.refactorization
        state.nupdates = length(ws.factorization.updates)
        state.fixed || _refresh_refactor_metrics!(ws)
        # Preserve numerical reason priority when a safety limit coincides
        # with a residual or growth trigger.
        reason = refactor_reason(state,ws.progress.numerical_policy)
        reason != :none && return reason
        # Once the numerical limit fully recovers, economics may again grow
        # the interval beyond the configured initial value.
        return state.nupdates >= ws.dual_refactorization_interval ? :limit : :none
    end
    interval = min(ws.options.refactorization_interval, ws.dual_refactorization_interval)
    return length(ws.factorization.updates) >= interval ? :limit : :none
end


end

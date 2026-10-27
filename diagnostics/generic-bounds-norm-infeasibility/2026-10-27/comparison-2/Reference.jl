module BNIReference
import JSimplex
using JSimplex: SimplexWorkspace,Bound,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,bound_value,_lower_violation,_upper_violation,_can_preserve_primal_bound_value,_primal_relaxed_step,_legacy_primal_row_validation_enabled,_primal_direction_magnitude,_pipeline_column_rhs!,_checked_basis_solve!,_primal_cacheable_weight,_primal_unit_basis,_add_product_bounds,_infeasibility_bound_allowance
function _primal_bound_snap_feasible(workspace::SimplexWorkspace{T}, entering::Int,
                                    direction::T, column::Vector{T}, leaving_row::Int) where {T}
    leaving = workspace.basis.basic_indices[leaving_row]
    movement = -direction * column[leaving_row]
    bound = movement > zero(T) ? workspace.upper[leaving] : workspace.lower[leaving]
    step = (bound_value(bound) - workspace.primal[leaving]) / movement
    step >= zero(T) && return true
    state = movement > zero(T) ? AT_UPPER : AT_LOWER
    _can_preserve_primal_bound_value(workspace, leaving, state, bound) && return true
    # A tolerated bound violation has a negative ratio. Clipping it to zero
    # does not eliminate the movement imposed by fixing the leaving variable
    # exactly at its bound during the subsequent basis recomputation.
    value = workspace.primal[entering] + direction * step
    isfinite(value) || return false
    tolerance = workspace.options.primal_tolerance
    violation = max(zero(T), _lower_violation(workspace.lower[entering], value),
                    _upper_violation(workspace.upper[entering], value))
    violation <= tolerance || return false
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row == leaving_row && continue
        value = workspace.primal[index] - direction * column[row] * step
        isfinite(value) || return false
        bound_violation = max(zero(T), _lower_violation(workspace.lower[index], value),
                              _upper_violation(workspace.upper[index], value))
        # Use the same per-bound feasibility criterion as legacy Harris pricing
        # and recomputation, including the movement imposed by this bound snap.
        violation = max(violation, bound_violation)
        violation <= tolerance || return false
    end
    return true
end

function _primal_bound_snap_feasible(workspace::SimplexWorkspace{BigFloat}, entering::Int,
                                    direction::BigFloat, column::Vector{BigFloat}, leaving_row::Int)
    T = BigFloat
    leaving = workspace.basis.basic_indices[leaving_row]
    movement = -direction * column[leaving_row]
    bound = movement > 0 ? workspace.upper[leaving] : workspace.lower[leaving]
    step = (bound_value(bound) - workspace.primal[leaving]) / movement
    step >= 0 && return true
    state = movement > 0 ? AT_UPPER : AT_LOWER
    _can_preserve_primal_bound_value(workspace, leaving, state, bound) && return true
    # A tolerated bound violation has a negative ratio. Clipping it to zero
    # does not eliminate the movement imposed by fixing the leaving variable
    # exactly at its bound during the subsequent basis recomputation.
    value = workspace.primal[entering] + direction * step
    isfinite(value) || return false
    tolerance = workspace.options.primal_tolerance
    violation = max(zero(T), _lower_violation(workspace.lower[entering], value),
                    _upper_violation(workspace.upper[entering], value))
    violation <= tolerance || return false
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row == leaving_row && continue
        value = workspace.primal[index] - direction * column[row] * step
        isfinite(value) || return false
        bound_violation = max(zero(T), _lower_violation(workspace.lower[index], value),
                              _upper_violation(workspace.upper[index], value))
        # Use the same per-bound feasibility criterion as legacy Harris pricing
        # and recomputation, including the movement imposed by this bound snap.
        violation = max(violation, bound_violation)
        violation <= tolerance || return false
    end
    return true
end


function _primal_step_bounds_feasible(workspace::SimplexWorkspace{T}, direction::T,
                                      column::Vector{T}, step::T) where {T}
    tolerance = workspace.options.primal_tolerance
    for (row, index) in enumerate(workspace.basis.basic_indices)
        value = workspace.primal[index] - direction * column[row] * step
        isfinite(value) || return false
        violation = max(zero(T), _lower_violation(workspace.lower[index], value),
                        _upper_violation(workspace.upper[index], value))
        violation <= tolerance || return false
    end
    return true
end

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

# Keep a fresh zero, NaN handling and signed-zero selection on the fallback path.
_primal_nonnegative_step(value::BigFloat) = value > 0 ? value : max(zero(BigFloat),value)

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
        candidate = _primal_nonnegative_step(raw_step)
        if !has_step || candidate < strict_step ||
           (candidate == strict_step && strict_row == 0)
            strict_step = candidate
            strict_row = row
            strict_state = movement > 0 ? AT_UPPER : AT_LOWER
            has_step = true
        end
        relaxed = _primal_relaxed_step(raw_step, tolerance, movement)
        if isfinite(relaxed) && (!has_relaxed_limit || relaxed < relaxed_limit)
            relaxed_limit = _primal_nonnegative_step(relaxed)
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
        candidate = _primal_nonnegative_step(
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


function _primal_direction_weight(direction::AbstractVector{T}) where {T<:AbstractFloat}
    scale = one(T)
    for coefficient in direction
        scale = max(scale, _primal_direction_magnitude(coefficient))
    end
    scaled_square = abs2(inv(scale))
    for coefficient in direction
        scaled_square += abs2(coefficient / scale)
    end
    factor = sqrt(scaled_square)
    scale_mantissa, scale_exponent = frexp(scale)
    factor_mantissa, factor_exponent = frexp(factor)
    mantissa, correction = frexp(scale_mantissa * factor_mantissa)
    # Keep the exponent separately: a finite column can have a norm above floatmax(T).
    scaled_weight = (scale_exponent + factor_exponent + correction, mantissa)
    stored_weight = min(floatmax(T), scale * factor)
    return scaled_weight, stored_weight
end

function _primal_direction_weight(direction::AbstractVector{T}) where {T<:Rational}
    weight = one(Rational{BigInt})
    for coefficient in direction
        weight += abs2(big(coefficient))
    end
    stored_weight = T === Rational{BigInt} ? weight : one(T)
    return weight, stored_weight
end

function _primal_steepest_weight!(workspace::SimplexWorkspace{T}, index::Int) where {T}
    column = _pipeline_column_rhs!(workspace,index)
    direction = _checked_basis_solve!(workspace.scratch.row_solution,workspace,column;
                                      operation=:weight_ftran)
    scaled_weight, stored_weight = _primal_direction_weight(direction)
    workspace.pricing_weights[index] = stored_weight
    workspace.scratch.steepest_valid[index] = _primal_cacheable_weight(stored_weight)
    return scaled_weight
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

function _floating_infeasibility_certified(workspace::SimplexWorkspace{T},
                                          rho::Vector{T}, below::Bool) where {T<:AbstractFloat}
    # Every feasible working vector satisfies [A -I] * x == 0. A row
    # combination must stay positive over the tolerance envelope of the bounds.
    # This does not rely on the computed basic primal values.
    A = workspace.problem.A
    column_count = size(A, 2)
    orientation = below ? one(T) : -one(T)
    minimum_value = zero(T)
    for index in eachindex(workspace.lower)
        coefficient_lower = coefficient_upper = zero(T)
        if index <= column_count
            for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                coefficient_lower, coefficient_upper = _add_product_bounds(
                    coefficient_lower, coefficient_upper,
                    orientation * rho[A.rowval[position]], A.nzval[position],
                )
            end
        else
            coefficient_lower = coefficient_upper = -orientation * rho[index - column_count]
        end
        isfinite(coefficient_lower) && isfinite(coefficient_upper) || return false
        iszero(coefficient_lower) && iszero(coefficient_upper) && continue

        lower, upper = workspace.lower[index], workspace.upper[index]
        !isfinite(lower) && coefficient_upper > zero(T) && return false
        !isfinite(upper) && coefficient_lower < zero(T) && return false
        isfinite(lower) || isfinite(upper) || return false
        endpoint = isfinite(lower) ? bound_value(lower) : bound_value(upper)
        term = min(coefficient_lower * endpoint, coefficient_upper * endpoint)
        if isfinite(lower) && isfinite(upper)
            endpoint = bound_value(upper)
            term = min(term, coefficient_lower * endpoint, coefficient_upper * endpoint)
        end
        isfinite(term) || return false
        contribution = prevfloat(term)
        allowance = _infeasibility_bound_allowance(workspace,index)
        if !iszero(allowance)
            magnitude = nextfloat(max(abs(coefficient_lower),abs(coefficient_upper)))
            penalty = nextfloat(magnitude*allowance)
            isfinite(penalty) || return false
            contribution = prevfloat(contribution-penalty)
        end
        total = minimum_value + contribution
        isfinite(total) || return false
        minimum_value = prevfloat(total)
    end
    return minimum_value > zero(T)
end

_infeasibility_certified(w::SimplexWorkspace{T},rho::Vector{T},below::Bool) where {T<:AbstractFloat} = _floating_infeasibility_certified(w,rho,below)
_infeasibility_certified(w::SimplexWorkspace{T},rho::Vector{T},below::Bool) where {T<:Rational} = JSimplex._infeasibility_certified(w,rho,below)

end

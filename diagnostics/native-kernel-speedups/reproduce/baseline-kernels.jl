# Frozen arithmetic from production 9f9c2a0; diagnostic oracle only.
function _baseline_direction_residual!(workspace::SimplexWorkspace{T},
                                      direction::Vector{T}, pivot::T) where {T<:AbstractFloat}
    A = workspace.problem.A
    column_count = size(A, 2)
    residual = workspace.scratch.tau
    scale = workspace.scratch.row_rhs
    _pipeline_changed!(workspace,residual)
    _pipeline_changed!(workspace,scale)
    for row in eachindex(residual)
        rhs = scale[row]
        residual[row] = -rhs
        scale[row] = abs(rhs)
    end
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        value = direction[basis_row]
        if index <= column_count
            for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                row = A.rowval[position]
                term = A.nzval[position] * value
                residual[row] += term
                scale[row] += abs(term)
            end
        else
            row = index - column_count
            residual[row] -= value
            scale[row] += abs(value)
        end
    end
    roundoff = T(256) * eps(one(T))
    pivot_tolerance = sqrt(eps(one(T))) * abs(pivot)
    for row in eachindex(residual)
        isfinite(residual[row]) && isfinite(scale[row]) || return false
        tolerance = max(workspace.options.zero_tolerance, pivot_tolerance,
                        roundoff * (scale[row] + one(T)))
        abs(residual[row]) <= tolerance || return false
    end
    return true
end

# The entering direction can be accurate even when an updated factorization
# gives an inaccurate tableau row and therefore the wrong ratio-test choice.
# Check Bᵀ*rho = e_leaving against the current basis before the ratio test.
function _baseline_row_residual(workspace::SimplexWorkspace{T},
                                  rho::Vector{T}, leaving_row::Int) where {T<:AbstractFloat}
    A = workspace.problem.A
    column_count = size(A, 2)
    roundoff = T(256) * eps(one(T))
    worst_ratio = zero(T)
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        expected = basis_row == leaving_row ? one(T) : zero(T)
        residual = -expected
        scale = expected
        if index <= column_count
            for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                term = A.nzval[position] * rho[A.rowval[position]]
                residual += term
                scale += abs(term)
            end
        else
            term = -rho[index - column_count]
            residual += term
            scale += abs(term)
        end
        isfinite(residual) && isfinite(scale) || return T(Inf)
        tolerance = max(workspace.options.zero_tolerance,
                        roundoff * (scale + one(T)))
        isfinite(tolerance) || return T(Inf)
        worst_ratio = max(worst_ratio, abs(residual) / tolerance)
    end
    return worst_ratio
end

function _baseline_reduced_costs!(prices, workspace::SimplexWorkspace{T}, dual) where T
    A = workspace.problem.A
    row_count, column_count = size(A)
    for column in 1:column_count
        reduced_cost = workspace.costs[column]
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            reduced_cost -= A.nzval[position] * dual[A.rowval[position]]
        end
        prices[column] = reduced_cost
    end
    for row in 1:row_count
        index = column_count + row
        prices[index] = workspace.costs[index] + dual[row]
    end
    for index in workspace.basis.basic_indices
        prices[index] = zero(T)
    end
    return prices
end
function _baseline_direction_weight(direction::AbstractVector{T}) where {T<:AbstractFloat}
    scale = one(T)
    for coefficient in direction
        scale = max(scale, abs(coefficient))
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

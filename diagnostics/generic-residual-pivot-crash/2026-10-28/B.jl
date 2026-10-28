module RPCB
import JSimplex
using SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,_primal_direction_magnitude,PFIFactorization,_is_exact,_positive_tolerance,_backend_dimension,PackedEta
_crash_violation(args...) = JSimplex._crash_violation(args...)
function _dual_row_residual_ratio(workspace::SimplexWorkspace{T},
                                  rho::Vector{T}, leaving_row::Int) where {T<:AbstractFloat}
    A = workspace.problem.A
    row_count, column_count = size(A)
    length(rho) == length(workspace.basis.basic_indices) == row_count ||
        throw(DimensionMismatch("tableau residual vectors must match the row count"))
    roundoff = T(256) * eps(one(T))
    worst_ratio = zero(T)
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        1 <= index <= column_count + row_count || throw(BoundsError(workspace.primal, index))
        expected = basis_row == leaving_row ? one(T) : zero(T)
        residual = -expected
        scale = expected
        if index <= column_count
            @inbounds for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                term = A.nzval[position] * rho[A.rowval[position]]
                residual += term
                scale += abs(term)
            end
        else
            term = @inbounds -rho[index - column_count]
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

function _dual_row_residual_ratio(workspace::SimplexWorkspace{T},
                                  rho::Vector{T}, leaving_row::Int) where {T<:BigFloat}
    A = workspace.problem.A
    row_count, column_count = size(A)
    length(rho) == length(workspace.basis.basic_indices) == row_count ||
        throw(DimensionMismatch("tableau residual vectors must match the row count"))
    roundoff = T(256) * eps(one(T))
    worst_ratio = zero(T)
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        1 <= index <= column_count + row_count || throw(BoundsError(workspace.primal, index))
        expected = basis_row == leaving_row ? one(T) : zero(T)
        residual = -expected
        scale = expected
        if index <= column_count
            @inbounds for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                term = A.nzval[position] * rho[A.rowval[position]]
                residual += term
                scale += _primal_direction_magnitude(term)
            end
        else
            term = @inbounds -rho[index - column_count]
            residual += term
            scale += _primal_direction_magnitude(term)
        end
        isfinite(residual) && isfinite(scale) || return T(Inf)
        tolerance = max(workspace.options.zero_tolerance,
                        roundoff * (scale + Clong(1)))
        isfinite(tolerance) || return T(Inf)
        worst_ratio = max(worst_ratio, _primal_direction_magnitude(residual) / tolerance)
    end
    return worst_ratio
end

_pivot_magnitude(value::Real) = abs(value)
function _pivot_magnitude(value::BigFloat)
    isfinite(value) && value > 0 && return value
    return setprecision(BigFloat, precision(value)) do
        # Retain stored-precision negation and all exceptional/zero cases.
        abs(value)
    end
end

function replace_column!(
    factor::PFIFactorization{T},
    tableau_column::AbstractVector,
    pivot_row::Integer;
    zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                         _positive_tolerance(T, 1 // 10^12),
) where {T}
    tolerance = convert(T, zero_tolerance)
    isfinite(tolerance) && tolerance >= zero(T) ||
        throw(ArgumentError("zero_tolerance must be finite and nonnegative"))
    length(tableau_column) == _backend_dimension(factor.base) ||
        throw(DimensionMismatch("tableau column length must match the basis dimension"))

    pivot = Int(pivot_row)
    checkbounds(tableau_column, pivot)
    pivot_value = convert(T, tableau_column[pivot])
    _pivot_magnitude(pivot_value) > tolerance || throw(LinearAlgebra.ZeroPivotException(pivot))

    inverse_pivot = inv(pivot_value)
    direct_pack = tableau_column isa Vector{T} && T <: Union{Float32,Float64}
    if !isempty(factor.recycled_updates)
        retired = pop!(factor.recycled_updates)
        entry_count = tableau_column isa AbstractVector{T} ?
            count(!iszero, tableau_column) : 1
        indices = resize!(retired.indices, entry_count)
        values = resize!(retired.values, entry_count)
        if !direct_pack
            resize!(indices, 1)
            resize!(values, 1)
        end
        indices[1] = pivot
        values[1] = inverse_pivot
    elseif tableau_column isa AbstractVector{T}
        # Allocate the final capacity once, without first creating singleton
        # buffers that would immediately need to grow.
        entry_count = count(!iszero, tableau_column)
        indices = Vector{Int}(undef, entry_count)
        values = Vector{T}(undef, entry_count)
        if !direct_pack
            resize!(indices, 1)
            resize!(values, 1)
        end
        indices[1] = pivot
        values[1] = inverse_pivot
    else
        # Converting mixed-type inputs just to count nonzeros can allocate
        # heavily, so retain the single conversion pass.
        indices = Int[pivot]
        values = T[inverse_pivot]
    end
    if direct_pack
        # The stable native vector was counted above, so every destination
        # index fits. Keep pivot-first order and the original scalar divisions.
        entry = 1
        @inbounds for row in eachindex(tableau_column)
            row == pivot && continue
            value = convert(T, tableau_column[row])
            iszero(value) && continue
            entry += 1
            indices[entry] = row
            values[entry] = -(value / pivot_value)
        end
    else
        for row in eachindex(tableau_column)
            row == pivot && continue
            value = convert(T, tableau_column[row])
            iszero(value) && continue
            push!(indices, row)
            push!(values, -(value / pivot_value))
        end
    end
    push!(factor.updates, PackedEta{T}(indices, values, pivot))
    return factor
end

function _crash_rows!(rows,ws,column,policy)
    empty!(rows)
    scale = maximum(abs,column;init=zero(eltype(column)))
    iszero(scale) && return rows
    cutoff = policy.pivot_error_tolerance*scale
    for (row,j) in enumerate(ws.basis.basic_indices)
        abs(column[row]) > cutoff || continue
        _crash_violation(ws.primal[j],ws.lower[j],ws.upper[j],ws.options.primal_tolerance) > 0 || continue
        # Keep only a bounded number of strongest eligible pivots. Checking all
        # row scores would turn each column's selection into quadratic work.
        position = findfirst(r->abs(column[row])>abs(column[r]),rows)
        if isnothing(position)
            length(rows)<policy.max_pivot_candidates && push!(rows,row)
        else
            insert!(rows,position,row)
            length(rows)>policy.max_pivot_candidates && pop!(rows)
        end
    end
    return rows
end


end

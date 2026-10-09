# Frozen from 43bb7a0; evaluated inside JSimplex for diagnostic comparisons.
function reference_pack!(
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
    if !isempty(factor.recycled_updates)
        retired = pop!(factor.recycled_updates)
        entry_count = tableau_column isa AbstractVector{T} ?
            count(!iszero, tableau_column) : 1
        indices = resize!(retired.indices, entry_count)
        values = resize!(retired.values, entry_count)
        resize!(indices, 1)
        resize!(values, 1)
        indices[1] = pivot
        values[1] = inverse_pivot
    elseif tableau_column isa AbstractVector{T}
        # Allocate the final capacity once, without first creating singleton
        # buffers that would immediately need to grow.
        entry_count = count(!iszero, tableau_column)
        indices = Vector{Int}(undef, entry_count)
        values = Vector{T}(undef, entry_count)
        resize!(indices, 1)
        resize!(values, 1)
        indices[1] = pivot
        values[1] = inverse_pivot
    else
        # Converting mixed-type inputs just to count nonzeros can allocate
        # heavily, so retain the single conversion pass.
        indices = Int[pivot]
        values = T[inverse_pivot]
    end
    for row in eachindex(tableau_column)
        row == pivot && continue
        value = convert(T, tableau_column[row])
        iszero(value) && continue
        push!(indices, row)
        push!(values, -(value / pivot_value))
    end
    push!(factor.updates, PackedEta{T}(indices, values, pivot))
    return factor
end

# Diagnostic prototype; not production code.
function prototype_pack!(
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
    same_type = tableau_column isa Vector{T} && T <: Union{Float32,Float64}
    # Same-type inputs have an exact final length; mixed inputs may lose
    # nonzeros on conversion and retain the single conversion pass.
    entry_count = same_type ? count(!iszero, tableau_column) : 1
    if !isempty(factor.recycled_updates)
        retired = pop!(factor.recycled_updates)
        indices = resize!(retired.indices, entry_count)
        values = resize!(retired.values, entry_count)
    else
        indices = Vector{Int}(undef, entry_count)
        values = Vector{T}(undef, entry_count)
    end
    indices[1] = pivot
    values[1] = inverse_pivot
    if same_type
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

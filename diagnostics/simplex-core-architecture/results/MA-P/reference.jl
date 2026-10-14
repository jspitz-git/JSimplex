# Exact extracted production RHS staging loop; wrapper supplies column inputs.
function reference_rhs(A, lower::Vector{Bound{T}}, upper, value::T) where T
    column=1
    value_exact=_exact_rational(value)
    changes=Tuple{Int,Bound{T},Bound{T}}[]
    safe=true
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            row = A.rowval[position]
            shifted_lower, shifted_upper = lower[row], upper[row]
            if isfinite(shifted_lower) || isfinite(shifted_upper)
                coefficient = A.nzval[position]
                shift = if iszero(value_exact) || isone(coefficient)
                    value_exact
                elseif coefficient == -1
                    -value_exact
                else
                    coefficient_exact = _exact_rational(coefficient)
                    isone(value_exact) ? coefficient_exact :
                        value_exact == -1 ? -coefficient_exact :
                        coefficient_exact * value_exact
                end
                # A zero shift preserves each original bound's representation.
                shared_bounds = !iszero(shift) && shifted_lower == shifted_upper
                shifted_lower = _shift_bound_exact(T, shifted_lower, shift)
                shifted_upper = shared_bounds ? shifted_lower : _shift_bound_exact(T, shifted_upper, shift)
            end
            if isnothing(shifted_lower) || isnothing(shifted_upper)
                safe = false
                break
            end
            push!(changes, (row, shifted_lower, shifted_upper))
        end
    return safe,changes
end

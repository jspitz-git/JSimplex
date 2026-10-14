# Throwaway MA-P scratch is private to one RHS column propagation call.
make_scratch()=(zero(Q),zero(Q),MA.buffer_for(*,Q,Q),MA.buffer_for(-,Q,Q))
function private_shift(::Type{T},bound::Bound{T},shift::Q,scratch) where T
    iszero(shift) && return bound
    isfinite(bound) || return bound
    borrowed=false
    exact_value=if iszero(bound_value(bound))
        borrowed=shift === scratch[1]
        -shift
    else
        bound_exact=_exact_rational(bound_value(bound))
        if bound_exact==shift
            zero(Q)
        elseif denominator(bound_exact)==denominator(shift)
            Q(numerator(bound_exact)-numerator(shift),denominator(bound_exact))
        else
            borrowed=true
            MA.buffered_operate_to!(scratch[4],scratch[2],-,bound_exact,shift)
        end
    end
    # Q conversion may return its input: detach mutable leaves before publication.
    owned=T===Q && borrowed ? MA.mutable_copy(exact_value) : exact_value
    value=_represent_exact(T,owned)
    return isnothing(value) ? nothing : Bound(value)
end
# Exact extracted production RHS staging loop; wrapper supplies column inputs.
function candidate_rhs(A, lower::Vector{Bound{T}}, upper, value::T) where T
    column=1
    value_exact=_exact_rational(value)
    changes=Tuple{Int,Bound{T},Bound{T}}[]
    safe=true
    scratch=make_scratch()
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
                        MA.buffered_operate_to!(scratch[3],scratch[1],*,coefficient_exact,value_exact)
                end
                # A zero shift preserves each original bound's representation.
                shared_bounds = !iszero(shift) && shifted_lower == shifted_upper
                shifted_lower = private_shift(T, shifted_lower, shift, scratch)
                shifted_upper = shared_bounds ? shifted_lower : private_shift(T, shifted_upper, shift, scratch)
            end
            if isnothing(shifted_lower) || isnothing(shifted_upper)
                safe = false
                break
            end
            push!(changes, (row, shifted_lower, shifted_upper))
        end
    return safe,changes
end

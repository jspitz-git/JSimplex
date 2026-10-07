# These helpers are only used with finite hardware floats. Spell out the
# Float32 significand conversion to avoid allocating tuple conversions in
# Base.decompose(Float32) on Julia 1.13.
function _native_dyadic_parts(x::Float64)
    bits = reinterpret(UInt64, x)
    exponent_bits = Int((bits >> 52) & 0x7ff)
    significand_bits = Int(bits & 0x000fffffffffffff) | ((exponent_bits != 0) << 52)
    return significand_bits, exponent_bits - 1075 + (exponent_bits == 0), signbit(x) ? -1 : 1
end
function _native_dyadic_parts(x::Float32)
    bits = reinterpret(UInt32, x)
    exponent_bits = Int((bits >> 23) & 0xff)
    significand_bits = Int(bits & 0x007fffff) | ((exponent_bits != 0) << 23)
    return significand_bits, exponent_bits - 150 + (exponent_bits == 0), signbit(x) ? -1 : 1
end

# Error-free FastTwoSum in the safe native range. Extreme cancellation,
# overflow or underflow uncertainty is left to the exact fallback.
@inline function _native_row_sum_pair(left::T, right::T) where {T<:Union{Float32,Float64}}
    isfinite(left) && isfinite(right) || return nothing
    iszero(left) && return (right, zero(T))
    iszero(right) && return (left, zero(T))
    left == -right && return (zero(T), zero(T))
    total = left + right
    isfinite(total) && min(abs(left),abs(right)) >= ldexp(nextfloat(zero(T)),precision(T)) || return nothing
    large, small = abs(left) >= abs(right) ? (left,right) : (right,left)
    error = (large-total)+small
    isfinite(error) || return nothing
    return total, error
end

@inline function _native_row_product_pair(left::T, right::T) where {T<:Union{Float32,Float64}}
    (iszero(left) || iszero(right)) && return (zero(T),zero(T))
    abs(left) == one(T) && return (left*right,zero(T))
    abs(right) == one(T) && return (left*right,zero(T))
    value = left*right
    # Below this threshold an exact FMA residual may itself underflow.
    isfinite(value) && abs(value) >= ldexp(nextfloat(zero(T)),2*precision(T)) || return nothing
    return value, fma(left,right,-value)
end

@inline function _native_row_difference(high::T, lower::T, upper::T, bound::T) where T
    pair = _native_row_sum_pair(high,-bound)
    isnothing(pair) && return nothing
    difference, error = pair
    tail_lower, _ = _primal_sum_bounds(lower,error)
    _, tail_upper = _primal_sum_bounds(upper,error)
    result_lower, _ = _primal_sum_bounds(difference,tail_lower)
    _, result_upper = _primal_sum_bounds(difference,tail_upper)
    return result_lower,result_upper
end

# Keep a rounded leading sum and an outward-rounded interval for its exact
# residual. Compare the compensated difference to each bound, so a large
# bound does not round away the user's small absolute tolerance.
function _native_primal_rows_filter(problem::LinearProblem{T}, primal::Vector{T},
                                    tolerance::T, rows::Vector{Int},row_lower,row_upper) where {T<:Union{Float32,Float64}}
    (rounding(T) == RoundNearest && !get_zero_subnormals()) || return rows
    A = problem.A
    slots = zeros(Int,size(A,1))
    for (slot,row) in enumerate(rows); slots[row]=slot; end
    high = zeros(T,length(rows))
    lower, upper = zeros(T,length(rows)),zeros(T,length(rows))
    uncertain = falses(length(rows))
    for column in axes(A,2), position in nzrange(A,column)
        slot = slots[A.rowval[position]]
        slot == 0 && continue
        a,x = A.nzval[position],primal[column]
        isfinite(a) && isfinite(x) || return false
        uncertain[slot] && continue
        product = _native_row_product_pair(a,x)
        if isnothing(product)
            uncertain[slot]=true
            continue
        end
        value, product_error = product
        pair = _native_row_sum_pair(high[slot],value)
        if isnothing(pair)
            uncertain[slot]=true
            continue
        end
        high[slot], sum_error = pair
        lower[slot], _ = _primal_sum_bounds(lower[slot],product_error)
        _, upper[slot] = _primal_sum_bounds(upper[slot],product_error)
        lower[slot], _ = _primal_sum_bounds(lower[slot],sum_error)
        _, upper[slot] = _primal_sum_bounds(upper[slot],sum_error)
    end
    unresolved = Int[]
    for (slot,row) in enumerate(rows)
        h,lo,hi = high[slot],lower[slot],upper[slot]
        value_lower, _ = _primal_sum_bounds(h,lo)
        _, value_upper = _primal_sum_bounds(h,hi)
        ambiguous = uncertain[slot] || !isfinite(value_lower) || !isfinite(value_upper)
        if !ambiguous
            if isfinite(row_lower[row])
                difference = _native_row_difference(h,lo,hi,bound_value(row_lower[row]))
                if isnothing(difference)
                    ambiguous=true
                else
                    difference[2] < -tolerance && return false
                    ambiguous |= difference[1] < -tolerance
                end
            end
            if isfinite(row_upper[row])
                difference = _native_row_difference(h,lo,hi,bound_value(row_upper[row]))
                if isnothing(difference)
                    ambiguous=true
                else
                    difference[1] > tolerance && return false
                    ambiguous |= difference[2] > tolerance
                end
            end
        end
        ambiguous && push!(unresolved,row)
    end
    return isempty(unresolved) ? true : unresolved
end

function _refined_primal_rows_feasible(problem::LinearProblem{T}, primal::Vector{T},
                                      tolerance::T, rows::Vector{Int},
                                      row_lower=problem.row_lower,
                                      row_upper=problem.row_upper) where {T<:Union{Float32,Float64}}
    native = _native_primal_rows_filter(problem,primal,tolerance,rows,row_lower,row_upper)
    native isa Bool && return native
    return _exact_primal_rows_feasible(problem,primal,tolerance,native,row_lower,row_upper)
end

# Finite hardware floats are dyadic. Scale their exact values to a common
# integer lattice; GMP mutators reuse private storage instead of allocating
# Rational{BigInt} temporaries for every coefficient in every fallback check.
function _scaled_native_integer!(out::BigInt, value::T, scale::Int) where {T<:Union{Float32,Float64}}
    numerator, power, sign = _native_dyadic_parts(value)
    # The integer significand fits exactly in Float64, including Float32 input.
    Base.GMP.MPZ.set_d!(out, Float64(numerator) * sign)
    return Base.GMP.MPZ.mul_2exp!(out, out, power + scale)
end

function _exact_primal_rows_feasible(problem::LinearProblem{T}, primal::Vector{T},
                                       tolerance::T, rows::Vector{Int},
                                       row_lower=problem.row_lower,
                                       row_upper=problem.row_upper) where {T<:Union{Float32,Float64}}
    A = problem.A
    row_slot = zeros(Int, size(A, 1))
    for (slot, row) in enumerate(rows)
        row_slot[row] = slot
    end
    # A product of the two smallest subnormals must remain representable.
    # This is 2^2148 for Float64 and 2^298 for Float32. No floating product
    # or sum is formed, so cancellation after native overflow remains exact.
    scale = 2 * (precision(T) - 1 - exponent(floatmin(T)))
    activities = [BigInt(0) for _ in rows]
    value, term = BigInt(0), BigInt(0)
    for column in axes(A, 2)
        value_ready = false
        value_power = 0
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            slot = row_slot[A.rowval[position]]
            slot == 0 && continue
            coefficient = A.nzval[position]
            isfinite(coefficient) && isfinite(primal[column]) || return false
            # Floating zero comparisons can discard stored subnormals under
            # FTZ/DAZ, precisely when the native filter delegates here.
            (iszero(_native_dyadic_parts(coefficient)[1]) ||
             iszero(_native_dyadic_parts(primal[column])[1])) && continue
            if !value_ready
                numerator, value_power, sign = _native_dyadic_parts(primal[column])
                Base.GMP.MPZ.set_d!(value, Float64(numerator) * sign)
                value_ready = true
            end
            numerator, power, sign = _native_dyadic_parts(coefficient)
            Base.GMP.MPZ.set_d!(term, Float64(numerator) * sign)
            Base.GMP.MPZ.mul!(term, term, value)
            Base.GMP.MPZ.mul_2exp!(term, term, power + value_power + scale)
            Base.GMP.MPZ.add!(activities[slot], activities[slot], term)
        end
    end
    exact_tolerance = _scaled_native_integer!(BigInt(0), tolerance, scale)
    finite_limit = _scaled_native_integer!(BigInt(0), floatmax(T), scale)
    negative_limit = Base.GMP.MPZ.neg!(BigInt(0), finite_limit)
    for (slot, row) in enumerate(rows)
        # A final activity outside the native range is unsafe even for an
        # unbounded row. Test exact values, not rounded or enlarged bounds.
        activity = activities[slot]
        negative_limit <= activity <= finite_limit || return false
        lower = row_lower[row]
        upper = row_upper[row]
        if isfinite(lower)
            _scaled_native_integer!(term, bound_value(lower), scale)
            Base.GMP.MPZ.sub!(term, term, exact_tolerance)
            activity >= term || return false
        end
        if isfinite(upper)
            _scaled_native_integer!(term, bound_value(upper), scale)
            Base.GMP.MPZ.add!(term, term, exact_tolerance)
            activity <= term || return false
        end
    end
    return true
end

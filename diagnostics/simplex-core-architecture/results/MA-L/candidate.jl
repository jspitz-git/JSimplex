# MA-L UNEXECUTED isolated candidate. No production method overwrite.
function _mal_private_add(scratch, x::ExactValue, y::ExactValue, lo, hi)
    pool, buffer = scratch
    out = pool[1] !== lo && pool[1] !== hi ? pool[1] :
          pool[2] !== lo && pool[2] !== hi ? pool[2] : pool[3]
    if denominator(x) == denominator(y)
        MA.operate_to!(numerator(out), +, numerator(x), numerator(y))
        MA.operate_to!(denominator(out), copy, denominator(x))
        MA.operate_to!(buffer[1], gcd, numerator(out), denominator(out))
        if !isone(buffer[1])
            MA.operate!(div, numerator(out), buffer[1])
            MA.operate!(div, denominator(out), buffer[1])
        end
        return out
    end
    return MA.buffered_operate_to!(buffer, out, +, x, y)
end

function candidate_bounds(problem::LinearProblem, row_terms,
                                         pivot_column::Int, pivot::ExactValue,
                                         rhs::ExactValue)
    lower = problem.column_lower[pivot_column]
    upper = problem.column_upper[pivot_column]
    !isfinite(lower) && !isfinite(upper) && return true
    positive_pivot = numerator(pivot) > 0
    other_min::ExactEndpoint = isfinite(positive_pivot ? upper : lower) ? zero(ExactValue) : nothing
    other_max::ExactEndpoint = !isfinite(positive_pivot ? lower : upper) ? nothing :
        isnothing(other_min) ? zero(ExactValue) : other_min
    for (column, stored) in row_terms
        column == pivot_column && continue
        coefficient = _exact_rational(stored)
        positive_coefficient = numerator(coefficient) > 0
        min_bound = positive_coefficient ? problem.column_lower[column] :
                                      problem.column_upper[column]
        max_bound = positive_coefficient ? problem.column_upper[column] :
                                      problem.column_lower[column]
        shared_activity = other_min === other_max
        min_product::ExactEndpoint = nothing
        other_min = if isnothing(other_min) || !isfinite(min_bound)
            nothing
        elseif iszero(bound_value(min_bound))
            other_min
        else
            value = _exact_rational(bound_value(min_bound))
            product = isone(coefficient) ? value : coefficient == -1 ? -value :
                isone(value) ? coefficient : value == -1 ? -coefficient : coefficient * value
            if !isnothing(other_max) && min_bound == max_bound
                min_product = product
            end
            iszero(other_min) ? product :
                denominator(other_min) == denominator(product) ?
                Rational{BigInt}(numerator(other_min) + numerator(product), denominator(other_min)) :
                other_min + product
        end
        other_max = if isnothing(other_max) || !isfinite(max_bound)
            nothing
        elseif iszero(bound_value(max_bound))
            other_max
        else
            product = if !isnothing(min_product)
                min_product
            else
                value = _exact_rational(bound_value(max_bound))
                isone(coefficient) ? value : coefficient == -1 ? -value :
                    isone(value) ? coefficient : value == -1 ? -coefficient : coefficient * value
            end
            iszero(other_max) ? product :
                shared_activity && !isnothing(min_product) ? other_min :
                denominator(other_max) == denominator(product) ?
                Rational{BigInt}(numerator(other_max) + numerator(product), denominator(other_max)) :
                other_max + product
        end
        isnothing(other_min) && isnothing(other_max) && return false
    end
    lower_activity = positive_pivot ? other_max : other_min
    upper_activity = positive_pivot ? other_min : other_max
    shared_candidate::ExactEndpoint = nothing
    lower_implied = if !isfinite(lower)
        true
    elseif isnothing(lower_activity)
        false
    elseif rhs == lower_activity
        numerator(_exact_rational(bound_value(lower))) <= 0
    else
        difference = iszero(lower_activity) ? rhs :
            iszero(rhs) ? -lower_activity :
            denominator(rhs) == denominator(lower_activity) ?
            Rational{BigInt}(numerator(rhs) - numerator(lower_activity), denominator(rhs)) :
            rhs - lower_activity
        candidate = isone(pivot) ? difference : pivot == -1 ? -difference :
            denominator(difference) == denominator(pivot) ?
            Rational{BigInt}(numerator(difference), numerator(pivot)) : difference / pivot
        if isfinite(upper) && lower_activity === upper_activity &&
           !(isone(pivot) && iszero(lower_activity))
            shared_candidate = candidate
        end
        candidate >= _exact_rational(bound_value(lower))
    end
    upper_implied = if !isfinite(upper)
        true
    elseif isnothing(upper_activity)
        false
    elseif rhs == upper_activity
        numerator(_exact_rational(bound_value(upper))) >= 0
    elseif !isnothing(shared_candidate)
        shared_candidate <= _exact_rational(bound_value(upper))
    else
        difference = iszero(upper_activity) ? rhs :
            iszero(rhs) ? -upper_activity :
            denominator(rhs) == denominator(upper_activity) ?
            Rational{BigInt}(numerator(rhs) - numerator(upper_activity), denominator(rhs)) :
            rhs - upper_activity
        candidate = isone(pivot) ? difference : pivot == -1 ? -difference :
            denominator(difference) == denominator(pivot) ?
            Rational{BigInt}(numerator(difference), numerator(pivot)) : difference / pivot
        candidate <= _exact_rational(bound_value(upper))
    end
    return lower_implied && upper_implied
end

function candidate_bounds(problem::LinearProblem{Rational{BigInt}},
                          row_terms::Vector{Tuple{Int,Rational{BigInt}}},
                          pivot_column::Int, pivot::ExactValue, rhs::ExactValue)
    length(row_terms) == 8 || return invoke(candidate_bounds,
        Tuple{LinearProblem,Any,Int,ExactValue,ExactValue},
        problem,row_terms,pivot_column,pivot,rhs)
    return _ma_equality_bounds8(problem,row_terms,pivot_column,pivot,rhs)
end

function _ma_equality_bounds8(problem::LinearProblem, row_terms,
                                         pivot_column::Int, pivot::ExactValue,
                                         rhs::ExactValue)
    lower = problem.column_lower[pivot_column]
    upper = problem.column_upper[pivot_column]
    !isfinite(lower) && !isfinite(upper) && return true
    positive_pivot = numerator(pivot) > 0
    other_min::ExactEndpoint = isfinite(positive_pivot ? upper : lower) ? zero(ExactValue) : nothing
    other_max::ExactEndpoint = !isfinite(positive_pivot ? lower : upper) ? nothing :
        isnothing(other_min) ? zero(ExactValue) : other_min
    scratch = nothing
    eligible_count = 0
    decided = isnothing(other_min) || isnothing(other_max)
    for (position, (column, stored)) in enumerate(row_terms)
        position == 4 && (decided = true)
        column == pivot_column && continue
        coefficient = _exact_rational(stored)
        positive_coefficient = numerator(coefficient) > 0
        min_bound = positive_coefficient ? problem.column_lower[column] :
                                      problem.column_upper[column]
        max_bound = positive_coefficient ? problem.column_upper[column] :
                                      problem.column_lower[column]
        shared_activity = other_min === other_max
        min_product::ExactEndpoint = nothing
        check_pair = !decided && !isnothing(other_min) && !isnothing(other_max) &&
                     isfinite(min_bound) && isfinite(max_bound)
        equal_bounds = check_pair ? min_bound == max_bound : false
        eligible_term = check_pair && !equal_bounds
        other_min = if isnothing(other_min) || !isfinite(min_bound)
            nothing
        elseif iszero(bound_value(min_bound))
            other_min
        else
            value = _exact_rational(bound_value(min_bound))
            product = isone(coefficient) ? value : coefficient == -1 ? -value :
                isone(value) ? coefficient : value == -1 ? -coefficient : coefficient * value
            if !isnothing(other_max) && (check_pair ? equal_bounds : min_bound == max_bound)
                min_product = product
            end
            if iszero(other_min)
                product
            elseif !isnothing(scratch)
                _mal_private_add(scratch, other_min, product, other_min, other_max)
            elseif denominator(other_min) == denominator(product)
                Rational{BigInt}(numerator(other_min) + numerator(product), denominator(other_min))
            else
                if eligible_term && !decided && !iszero(product)
                    eligible_count += 1
                    if eligible_count == 2
                        decided = true
                        if (numerator(other_min) > 0) == (numerator(product) > 0) &&
                           ndigits(numerator(other_min); base=2) >= 129 &&
                           ndigits(numerator(product); base=2) >= 129
                            scratch = ((zero(ExactValue), zero(ExactValue), zero(ExactValue)),
                                       MA.buffer_for(+, ExactValue, ExactValue))
                        end
                    end
                end
                isnothing(scratch) ? other_min + product :
                    _mal_private_add(scratch, other_min, product, other_min, other_max)
            end
        end
        other_max = if isnothing(other_max) || !isfinite(max_bound)
            nothing
        elseif iszero(bound_value(max_bound))
            other_max
        else
            product = if !isnothing(min_product)
                min_product
            else
                value = _exact_rational(bound_value(max_bound))
                isone(coefficient) ? value : coefficient == -1 ? -value :
                    isone(value) ? coefficient : value == -1 ? -coefficient : coefficient * value
            end
            if iszero(other_max)
                product
            elseif shared_activity && !isnothing(min_product)
                other_min
            elseif !isnothing(scratch)
                _mal_private_add(scratch, other_max, product, other_min, other_max)
            elseif denominator(other_max) == denominator(product)
                Rational{BigInt}(numerator(other_max) + numerator(product), denominator(other_max))
            else
                if eligible_term && !decided && !iszero(product)
                    eligible_count += 1
                    if eligible_count == 2
                        decided = true
                        if (numerator(other_max) > 0) == (numerator(product) > 0) &&
                           ndigits(numerator(other_max); base=2) >= 129 &&
                           ndigits(numerator(product); base=2) >= 129
                            scratch = ((zero(ExactValue), zero(ExactValue), zero(ExactValue)),
                                       MA.buffer_for(+, ExactValue, ExactValue))
                        end
                    end
                end
                isnothing(scratch) ? other_max + product :
                    _mal_private_add(scratch, other_max, product, other_min, other_max)
            end
        end
        isnothing(other_min) && isnothing(other_max) && return false
    end
    lower_activity = positive_pivot ? other_max : other_min
    upper_activity = positive_pivot ? other_min : other_max
    shared_candidate::ExactEndpoint = nothing
    lower_implied = if !isfinite(lower)
        true
    elseif isnothing(lower_activity)
        false
    elseif rhs == lower_activity
        numerator(_exact_rational(bound_value(lower))) <= 0
    else
        difference = iszero(lower_activity) ? rhs :
            iszero(rhs) ? -lower_activity :
            denominator(rhs) == denominator(lower_activity) ?
            Rational{BigInt}(numerator(rhs) - numerator(lower_activity), denominator(rhs)) :
            rhs - lower_activity
        candidate = isone(pivot) ? difference : pivot == -1 ? -difference :
            denominator(difference) == denominator(pivot) ?
            Rational{BigInt}(numerator(difference), numerator(pivot)) : difference / pivot
        if isfinite(upper) && lower_activity === upper_activity &&
           !(isone(pivot) && iszero(lower_activity))
            shared_candidate = candidate
        end
        candidate >= _exact_rational(bound_value(lower))
    end
    upper_implied = if !isfinite(upper)
        true
    elseif isnothing(upper_activity)
        false
    elseif rhs == upper_activity
        numerator(_exact_rational(bound_value(upper))) >= 0
    elseif !isnothing(shared_candidate)
        shared_candidate <= _exact_rational(bound_value(upper))
    else
        difference = iszero(upper_activity) ? rhs :
            iszero(rhs) ? -upper_activity :
            denominator(rhs) == denominator(upper_activity) ?
            Rational{BigInt}(numerator(rhs) - numerator(upper_activity), denominator(rhs)) :
            rhs - upper_activity
        candidate = isone(pivot) ? difference : pivot == -1 ? -difference :
            denominator(difference) == denominator(pivot) ?
            Rational{BigInt}(numerator(difference), numerator(pivot)) : difference / pivot
        candidate <= _exact_rational(bound_value(upper))
    end
    return lower_implied && upper_implied
end

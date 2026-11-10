struct BoundPropagationStep{T<:Real} <: AbstractPostsolveStep
    map::PresolveMap{T}
    old_lower::Vector{Bound{T}}
    old_upper::Vector{Bound{T}}
end

function _other_activity(total::ExactValue, unbounded::Int,
                         term::Union{Nothing,ExactValue}, activity_zero::ExactEndpoint=nothing)
    remaining = unbounded - isnothing(term)
    remaining == 0 || return nothing
    (isnothing(term) || iszero(term)) && return total
    iszero(total) && return -term
    if total == term
        # The caller may share its zero because activity arithmetic replaces values.
        return isnothing(activity_zero) ? zero(ExactValue) : activity_zero
    end
    if denominator(total) == denominator(term)
        return Rational{BigInt}(numerator(total) - numerator(term), denominator(total))
    end
    return total - term
end

function _cached_bound_rational!(cache::Vector{ExactEndpoint}, bounds, column::Int)
    value = cache[column]
    if isnothing(value) && isfinite(bounds[column])
        value = _exact_rational(bound_value(bounds[column]))
        cache[column] = value
    end
    return value
end

function _propagation_failure(problem::LinearProblem, row::Int, keep::BitVector,
                              message::String)
    rows = findall(keep)
    return PresolveFailure(INFEASIBLE, "row $row $message", length(rows),
        size(problem.A, 2),
        count(value -> !iszero(value), problem.A[rows, :].nzval))
end

# Return both the stored endpoint and its exact value. The latter is also the
# activity cache entry: retaining the unrounded candidate would strengthen a
# subsequent implication beyond the bounds actually stored in the model.
# Inline to keep the optional pair scalarized instead of boxing each endpoint.
@inline function _propagation_bound(::Type{T}, candidate::ExactValue, upper::Bool,
                             directed::Bool) where {T}
    if !directed
        value = _represent_exact(T, candidate)
        return isnothing(value) ? nothing : (value, candidate)
    end
    value = try
        T(candidate)
    catch exception
        exception isa InexactError || exception isa OverflowError ||
            exception isa DomainError || rethrow()
        return nothing
    end
    isfinite(value) || return nothing
    # Common exact endpoints avoid a new BigInt rational altogether.
    ((iszero(value) && iszero(candidate)) ||
     (isone(value) && isone(candidate)) ||
     (value == -1 && candidate == -1)) && return (value, candidate)
    stored = _exact_rational(value)
    stored == candidate && return (value, candidate)
    if upper ? stored < candidate : stored > candidate
        value = upper ? nextfloat(value) : prevfloat(value)
        isfinite(value) || return nothing
        stored = _exact_rational(value)
    end
    (upper ? stored >= candidate : stored <= candidate) || return nothing
    return value, stored
end

# BigFloat(Rational) rounds numerator and denominator separately. In particular,
# with mixed input/working precisions its error need not fit one adjacent value.
# MPFR rounds the exact quotient once, at the current working precision; the
# bridge retains its rational owner for the duration of the read-only call.
function _propagation_bound(::Type{BigFloat}, candidate::ExactValue, upper::Bool,
                            directed::Bool)
    if !directed
        value = _represent_exact(BigFloat, candidate)
        return isnothing(value) ? nothing : (value, candidate)
    end
    value = BigFloat(; precision=precision(BigFloat))
    quotient = Base.GMP.MPQ._MPQ(candidate)
    mode = upper ? Base.MPFR.MPFRRoundUp : Base.MPFR.MPFRRoundDown
    ccall((:mpfr_set_q, Base.MPFR.libmpfr), Cint,
          (Ref{BigFloat}, Base.GMP.MPQ.mpq_t, Base.MPFR.MPFRRoundingMode),
          value, quotient, mode)
    isfinite(value) || return nothing
    ((iszero(value) && iszero(candidate)) ||
     (isone(value) && isone(candidate)) ||
     (value == -1 && candidate == -1)) && return (value, candidate)
    stored = _exact_rational(value)
    (upper ? stored >= candidate : stored <= candidate) || return nothing
    return value, stored == candidate ? candidate : stored
end

function propagate_row_bounds(problem::LinearProblem{T}; directed_bounds::Bool=true) where {T}
    return _propagate_row_bounds(problem, trues(size(problem.A, 1)); directed_bounds)
end

function _propagate_row_bounds(problem::LinearProblem{T}, rows_to_visit::BitVector,
                               changed_columns::BitVector=falses(size(problem.A, 2));
                               directed_bounds::Bool=true, history=nothing) where {T}
    m, n = size(problem.A)
    length(rows_to_visit) == m && length(changed_columns) == n ||
        throw(ArgumentError("propagation worklist dimensions do not match the model"))
    any(rows_to_visit) || return identity_presolve(problem)
    directed = directed_bounds && (T === BigFloat ||
        ((T === Float32 || T === Float64) && rounding(T) == RoundNearest && !get_zero_subnormals()))
    active = copy(rows_to_visit)
    expand_active = !all(active)
    entries = _row_entries(problem.A)
    lower, upper = problem.column_lower, problem.column_upper
    # Convert a finite bound only when an active row needs it. Accepted
    # tightenings cache the stored endpoint, so later rows see current bounds.
    exact_lower = Vector{ExactEndpoint}(nothing, n)
    exact_upper = Vector{ExactEndpoint}(nothing, n)
    coefficients = ExactValue[]
    min_terms, max_terms = ExactEndpoint[], ExactEndpoint[]
    keep = trues(m)
    # Exact activity arithmetic replaces values; initialize a shared zero lazily.
    activity_zero = nothing
    for row in 1:m
        active[row] || continue
        columns = entries[row]
        isempty(columns) && continue
        resize!(coefficients, length(columns))
        resize!(min_terms, length(columns))
        resize!(max_terms, length(columns))
        isnothing(activity_zero) && (activity_zero = zero(ExactValue))
        min_sum, max_sum = activity_zero, activity_zero
        min_unbounded, max_unbounded = 0, 0
        for (position, (column, stored)) in enumerate(columns)
            coefficient = _exact_rational(stored)
            coefficients[position] = coefficient
            unit_coefficient = isone(coefficient)
            negative_unit_coefficient = coefficient == -1
            low = _cached_bound_rational!(exact_lower, lower, column)
            # A fixed column can seed both caches from one exact conversion.
            if isnothing(exact_upper[column]) && !isnothing(low) && lower[column] == upper[column]
                exact_upper[column] = low
            end
            high = _cached_bound_rational!(exact_upper, upper, column)
            min_bound, max_bound = coefficient > 0 ? (low, high) : (high, low)
            # Cache updates replace values, so bounds and computed products can be shared.
            min_term = isnothing(min_bound) || unit_coefficient || iszero(min_bound) ? min_bound :
                       negative_unit_coefficient ? -min_bound : coefficient * min_bound
            max_term = isnothing(max_bound) || unit_coefficient || iszero(max_bound) ? max_bound :
                       max_bound == min_bound ? min_term :
                       negative_unit_coefficient ? -max_bound : coefficient * max_bound
            min_terms[position], max_terms[position] = min_term, max_term
            previous_min_sum = min_sum
            if isnothing(min_term)
                min_unbounded += 1
            elseif !iszero(min_term)
                if iszero(min_sum)
                    min_sum = min_term
                elseif denominator(min_sum) == denominator(min_term)
                    summed_numerator = numerator(min_sum) + numerator(min_term)
                    min_sum = iszero(summed_numerator) ? activity_zero :
                        Rational{BigInt}(summed_numerator, denominator(min_sum))
                else
                    min_sum += min_term
                end
            end
            if isnothing(max_term)
                max_unbounded += 1
            elseif !iszero(max_term)
                if iszero(max_sum)
                    max_sum = max_term
                elseif max_sum === previous_min_sum && max_term === min_term
                    # Matching operands can share the already computed immutable sum.
                    max_sum = min_sum
                elseif denominator(max_sum) == denominator(max_term)
                    summed_numerator = numerator(max_sum) + numerator(max_term)
                    max_sum = iszero(summed_numerator) ? activity_zero :
                        Rational{BigInt}(summed_numerator, denominator(max_sum))
                else
                    max_sum += max_term
                end
            end
        end
        stored_lower, stored_upper = problem.row_lower[row], problem.row_upper[row]
        has_row_lower, has_row_upper = isfinite(stored_lower), isfinite(stored_upper)
        # Flags distinguish unbounded sides; zero endpoints reuse the activity seed.
        row_lower = has_row_lower && !iszero(bound_value(stored_lower)) ?
            _exact_rational(bound_value(stored_lower)) : (activity_zero::ExactValue)
        # Equal stored bounds share their exact conversion, including mixed precision.
        row_upper = has_row_upper && !iszero(bound_value(stored_upper)) ?
            (stored_lower == stored_upper ? row_lower : _exact_rational(bound_value(stored_upper))) : (activity_zero::ExactValue)
        if (has_row_upper && min_unbounded == 0 && min_sum > row_upper) ||
           (has_row_lower && max_unbounded == 0 && max_sum < row_lower)
            return _propagation_failure(problem, row, keep,
                "contradicts current column bounds")
        end
        lower_implied = !has_row_lower ||
            (min_unbounded == 0 && min_sum >= row_lower)
        upper_implied = !has_row_upper ||
            (max_unbounded == 0 && max_sum <= row_upper)
        if lower_implied && upper_implied
            keep[row] = false
            continue
        end

        for (position, (column, _)) in enumerate(columns)
            coefficient = coefficients[position]
            other_min = !has_row_upper ? nothing :
                _other_activity(min_sum, min_unbounded, min_terms[position], activity_zero)
            other_max = !has_row_lower ? nothing :
                _other_activity(max_sum, max_unbounded, max_terms[position], activity_zero)
            candidate_lower::ExactEndpoint = nothing
            candidate_upper::ExactEndpoint = nothing
            if coefficient > 0
                if has_row_lower && !isnothing(other_max)
                    difference = iszero(other_max) ? row_lower :
                                 iszero(row_lower) ? -other_max :
                                 row_lower == other_max ? (activity_zero::ExactValue) :
                                 denominator(row_lower) == denominator(other_max) ?
                                 Rational{BigInt}(numerator(row_lower) - numerator(other_max), denominator(row_lower)) :
                                 row_lower - other_max
                    candidate_lower = isone(coefficient) || iszero(difference) ? difference :
                                      denominator(difference) == denominator(coefficient) ?
                                      Rational{BigInt}(numerator(difference), numerator(coefficient)) : difference / coefficient
                end
                if has_row_upper && !isnothing(other_min)
                    difference = iszero(other_min) ? row_upper :
                                 iszero(row_upper) ? -other_min :
                                 row_upper == other_min ? (activity_zero::ExactValue) :
                                 denominator(row_upper) == denominator(other_min) ?
                                 Rational{BigInt}(numerator(row_upper) - numerator(other_min), denominator(row_upper)) :
                                 row_upper - other_min
                    candidate_upper = isone(coefficient) || iszero(difference) ? difference :
                                      denominator(difference) == denominator(coefficient) ?
                                      Rational{BigInt}(numerator(difference), numerator(coefficient)) : difference / coefficient
                end
            else
                if has_row_upper && !isnothing(other_min)
                    difference = iszero(other_min) ? row_upper :
                                 iszero(row_upper) ? -other_min :
                                 row_upper == other_min ? (activity_zero::ExactValue) :
                                 denominator(row_upper) == denominator(other_min) ?
                                 Rational{BigInt}(numerator(row_upper) - numerator(other_min), denominator(row_upper)) :
                                 row_upper - other_min
                    candidate_lower = iszero(difference) ? difference :
                                      coefficient == -1 ? -difference :
                                      denominator(difference) == denominator(coefficient) ?
                                      Rational{BigInt}(numerator(difference), numerator(coefficient)) : difference / coefficient
                end
                if has_row_lower && !isnothing(other_max)
                    difference = iszero(other_max) ? row_lower :
                                 iszero(row_lower) ? -other_max :
                                 row_lower == other_max ? (activity_zero::ExactValue) :
                                 denominator(row_lower) == denominator(other_max) ?
                                 Rational{BigInt}(numerator(row_lower) - numerator(other_max), denominator(row_lower)) :
                                 row_lower - other_max
                    candidate_upper = iszero(difference) ? difference :
                                      coefficient == -1 ? -difference :
                                      denominator(difference) == denominator(coefficient) ?
                                      Rational{BigInt}(numerator(difference), numerator(coefficient)) : difference / coefficient
                end
            end
            if !isnothing(candidate_lower)
                if isfinite(upper[column]) &&
                   candidate_lower > exact_upper[column]
                    return _propagation_failure(problem, row, keep,
                        "implies incompatible column bounds")
                end
                # A non-improving exact bound cannot tighten, regardless of working precision.
                converted = !isnothing(exact_lower[column]) && candidate_lower <= exact_lower[column] ? nothing :
                    _propagation_bound(T, candidate_lower, false, directed)
                if !isnothing(converted) &&
                   (!isfinite(lower[column]) || converted[1] > bound_value(lower[column]))
                    value, stored = converted
                    lower === problem.column_lower && (lower = copy(lower))
                    if !isnothing(history)
                        _PropagationHistory.record!(history,problem,row,columns,lower,upper,
                            position,column,lower[column],value,false)
                    end
                    lower[column] = Bound(value)
                    exact_lower[column] = stored
                    changed_columns[column] = true
                    expand_active &&
                        _mark_incident_rows!(active, problem.A, column, row + 1)
                end
            end
            if !isnothing(candidate_upper)
                if isfinite(lower[column]) &&
                   candidate_upper < exact_lower[column]
                    return _propagation_failure(problem, row, keep,
                        "implies incompatible column bounds")
                end
                converted = !isnothing(exact_upper[column]) && candidate_upper >= exact_upper[column] ? nothing :
                    _propagation_bound(T, candidate_upper, true, directed)
                if !isnothing(converted) &&
                   (!isfinite(upper[column]) || converted[1] < bound_value(upper[column]))
                    value, stored = converted
                    upper === problem.column_upper && (upper = copy(upper))
                    if !isnothing(history)
                        _PropagationHistory.record!(history,problem,row,columns,lower,upper,
                            position,column,upper[column],value,true)
                    end
                    upper[column] = Bound(value)
                    exact_upper[column] = stored
                    changed_columns[column] = true
                    expand_active &&
                        _mark_incident_rows!(active, problem.A, column, row + 1)
                end
            end
        end
    end
    result = _row_result(problem, findall(keep);
                         column_lower=lower, column_upper=upper)
    # _row_result returns either the identity tuple or one PresolveMap.
    result isa PresolveResult{T,Tuple{}} && return result
    step = BoundPropagationStep(only(result.postsolve_stack),
                                problem.column_lower, problem.column_upper)
    return PresolveResult(result.problem, (step,), n)
end

postsolve_primal(step::BoundPropagationStep, primal::Vector) =
    postsolve_primal(step.map, primal)

function restore_basis(step::BoundPropagationStep, basis::Basis)
    restored = restore_basis(step.map, basis)
    for column in eachindex(step.old_lower)
        state = restored.states[column]
        if state == AT_LOWER && !isfinite(step.old_lower[column])
            restored.states[column] = isfinite(step.old_upper[column]) ?
                AT_UPPER : FREE_NONBASIC
        elseif state == AT_UPPER && !isfinite(step.old_upper[column])
            restored.states[column] = isfinite(step.old_lower[column]) ?
                AT_LOWER : FREE_NONBASIC
        end
    end
    return restored
end

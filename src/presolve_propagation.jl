struct BoundPropagationStep{T<:Real} <: AbstractPostsolveStep
    map::PresolveMap{T}
    old_lower::Vector{Bound{T}}
    old_upper::Vector{Bound{T}}
end

function _other_activity(total::ExactValue, unbounded::Int,
                         term::Union{Nothing,ExactValue})
    remaining = unbounded - isnothing(term)
    return remaining == 0 ? total - (isnothing(term) ? zero(ExactValue) : term) : nothing
end

function _propagation_failure(problem::LinearProblem, row::Int, keep::BitVector,
                              message::String)
    rows = findall(keep)
    return PresolveFailure(INFEASIBLE, "row $row $message", length(rows),
        size(problem.A, 2),
        count(value -> !iszero(value), problem.A[rows, :].nzval))
end

function propagate_row_bounds(problem::LinearProblem{T}) where {T}
    m, n = size(problem.A)
    entries = _row_entries(problem.A)
    lower, upper = copy(problem.column_lower), copy(problem.column_upper)
    keep = trues(m)
    for row in 1:m
        columns = entries[row]
        isempty(columns) && continue
        min_terms = Vector{Union{Nothing,ExactValue}}(undef, length(columns))
        max_terms = similar(min_terms)
        min_sum, max_sum = zero(ExactValue), zero(ExactValue)
        min_unbounded, max_unbounded = 0, 0
        for (position, (column, stored)) in enumerate(columns)
            coefficient = _exact_rational(stored)
            min_bound = coefficient > 0 ? lower[column] : upper[column]
            max_bound = coefficient > 0 ? upper[column] : lower[column]
            min_term = isfinite(min_bound) ?
                coefficient * _exact_rational(bound_value(min_bound)) : nothing
            max_term = isfinite(max_bound) ?
                coefficient * _exact_rational(bound_value(max_bound)) : nothing
            min_terms[position], max_terms[position] = min_term, max_term
            if isnothing(min_term)
                min_unbounded += 1
            else
                min_sum += min_term
            end
            if isnothing(max_term)
                max_unbounded += 1
            else
                max_sum += max_term
            end
        end
        row_lower = _bound_rational(problem.row_lower[row])
        row_upper = _bound_rational(problem.row_upper[row])
        if (!isnothing(row_upper) && min_unbounded == 0 && min_sum > row_upper) ||
           (!isnothing(row_lower) && max_unbounded == 0 && max_sum < row_lower)
            return _propagation_failure(problem, row, keep,
                "contradicts current column bounds")
        end
        lower_implied = isnothing(row_lower) ||
            (min_unbounded == 0 && min_sum >= row_lower)
        upper_implied = isnothing(row_upper) ||
            (max_unbounded == 0 && max_sum <= row_upper)
        if lower_implied && upper_implied
            keep[row] = false
            continue
        end

        for (position, (column, stored)) in enumerate(columns)
            coefficient = _exact_rational(stored)
            other_min = _other_activity(min_sum, min_unbounded, min_terms[position])
            other_max = _other_activity(max_sum, max_unbounded, max_terms[position])
            candidate_lower::ExactEndpoint = nothing
            candidate_upper::ExactEndpoint = nothing
            if coefficient > 0
                if !isnothing(row_lower) && !isnothing(other_max)
                    candidate_lower = (row_lower - other_max) / coefficient
                end
                if !isnothing(row_upper) && !isnothing(other_min)
                    candidate_upper = (row_upper - other_min) / coefficient
                end
            else
                if !isnothing(row_upper) && !isnothing(other_min)
                    candidate_lower = (row_upper - other_min) / coefficient
                end
                if !isnothing(row_lower) && !isnothing(other_max)
                    candidate_upper = (row_lower - other_max) / coefficient
                end
            end
            if !isnothing(candidate_lower)
                if isfinite(upper[column]) &&
                   candidate_lower > _exact_rational(bound_value(upper[column]))
                    return _propagation_failure(problem, row, keep,
                        "implies incompatible column bounds")
                end
                value = _represent_exact(T, candidate_lower)
                if !isnothing(value) &&
                   (!isfinite(lower[column]) || value > bound_value(lower[column]))
                    lower[column] = Bound(value)
                end
            end
            if !isnothing(candidate_upper)
                if isfinite(lower[column]) &&
                   candidate_upper < _exact_rational(bound_value(lower[column]))
                    return _propagation_failure(problem, row, keep,
                        "implies incompatible column bounds")
                end
                value = _represent_exact(T, candidate_upper)
                if !isnothing(value) &&
                   (!isfinite(upper[column]) || value < bound_value(upper[column]))
                    upper[column] = Bound(value)
                end
            end
        end
    end
    result = _row_result(problem, findall(keep);
                         column_lower=lower, column_upper=upper)
    isempty(result.postsolve_stack) && return result
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

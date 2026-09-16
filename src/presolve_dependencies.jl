const ExactValue = Rational{BigInt}
const ExactEndpoint = Union{Nothing,ExactValue}

function _normalized_interval(problem::LinearProblem, row::Int, pivot::ExactValue)
    lower = _bound_rational(problem.row_lower[row])
    upper = _bound_rational(problem.row_upper[row])
    return pivot > 0 ?
        (isnothing(lower) ? nothing : lower / pivot,
         isnothing(upper) ? nothing : upper / pivot) :
        (isnothing(upper) ? nothing : upper / pivot,
         isnothing(lower) ? nothing : lower / pivot)
end

_interval_subset(inner, outer) =
    (isnothing(outer[1]) || (!isnothing(inner[1]) && inner[1] >= outer[1])) &&
    (isnothing(outer[2]) || (!isnothing(inner[2]) && inner[2] <= outer[2]))

_interval_disjoint(a, b) =
    (!isnothing(a[1]) && !isnothing(b[2]) && a[1] > b[2]) ||
    (!isnothing(b[1]) && !isnothing(a[2]) && b[1] > a[2])

function reduce_parallel_rows(problem::LinearProblem{T}) where {T}
    m, n = size(problem.A)
    entries = _row_entries(problem.A)
    keep = trues(m)
    groups = Dict{Tuple,Vector{Int}}()
    intervals = Vector{Tuple{ExactEndpoint,ExactEndpoint}}(undef, m)
    for row in 1:m
        isempty(entries[row]) && continue
        pivot = _exact_rational(first(entries[row])[2])
        signature = Tuple((column, _exact_rational(value) / pivot)
                          for (column, value) in entries[row])
        current = _normalized_interval(problem, row, pivot)
        intervals[row] = current
        representatives = get!(groups, signature, Int[])
        redundant = false
        for previous in representatives
            keep[previous] || continue
            prior = intervals[previous]
            if _interval_disjoint(prior, current)
                return PresolveFailure(INFEASIBLE,
                    "proportional rows $previous and $row have disjoint bounds",
                    count(identity, keep), n,
                    count(value -> !iszero(value), problem.A.nzval))
            elseif _interval_subset(prior, current)
                redundant = true
                break
            elseif _interval_subset(current, prior)
                keep[previous] = false
            end
        end
        if redundant
            keep[row] = false
        else
            push!(representatives, row)
        end
    end
    return _row_result(problem, findall(keep))
end

function _subtract_scaled!(target::Dict{Int,ExactValue},
                           source::Dict{Int,ExactValue}, scale::ExactValue)
    for (index, value) in source
        updated = get(target, index, zero(ExactValue)) - scale * value
        if iszero(updated)
            delete!(target, index)
        else
            target[index] = updated
        end
    end
end

function _implied_interval(problem::LinearProblem,
                           combination::Dict{Int,ExactValue}, current::Int)
    lower::ExactEndpoint = zero(ExactValue)
    upper::ExactEndpoint = zero(ExactValue)
    for (row, negated_coefficient) in combination
        row == current && continue
        coefficient = -negated_coefficient
        iszero(coefficient) && continue
        source_lower = coefficient > 0 ? problem.row_lower[row] : problem.row_upper[row]
        source_upper = coefficient > 0 ? problem.row_upper[row] : problem.row_lower[row]
        lower = isnothing(lower) || !isfinite(source_lower) ? nothing :
                lower + coefficient * _exact_rational(bound_value(source_lower))
        upper = isnothing(upper) || !isfinite(source_upper) ? nothing :
                upper + coefficient * _exact_rational(bound_value(source_upper))
    end
    return (lower, upper)
end

function reduce_dependent_rows(problem::LinearProblem{T}) where {T}
    m, n = size(problem.A)
    # Exact rational elimination is deliberately bounded on large models.
    (m > 256 || count(value -> !iszero(value), problem.A.nzval) > 10000) &&
        return identity_presolve(problem)
    entries = _row_entries(problem.A)
    pivots = Dict{Int,Tuple{Dict{Int,ExactValue},Dict{Int,ExactValue}}}()
    keep = trues(m)
    work = 0
    for row in 1:m
        coefficients = Dict(column => _exact_rational(value)
                            for (column, value) in entries[row])
        isempty(coefficients) && continue
        combination = Dict(row => one(ExactValue))
        while !isempty(coefficients)
            pivot = minimum(keys(coefficients))
            if !haskey(pivots, pivot)
                scale = coefficients[pivot]
                for index in keys(coefficients)
                    coefficients[index] /= scale
                end
                for index in keys(combination)
                    combination[index] /= scale
                end
                pivots[pivot] = (coefficients, combination)
                break
            end
            basis_row, basis_combination = pivots[pivot]
            scale = coefficients[pivot]
            work += length(basis_row) + length(basis_combination)
            work > 200000 && return _row_result(problem, findall(keep))
            _subtract_scaled!(coefficients, basis_row, scale)
            _subtract_scaled!(combination, basis_combination, scale)
        end
        isempty(coefficients) || continue
        implied = _implied_interval(problem, combination, row)
        required = (_bound_rational(problem.row_lower[row]),
                    _bound_rational(problem.row_upper[row]))
        if _interval_disjoint(implied, required)
            return PresolveFailure(INFEASIBLE,
                "dependent row $row contradicts retained row bounds",
                count(identity, keep) - 1, n,
                count(value -> !iszero(value), problem.A.nzval))
        end
        _interval_subset(implied, required) && (keep[row] = false)
    end
    return _row_result(problem, findall(keep))
end

const ExactValue = Rational{BigInt}
const ExactEndpoint = Union{Nothing,ExactValue}
const ParallelSignatureGroups = Dict{Vector{ExactValue},Vector{Int}}

function _normalized_zero_interval(problem::LinearProblem, row::Int, pivot::ExactValue)
    lower = _bound_rational(problem.row_lower[row])
    upper = _bound_rational(problem.row_upper[row])
    # Pivots come from nonzero row entries, so zero endpoints need no division.
    return pivot > 0 ?
        (isnothing(lower) || iszero(lower) ? lower : lower / pivot,
         isnothing(upper) || iszero(upper) ? upper : upper / pivot) :
        (isnothing(upper) || iszero(upper) ? upper : upper / pivot,
         isnothing(lower) || iszero(lower) ? lower : lower / pivot)
end

function _normalized_negative_unit_interval(problem::LinearProblem, row::Int)
    lower = _bound_rational(problem.row_lower[row])
    upper = _bound_rational(problem.row_upper[row])
    return (isnothing(upper) || iszero(upper) ? upper : -upper,
            isnothing(lower) || iszero(lower) ? lower : -lower)
end

function _normalized_interval(problem::LinearProblem, row::Int, pivot::ExactValue)
    isone(pivot) && return (_bound_rational(problem.row_lower[row]),
                            _bound_rational(problem.row_upper[row]))
    pivot == -1 && return _normalized_negative_unit_interval(problem, row)
    if (isfinite(problem.row_lower[row]) && iszero(bound_value(problem.row_lower[row]))) ||
       (isfinite(problem.row_upper[row]) && iszero(bound_value(problem.row_upper[row])))
        return _normalized_zero_interval(problem, row, pivot)
    end
    # Keep converted nonzero endpoints local to their division-only return path.
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

function _parallel_signature(terms)
    pivot_value = first(terms)[2]
    pivot = _exact_rational(pivot_value)
    isone(pivot) && return ExactValue[value == pivot_value ? pivot : _exact_rational(value)
                                     for (_, value) in terms]
    # Every coefficient equal to the nonzero pivot normalizes to the same one.
    unit = one(ExactValue)
    negative_unit = pivot == -1
    return ExactValue[value == pivot_value ? unit :
                      negative_unit ? -_exact_rational(value) : _exact_rational(value) / pivot
                      for (_, value) in terms]
end

function reduce_parallel_rows(problem::LinearProblem{T}) where {T}
    m, n = size(problem.A)
    entries = _row_entries(problem.A)
    keep = trues(m)
    groups = Dict{Vector{Int},Union{Int,ParallelSignatureGroups}}()
    intervals = nothing
    for row in 1:m
        terms = entries[row]
        isempty(terms) && continue
        # Most supports occur once, so defer exact ratios until a collision.
        support = Int[column for (column, _) in terms]
        bucket = get(groups, support, nothing)
        if isnothing(bucket)
            groups[support] = row
            continue
        elseif bucket isa Int
            first_row = bucket
            signatures = ParallelSignatureGroups()
            signatures[_parallel_signature(entries[first_row])] = [first_row]
            groups[support] = signatures
            bucket = signatures
        end
        signature = _parallel_signature(terms)
        representatives = get!(bucket, signature) do
            Int[]
        end
        if isempty(representatives)
            push!(representatives, row)
            continue
        end
        # Intervals are compared only after a proportional row is found.
        if isnothing(intervals)
            intervals = Vector{Tuple{ExactEndpoint,ExactEndpoint}}(undef, m)
        end
        pivot = _exact_rational(first(terms)[2])
        current = _normalized_interval(problem, row, pivot)
        intervals[row] = current
        redundant = false
        for previous in representatives
            keep[previous] || continue
            prior = isassigned(intervals, previous) ? intervals[previous] :
                    _normalized_interval(problem, previous,
                        _exact_rational(first(entries[previous])[2]))
            intervals[previous] = prior
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
    # Keep the lazy cache concrete to avoid extra allocations in the loop.
    negated_scale = scale
    has_negated_scale = false
    for (index, value) in source
        # Avoid constructing a BigInt zero on every lookup, including hits.
        # Exact cancellation also needs no rational subtraction or normalization.
        previous = get(target, index, nothing)
        if isnothing(previous) && (scale == -1 || value == -1)
            updated = scale == -1 ? value : scale
            iszero(updated) || (target[index] = updated)
            continue
        end
        if isnothing(previous) && isone(value)
            if !has_negated_scale
                negated_scale = -scale
                has_negated_scale = true
            end
            iszero(negated_scale) || (target[index] = negated_scale)
            continue
        end
        product = isone(scale) ? value : isone(value) ? scale :
                  scale == -1 ? -value : value == -1 ? -scale : scale * value
        if !isnothing(previous) && previous == product
            delete!(target, index)
            continue
        end
        updated = isnothing(previous) ? -product : previous - product
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
    upper::ExactEndpoint = lower
    for (row, negated_coefficient) in combination
        row == current && continue
        iszero(negated_coefficient) && continue
        source_lower = negated_coefficient < 0 ? problem.row_lower[row] : problem.row_upper[row]
        source_upper = negated_coefficient < 0 ? problem.row_upper[row] : problem.row_lower[row]
        coefficient = nothing
        if isnothing(lower) || !isfinite(source_lower)
            lower = nothing
        elseif !iszero(bound_value(source_lower))
            coefficient = -negated_coefficient
            value = _exact_rational(bound_value(source_lower))
            term = isone(coefficient) ? value : coefficient == -1 ? -value : coefficient * value
            lower = iszero(lower) ? term : lower + term
        end
        if isnothing(upper) || !isfinite(source_upper)
            upper = nothing
        elseif !iszero(bound_value(source_upper))
            # A computed lower contribution also serves an equal upper endpoint.
            if isnothing(coefficient) || bound_value(source_lower) != bound_value(source_upper)
                isnothing(coefficient) && (coefficient = -negated_coefficient)
                value = _exact_rational(bound_value(source_upper))
                term = isone(coefficient) ? value : coefficient == -1 ? -value : coefficient * value
            end
            upper = iszero(upper) ? term : upper + term
        end
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
    proof_seed = nothing
    for row in 1:m
        terms = entries[row]
        isempty(terms) && continue
        coefficients = Dict(column => _exact_rational(value)
                            for (column, value) in terms)
        isnothing(proof_seed) && (proof_seed = one(ExactValue))
        combination = Dict(row => proof_seed)
        while !isempty(coefficients)
            pivot = minimum(keys(coefficients))
            if !haskey(pivots, pivot)
                scale = coefficients[pivot]
                # A unit pivot already normalizes both the row and its proof.
                if !isone(scale)
                    negative_unit = scale == -1
                    for index in keys(coefficients)
                        value = coefficients[index]
                        coefficients[index] = value == scale ? proof_seed :
                                              negative_unit ? -value : value / scale
                    end
                    for index in keys(combination)
                        value = combination[index]
                        combination[index] = negative_unit ? -value : value / scale
                    end
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

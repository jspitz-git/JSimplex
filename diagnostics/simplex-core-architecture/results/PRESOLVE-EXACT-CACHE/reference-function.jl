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

struct DoubletonStep{T<:Real} <: AbstractPostsolveStep
    map::PresolveMap{T}
    eliminated::Int
    retained::Int
    equality_row::Int
    alpha::T
    beta::T
end

function substitute_free_doubleton(problem::LinearProblem{T}) where {T}
    m, n = size(problem.A)
    entries = _row_entries(problem.A)
    for equality_row in 1:m
        length(entries[equality_row]) == 2 || continue
        lower, upper = problem.row_lower[equality_row], problem.row_upper[equality_row]
        isfinite(lower) && isfinite(upper) &&
            bound_value(lower) == bound_value(upper) || continue
        for (eliminated, coefficient) in entries[equality_row]
            !isfinite(problem.column_lower[eliminated]) &&
                !isfinite(problem.column_upper[eliminated]) || continue
            retained, retained_coefficient =
                only(filter(entry -> entry[1] != eliminated, entries[equality_row]))
            alpha_exact = _exact_rational(bound_value(lower)) / _exact_rational(coefficient)
            beta_exact = -_exact_rational(retained_coefficient) / _exact_rational(coefficient)
            alpha = _represent_exact(T, alpha_exact)
            beta = _represent_exact(T, beta_exact)
            (isnothing(alpha) || isnothing(beta)) && continue
            cost_exact = _exact_rational(problem.objective[retained]) +
                         _exact_rational(problem.objective[eliminated]) * beta_exact
            constant_exact = _exact_rational(problem.objective_constant) +
                             _exact_rational(problem.objective[eliminated]) * alpha_exact
            new_cost = _represent_exact(T, cost_exact)
            new_constant = _represent_exact(T, constant_exact)
            (isnothing(new_cost) || isnothing(new_constant)) && continue

            new_A = copy(problem.A)
            row_lower, row_upper = copy(problem.row_lower), copy(problem.row_upper)
            valid = true
            for position in problem.A.colptr[eliminated]:(problem.A.colptr[eliminated + 1] - 1)
                row = problem.A.rowval[position]
                row == equality_row && continue
                coefficient_exact = _exact_rational(problem.A.nzval[position])
                iszero(coefficient_exact) && continue
                updated = _represent_exact(T,
                    _exact_rational(problem.A[row, retained]) + coefficient_exact * beta_exact)
                shifted_lower = _shift_bound_exact(T, row_lower[row],
                                                   coefficient_exact * alpha_exact)
                shifted_upper = _shift_bound_exact(T, row_upper[row],
                                                   coefficient_exact * alpha_exact)
                if isnothing(updated) || isnothing(shifted_lower) || isnothing(shifted_upper)
                    valid = false
                    break
                end
                new_A[row, retained] = updated
                row_lower[row], row_upper[row] = shifted_lower, shifted_upper
            end
            valid || continue
            rows = [row for row in 1:m if row != equality_row]
            columns = [column for column in 1:n if column != eliminated]
            reduced_A = new_A[rows, columns]
            dropzeros!(reduced_A)
            objective = copy(problem.objective)
            objective[retained] = new_cost
            reduced = LinearProblem{T}(
                reduced_A, objective[columns], new_constant, problem.objective_sense,
                row_lower[rows], row_upper[rows], problem.column_lower[columns],
                problem.column_upper[columns], problem.variable_domains[columns],
                problem.name,
                isempty(problem.row_names) ? String[] : problem.row_names[rows],
                isempty(problem.column_names) ? String[] : problem.column_names[columns],
            )
            step = DoubletonStep{T}(
                PresolveMap{T}(rows, columns,
                    Vector{Union{Nothing,T}}(nothing, n),
                    fill(FREE_NONBASIC, n), m),
                eliminated, retained, equality_row, alpha, beta,
            )
            return PresolveResult(reduced, (step,), n)
        end
    end
    return identity_presolve(problem)
end

function postsolve_primal(step::DoubletonStep{T}, primal::Vector{T}) where {T}
    restored = Vector{T}(undef, length(step.map.removed_values))
    restored[step.map.columns] .= primal
    restored[step.eliminated] = step.alpha + step.beta * restored[step.retained]
    return restored
end

function restore_basis(step::DoubletonStep, basis::Basis)
    restored = restore_basis(step.map, basis)
    n = length(step.map.removed_values)
    restored.basic_indices[step.equality_row] = step.eliminated
    restored.states[step.eliminated] = BASIC
    restored.states[n + step.equality_row] = AT_LOWER
    return restored
end

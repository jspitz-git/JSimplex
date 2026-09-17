struct SingletonEqualityRecord{T<:Real}
    row::Int
    column::Int
    rhs::T
    coefficient::T
    terms::Vector{Tuple{Int,T}}
end

struct SingletonEqualityStep{T<:Real} <: AbstractPostsolveStep
    map::PresolveMap{T}
    records::Vector{SingletonEqualityRecord{T}}
end

function _project_equality_bound(::Type{T}, rhs::ExactValue,
                                 coefficient::ExactValue, bound::Bound{T}) where {T}
    isfinite(bound) || return _unbounded_bound(T)
    projected = _represent_exact(T, rhs - coefficient * _exact_rational(bound_value(bound)))
    return isnothing(projected) ? nothing : Bound(projected)
end

function aggregate_singleton_equalities(problem::LinearProblem{T}) where {T}
    A = problem.A
    m, n = size(A)
    entries = _row_entries(A)
    removed = falses(n)
    row_lower, row_upper = copy(problem.row_lower), copy(problem.row_upper)
    objective_updates = Dict{Int,ExactValue}()
    constant_exact = _exact_rational(problem.objective_constant)
    records = SingletonEqualityRecord{T}[]

    for row in 1:m
        terms = entries[row]
        length(terms) >= 2 || continue
        lower, upper = problem.row_lower[row], problem.row_upper[row]
        isfinite(lower) && isfinite(upper) &&
            bound_value(lower) == bound_value(upper) || continue
        rhs = bound_value(lower)
        rhs_exact = _exact_rational(rhs)
        for (column, coefficient) in terms
            A.colptr[column + 1] - A.colptr[column] == 1 || continue
            removed[column] && continue
            coefficient_exact = _exact_rational(coefficient)
            projected_lower = _project_equality_bound(T, rhs_exact, coefficient_exact,
                coefficient_exact > 0 ? problem.column_upper[column] : problem.column_lower[column])
            projected_upper = _project_equality_bound(T, rhs_exact, coefficient_exact,
                coefficient_exact > 0 ? problem.column_lower[column] : problem.column_upper[column])
            (isnothing(projected_lower) || isnothing(projected_upper)) && continue

            objective_ratio = _exact_rational(problem.objective[column]) / coefficient_exact
            new_constant = constant_exact + objective_ratio * rhs_exact
            isnothing(_represent_exact(T, new_constant)) && continue
            changes = Tuple{Int,ExactValue}[]
            valid = true
            for (other, stored) in terms
                other == column && continue
                old_cost = get(objective_updates, other,
                               _exact_rational(problem.objective[other]))
                new_cost = old_cost - objective_ratio * _exact_rational(stored)
                if isnothing(_represent_exact(T, new_cost))
                    valid = false
                    break
                end
                push!(changes, (other, new_cost))
            end
            valid || continue

            row_lower[row], row_upper[row] = projected_lower, projected_upper
            for (other, new_cost) in changes
                objective_updates[other] = new_cost
            end
            constant_exact = new_constant
            removed[column] = true
            push!(records, SingletonEqualityRecord{T}(row, column, rhs, coefficient,
                [(other, stored) for (other, stored) in terms if other != column]))
            break
        end
    end
    isempty(records) && return identity_presolve(problem)

    objective = copy(problem.objective)
    for (column, value) in objective_updates
        objective[column] = something(_represent_exact(T, value))
    end
    columns = findall(.!removed)
    rows = collect(1:m)
    reduced = LinearProblem{T}(
        A[:, columns], objective[columns],
        something(_represent_exact(T, constant_exact)), problem.objective_sense,
        row_lower, row_upper, problem.column_lower[columns],
        problem.column_upper[columns], problem.variable_domains[columns],
        problem.name, problem.row_names,
        isempty(problem.column_names) ? String[] : problem.column_names[columns],
    )
    map = PresolveMap{T}(rows, columns,
        Vector{Union{Nothing,T}}(nothing, n), fill(FREE_NONBASIC, n), m)
    return PresolveResult(reduced, (SingletonEqualityStep{T}(map, records),), n)
end

function postsolve_primal(step::SingletonEqualityStep{T}, primal::Vector{T}) where {T}
    restored = Vector{T}(undef, length(step.map.removed_values))
    restored[step.map.columns] .= primal
    for record in step.records
        activity = zero(T)
        for (column, coefficient) in record.terms
            activity += coefficient * restored[column]
        end
        restored[record.column] = (record.rhs - activity) / record.coefficient
    end
    return restored
end

function restore_basis(step::SingletonEqualityStep, basis::Basis)
    restored = restore_basis(step.map, basis)
    n = length(step.map.removed_values)
    basic_position = zeros(Int, length(restored.states))
    for (row, index) in enumerate(restored.basic_indices)
        basic_position[index] = row
    end
    for record in step.records
        row_state = restored.states[n + record.row]
        if row_state == BASIC
            restored.basic_indices[basic_position[n + record.row]] = record.column
            restored.states[record.column] = BASIC
        elseif row_state == AT_LOWER
            restored.states[record.column] =
                record.coefficient > 0 ? AT_UPPER : AT_LOWER
        elseif row_state == AT_UPPER
            restored.states[record.column] =
                record.coefficient > 0 ? AT_LOWER : AT_UPPER
        else
            restored.states[record.column] = FREE_NONBASIC
        end
        restored.states[n + record.row] = AT_LOWER
    end
    return restored
end

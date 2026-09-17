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

struct SparseEqualityRecord{T<:Real}
    row::Int
    column::Int
    rhs::T
    coefficient::T
    terms::Vector{Tuple{Int,T}}
    removed_row::Bool
end

struct SparseEqualityStep{T<:Real} <: AbstractPostsolveStep
    map::PresolveMap{T}
    records::Vector{SparseEqualityRecord{T}}
end

function _equality_implies_column_bounds(problem::LinearProblem, row_terms,
                                         pivot_column::Int, pivot::ExactValue,
                                         rhs::ExactValue)
    other_min::ExactEndpoint = zero(ExactValue)
    other_max::ExactEndpoint = zero(ExactValue)
    for (column, stored) in row_terms
        column == pivot_column && continue
        coefficient = _exact_rational(stored)
        min_bound = coefficient > 0 ? problem.column_lower[column] :
                                      problem.column_upper[column]
        max_bound = coefficient > 0 ? problem.column_upper[column] :
                                      problem.column_lower[column]
        other_min = isnothing(other_min) || !isfinite(min_bound) ? nothing :
                    other_min + coefficient * _exact_rational(bound_value(min_bound))
        other_max = isnothing(other_max) || !isfinite(max_bound) ? nothing :
                    other_max + coefficient * _exact_rational(bound_value(max_bound))
    end
    lower = problem.column_lower[pivot_column]
    upper = problem.column_upper[pivot_column]
    lower_activity = pivot > 0 ? other_max : other_min
    upper_activity = pivot > 0 ? other_min : other_max
    lower_implied = !isfinite(lower) ||
        (!isnothing(lower_activity) &&
         (rhs - lower_activity) / pivot >= _exact_rational(bound_value(lower)))
    upper_implied = !isfinite(upper) ||
        (!isnothing(upper_activity) &&
         (rhs - upper_activity) / pivot <= _exact_rational(bound_value(upper)))
    return lower_implied && upper_implied
end

function aggregate_sparse_equalities(problem::LinearProblem{T}) where {T}
    A = problem.A
    m, n = size(A)
    entries = _row_entries(A)
    removed_rows, removed_columns = falses(m), falses(n)
    modified_rows, blocked_pivots = falses(m), falses(n)
    row_lower, row_upper = copy(problem.row_lower), copy(problem.row_upper)
    objective_updates = Dict{Int,ExactValue}()
    matrix_updates = Dict{Tuple{Int,Int},ExactValue}()
    constant_exact = _exact_rational(problem.objective_constant)
    records = SparseEqualityRecord{T}[]
    estimated_updates = 0

    for row in 1:m
        # A row changed by an earlier substitution cannot supply an independent
        # equality for this batch.
        modified_rows[row] && continue
        terms = entries[row]
        2 <= length(terms) <= 8 || continue
        lower, upper = problem.row_lower[row], problem.row_upper[row]
        isfinite(lower) && isfinite(upper) &&
            bound_value(lower) == bound_value(upper) || continue
        any(entry -> removed_columns[entry[1]], terms) && continue
        rhs = bound_value(lower)
        rhs_exact = _exact_rational(rhs)

        for (column, coefficient) in terms
            blocked_pivots[column] && continue
            column_degree = A.colptr[column + 1] - A.colptr[column]
            column_degree >= 2 || continue
            fill_estimate = (length(terms) - 1) * (column_degree - 1)
            fill_estimate <= 10 && estimated_updates + fill_estimate <= 200_000 || continue
            pivot = _exact_rational(coefficient)
            implied = _equality_implies_column_bounds(problem, terms, column,
                                                       pivot, rhs_exact)
            projected_lower = implied ? nothing : _project_equality_bound(T, rhs_exact,
                pivot, pivot > 0 ? problem.column_upper[column] : problem.column_lower[column])
            projected_upper = implied ? nothing : _project_equality_bound(T, rhs_exact,
                pivot, pivot > 0 ? problem.column_lower[column] : problem.column_upper[column])
            !implied && (isnothing(projected_lower) || isnothing(projected_upper)) && continue

            ratio = _exact_rational(problem.objective[column]) / pivot
            new_constant = constant_exact + ratio * rhs_exact
            isnothing(_represent_exact(T, new_constant)) && continue
            cost_changes = Tuple{Int,ExactValue}[]
            valid = true
            for (other, value) in terms
                other == column && continue
                old_cost = get(objective_updates, other,
                               _exact_rational(problem.objective[other]))
                updated = old_cost - ratio * _exact_rational(value)
                if isnothing(_represent_exact(T, updated))
                    valid = false
                    break
                end
                push!(cost_changes, (other, updated))
            end
            valid || continue

            bound_changes = Tuple{Int,Bound{T},Bound{T}}[]
            coefficient_changes = Tuple{Tuple{Int,Int},ExactValue}[]
            for position in A.colptr[column]:(A.colptr[column + 1] - 1)
                other_row = A.rowval[position]
                other_row == row && continue
                multiplier = _exact_rational(A.nzval[position]) / pivot
                shift = multiplier * rhs_exact
                shifted_lower = _shift_bound_exact(T, row_lower[other_row], shift)
                shifted_upper = _shift_bound_exact(T, row_upper[other_row], shift)
                if isnothing(shifted_lower) || isnothing(shifted_upper)
                    valid = false
                    break
                end
                push!(bound_changes, (other_row, shifted_lower, shifted_upper))
                for (other, value) in terms
                    other == column && continue
                    key = (other_row, other)
                    old_value = get(matrix_updates, key, _exact_rational(A[other_row, other]))
                    updated = old_value - multiplier * _exact_rational(value)
                    if isnothing(_represent_exact(T, updated))
                        valid = false
                        break
                    end
                    push!(coefficient_changes, (key, updated))
                end
                valid || break
            end
            valid || continue

            for (other, updated) in cost_changes
                objective_updates[other] = updated
            end
            for (other_row, shifted_lower, shifted_upper) in bound_changes
                row_lower[other_row], row_upper[other_row] = shifted_lower, shifted_upper
                modified_rows[other_row] = true
            end
            for (key, updated) in coefficient_changes
                matrix_updates[key] = updated
            end
            constant_exact = new_constant
            if implied
                removed_rows[row] = true
            else
                row_lower[row], row_upper[row] = projected_lower, projected_upper
            end
            modified_rows[row] = true
            removed_columns[column] = true
            # Do not later pivot on a variable needed to reconstruct this one.
            for (other, _) in terms
                blocked_pivots[other] = true
            end
            push!(records, SparseEqualityRecord{T}(row, column, rhs, coefficient,
                [(other, value) for (other, value) in terms if other != column], implied))
            estimated_updates += fill_estimate
            break
        end
        length(records) >= 50_000 && break
    end
    isempty(records) && return identity_presolve(problem)

    rows, columns = findall(.!removed_rows), findall(.!removed_columns)
    row_index, column_index = zeros(Int, m), zeros(Int, n)
    for (new, old) in enumerate(rows)
        row_index[old] = new
    end
    for (new, old) in enumerate(columns)
        column_index[old] = new
    end
    coordinates_row, coordinates_column, values = Int[], Int[], T[]
    for column in columns
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            row = A.rowval[position]
            removed_rows[row] && continue
            exact = pop!(matrix_updates, (row, column), nothing)
            value = isnothing(exact) ? A.nzval[position] :
                    something(_represent_exact(T, exact))
            iszero(value) && continue
            push!(coordinates_row, row_index[row])
            push!(coordinates_column, column_index[column])
            push!(values, value)
        end
    end
    for ((row, column), exact) in matrix_updates
        (removed_rows[row] || removed_columns[column]) && continue
        value = something(_represent_exact(T, exact))
        iszero(value) && continue
        push!(coordinates_row, row_index[row])
        push!(coordinates_column, column_index[column])
        push!(values, value)
    end
    objective = copy(problem.objective)
    for (column, exact) in objective_updates
        objective[column] = something(_represent_exact(T, exact))
    end
    reduced = LinearProblem{T}(
        sparse(coordinates_row, coordinates_column, values, length(rows), length(columns)),
        objective[columns], something(_represent_exact(T, constant_exact)),
        problem.objective_sense, row_lower[rows], row_upper[rows],
        problem.column_lower[columns], problem.column_upper[columns],
        problem.variable_domains[columns], problem.name,
        isempty(problem.row_names) ? String[] : problem.row_names[rows],
        isempty(problem.column_names) ? String[] : problem.column_names[columns],
    )
    map = PresolveMap{T}(rows, columns,
        Vector{Union{Nothing,T}}(nothing, n), fill(FREE_NONBASIC, n), m)
    return PresolveResult(reduced, (SparseEqualityStep{T}(map, records),), n)
end

function postsolve_primal(step::SparseEqualityStep{T}, primal::Vector{T}) where {T}
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

function restore_basis(step::SparseEqualityStep, basis::Basis)
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

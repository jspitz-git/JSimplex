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
    if iszero(bound_value(bound))
        projected = _represent_exact(T, rhs)
        return isnothing(projected) ? nothing : Bound(projected)
    end
    value = _exact_rational(bound_value(bound))
    product = isone(coefficient) ? value : coefficient == -1 ? -value :
              isone(value) ? coefficient : value == -1 ? -coefficient : coefficient * value
    projected = _represent_exact(T, iszero(rhs) ? -product :
        rhs == product ? zero(ExactValue) :
        denominator(rhs) == denominator(product) ?
        Rational{BigInt}(numerator(rhs) - numerator(product), denominator(rhs)) : rhs - product)
    return isnothing(projected) ? nothing : Bound(projected)
end

function _singleton_objective_value(::Type{T}, value::ExactValue) where {T<:Real}
    represented = _represent_exact(T, value)
    !isnothing(represented) && return represented
    # Only singleton objective updates may be rounded; bounds and the
    # objective constant still use _represent_exact.
    (T === Float32 || T === Float64) || return nothing
    rounded = try
        T(value)
    catch exception
        exception isa InexactError || exception isa OverflowError ||
            exception isa DomainError || rethrow()
        return nothing
    end
    isfinite(rounded) || return nothing
    error = abs(value - _exact_rational(rounded))
    limit = abs(value) * _exact_rational(8 * eps(T))
    return error <= limit ? rounded : nothing
end

function aggregate_singleton_equalities(problem::LinearProblem{T}) where {T}
    A = problem.A
    m, n = size(A)
    entries = _row_entries(A)
    removed = falses(n)
    row_lower, row_upper = problem.row_lower, problem.row_upper
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
        # Prefer a candidate that preserves the objective exactly when several
        # singleton columns occur in the same equality.
        exact_candidate = nothing
        rounded_candidate = nothing
        for (column, coefficient) in terms
            A.colptr[column + 1] - A.colptr[column] == 1 || continue
            removed[column] && continue
            coefficient_exact = _exact_rational(coefficient)
            projected_lower = _project_equality_bound(T, rhs_exact, coefficient_exact,
                coefficient_exact > 0 ? problem.column_upper[column] : problem.column_lower[column])
            projected_upper = problem.column_lower[column] == problem.column_upper[column] ?
                projected_lower : _project_equality_bound(T, rhs_exact, coefficient_exact,
                coefficient_exact > 0 ? problem.column_lower[column] : problem.column_upper[column])
            (isnothing(projected_lower) || isnothing(projected_upper)) && continue

            objective_exact = _exact_rational(problem.objective[column])
            objective_ratio = iszero(objective_exact) || isone(coefficient_exact) ? objective_exact :
                coefficient_exact == -1 ? -objective_exact :
                denominator(objective_exact) == denominator(coefficient_exact) ?
                Rational{BigInt}(numerator(objective_exact), numerator(coefficient_exact)) : objective_exact / coefficient_exact
            new_constant = if iszero(objective_ratio) || iszero(rhs_exact)
                constant_exact
            else
                product = isone(objective_ratio) ? rhs_exact : objective_ratio == -1 ? -rhs_exact :
                    isone(rhs_exact) ? objective_ratio : rhs_exact == -1 ? -objective_ratio : objective_ratio * rhs_exact
                if iszero(constant_exact)
                    product
                elseif denominator(constant_exact) == denominator(product)
                    summed_numerator = numerator(constant_exact) + numerator(product)
                    iszero(summed_numerator) ? zero(ExactValue) :
                        Rational{BigInt}(summed_numerator, denominator(constant_exact))
                else
                    constant_exact + product
                end
            end
            isnothing(_represent_exact(T, new_constant)) && continue
            changes = Tuple{Int,ExactValue}[]
            valid = true
            needs_rounding = false
            for (other, stored) in terms
                other == column && continue
                old_cost = get(objective_updates, other) do
                    _exact_rational(problem.objective[other])
                end
                new_cost = if iszero(objective_ratio)
                    old_cost
                else
                    value = _exact_rational(stored)
                    product = isone(objective_ratio) ? value : objective_ratio == -1 ? -value :
                        isone(value) ? objective_ratio : value == -1 ? -objective_ratio : objective_ratio * value
                    iszero(old_cost) ? -product : old_cost == product ? zero(ExactValue) :
                        denominator(old_cost) == denominator(product) ?
                            Rational{BigInt}(numerator(old_cost) - numerator(product), denominator(old_cost)) :
                            old_cost - product
                end
                if isnothing(_represent_exact(T, new_cost))
                    if isnothing(_singleton_objective_value(T, new_cost))
                        valid = false
                        break
                    end
                    needs_rounding = true
                end
                push!(changes, (other, new_cost))
            end
            valid || continue
            candidate = (column, coefficient, projected_lower, projected_upper,
                         new_constant, changes)
            if needs_rounding
                isnothing(rounded_candidate) && (rounded_candidate = candidate)
            else
                exact_candidate = candidate
                break
            end
        end
        chosen = isnothing(exact_candidate) ? rounded_candidate : exact_candidate
        isnothing(chosen) && continue
        column, coefficient, projected_lower, projected_upper,
            new_constant, changes = chosen
        # Rejected candidates need no private bounds; copy before the first write.
        if row_lower === problem.row_lower
            row_lower, row_upper = copy(row_lower), copy(row_upper)
        end
        row_lower[row], row_upper[row] = projected_lower, projected_upper
        for (other, new_cost) in changes
            objective_updates[other] = new_cost
        end
        constant_exact = new_constant
        removed[column] = true
        push!(records, SingletonEqualityRecord{T}(row, column, rhs, coefficient,
            [(other, stored) for (other, stored) in terms if other != column]))
    end
    isempty(records) && return identity_presolve(problem)

    objective = copy(problem.objective)
    for (column, value) in objective_updates
        objective[column] = something(_singleton_objective_value(T, value))
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

function aggregate_sparse_equalities(problem::LinearProblem{T}) where {T}
    A = problem.A
    m, n = size(A)
    entries = _row_entries(A)
    removed_rows, removed_columns = falses(m), falses(n)
    modified_rows, blocked_pivots = falses(m), falses(n)
    row_lower, row_upper = problem.row_lower, problem.row_upper
    objective_updates = Dict{Int,ExactValue}()
    matrix_updates = Dict{Tuple{Int,Int},ExactValue}()
    constant_exact = _exact_rational(problem.objective_constant)
    records = SparseEqualityRecord{T}[]
    estimated_updates = 0
    # Allocate scratch only when a candidate reaches its staging phase, then
    # clear it before reuse so rejected candidates cannot leak partial updates.
    cost_changes = nothing
    bound_changes = nothing
    coefficient_changes = nothing

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
            positive_pivot = numerator(pivot) > 0
            projected_lower = implied ? nothing : _project_equality_bound(T, rhs_exact,
                pivot, positive_pivot ? problem.column_upper[column] : problem.column_lower[column])
            projected_upper = implied ? nothing :
                problem.column_lower[column] == problem.column_upper[column] ? projected_lower :
                _project_equality_bound(T, rhs_exact,
                pivot, positive_pivot ? problem.column_lower[column] : problem.column_upper[column])
            !implied && (isnothing(projected_lower) || isnothing(projected_upper)) && continue

            objective_exact = _exact_rational(problem.objective[column])
            ratio = iszero(objective_exact) || isone(pivot) ? objective_exact :
                pivot == -1 ? -objective_exact :
                denominator(objective_exact) == denominator(pivot) ?
                Rational{BigInt}(numerator(objective_exact), numerator(pivot)) : objective_exact / pivot
            new_constant = if iszero(ratio) || iszero(rhs_exact)
                constant_exact
            else
                product = isone(ratio) ? rhs_exact : ratio == -1 ? -rhs_exact :
                    isone(rhs_exact) ? ratio : rhs_exact == -1 ? -ratio : ratio * rhs_exact
                if iszero(constant_exact)
                    product
                elseif denominator(constant_exact) == denominator(product)
                    summed_numerator = numerator(constant_exact) + numerator(product)
                    iszero(summed_numerator) ? zero(ExactValue) :
                        Rational{BigInt}(summed_numerator, denominator(constant_exact))
                else
                    constant_exact + product
                end
            end
            isnothing(_represent_exact(T, new_constant)) && continue
            cost_changes = isnothing(cost_changes) ? Tuple{Int,ExactValue}[] : empty!(cost_changes)
            valid = true
            for (other, value) in terms
                other == column && continue
                old_cost = get(objective_updates, other) do
                    _exact_rational(problem.objective[other])
                end
                updated = if iszero(ratio)
                    old_cost
                else
                    term_exact = _exact_rational(value)
                    product = isone(ratio) ? term_exact : ratio == -1 ? -term_exact :
                        isone(term_exact) ? ratio : term_exact == -1 ? -ratio : ratio * term_exact
                    iszero(old_cost) ? -product :
                        old_cost == product ? zero(ExactValue) :
                        denominator(old_cost) == denominator(product) ?
                            Rational{BigInt}(numerator(old_cost) - numerator(product), denominator(old_cost)) :
                            old_cost - product
                end
                if isnothing(_represent_exact(T, updated))
                    valid = false
                    break
                end
                push!(cost_changes, (other, updated))
            end
            valid || continue

            bound_changes = isnothing(bound_changes) ? Tuple{Int,Bound{T},Bound{T}}[] : empty!(bound_changes)
            coefficient_changes = isnothing(coefficient_changes) ?
                Tuple{Tuple{Int,Int},ExactValue}[] : empty!(coefficient_changes)
            for position in A.colptr[column]:(A.colptr[column + 1] - 1)
                other_row = A.rowval[position]
                other_row == row && continue
                coefficient_exact = _exact_rational(A.nzval[position])
                multiplier = isone(pivot) ? coefficient_exact :
                    pivot == -1 ? -coefficient_exact :
                    denominator(coefficient_exact) == denominator(pivot) ?
                    Rational{BigInt}(numerator(coefficient_exact), numerator(pivot)) : coefficient_exact / pivot
                shifted_lower, shifted_upper = row_lower[other_row], row_upper[other_row]
                if isfinite(shifted_lower) || isfinite(shifted_upper)
                    shift = iszero(rhs_exact) ? rhs_exact :
                        iszero(multiplier) ? multiplier :
                        isone(multiplier) ? rhs_exact : multiplier == -1 ? -rhs_exact :
                        isone(rhs_exact) ? multiplier : rhs_exact == -1 ? -multiplier : multiplier * rhs_exact
                    # A zero shift preserves each original bound's representation.
                    shared_bounds = !iszero(shift) && shifted_lower == shifted_upper
                    shifted_lower = _shift_bound_exact(T, shifted_lower, shift)
                    shifted_upper = shared_bounds ? shifted_lower : _shift_bound_exact(T, shifted_upper, shift)
                end
                if isnothing(shifted_lower) || isnothing(shifted_upper)
                    valid = false
                    break
                end
                push!(bound_changes, (other_row, shifted_lower, shifted_upper))
                for (other, value) in terms
                    other == column && continue
                    key = (other_row, other)
                    old_value = get(matrix_updates, key) do
                        _exact_rational(A[other_row, other])
                    end
                    updated = if iszero(multiplier)
                        old_value
                    else
                        term_exact = _exact_rational(value)
                        product = isone(multiplier) ? term_exact : multiplier == -1 ? -term_exact :
                            isone(term_exact) ? multiplier : term_exact == -1 ? -multiplier : multiplier * term_exact
                        iszero(old_value) ? -product :
                            old_value == product ? zero(ExactValue) :
                            denominator(old_value) == denominator(product) ?
                                Rational{BigInt}(numerator(old_value) - numerator(product), denominator(old_value)) :
                                old_value - product
                    end
                    if isnothing(_represent_exact(T, updated))
                        valid = false
                        break
                    end
                    push!(coefficient_changes, (key, updated))
                end
                valid || break
            end
            valid || continue

            # Commit staged changes only to private bounds, reused by later rows.
            if row_lower === problem.row_lower
                row_lower, row_upper = copy(row_lower), copy(row_upper)
            end
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

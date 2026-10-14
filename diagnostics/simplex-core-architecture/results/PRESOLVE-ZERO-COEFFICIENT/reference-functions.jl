function zero_reference_aggregate(problem::LinearProblem{T}) where {T}
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
function zero_reference_dispatch!(problem, steps, trace, index::Int)
    index == 1 && return _apply_presolve_pass!(_presolve_basic, problem, steps, trace)
    index == 2 && return _apply_presolve_pass!(reduce_singleton_rows, problem, steps, trace)
    index == 3 && return _apply_presolve_pass!(aggregate_singleton_equalities, problem, steps, trace)
    index == 4 && return _apply_presolve_pass!(zero_reference_aggregate, problem, steps, trace)
    index == 5 && return _apply_presolve_pass!(reduce_parallel_rows, problem, steps, trace)
    index == 6 && return _apply_presolve_pass!(reduce_dependent_rows, problem, steps, trace)
    index == 7 && return _apply_presolve_pass!(substitute_free_doubleton, problem, steps, trace)
    index == 8 && return _apply_propagation_pass!(problem, steps, trace)
    index == 9 && return _apply_presolve_pass!(reduce_dual_fixings, problem, steps, trace)
    throw(ArgumentError("unknown presolve pass: $index"))
end
function zero_reference_presolve(problem::LinearProblem{T}) where {T}
    # Individual passes retain their small tuple results. The complete history
    # has runtime length, so accumulate it without changing the result's type.
    steps = PostsolveStep{T}[]
    current = problem
    propagation_trace = PropagationTrace{T}()
    last_relevant_pass = _PRESOLVE_PASS_COUNT
    for _ in 1:12
        last_changed_pass = 0
        for index in 1:_PRESOLVE_PASS_COUNT
            index > last_relevant_pass && break
            next = zero_reference_dispatch!(current, steps, propagation_trace, index)
            next isa PresolveFailure && return next
            current, changed = next
            if changed
                last_changed_pass = index
                last_relevant_pass = _PRESOLVE_PASS_COUNT
            end
        end
        last_changed_pass == 0 && break
        # Later passes already saw the final model in this round. Revisit them
        # only if an earlier pass changes that model in the next round.
        last_relevant_pass = last_changed_pass
    end
    return PresolveResult(current, steps, size(problem.A, 2))
end

struct DoubletonStep{T<:Real} <: AbstractPostsolveStep
    map::PresolveMap{T}
    eliminated::Int
    retained::Int
    equality_row::Int
    alpha::T
    beta::T
end

function _doubleton_row_positions(A::SparseMatrixCSC)
    # Store two (column, CSC position) pairs. A negative first column marks
    # rows with more than two nonzeros; a zero second column means fewer than two.
    positions = fill((0, 0, 0, 0), size(A, 1))
    for column in axes(A, 2)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            iszero(A.nzval[position]) && continue
            row = A.rowval[position]
            first_column, first_position, second_column, _ = positions[row]
            first_column < 0 && continue
            if iszero(first_column)
                positions[row] = (column, position, 0, 0)
            elseif iszero(second_column)
                positions[row] = (first_column, first_position, column, position)
            else
                positions[row] = (-1, 0, 0, 0)
            end
        end
    end
    return positions
end

function substitute_free_doubleton(problem::LinearProblem{T}) where {T}
    m, n = size(problem.A)
    positions = _doubleton_row_positions(problem.A)
    for equality_row in 1:m
        first_column, first_position, second_column, second_position = positions[equality_row]
        second_column > 0 || continue
        lower, upper = problem.row_lower[equality_row], problem.row_upper[equality_row]
        isfinite(lower) && isfinite(upper) &&
            bound_value(lower) == bound_value(upper) || continue
        terms = ((first_column, problem.A.nzval[first_position]),
                 (second_column, problem.A.nzval[second_position]))
        for (eliminated, coefficient) in terms
            !isfinite(problem.column_lower[eliminated]) &&
                !isfinite(problem.column_upper[eliminated]) || continue
            retained, retained_coefficient = only(filter(entry -> entry[1] != eliminated, terms))
            rhs_exact = _exact_rational(bound_value(lower))
            retained_exact = _exact_rational(retained_coefficient)
            if isone(coefficient)
                alpha_exact = rhs_exact
                beta_exact = -retained_exact
            elseif coefficient == -1
                alpha_exact = -rhs_exact
                beta_exact = retained_exact
            else
                pivot_exact = _exact_rational(coefficient)
                alpha_exact = iszero(rhs_exact) ? rhs_exact :
                    denominator(rhs_exact) == denominator(pivot_exact) ?
                    Rational{BigInt}(numerator(rhs_exact), numerator(pivot_exact)) : rhs_exact / pivot_exact
                beta_exact = denominator(retained_exact) == denominator(pivot_exact) ?
                    Rational{BigInt}(-numerator(retained_exact), numerator(pivot_exact)) : -retained_exact / pivot_exact
            end
            alpha = _represent_exact(T, alpha_exact)
            beta = _represent_exact(T, beta_exact)
            (isnothing(alpha) || isnothing(beta)) && continue
            eliminated_cost = problem.objective[eliminated]
            if iszero(eliminated_cost)
                cost_exact = _exact_rational(problem.objective[retained])
                constant_exact = _exact_rational(problem.objective_constant)
            else
                if isone(eliminated_cost)
                    cost_shift = beta_exact
                    constant_shift = alpha_exact
                elseif eliminated_cost == -1
                    cost_shift = -beta_exact
                    constant_shift = iszero(alpha_exact) ? alpha_exact : -alpha_exact
                else
                    eliminated_cost_exact = _exact_rational(eliminated_cost)
                    cost_shift = isone(beta_exact) ? eliminated_cost_exact :
                                 beta_exact == -1 ? -eliminated_cost_exact :
                                 eliminated_cost_exact * beta_exact
                    constant_shift = iszero(alpha_exact) ? alpha_exact :
                                     isone(alpha_exact) ? eliminated_cost_exact :
                                     alpha_exact == -1 ? -eliminated_cost_exact :
                                     eliminated_cost_exact * alpha_exact
                end
                retained_cost = problem.objective[retained]
                cost_exact = if iszero(retained_cost)
                    cost_shift
                else
                    retained_cost_exact = _exact_rational(retained_cost)
                    if denominator(retained_cost_exact) == denominator(cost_shift)
                        summed_numerator = numerator(retained_cost_exact) + numerator(cost_shift)
                        iszero(summed_numerator) ? zero(Rational{BigInt}) :
                            Rational{BigInt}(summed_numerator, denominator(retained_cost_exact))
                    else
                        retained_cost_exact + cost_shift
                    end
                end
                constant_exact = if iszero(alpha_exact)
                    _exact_rational(problem.objective_constant)
                elseif iszero(problem.objective_constant)
                    constant_shift
                else
                    stored_constant_exact = _exact_rational(problem.objective_constant)
                    if denominator(stored_constant_exact) == denominator(constant_shift)
                        summed_numerator = numerator(stored_constant_exact) + numerator(constant_shift)
                        iszero(summed_numerator) ? zero(Rational{BigInt}) :
                            Rational{BigInt}(summed_numerator, denominator(stored_constant_exact))
                    else
                        stored_constant_exact + constant_shift
                    end
                end
            end
            new_cost = _represent_exact(T, cost_exact)
            new_constant = _represent_exact(T, constant_exact)
            (isnothing(new_cost) || isnothing(new_constant)) && continue

            new_A = copy(problem.A)
            row_lower, row_upper = copy(problem.row_lower), copy(problem.row_upper)
            valid = true
            for position in problem.A.colptr[eliminated]:(problem.A.colptr[eliminated + 1] - 1)
                row = problem.A.rowval[position]
                row == equality_row && continue
                row_coefficient = problem.A.nzval[position]
                iszero(row_coefficient) && continue
                coefficient_exact = _exact_rational(row_coefficient)
                old_value = problem.A[row, retained]
                product = isone(coefficient_exact) ? beta_exact :
                          coefficient_exact == -1 ? -beta_exact :
                          isone(beta_exact) ? coefficient_exact :
                          beta_exact == -1 ? -coefficient_exact :
                          coefficient_exact * beta_exact
                updated_exact = if iszero(old_value)
                    product
                else
                    old_value_exact = _exact_rational(old_value)
                    if denominator(old_value_exact) == denominator(product)
                        summed_numerator = numerator(old_value_exact) + numerator(product)
                        iszero(summed_numerator) ? zero(Rational{BigInt}) :
                            Rational{BigInt}(summed_numerator, denominator(old_value_exact))
                    else
                        old_value_exact + product
                    end
                end
                updated = _represent_exact(T, updated_exact)
                shifted_lower, shifted_upper = row_lower[row], row_upper[row]
                if isfinite(shifted_lower) || isfinite(shifted_upper)
                    shift = iszero(alpha_exact) ? alpha_exact :
                            isone(coefficient_exact) ? alpha_exact :
                            coefficient_exact == -1 ? -alpha_exact :
                            isone(alpha_exact) ? coefficient_exact :
                            alpha_exact == -1 ? -coefficient_exact :
                            coefficient_exact * alpha_exact
                    # A zero shift preserves each original bound's representation.
                    shared_bounds = !iszero(shift) && shifted_lower == shifted_upper
                    shifted_lower = _shift_bound_exact(T, shifted_lower, shift)
                    shifted_upper = shared_bounds ? shifted_lower : _shift_bound_exact(T, shifted_upper, shift)
                end
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

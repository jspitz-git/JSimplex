struct PresolveFailure
    status::TerminationStatus
    message::String
    rows::Int
    columns::Int
    nonzeros::Int
end

struct PresolveMap{T<:Real} <: AbstractPostsolveStep
    rows::Vector{Int}
    columns::Vector{Int}
    removed_values::Vector{Union{Nothing,T}}
    removed_states::Vector{VariableState}
    original_row_count::Int
end

_exact_rational(value::Real) = Rational{BigInt}(value)
_exact_rational(value::BigFloat) =
    setprecision(BigFloat, max(precision(value), precision(BigFloat))) do
        Rational{BigInt}(value)
    end

# Accept a floating reduction only if its new stored value is the exact result
# of arithmetic on the stored inputs. This avoids changing an LP certificate by
# rounding a bound or objective constant before the simplex sees it.
function _represent_exact(::Type{T}, value::Rational{BigInt}) where {T<:Real}
    converted = try
        T(value)
    catch exception
        exception isa InexactError || exception isa OverflowError ||
            exception isa DomainError || rethrow()
        return nothing
    end
    isfinite(converted) || return nothing
    iszero(converted) && return iszero(value) ? converted : nothing
    isone(converted) && return isone(value) ? converted : nothing
    converted == -1 && return value == -1 ? converted : nothing
    return _exact_rational(converted) == value ? converted : nothing
end

function _shift_bound_exact(::Type{T}, bound::Bound{T}, shift::Rational{BigInt}) where {T}
    iszero(shift) && return bound
    isfinite(bound) || return bound
    exact_value = if iszero(bound_value(bound))
        -shift
    else
        bound_exact = _exact_rational(bound_value(bound))
        bound_exact == shift ? zero(Rational{BigInt}) :
            denominator(bound_exact) == denominator(shift) ?
            Rational{BigInt}(numerator(bound_exact) - numerator(shift), denominator(bound_exact)) :
            bound_exact - shift
    end
    value = _represent_exact(T, exact_value)
    return isnothing(value) ? nothing : Bound(value)
end

function _elimination_value(problem::LinearProblem{T}, column::Int) where {T}
    lower, upper = problem.column_lower[column], problem.column_upper[column]
    if isfinite(lower) && isfinite(upper) && bound_value(lower) == bound_value(upper)
        return bound_value(lower), AT_LOWER
    end
    A = problem.A
    all(position -> iszero(A.nzval[position]),
        A.colptr[column]:(A.colptr[column + 1] - 1)) || return nothing
    cost = problem.objective[column]
    if iszero(cost)
        isfinite(lower) && return bound_value(lower), AT_LOWER
        isfinite(upper) && return bound_value(upper), AT_UPPER
        return zero(T), FREE_NONBASIC
    end
    choose_lower = (cost > zero(T)) == (problem.objective_sense == MIN_SENSE)
    bound = choose_lower ? lower : upper
    isfinite(bound) || return nothing
    return bound_value(bound), choose_lower ? AT_LOWER : AT_UPPER
end

function _presolve_basic(problem::LinearProblem{T}; selections=nothing) where {T}
    A = problem.A
    row_count, column_count = size(A)
    lower, upper = problem.row_lower, problem.row_upper
    constant = problem.objective_constant
    kept_columns = trues(column_count)
    removed_values = Vector{Union{Nothing,T}}(nothing, column_count)
    removed_states = fill(FREE_NONBASIC, column_count)
    changes = nothing

    for column in 1:column_count
        selected = isnothing(selections) ? _elimination_value(problem, column) :
                   selections[column]
        isnothing(selected) && continue
        value, state = selected
        value_exact = _exact_rational(value)
        cost = problem.objective[column]
        shifted_constant = if iszero(cost) || iszero(value_exact)
            constant
        else
            contribution = if isone(cost)
                value_exact
            elseif cost == -1
                -value_exact
            else
                cost_exact = _exact_rational(cost)
                isone(value_exact) ? cost_exact :
                    value_exact == -1 ? -cost_exact : cost_exact * value_exact
            end
            shifted_exact = if iszero(constant)
                contribution
            else
                constant_exact = _exact_rational(constant)
                if denominator(constant_exact) == denominator(contribution)
                    summed_numerator = numerator(constant_exact) + numerator(contribution)
                    iszero(summed_numerator) ? zero(Rational{BigInt}) :
                        Rational{BigInt}(summed_numerator, denominator(constant_exact))
                else
                    constant_exact + contribution
                end
            end
            _represent_exact(T, shifted_exact)
        end
        isnothing(shifted_constant) && continue
        # Clear staged changes even after a rejection or before an empty column.
        changes = isnothing(changes) ? Tuple{Int,Bound{T},Bound{T}}[] : empty!(changes)
        safe = true
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            row = A.rowval[position]
            shifted_lower, shifted_upper = lower[row], upper[row]
            if isfinite(shifted_lower) || isfinite(shifted_upper)
                coefficient = A.nzval[position]
                shift = if iszero(value_exact) || isone(coefficient)
                    value_exact
                elseif coefficient == -1
                    -value_exact
                else
                    coefficient_exact = _exact_rational(coefficient)
                    isone(value_exact) ? coefficient_exact :
                        value_exact == -1 ? -coefficient_exact :
                        coefficient_exact * value_exact
                end
                # A zero shift preserves each original bound's representation.
                shared_bounds = !iszero(shift) && shifted_lower == shifted_upper
                shifted_lower = _shift_bound_exact(T, shifted_lower, shift)
                shifted_upper = shared_bounds ? shifted_lower : _shift_bound_exact(T, shifted_upper, shift)
            end
            if isnothing(shifted_lower) || isnothing(shifted_upper)
                safe = false
                break
            end
            push!(changes, (row, shifted_lower, shifted_upper))
        end
        safe || continue
        # Rejected and empty-column eliminations need no private row bounds.
        # Copy once, immediately before committing the first staged row changes.
        if !isempty(changes) && lower === problem.row_lower
            lower, upper = copy(lower), copy(upper)
        end
        for (row, shifted_lower, shifted_upper) in changes
            lower[row], upper[row] = shifted_lower, shifted_upper
        end
        constant = shifted_constant
        kept_columns[column] = false
        removed_values[column] = value
        removed_states[column] = state
    end

    columns = findall(kept_columns)
    nonempty_rows = falses(row_count)
    nonzero_count = 0
    # Inspect retained columns directly; materialize only the final submatrix.
    for column in columns
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            iszero(A.nzval[position]) && continue
            nonempty_rows[A.rowval[position]] = true
            nonzero_count += 1
        end
    end
    rows = findall(nonempty_rows)
    for row in 1:row_count
        nonempty_rows[row] && continue
        if (isfinite(lower[row]) && bound_value(lower[row]) > zero(T)) ||
           (isfinite(upper[row]) && bound_value(upper[row]) < zero(T))
            return PresolveFailure(INFEASIBLE, "empty row $row is infeasible",
                                  length(rows), length(columns),
                                  nonzero_count)
        end
    end
    length(columns) == column_count && length(rows) == row_count &&
        return identity_presolve(problem)

    reduced = LinearProblem{T}(
        A[rows, columns], problem.objective[columns], constant,
        problem.objective_sense, lower[rows], upper[rows],
        problem.column_lower[columns], problem.column_upper[columns],
        problem.variable_domains[columns], problem.name,
        isempty(problem.row_names) ? String[] : problem.row_names[rows],
        isempty(problem.column_names) ? String[] : problem.column_names[columns],
    )
    step = PresolveMap{T}(rows, columns, removed_values, removed_states, row_count)
    return PresolveResult(reduced, (step,), column_count)
end

function postsolve_primal(step::PresolveMap{T}, primal::Vector{T}) where {T}
    restored = Vector{T}(undef, length(step.removed_values))
    for column in eachindex(restored)
        value = step.removed_values[column]
        isnothing(value) || (restored[column] = value)
    end
    restored[step.columns] .= primal
    return restored
end

restore_basis(result::PresolveResult, basis::Basis) =
    _restore_basis(result.postsolve_stack, basis)

_restore_basis(::Tuple{}, basis::Basis) = Basis(basis.basic_indices, basis.states)
_restore_basis(steps::Tuple, basis::Basis) =
    restore_basis(first(steps), _restore_basis(Base.tail(steps), basis))

function _compose_presolve(original::PresolveResult, next::PresolveResult)
    return PresolveResult(next.problem,
        (original.postsolve_stack..., next.postsolve_stack...),
        original.original_column_count)
end

function presolve_problem(problem::LinearProblem{T}) where {T}
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
            next = _dispatch_presolve_pass!(current, steps, propagation_trace, index)
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

function restore_basis(step::PresolveMap, basis::Basis)
    original_columns = length(step.removed_values)
    reduced_columns = length(step.columns)
    states = Vector{VariableState}(undef, original_columns + step.original_row_count)
    states[1:original_columns] .= step.removed_states
    states[original_columns + 1:end] .= BASIC
    for (reduced, original) in enumerate(step.columns)
        states[original] = basis.states[reduced]
    end
    for (reduced, original) in enumerate(step.rows)
        states[original_columns + original] = basis.states[reduced_columns + reduced]
    end
    basic_indices = collect(original_columns + 1:original_columns + step.original_row_count)
    for (reduced_row, index) in enumerate(basis.basic_indices)
        original_row = step.rows[reduced_row]
        basic_indices[original_row] = index <= reduced_columns ? step.columns[index] :
                                      original_columns + step.rows[index - reduced_columns]
    end
    return Basis(basic_indices, states, Val(:owned))
end

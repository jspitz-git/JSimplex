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
    return _exact_rational(converted) == value ? converted : nothing
end

function _shift_bound_exact(::Type{T}, bound::Bound{T}, shift::Rational{BigInt}) where {T}
    iszero(shift) && return bound
    isfinite(bound) || return bound
    value = _represent_exact(T, _exact_rational(bound_value(bound)) - shift)
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

function presolve_problem(problem::LinearProblem{T}) where {T}
    A = problem.A
    row_count, column_count = size(A)
    lower, upper = copy(problem.row_lower), copy(problem.row_upper)
    constant = problem.objective_constant
    kept_columns = trues(column_count)
    removed_values = Vector{Union{Nothing,T}}(nothing, column_count)
    removed_states = fill(FREE_NONBASIC, column_count)

    for column in 1:column_count
        selected = _elimination_value(problem, column)
        isnothing(selected) && continue
        value, state = selected
        contribution = _exact_rational(problem.objective[column]) * _exact_rational(value)
        shifted_constant = iszero(contribution) ? constant :
                           _represent_exact(T, _exact_rational(constant) + contribution)
        isnothing(shifted_constant) && continue
        changes = Tuple{Int,Bound{T},Bound{T}}[]
        safe = true
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            row = A.rowval[position]
            shift = _exact_rational(A.nzval[position]) * _exact_rational(value)
            shifted_lower = _shift_bound_exact(T, lower[row], shift)
            shifted_upper = _shift_bound_exact(T, upper[row], shift)
            if isnothing(shifted_lower) || isnothing(shifted_upper)
                safe = false
                break
            end
            push!(changes, (row, shifted_lower, shifted_upper))
        end
        safe || continue
        for (row, shifted_lower, shifted_upper) in changes
            lower[row], upper[row] = shifted_lower, shifted_upper
        end
        constant = shifted_constant
        kept_columns[column] = false
        removed_values[column] = value
        removed_states[column] = state
    end

    columns = findall(kept_columns)
    candidate = A[:, columns]
    nonempty_rows = falses(row_count)
    for position in eachindex(candidate.nzval)
        iszero(candidate.nzval[position]) ||
            (nonempty_rows[candidate.rowval[position]] = true)
    end
    rows = findall(nonempty_rows)
    for row in 1:row_count
        nonempty_rows[row] && continue
        if (isfinite(lower[row]) && bound_value(lower[row]) > zero(T)) ||
           (isfinite(upper[row]) && bound_value(upper[row]) < zero(T))
            return PresolveFailure(INFEASIBLE, "empty row $row is infeasible",
                                  length(rows), length(columns),
                                  count(value -> !iszero(value), candidate.nzval))
        end
    end
    length(columns) == column_count && length(rows) == row_count &&
        return identity_presolve(problem)

    reduced = LinearProblem{T}(
        candidate[rows, :], problem.objective[columns], constant,
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
    isempty(result.postsolve_stack) ? Basis(basis.basic_indices, basis.states) :
    restore_basis(only(result.postsolve_stack), basis)

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
    basic_indices = original_columns .+ collect(1:step.original_row_count)
    for (reduced_row, index) in enumerate(basis.basic_indices)
        original_row = step.rows[reduced_row]
        basic_indices[original_row] = index <= reduced_columns ? step.columns[index] :
                                      original_columns + step.rows[index - reduced_columns]
    end
    return Basis(basic_indices, states)
end

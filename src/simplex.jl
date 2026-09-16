@enum VariableState::UInt8 BASIC AT_LOWER AT_UPPER FREE_NONBASIC

struct Basis
    basic_indices::Vector{Int}
    states::Vector{VariableState}

    function Basis(
        basic_indices::AbstractVector{<:Integer},
        states::AbstractVector{VariableState},
    )
        return new(Int.(basic_indices), collect(states))
    end
end

struct SimplexProgressContext{T<:Real}
    start_ns::UInt64
    objective::Vector{T}
    objective_constant::T
end

mutable struct SimplexScratch{T<:Real}
    basic_mask::BitVector
    row_rhs::Vector{T}
    row_solution::Vector{T}
    rho::Vector{T}
    tau::Vector{T}
    tableau_row::Vector{T}
    candidates::Vector{Int}
    basis_rows::Vector{Int}
    basis_columns::Vector{Int}
    basis_values::Vector{T}
end

function SimplexScratch(::Type{T}, row_count::Int, variable_count::Int) where {T<:Real}
    candidates = Int[]
    sizehint!(candidates, variable_count)
    basis_rows, basis_columns, basis_values = Int[], Int[], T[]
    sizehint!(basis_rows, row_count)
    sizehint!(basis_columns, row_count)
    sizehint!(basis_values, row_count)
    return SimplexScratch(
        falses(variable_count), zeros(T, row_count), zeros(T, row_count),
        zeros(T, row_count), zeros(T, row_count), zeros(T, variable_count),
        candidates, basis_rows, basis_columns, basis_values,
    )
end

function SimplexProgressContext(problem::LinearProblem{T}; start_ns::UInt64=time_ns()) where {T}
    return SimplexProgressContext{T}(
        start_ns,
        copy(problem.objective),
        problem.objective_constant,
    )
end

mutable struct SimplexWorkspace{T<:Real,F,M,R}
    problem::LinearProblem{T}
    options::SolverOptions{T,M,R}
    progress::SimplexProgressContext{T}
    costs::Vector{T}
    lower::Vector{Bound{T}}
    upper::Vector{Bound{T}}
    basis::Basis
    primal::Vector{T}
    reduced_costs::Vector{T}
    pricing_weights::Vector{T}
    devex_reference::BitVector
    factorization::F
    scratch::SimplexScratch{T}
    iterations::Int
    refactorizations::Int
    perturbed::Bool
end

function reset_devex!(workspace::SimplexWorkspace{T})::Nothing where {T}
    fill!(workspace.devex_reference, false)
    workspace.devex_reference[workspace.basis.basic_indices] .= true
    fill!(workspace.pricing_weights, one(T))
    return nothing
end

function _validate_basis(workspace::SimplexWorkspace)
    row_count, column_count = size(workspace.problem.A)
    variable_count = row_count + column_count
    basis = workspace.basis

    length(basis.states) == variable_count ||
        throw(ArgumentError("basis state count must match the working variable count"))
    length(basis.basic_indices) == row_count ||
        throw(ArgumentError("basis must contain one basic variable per row"))
    all(index -> 1 <= index <= variable_count, basis.basic_indices) ||
        throw(ArgumentError("basis indices must refer to working variables"))
    is_basic = workspace.scratch.basic_mask
    fill!(is_basic, false)
    for index in basis.basic_indices
        is_basic[index] && throw(ArgumentError("basis indices must be unique"))
        is_basic[index] = true
    end
    for index in eachindex(basis.states)
        (basis.states[index] == BASIC) == is_basic[index] ||
            throw(ArgumentError("basis indices and variable states must agree"))
    end
    return nothing
end

function basis_matrix(workspace::SimplexWorkspace{T}) where {T}
    _validate_basis(workspace)
    A = workspace.problem.A
    row_count, column_count = size(A)
    basis = workspace.basis
    rows = workspace.scratch.basis_rows
    columns = workspace.scratch.basis_columns
    values = workspace.scratch.basis_values
    empty!(rows)
    empty!(columns)
    empty!(values)

    nonzero_count = 0
    for variable_index in basis.basic_indices
        nonzero_count += variable_index <= column_count ?
            A.colptr[variable_index + 1] - A.colptr[variable_index] : 1
    end
    sizehint!(rows, nonzero_count)
    sizehint!(columns, nonzero_count)
    sizehint!(values, nonzero_count)

    for (basis_column, variable_index) in enumerate(basis.basic_indices)
        if variable_index <= column_count
            for position in A.colptr[variable_index]:(A.colptr[variable_index + 1] - 1)
                push!(rows, A.rowval[position])
                push!(columns, basis_column)
                push!(values, A.nzval[position])
            end
        else
            push!(rows, variable_index - column_count)
            push!(columns, basis_column)
            push!(values, -one(T))
        end
    end
    return sparse(rows, columns, values, row_count, row_count)
end

function _nonbasic_value(workspace::SimplexWorkspace{T}, index::Int) where {T}
    state = workspace.basis.states[index]
    if state == AT_LOWER
        value = workspace.lower[index]
        isfinite(value) || throw(ArgumentError("a lower-bound nonbasic variable needs a finite lower bound"))
        return bound_value(value)
    elseif state == AT_UPPER
        value = workspace.upper[index]
        isfinite(value) || throw(ArgumentError("an upper-bound nonbasic variable needs a finite upper bound"))
        return bound_value(value)
    elseif state == FREE_NONBASIC
        return zero(T)
    end
    throw(ArgumentError("basic variables do not have nonbasic values"))
end

function recompute!(workspace::SimplexWorkspace{T}; refactorize::Bool=false,
                    caller_guard=nothing) where {T}
    _validate_basis(workspace)
    if refactorize
        try
            @logmsg workspace.options.log_level "Refactorizing basis" iterations=workspace.iterations refactorizations=workspace.refactorizations + 1
        catch exception
            # A logger is caller code, even when it throws a numerical exception.
            # Share provenance with every enclosing numerical handler.
            isnothing(caller_guard) || (caller_guard.exception = exception)
            rethrow()
        end
        B = basis_matrix(workspace)
        refactorize!(workspace.factorization, B)
        workspace.refactorizations += 1
        workspace.options.pricing == :devex && reset_devex!(workspace)
    end

    A = workspace.problem.A
    row_count, column_count = size(A)
    basis = workspace.basis
    is_basic = workspace.scratch.basic_mask
    rhs = workspace.scratch.row_rhs
    fill!(rhs, zero(T))

    for index in eachindex(basis.states)
        is_basic[index] && continue
        value = _nonbasic_value(workspace, index)
        workspace.primal[index] = value
        if index <= column_count
            for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                rhs[A.rowval[position]] -= A.nzval[position] * value
            end
        else
            rhs[index - column_count] += value
        end
    end

    basic_primal = forward_solve!(workspace.scratch.row_solution,
                                  workspace.factorization, rhs)
    for (row, index) in enumerate(basis.basic_indices)
        workspace.primal[index] = basic_primal[row]
        rhs[row] = workspace.costs[index]
    end

    dual = transpose_solve!(workspace.scratch.rho, workspace.factorization, rhs)
    for column in 1:column_count
        reduced_cost = workspace.costs[column]
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            reduced_cost -= A.nzval[position] * dual[A.rowval[position]]
        end
        workspace.reduced_costs[column] = reduced_cost
    end
    for row in 1:row_count
        index = column_count + row
        workspace.reduced_costs[index] = workspace.costs[index] + dual[row]
    end
    for index in basis.basic_indices
        workspace.reduced_costs[index] = zero(T)
    end
    refactorize && _report_simplex_progress(workspace, caller_guard)
    return workspace
end

recompute!(workspace::SimplexWorkspace, refactorize::Bool) =
    recompute!(workspace; refactorize=refactorize)

function initialize_workspace(
    problem::LinearProblem{T},
    options::SolverOptions;
    progress::SimplexProgressContext{T}=SimplexProgressContext(problem),
) where {T}
    typed_options = SolverOptions(T, options)
    row_count, column_count = size(problem.A)
    variable_count = row_count + column_count
    costs = vcat(copy(problem.objective), zeros(T, row_count))
    lower = vcat(copy(problem.column_lower), copy(problem.row_lower))
    upper = vcat(copy(problem.column_upper), copy(problem.row_upper))
    states = Vector{VariableState}(undef, variable_count)

    for index in 1:column_count
        if isfinite(lower[index])
            states[index] = AT_LOWER
        elseif isfinite(upper[index])
            states[index] = AT_UPPER
        else
            states[index] = FREE_NONBASIC
        end
    end
    states[column_count + 1:end] .= BASIC

    basis = Basis(collect(column_count + 1:variable_count), states)
    initial_basis = spdiagm(0 => fill(-one(T), row_count))
    factorization = _basis_factorization(initial_basis, typed_options)
    scratch = SimplexScratch(T, row_count, variable_count)
    devex_reference = falses(variable_count)
    devex_reference[basis.basic_indices] .= true
    workspace = SimplexWorkspace(
        problem, typed_options, progress, costs, lower, upper, basis, zeros(T, variable_count),
        zeros(T, variable_count), ones(T, variable_count), devex_reference,
        factorization, scratch, 0, 0, false,
    )
    return recompute!(workspace)
end

function primal_infeasibility_summary(workspace::SimplexWorkspace{T}) where {T}
    infeasibility = zero(T)
    count = 0
    tolerance = workspace.options.primal_tolerance
    for index in workspace.basis.basic_indices
        value = workspace.primal[index]
        lower_violation = _lower_violation(workspace.lower[index], value)
        upper_violation = _upper_violation(workspace.upper[index], value)
        if lower_violation > tolerance
            infeasibility += lower_violation
            count += 1
        elseif upper_violation > tolerance
            infeasibility += upper_violation
            count += 1
        end
    end
    return infeasibility, count
end

primal_infeasibility(workspace::SimplexWorkspace) = first(primal_infeasibility_summary(workspace))

function dual_infeasibility_summary(workspace::SimplexWorkspace{T}) where {T}
    infeasibility = zero(T)
    count = 0
    tolerance = workspace.options.dual_tolerance
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue

        reduced_cost = workspace.reduced_costs[index]
        if state == AT_LOWER && reduced_cost < -tolerance
            infeasibility -= reduced_cost
            count += 1
        elseif state == AT_UPPER && reduced_cost > tolerance
            infeasibility += reduced_cost
            count += 1
        elseif state == FREE_NONBASIC && abs(reduced_cost) > tolerance
            infeasibility += abs(reduced_cost)
            count += 1
        end
    end
    return infeasibility, count
end

dual_infeasibility(workspace::SimplexWorkspace) = first(dual_infeasibility_summary(workspace))

function _progress_objective_value(
    context::SimplexProgressContext{T},
    primal::AbstractVector{T},
) where {T}
    return dot(context.objective, primal) + context.objective_constant
end

function _progress_objective_value(
    context::SimplexProgressContext{BigFloat},
    primal::AbstractVector{BigFloat},
)
    value = context.objective_constant
    for (coefficient, primal_value) in zip(context.objective, primal)
        value = setprecision(
            BigFloat,
            max(precision(value), precision(coefficient), precision(primal_value)),
        ) do
            value + coefficient * primal_value
        end
    end
    return value
end

function _report_simplex_progress(workspace::SimplexWorkspace, caller_guard)
    workspace.options.verbose || return nothing
    column_count = size(workspace.problem.A, 2)
    context = workspace.progress
    objective_value = _progress_objective_value(
        context, @view(workspace.primal[1:column_count]),
    )
    primal_sum, primal_count = primal_infeasibility_summary(workspace)
    dual_sum, dual_count = dual_infeasibility_summary(workspace)
    elapsed = (time_ns() - context.start_ns) / 1.0e9
    message = string(
        "iter=", workspace.iterations,
        " obj=", objective_value,
        " pinf=", primal_sum, " (", primal_count, ")",
        " dinf=", dual_sum, " (", dual_count, ")",
        " time=", elapsed, "s",
    )
    try
        @info message
    catch exception
        isnothing(caller_guard) || (caller_guard.exception = exception)
        rethrow()
    end
    return nothing
end

_is_fixed(lower::Bound, upper::Bound) =
    isfinite(lower) && isfinite(upper) && bound_value(lower) == bound_value(upper)
_lower_violation(bound::Bound{T}, value::T) where {T} =
    isfinite(bound) ? bound_value(bound) - value : zero(T)
_upper_violation(bound::Bound{T}, value::T) where {T} =
    isfinite(bound) ? value - bound_value(bound) : zero(T)

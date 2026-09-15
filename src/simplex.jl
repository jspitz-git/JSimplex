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

mutable struct SimplexWorkspace{T<:Real,F}
    problem::LinearProblem{T}
    options::SolverOptions{T}
    costs::Vector{T}
    lower::Vector{Bound{T}}
    upper::Vector{Bound{T}}
    basis::Basis
    primal::Vector{T}
    reduced_costs::Vector{T}
    pricing_weights::Vector{T}
    factorization::PFIFactorization{T,F}
    iterations::Int
    refactorizations::Int
    perturbed::Bool
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
    length(unique(basis.basic_indices)) == row_count ||
        throw(ArgumentError("basis indices must be unique"))

    is_basic = falses(variable_count)
    is_basic[basis.basic_indices] .= true
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
    rows = Int[]
    columns = Int[]
    values = T[]

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
    end

    A = workspace.problem.A
    row_count, column_count = size(A)
    basis = workspace.basis
    is_basic = falses(length(basis.states))
    is_basic[basis.basic_indices] .= true
    rhs = zeros(T, row_count)

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

    basic_primal = forward_solve(workspace.factorization, rhs)
    workspace.primal[basis.basic_indices] .= basic_primal

    dual = transpose_solve(workspace.factorization, workspace.costs[basis.basic_indices])
    workspace.reduced_costs[1:column_count] .=
        workspace.costs[1:column_count] .- transpose(A) * dual
    workspace.reduced_costs[column_count + 1:end] .=
        workspace.costs[column_count + 1:end] .+ dual
    workspace.reduced_costs[basis.basic_indices] .= zero(T)
    return workspace
end

recompute!(workspace::SimplexWorkspace, refactorize::Bool) =
    recompute!(workspace; refactorize=refactorize)

function initialize_workspace(problem::LinearProblem{T}, options::SolverOptions) where {T}
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
    factorization = PFIFactorization(initial_basis)
    workspace = SimplexWorkspace(
        problem, typed_options, costs, lower, upper, basis, zeros(T, variable_count),
        zeros(T, variable_count), ones(T, variable_count),
        factorization, 0, 0, false,
    )
    return recompute!(workspace)
end

function primal_infeasibility(workspace::SimplexWorkspace{T}) where {T}
    _validate_basis(workspace)
    infeasibility = zero(T)
    tolerance = workspace.options.primal_tolerance
    for index in workspace.basis.basic_indices
        value = workspace.primal[index]
        lower_violation = _lower_violation(workspace.lower[index], value)
        upper_violation = _upper_violation(workspace.upper[index], value)
        if lower_violation > tolerance
            infeasibility += lower_violation
        elseif upper_violation > tolerance
            infeasibility += upper_violation
        end
    end
    return infeasibility
end

function dual_infeasibility(workspace::SimplexWorkspace{T}) where {T}
    _validate_basis(workspace)
    infeasibility = zero(T)
    tolerance = workspace.options.dual_tolerance
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue

        reduced_cost = workspace.reduced_costs[index]
        if state == AT_LOWER && reduced_cost < -tolerance
            infeasibility -= reduced_cost
        elseif state == AT_UPPER && reduced_cost > tolerance
            infeasibility += reduced_cost
        elseif state == FREE_NONBASIC && abs(reduced_cost) > tolerance
            infeasibility += abs(reduced_cost)
        end
    end
    return infeasibility
end

_is_fixed(lower::Bound, upper::Bound) =
    isfinite(lower) && isfinite(upper) && bound_value(lower) == bound_value(upper)
_lower_violation(bound::Bound{T}, value::T) where {T} =
    isfinite(bound) ? bound_value(bound) - value : zero(T)
_upper_violation(bound::Bound{T}, value::T) where {T} =
    isfinite(bound) ? value - bound_value(bound) : zero(T)

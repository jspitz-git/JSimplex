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

mutable struct SimplexWorkspace
    problem::LinearProblem
    options::SolverOptions
    costs::Vector{Float64}
    lower::Vector{Float64}
    upper::Vector{Float64}
    basis::Basis
    primal::Vector{Float64}
    reduced_costs::Vector{Float64}
    pricing_weights::Vector{Float64}
    factorization::PFIFactorization
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

function basis_matrix(workspace::SimplexWorkspace)
    _validate_basis(workspace)
    A = workspace.problem.A
    row_count, column_count = size(A)
    basis = workspace.basis
    rows = Int[]
    columns = Int[]
    values = Float64[]

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
            push!(values, -1.0)
        end
    end
    return sparse(rows, columns, values, row_count, row_count)
end

function _nonbasic_value(workspace::SimplexWorkspace, index::Int)
    state = workspace.basis.states[index]
    if state == AT_LOWER
        value = workspace.lower[index]
        isfinite(value) || throw(ArgumentError("a lower-bound nonbasic variable needs a finite lower bound"))
        return value
    elseif state == AT_UPPER
        value = workspace.upper[index]
        isfinite(value) || throw(ArgumentError("an upper-bound nonbasic variable needs a finite upper bound"))
        return value
    elseif state == FREE_NONBASIC
        return 0.0
    end
    throw(ArgumentError("basic variables do not have nonbasic values"))
end

function recompute!(workspace::SimplexWorkspace; refactorize::Bool=false)
    _validate_basis(workspace)
    if refactorize
        @logmsg workspace.options.log_level "Refactorizing basis" iterations=workspace.iterations refactorizations=workspace.refactorizations + 1
        B = basis_matrix(workspace)
        if isempty(B)
            workspace.factorization.base = lu(zeros(Float64, 0, 0))
            empty!(workspace.factorization.updates)
        else
            refactorize!(workspace.factorization, B)
        end
        workspace.refactorizations += 1
    end

    A = workspace.problem.A
    row_count, column_count = size(A)
    basis = workspace.basis
    is_basic = falses(length(basis.states))
    is_basic[basis.basic_indices] .= true
    rhs = zeros(Float64, row_count)

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
    workspace.reduced_costs[basis.basic_indices] .= 0.0
    return workspace
end

recompute!(workspace::SimplexWorkspace, refactorize::Bool) =
    recompute!(workspace; refactorize=refactorize)

function initialize_workspace(problem::LinearProblem, options::SolverOptions)
    row_count, column_count = size(problem.A)
    variable_count = row_count + column_count
    costs = vcat(copy(problem.objective), zeros(Float64, row_count))
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
    initial_basis = spdiagm(0 => fill(-1.0, row_count))
    factorization = if iszero(row_count)
        PFIFactorization(lu(zeros(Float64, 0, 0)), PackedEta[])
    else
        PFIFactorization(initial_basis)
    end
    workspace = SimplexWorkspace(
        problem, options, costs, lower, upper, basis, zeros(Float64, variable_count),
        zeros(Float64, variable_count), ones(Float64, variable_count),
        factorization, 0, 0, false,
    )
    return recompute!(workspace)
end

function primal_infeasibility(workspace::SimplexWorkspace)
    _validate_basis(workspace)
    infeasibility = 0.0
    tolerance = workspace.options.primal_tolerance
    for index in workspace.basis.basic_indices
        value = workspace.primal[index]
        if value < workspace.lower[index] - tolerance
            infeasibility += workspace.lower[index] - value
        elseif value > workspace.upper[index] + tolerance
            infeasibility += value - workspace.upper[index]
        end
    end
    return infeasibility
end

function dual_infeasibility(workspace::SimplexWorkspace)
    _validate_basis(workspace)
    infeasibility = 0.0
    tolerance = workspace.options.dual_tolerance
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        workspace.lower[index] == workspace.upper[index] && continue

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

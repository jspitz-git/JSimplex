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

    # Internal transfer of freshly allocated arrays; the two-argument
    # constructor continues to copy caller-owned inputs.
    Basis(basic_indices::Vector{Int}, states::Vector{VariableState}, ::Val{:owned}) =
        new(basic_indices, states)
end

struct SimplexProgressContext{T<:Real,D}
    start_ns::UInt64
    objective::Vector{T}
    objective_constant::T
    scaling::Scaling{T}
    iteration_offset::Int
    diagnostics::D
end

mutable struct SimplexScratch{T<:Real}
    basic_mask::BitVector
    row_rhs::Vector{T}
    row_solution::Vector{T}
    rho::Vector{T}
    tau::Vector{T}
    tableau_row::Vector{T}
    pricing_row::Vector{T}
    steepest_valid::BitVector
    steepest_initialized::Bool
    candidates::Vector{Int}
    # Borrowed by ratio-test callers until the next ratio test on this workspace.
    flips::Vector{Int}
    # Breakpoints are rebuilt for each boxed ratio test, then read during sorting.
    ratio_steps::Vector{T}
    # Private assembly storage; backends must own their factorization data.
    basis_matrix::Union{Nothing,SparseMatrixCSC{T,Int}}
end

function SimplexScratch(::Type{T}, row_count::Int, variable_count::Int) where {T<:Real}
    candidates = Int[]
    sizehint!(candidates, variable_count)
    return SimplexScratch(
        falses(variable_count), zeros(T, row_count), zeros(T, row_count),
        zeros(T, row_count), zeros(T, row_count), zeros(T, variable_count),
        zeros(T, variable_count), falses(variable_count), false,
        candidates, Int[], T[], nothing,
    )
end

function SimplexProgressContext(problem::LinearProblem{T}; start_ns::UInt64=time_ns(),
                                scaling::Scaling{T}=identity_scaling(problem),
                                iteration_offset::Int=0, diagnostics=nothing) where {T}
    return SimplexProgressContext{T,typeof(diagnostics)}(
        start_ns,
        copy(problem.objective),
        problem.objective_constant,
        scaling,
        iteration_offset,
        diagnostics,
    )
end

mutable struct SimplexWorkspace{T<:Real,F,M,R,D}
    problem::LinearProblem{T}
    options::SolverOptions{T,M,R}
    progress::SimplexProgressContext{T,D}
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
    zero_dual_step_streak::Int
    dual_pricing_fallback::Bool
    dual_devex_fallback::Bool
    dual_refactorization_interval::Int
    dual_recent_repairs::Int
    dual_bad_update_min::Int
    dual_stable_refactorizations::Int
    dual_nonzero_steps_since_refactorization::Int
end

_simplex_event!(workspace::SimplexWorkspace, reason::Symbol) =
    _diagnostic_event!(workspace.progress.diagnostics, reason, workspace)

@inline _timed_simplex(f, workspace::SimplexWorkspace, reason::Symbol) =
    _diagnostic_kernel(f, workspace.progress.diagnostics, reason)

function reset_devex!(workspace::SimplexWorkspace{T})::Nothing where {T}
    fill!(workspace.devex_reference, false)
    workspace.devex_reference[workspace.basis.basic_indices] .= true
    fill!(workspace.pricing_weights, one(T))
    return nothing
end

function _restore_original_costs!(workspace::SimplexWorkspace{T}) where {T}
    column_count = size(workspace.problem.A, 2)
    copyto!(workspace.costs, 1, workspace.problem.objective, 1, column_count)
    fill!(@view(workspace.costs[column_count + 1:end]), zero(T))
    workspace.perturbed && _simplex_event!(workspace, :restore_perturbations)
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
    return _assemble_basis_matrix(workspace, nothing)
end

# The returned matrix is borrowed until the next assembly on this workspace.
function _basis_matrix!(workspace::SimplexWorkspace)
    _validate_basis(workspace)
    storage = workspace.scratch.basis_matrix
    B = _assemble_basis_matrix(workspace, storage)
    # CSC is immutable: assigning it to the nullable field boxes a new wrapper.
    # Only install new storage; reused arrays are already held by the cache.
    if isnothing(storage) || size(storage) != size(B)
        workspace.scratch.basis_matrix = B
    end
    return B
end

function _assemble_basis_matrix(workspace::SimplexWorkspace{T},
                                storage::Union{Nothing,SparseMatrixCSC{T,Int}}) where {T}
    A = workspace.problem.A
    row_count, column_count = size(A)
    basis = workspace.basis
    nonzero_count = 0
    for variable_index in basis.basic_indices
        nonzero_count += variable_index <= column_count ?
            A.colptr[variable_index + 1] - A.colptr[variable_index] : 1
    end
    # Structural columns already have sorted CSC row indices; slack columns
    # contain one entry. Public results own new arrays; internal refactorization
    # reuses scratch capacity, even when the number of stored entries decreases.
    reuse = !isnothing(storage) && size(storage) == (row_count, row_count)
    if reuse
        column_pointers = storage.colptr
        rows = resize!(storage.rowval, nonzero_count)
        values = resize!(storage.nzval, nonzero_count)
    else
        column_pointers = Vector{Int}(undef, row_count + 1)
        rows = Vector{Int}(undef, nonzero_count)
        values = Vector{T}(undef, nonzero_count)
    end
    next_position = 1

    for (basis_column, variable_index) in enumerate(basis.basic_indices)
        column_pointers[basis_column] = next_position
        if variable_index <= column_count
            first_position = A.colptr[variable_index]
            count = A.colptr[variable_index + 1] - first_position
            copyto!(rows, next_position, A.rowval, first_position, count)
            copyto!(values, next_position, A.nzval, first_position, count)
            next_position += count
        else
            rows[next_position] = variable_index - column_count
            values[next_position] = -one(T)
            next_position += 1
        end
    end
    column_pointers[end] = next_position
    return reuse ? storage : SparseMatrixCSC(row_count, row_count, column_pointers, rows, values)
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
                    caller_guard=nothing, diagnostic_reason::Symbol=:refactor_other) where {T}
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
        B = _basis_matrix!(workspace)
        _timed_simplex(workspace, :refactorization) do
            refactorize!(workspace.factorization, B)
        end
        workspace.refactorizations += 1
        _simplex_event!(workspace, diagnostic_reason)
        workspace.dual_nonzero_steps_since_refactorization = 0
        (workspace.options.pricing == :devex || workspace.dual_devex_fallback) &&
            !workspace.dual_pricing_fallback && reset_devex!(workspace)
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
    costs = Vector{T}(undef, variable_count)
    copyto!(costs, 1, problem.objective, 1, column_count)
    fill!(@view(costs[column_count + 1:variable_count]), zero(T))
    # Concatenation already creates the workspace's independent bound arrays.
    lower = vcat(problem.column_lower, problem.row_lower)
    upper = vcat(problem.column_upper, problem.row_upper)
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

    basis = Basis(collect(column_count + 1:variable_count), states, Val(:owned))
    initial_basis = spdiagm(0 => fill(-one(T), row_count))
    factorization = _basis_factorization(initial_basis, typed_options)
    scratch = SimplexScratch(T, row_count, variable_count)
    scratch.basis_matrix = initial_basis
    devex_reference = falses(variable_count)
    devex_reference[basis.basic_indices] .= true
    workspace = SimplexWorkspace(
        problem, typed_options, progress, costs, lower, upper, basis, zeros(T, variable_count),
        zeros(T, variable_count), ones(T, variable_count), devex_reference,
        factorization, scratch, 0, 0, false, 0, false, false,
        typed_options.refactorization_interval, 0,
        typemax(Int), 0, 0,
    )
    recompute!(workspace)
    _simplex_event!(workspace, :refactor_initial)
    return workspace
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
    context = workspace.progress
    objective_value = _progress_objective_value(
        context,
        unscale_primal(context.scaling,
                       @view(workspace.primal[1:length(context.objective)])),
    )
    primal_sum, primal_count = primal_infeasibility_summary(workspace)
    dual_sum, dual_count = dual_infeasibility_summary(workspace)
    elapsed = (time_ns() - context.start_ns) / 1.0e9
    message = string(
        "iter=", context.iteration_offset + workspace.iterations,
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

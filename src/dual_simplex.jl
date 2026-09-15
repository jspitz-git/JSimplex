struct DualTermination
    status::TerminationStatus
    message::String
end

struct DualRunResult
    status::TerminationStatus
    objective_value::Union{Nothing,Float64}
    primal::Union{Nothing,Vector{Float64}}
    iterations::Int
    refactorizations::Int
    message::String
end

_is_numerical_exception(exception) =
    exception isa SingularException || exception isa ZeroPivotException

mutable struct _StopCallback{F}
    callback::F
    exception::Any
end

function (stop::_StopCallback)()
    stop.exception = nothing
    try
        return stop.callback()
    catch exception
        stop.exception = exception
        rethrow()
    end
end

# Share provenance across nested numerical catches while rethrowing the
# caller's original callback or logger exception, including
# SingularException/ZeroPivotException. Refactorization logging shares this guard.
_guard_stop_callback(stop::_StopCallback) = stop
_guard_stop_callback(stop) = _StopCallback(stop, nothing)

_numerical_failure() = DualTermination(NUMERICAL_ERROR, "non-finite simplex iterate")

function _finite_workspace(workspace::SimplexWorkspace)
    return all(isfinite, workspace.primal) && all(isfinite, workspace.reduced_costs) &&
           all(isfinite, workspace.costs) &&
           all(weight -> isfinite(weight) && weight > 0.0, workspace.pricing_weights)
end

function dual_edge_selection(workspace::SimplexWorkspace)::Int
    leaving_row = -1
    best_score = 0.0
    for (row, index) in enumerate(workspace.basis.basic_indices)
        violation = max(_lower_violation(workspace.lower[index], workspace.primal[index]),
                        _upper_violation(workspace.upper[index], workspace.primal[index]))
        violation > workspace.options.primal_tolerance || continue
        score = violation^2 / workspace.pricing_weights[index]
        if score > best_score
            leaving_row = row
            best_score = score
        end
    end
    return leaving_row
end

function _dual_pivot_eligible(workspace::SimplexWorkspace, index, coefficient, tolerance)
    state = workspace.basis.states[index]
    _is_fixed(workspace.lower[index], workspace.upper[index]) && return false
    return (state == AT_LOWER && coefficient > tolerance) ||
           (state == AT_UPPER && coefficient < -tolerance) ||
           (state == FREE_NONBASIC && abs(coefficient) > tolerance)
end

# The row is oriented so that a positive dual step repairs the leaving bound.
function dual_ratio_test(workspace::SimplexWorkspace, tableau_row::Vector{Float64})::Int
    candidates = Int[]
    maximum_step = Inf
    tolerance = workspace.options.dual_tolerance
    for index in eachindex(tableau_row)
        coefficient = tableau_row[index]
        _dual_pivot_eligible(workspace, index, coefficient, 1.0e-7) || continue
        push!(candidates, index)
        relaxed_step = (workspace.reduced_costs[index] +
                        copysign(tolerance, coefficient)) / coefficient
        maximum_step = min(maximum_step, relaxed_step)
    end

    entering_index = -1
    largest_pivot = 0.0
    for index in candidates
        coefficient = tableau_row[index]
        step = workspace.reduced_costs[index] / coefficient
        if step <= maximum_step && abs(coefficient) > largest_pivot
            entering_index = index
            largest_pivot = abs(coefficient)
        end
    end
    return entering_index
end

function price!(tableau_row::Vector{Float64}, workspace::SimplexWorkspace,
                rho::Vector{Float64})::Nothing
    A = workspace.problem.A
    row_count, column_count = size(A)
    for column in 1:column_count
        value = 0.0
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            value += rho[A.rowval[position]] * A.nzval[position]
        end
        tableau_row[column] = value
    end
    for row in 1:row_count
        tableau_row[column_count + row] = -rho[row]
    end
    return nothing
end

function update_duals!(workspace::SimplexWorkspace, tableau_row, leaving_index,
                      entering_index, dual_step)::Nothing
    for index in eachindex(workspace.reduced_costs)
        state = workspace.basis.states[index]
        (state == BASIC || index == entering_index) && continue
        reduced_cost = workspace.reduced_costs[index] - dual_step * tableau_row[index]
        if !_is_fixed(workspace.lower[index], workspace.upper[index])
            tolerance = workspace.options.dual_tolerance
            violated = ((state == AT_LOWER || state == FREE_NONBASIC) && reduced_cost < -tolerance) ||
                       ((state == AT_UPPER || state == FREE_NONBASIC) && reduced_cost > tolerance)
            if violated
                # Shift to zero to leave room for recomputation roundoff.
                workspace.costs[index] -= reduced_cost
                workspace.perturbed = true
                reduced_cost = 0.0
            end
        end
        workspace.reduced_costs[index] = reduced_cost
    end
    workspace.reduced_costs[leaving_index] = -dual_step
    workspace.reduced_costs[entering_index] = 0.0
    return nothing
end

function update_primals!(workspace::SimplexWorkspace, tableau_column,
                        entering_index, leaving_row, primal_step)::Nothing
    for (row, index) in enumerate(workspace.basis.basic_indices)
        workspace.primal[index] -= primal_step * tableau_column[row]
    end
    workspace.primal[entering_index] += primal_step
    return nothing
end

function update_dse!(workspace::SimplexWorkspace, rho, tableau_column,
                    entering_index, pivot)::Nothing
    entering_weight = dot(rho, rho) / pivot^2
    tau = forward_solve(workspace.factorization, rho)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        coefficient = tableau_column[row]
        workspace.pricing_weights[index] = max(
            1.0e-4, workspace.pricing_weights[index] + coefficient *
            (coefficient * entering_weight - 2.0 * tau[row] / pivot),
        )
    end
    workspace.pricing_weights[entering_index] = entering_weight
    return nothing
end

function dual_iteration!(workspace::SimplexWorkspace, stop_requested)::Union{Nothing,DualTermination}
    stop_requested = _guard_stop_callback(stop_requested)
    stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
    _finite_workspace(workspace) || return _numerical_failure()
    try
        return _dual_iteration!(workspace, stop_requested)
    catch exception
        exception === stop_requested.exception && rethrow()
        _is_numerical_exception(exception) || rethrow()
        return DualTermination(NUMERICAL_ERROR, sprint(showerror, exception))
    end
end

function _dual_iteration!(workspace::SimplexWorkspace, stop_requested)
    leaving_row = dual_edge_selection(workspace)
    leaving_row == -1 && return DualTermination(OPTIMAL, "optimal solution found")
    leaving_index = workspace.basis.basic_indices[leaving_row]
    below = _lower_violation(workspace.lower[leaving_index], workspace.primal[leaving_index]) > 0.0
    bound = below ? workspace.lower[leaving_index] : workspace.upper[leaving_index]
    delta = workspace.primal[leaving_index] - bound_value(bound)

    row_count, column_count = size(workspace.problem.A)
    unit = zeros(Float64, row_count)
    unit[leaving_row] = 1.0
    rho = transpose_solve(workspace.factorization, unit)
    tableau_row = zeros(Float64, row_count + column_count)
    price!(tableau_row, workspace, rho)
    all(isfinite, rho) && all(isfinite, tableau_row) || return _numerical_failure()
    oriented_row = below ? -tableau_row : tableau_row
    entering_index = dual_ratio_test(workspace, oriented_row)
    if entering_index == -1
        # A tolerance cannot turn a nonzero, sign-eligible coefficient into a
        # mathematical infeasibility proof.
        if any(index -> _dual_pivot_eligible(workspace, index, oriented_row[index],
                                             0.0), eachindex(oriented_row))
            return DualTermination(NUMERICAL_ERROR, "eligible pivots are below the Harris safety cutoff")
        end
        return DualTermination(INFEASIBLE, "no eligible dual pivot")
    end

    column = zeros(Float64, row_count)
    if entering_index <= column_count
        A = workspace.problem.A
        for position in A.colptr[entering_index]:(A.colptr[entering_index + 1] - 1)
            column[A.rowval[position]] = A.nzval[position]
        end
    else
        column[entering_index - column_count] = -1.0
    end
    tableau_column = forward_solve(workspace.factorization, column)
    all(isfinite, tableau_column) || return _numerical_failure()
    pivot = tableau_column[leaving_row]
    abs(pivot) > workspace.options.zero_tolerance || throw(ZeroPivotException(leaving_row))
    primal_step = delta / pivot
    dual_step = workspace.reduced_costs[entering_index] / tableau_row[entering_index]
    isfinite(primal_step) && isfinite(dual_step) || return _numerical_failure()
    if dual_step * sign(delta) < 0.0
        # Harris may accept a reduced cost on the infeasible side of zero,
        # within dual tolerance. Do not move backwards in the dual direction.
        workspace.costs[entering_index] -= workspace.reduced_costs[entering_index]
        workspace.reduced_costs[entering_index] = 0.0
        workspace.perturbed = true
        dual_step = 0.0
    end
    update_duals!(workspace, tableau_row, leaving_index, entering_index, dual_step)
    update_primals!(workspace, tableau_column, entering_index, leaving_row, primal_step)
    update_dse!(workspace, rho, tableau_column, entering_index, pivot)
    _finite_workspace(workspace) || return _numerical_failure()
    replace_column!(workspace.factorization, tableau_column, leaving_row;
                    zero_tolerance=workspace.options.zero_tolerance)
    workspace.basis.basic_indices[leaving_row] = entering_index
    workspace.basis.states[entering_index] = BASIC
    workspace.basis.states[leaving_index] = below ? AT_LOWER : AT_UPPER
    workspace.primal[leaving_index] = bound_value(bound)
    # Count the completed pivot even when its subsequent refactorization times out.
    workspace.iterations += 1
    if length(workspace.factorization.updates) >= workspace.options.refactorization_interval
        stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
        recompute!(workspace; refactorize=true, caller_guard=stop_requested)
    end
    _finite_workspace(workspace) || return _numerical_failure()
    return nothing
end

function _within_primal_bounds(values, lower, upper, tolerance)
    all(isfinite, values) || return false
    for index in eachindex(values)
        _lower_violation(lower[index], values[index]) > tolerance && return false
        _upper_violation(upper[index], values[index]) > tolerance && return false
    end
    return true
end

function _original_primal_feasible(workspace::SimplexWorkspace, primal::Vector{Float64})
    problem = workspace.problem
    # Use the configured absolute tolerance in the original constraint units.
    # Scaling it by the sum of absolute products would hide cancellation in A * x.
    tolerance = workspace.options.primal_tolerance
    _within_primal_bounds(primal, problem.column_lower, problem.column_upper, tolerance) || return false
    return _within_primal_bounds(problem.A * primal, problem.row_lower, problem.row_upper, tolerance)
end

function _internal_solution(workspace::SimplexWorkspace, status::TerminationStatus,
                            message::String)
    primal = status == OPTIMAL ? copy(workspace.primal[1:size(workspace.problem.A, 2)]) : nothing
    objective = isnothing(primal) ? nothing :
                dot(workspace.problem.objective, primal) + workspace.problem.objective_constant
    if status == OPTIMAL && (!_finite_workspace(workspace) || !isfinite(objective))
        return _internal_solution(workspace, _numerical_failure())
    end
    if status == OPTIMAL && !_original_primal_feasible(workspace, primal)
        return _internal_solution(workspace, NUMERICAL_ERROR,
                                  "structural primal failed original-model feasibility checks")
    end
    return DualRunResult(status, objective, primal, workspace.iterations,
                         workspace.refactorizations, message)
end

_internal_solution(workspace::SimplexWorkspace, terminal::DualTermination) =
    _internal_solution(workspace, terminal.status, terminal.message)

function _flip_bounds!(workspace::SimplexWorkspace)
    flipped = false
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        isfinite(workspace.lower[index]) && isfinite(workspace.upper[index]) || continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        reduced_cost = workspace.reduced_costs[index]
        if state == AT_LOWER && reduced_cost < -workspace.options.dual_tolerance
            workspace.basis.states[index] = AT_UPPER
            flipped = true
        elseif state == AT_UPPER && reduced_cost > workspace.options.dual_tolerance
            workspace.basis.states[index] = AT_LOWER
            flipped = true
        end
    end
    flipped && recompute!(workspace)
    return nothing
end

function _dual_optimize!(workspace::SimplexWorkspace, stop_requested)::DualTermination
    while true
        stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
        _finite_workspace(workspace) || return _numerical_failure()
        dual_infeasibility(workspace) <= workspace.options.dual_tolerance ||
            return DualTermination(NUMERICAL_ERROR, "dual feasibility lost")
        if primal_infeasibility(workspace) <= workspace.options.primal_tolerance
            return DualTermination(OPTIMAL, "optimal solution found")
        end
        workspace.iterations < workspace.options.iteration_limit ||
            return DualTermination(ITERATION_LIMIT, "iteration limit reached")
        terminal = dual_iteration!(workspace, stop_requested)
        isnothing(terminal) || return terminal
    end
end

function _auxiliary_workspace(workspace::SimplexWorkspace)
    lower = similar(workspace.lower)
    upper = similar(workspace.upper)
    basis = Basis(workspace.basis.basic_indices, workspace.basis.states)
    for index in eachindex(lower)
        has_lower = isfinite(workspace.lower[index])
        has_upper = isfinite(workspace.upper[index])
        if has_lower && has_upper
            lower[index], upper[index] = Bound(0.0), Bound(0.0)
        elseif has_lower
            lower[index], upper[index] = Bound(0.0), Bound(1.0)
        elseif has_upper
            lower[index], upper[index] = Bound(-1.0), Bound(0.0)
        else
            lower[index], upper[index] = Bound(-1000.0), Bound(1000.0)
        end
        if basis.states[index] != BASIC
            basis.states[index] = workspace.reduced_costs[index] < 0.0 ? AT_UPPER : AT_LOWER
        end
    end
    # LU and existing eta data are only read by solves. Each workspace owns
    # its update list; refactorization replaces its own base factorization.
    factorization = PFIFactorization(workspace.factorization.base,
                                     copy(workspace.factorization.updates))
    auxiliary = SimplexWorkspace(
        workspace.problem, workspace.options, copy(workspace.costs), lower, upper,
        basis, copy(workspace.primal), copy(workspace.reduced_costs),
        copy(workspace.pricing_weights), factorization, workspace.iterations,
        workspace.refactorizations, workspace.perturbed,
    )
    return recompute!(auxiliary)
end

function _classify_recession!(workspace::SimplexWorkspace, stop_requested)
    # A negative auxiliary optimum certifies a recession direction. Original
    # feasibility is still required: an infeasible LP can have such a direction.
    feasibility = initialize_workspace(workspace.problem, workspace.options)
    feasibility.iterations = workspace.iterations
    feasibility.refactorizations = workspace.refactorizations
    fill!(feasibility.costs, 0.0)
    recompute!(feasibility)
    terminal = _dual_optimize!(feasibility, stop_requested)
    workspace.iterations = feasibility.iterations
    workspace.refactorizations = feasibility.refactorizations
    terminal.status == OPTIMAL || return terminal
    primal = copy(feasibility.primal[1:size(workspace.problem.A, 2)])
    _original_primal_feasible(feasibility, primal) ||
        return DualTermination(NUMERICAL_ERROR,
                               "recession feasibility primal failed original-model feasibility checks")
    return DualTermination(UNBOUNDED, "unbounded improving direction")
end

function _recession_row_roundoff(A::SparseMatrixCSC{Float64,Int}, structural::Vector{Float64})
    magnitudes = zeros(size(A, 1))
    terms = zeros(Int, size(A, 1))
    for column in axes(A, 2)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            row = A.rowval[position]
            magnitudes[row] += abs(A.nzval[position] * structural[column])
            terms[row] += 1
        end
    end
    for row in eachindex(magnitudes)
        # gamma_(2k), with unit roundoff eps/2, conservatively covers a k-term
        # dot product and the rounded sum of absolute products used to bound it.
        relative_error = terms[row] * eps(Float64)
        magnitudes[row] = relative_error < 1.0 ?
            relative_error / (1.0 - relative_error) * magnitudes[row] : Inf
    end
    return magnitudes
end

function _recession_direction_status(workspace::SimplexWorkspace, auxiliary::SimplexWorkspace)
    column_count = size(workspace.problem.A, 2)
    structural = auxiliary.primal[1:column_count]
    direction = vcat(structural, workspace.problem.A * structural)
    all(isfinite, direction) || return :invalid
    row_roundoff = _recession_row_roundoff(workspace.problem.A, structural)
    all(isfinite, row_roundoff) || return :invalid
    # Row cancellation within its dot-product error bound represents zero.
    # A larger nonzero violation within tolerance is numerically inconclusive.
    tolerance = workspace.options.zero_tolerance
    ambiguous = false
    for index in eachindex(direction)
        violation = max(isfinite(workspace.lower[index]) ? -direction[index] : 0.0,
                        isfinite(workspace.upper[index]) ? direction[index] : 0.0)
        roundoff = index <= column_count ? 0.0 : row_roundoff[index - column_count]
        violation <= roundoff && continue
        violation > tolerance && return :invalid
        ambiguous = true
    end
    improvement = dot(workspace.costs, direction)
    isfinite(improvement) && improvement < -workspace.options.dual_tolerance || return :invalid
    return ambiguous ? :ambiguous : :certified
end

function make_dual_feasible!(workspace::SimplexWorkspace, stop_requested)::Union{Nothing,DualTermination}
    stop_requested = _guard_stop_callback(stop_requested)
    stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
    _finite_workspace(workspace) || return _numerical_failure()
    try
        return _make_dual_feasible!(workspace, stop_requested)
    catch exception
        exception === stop_requested.exception && rethrow()
        _is_numerical_exception(exception) || rethrow()
        return DualTermination(NUMERICAL_ERROR, sprint(showerror, exception))
    end
end

function _make_dual_feasible!(workspace::SimplexWorkspace, stop_requested)
    recompute!(workspace)
    _flip_bounds!(workspace)
    _finite_workspace(workspace) || return _numerical_failure()
    dual_infeasibility(workspace) <= workspace.options.dual_tolerance && return nothing

    auxiliary = _auxiliary_workspace(workspace)
    terminal = _dual_optimize!(auxiliary, stop_requested)
    workspace.iterations = auxiliary.iterations
    workspace.refactorizations = auxiliary.refactorizations
    terminal.status == OPTIMAL || return terminal
    if dot(workspace.costs, auxiliary.primal) < -workspace.options.dual_tolerance
        direction_status = _recession_direction_status(workspace, auxiliary)
        direction_status == :ambiguous &&
            return DualTermination(NUMERICAL_ERROR, "auxiliary direction has a nonzero bound violation within tolerance")
        direction_status == :certified ||
            return DualTermination(NUMERICAL_ERROR, "auxiliary vector does not certify an improving direction")
        return _classify_recession!(workspace, stop_requested)
    end

    basis = Basis(auxiliary.basis.basic_indices, auxiliary.basis.states)
    for index in eachindex(basis.states)
        basis.states[index] == BASIC && continue
        if !isfinite(workspace.lower[index]) && !isfinite(workspace.upper[index])
            basis.states[index] = FREE_NONBASIC
        elseif !isfinite(workspace.lower[index])
            basis.states[index] = AT_UPPER
        elseif !isfinite(workspace.upper[index])
            basis.states[index] = AT_LOWER
        end
    end
    stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
    workspace.basis = basis
    workspace.pricing_weights .= auxiliary.pricing_weights
    workspace.costs .= auxiliary.costs
    workspace.perturbed = auxiliary.perturbed
    recompute!(workspace; refactorize=true, caller_guard=stop_requested)
    _flip_bounds!(workspace)
    _finite_workspace(workspace) || return _numerical_failure()
    if dual_infeasibility(workspace) > workspace.options.dual_tolerance
        return DualTermination(NUMERICAL_ERROR, "auxiliary basis is not dual feasible")
    end
    return nothing
end

function _solve_continuous_dual(problem::LinearProblem, options::SolverOptions;
                                stop_requested::Function=() -> false)
    stop_requested = _guard_stop_callback(stop_requested)
    workspace = nothing
    try
        workspace = initialize_workspace(problem, options)
        return _solve_continuous_dual!(workspace, stop_requested)
    catch exception
        exception === stop_requested.exception && rethrow()
        _is_numerical_exception(exception) || rethrow()
        return DualRunResult(NUMERICAL_ERROR, nothing, nothing,
                             isnothing(workspace) ? 0 : workspace.iterations,
                             isnothing(workspace) ? 0 : workspace.refactorizations,
                             sprint(showerror, exception))
    end
end

function _solve_continuous_dual!(workspace::SimplexWorkspace, stop_requested)
    problem, options = workspace.problem, workspace.options
    stop_requested() && return _internal_solution(workspace, TIME_LIMIT, "time limit reached")
    _finite_workspace(workspace) || return _internal_solution(workspace, _numerical_failure())
    if iszero(size(problem.A, 1))
        for index in eachindex(workspace.costs)
            cost = workspace.costs[index]
            iszero(cost) && continue
            bound = cost > 0.0 ? workspace.lower[index] : workspace.upper[index]
            isfinite(bound) || return _internal_solution(workspace, UNBOUNDED, "unbounded improving direction")
            workspace.primal[index] = bound_value(bound)
        end
        return _internal_solution(workspace, OPTIMAL, "optimal solution found")
    end
    terminal = make_dual_feasible!(workspace, stop_requested)
    isnothing(terminal) || return _internal_solution(workspace, terminal)
    terminal = _dual_optimize!(workspace, stop_requested)
    terminal.status == OPTIMAL || return _internal_solution(workspace, terminal)
    workspace.costs .= vcat(problem.objective, zeros(size(problem.A, 1)))
    workspace.perturbed = false
    recompute!(workspace)
    status = primal_infeasibility(workspace) <= options.primal_tolerance &&
             dual_infeasibility(workspace) <= options.dual_tolerance ? OPTIMAL : NUMERICAL_ERROR
    return _internal_solution(workspace, status,
                              status == OPTIMAL ? "optimal solution found" : "dual feasibility lost")
end

function _primal_entering(workspace::SimplexWorkspace{T}, tolerance::T) where {T}
    entering = 0
    direction = zero(T)
    best_cost = tolerance
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        reduced_cost = workspace.reduced_costs[index]
        improving = (state == AT_LOWER && reduced_cost < -best_cost) ||
                    (state == AT_UPPER && reduced_cost > best_cost) ||
                    (state == FREE_NONBASIC && abs(reduced_cost) > best_cost)
        if improving
            entering = index
            direction = reduced_cost < zero(T) ? one(T) : -one(T)
            best_cost = abs(reduced_cost)
        end
    end
    return entering, direction
end

function _primal_ratio(workspace::SimplexWorkspace{T}, entering::Int, direction::T,
                       tableau_column::Vector{T}) where {T}
    opposite = direction > zero(T) ? workspace.upper[entering] : workspace.lower[entering]
    step = isfinite(opposite) ?
        (bound_value(opposite) - workspace.primal[entering]) / direction : nothing
    leaving_row = 0
    leaving_state = BASIC
    for (row, index) in enumerate(workspace.basis.basic_indices)
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > zero(T) ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        candidate = (bound_value(bound) - workspace.primal[index]) / movement
        isfinite(candidate) || return nothing, -1, BASIC
        candidate < -workspace.options.primal_tolerance && return nothing, -1, BASIC
        candidate = max(zero(T), candidate)
        if isnothing(step) || candidate < step ||
           (candidate == step && leaving_row == 0)
            step = candidate
            leaving_row = row
            leaving_state = movement > zero(T) ? AT_UPPER : AT_LOWER
        end
    end
    return step, leaving_row, leaving_state
end

function _primal_iteration!(workspace::SimplexWorkspace{T}, stop_requested,
                            reduced_cost_tolerance::T) where {T}
    entering, direction = _primal_entering(workspace, reduced_cost_tolerance)
    entering == 0 && return DualTermination(OPTIMAL, "optimal solution found")
    workspace.iterations < workspace.options.iteration_limit ||
        return DualTermination(ITERATION_LIMIT, "iteration limit reached")

    A = workspace.problem.A
    column_count = size(A, 2)
    column = workspace.scratch.row_rhs
    fill!(column, zero(T))
    if entering <= column_count
        for position in A.colptr[entering]:(A.colptr[entering + 1] - 1)
            column[A.rowval[position]] = A.nzval[position]
        end
    else
        column[entering - column_count] = -one(T)
    end
    tableau_column = forward_solve!(workspace.scratch.row_solution,
                                    workspace.factorization, column)
    all(isfinite, tableau_column) || return _numerical_failure()
    step, leaving_row, leaving_state = _primal_ratio(
        workspace, entering, direction, tableau_column,
    )
    leaving_row == -1 && return DualTermination(NUMERICAL_ERROR, "primal ratio test is inconclusive")
    if isnothing(step)
        structural = zeros(T, column_count)
        entering <= column_count && (structural[entering] = direction)
        for (row, index) in enumerate(workspace.basis.basic_indices)
            index <= column_count || continue
            structural[index] -= direction * tableau_column[row]
        end
        direction_status = _recession_direction_status(workspace, structural)
        direction_status == :certified &&
            return DualTermination(UNBOUNDED, "unbounded improving direction")
        return DualTermination(NUMERICAL_ERROR,
                               "primal improving direction does not certify unboundedness")
    end
    isfinite(step) || return _numerical_failure()
    if leaving_row == 0
        workspace.basis.states[entering] = direction > zero(T) ? AT_UPPER : AT_LOWER
    else
        abs(tableau_column[leaving_row]) > workspace.options.zero_tolerance ||
            return DualTermination(NUMERICAL_ERROR, "primal pivot is below the zero tolerance")
        replace_column!(workspace.factorization, tableau_column, leaving_row;
                        zero_tolerance=workspace.options.zero_tolerance)
        leaving = workspace.basis.basic_indices[leaving_row]
        workspace.basis.basic_indices[leaving_row] = entering
        workspace.basis.states[entering] = BASIC
        workspace.basis.states[leaving] = leaving_state
    end
    workspace.iterations += 1
    refactorize = length(workspace.factorization.updates) >=
                  workspace.options.refactorization_interval
    stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
    recompute!(workspace; refactorize, caller_guard=stop_requested)
    return nothing
end

function _primal_optimize!(workspace::SimplexWorkspace{T}, stop_requested,
                           reduced_cost_tolerance::T=workspace.options.dual_tolerance) where {T}
    while true
        stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
        _finite_workspace(workspace) || return _numerical_failure()
        primal_infeasibility(workspace) <= workspace.options.primal_tolerance ||
            return DualTermination(NUMERICAL_ERROR, "primal feasibility lost")
        terminal = _primal_iteration!(workspace, stop_requested, reduced_cost_tolerance)
        isnothing(terminal) || return terminal
    end
end

_primal_infeasibility_certified(workspace::SimplexWorkspace{T}, dual::Vector{T}) where {T<:AbstractFloat} =
    _floating_infeasibility_certified(workspace, dual, false)

function _primal_infeasibility_certified(workspace::SimplexWorkspace{T},
                                         dual::Vector{T}) where {T<:Rational}
    A = workspace.problem.A
    column_count = size(A, 2)
    minimum_value = zero(T)
    for index in eachindex(workspace.lower)
        coefficient = zero(T)
        if index <= column_count
            for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                coefficient -= dual[A.rowval[position]] * A.nzval[position]
            end
        else
            coefficient = dual[index - column_count]
        end
        iszero(coefficient) && continue
        bound = coefficient > zero(T) ? workspace.lower[index] : workspace.upper[index]
        isfinite(bound) || return false
        minimum_value += coefficient * bound_value(bound)
    end
    return minimum_value > zero(T)
end

function _primal_phase_one(problem::LinearProblem{T}, options::SolverOptions{T},
                           progress::SimplexProgressContext{T}, stop_requested) where {T}
    initial = initialize_workspace(problem, options; progress)
    row_count, column_count = size(problem.A)
    artificial_rows = Int[]
    artificial_signs = T[]
    row_states = VariableState[]
    for row in 1:row_count
        index = column_count + row
        value = initial.primal[index]
        if _lower_violation(initial.lower[index], value) > options.primal_tolerance
            push!(artificial_rows, row)
            push!(artificial_signs, one(T))
            push!(row_states, AT_LOWER)
        elseif _upper_violation(initial.upper[index], value) > options.primal_tolerance
            push!(artificial_rows, row)
            push!(artificial_signs, -one(T))
            push!(row_states, AT_UPPER)
        end
    end
    isempty(artificial_rows) && return initial, 0, initial

    # Each new column repairs one violated row while its row-activity variable
    # becomes nonbasic at the violated bound. The resulting basis is feasible.
    artificial_count = length(artificial_rows)
    artificial_matrix = sparse(artificial_rows, collect(1:artificial_count),
                               artificial_signs, row_count, artificial_count)
    phase_problem = LinearProblem{T}(
        hcat(problem.A, artificial_matrix),
        vcat(zeros(T, column_count), ones(T, artificial_count)),
        zero(T), MIN_SENSE, problem.row_lower, problem.row_upper,
        vcat(problem.column_lower, fill(Bound(zero(T)), artificial_count)),
        vcat(problem.column_upper, fill(Bound{T}(nothing), artificial_count)),
        fill(CONTINUOUS, column_count + artificial_count),
        problem.name, String[], String[],
    )
    workspace = initialize_workspace(phase_problem, options; progress)
    for artificial in 1:artificial_count
        row = artificial_rows[artificial]
        row_variable = column_count + artificial_count + row
        artificial_variable = column_count + artificial
        workspace.basis.basic_indices[row] = artificial_variable
        workspace.basis.states[artificial_variable] = BASIC
        workspace.basis.states[row_variable] = row_states[artificial]
    end
    recompute!(workspace; refactorize=true, caller_guard=stop_requested)
    return workspace, artificial_count, initial
end

function _solve_continuous_primal(problem::LinearProblem{T}, options::SolverOptions{T};
                                  stop_requested::Function=() -> false,
                                  progress::SimplexProgressContext{T}=
                                      SimplexProgressContext(problem)) where {T}
    stop_requested = _guard_stop_callback(stop_requested)
    workspace = nothing
    try
        workspace, artificial_count, initial = _primal_phase_one(
            problem, options, progress, stop_requested,
        )
        # A small phase-I reduced cost can still remove a large violation when
        # its column is small, so dual_tolerance must not suppress it.
        terminal = _primal_optimize!(workspace, stop_requested,
                                     artificial_count > 0 ? zero(T) : options.dual_tolerance)
        terminal.status == OPTIMAL || return _internal_solution(workspace, terminal)
        if artificial_count > 0
            column_count = size(problem.A, 2)
            phase_primal = copy(workspace.primal[1:column_count + artificial_count])
            _original_optimality_certified(workspace, phase_primal) ||
                return _internal_solution(workspace, NUMERICAL_ERROR,
                                          "phase I optimality certificate is inconclusive")
            artificial_sum = sum(workspace.primal[column_count + 1:column_count + artificial_count])
            isfinite(artificial_sum) || return _internal_solution(workspace, _numerical_failure())
            if artificial_sum > options.primal_tolerance
                dual = transpose_solve(workspace.factorization,
                                       workspace.costs[workspace.basis.basic_indices])
                certified = all(isfinite, dual) &&
                            _primal_infeasibility_certified(initial, dual)
                status = certified ? INFEASIBLE : NUMERICAL_ERROR
                message = certified ? "phase I optimum certifies infeasibility" :
                                      "phase I infeasibility certificate is inconclusive"
                return _internal_solution(workspace, status, message)
            end
            for artificial in 1:artificial_count
                index = column_count + artificial
                workspace.upper[index] = Bound(zero(T))
                workspace.problem.column_upper[index] = Bound(zero(T))
                workspace.problem.objective[index] = zero(T)
            end
            workspace.problem.objective[1:column_count] .= problem.objective
            workspace.costs .= vcat(workspace.problem.objective,
                                    zeros(T, size(problem.A, 1)))
            recompute!(workspace)
            terminal = _primal_optimize!(workspace, stop_requested)
            terminal.status == OPTIMAL || return _internal_solution(workspace, terminal)
        end
        run = _internal_solution(workspace, OPTIMAL, "optimal solution found")
        if run.status == OPTIMAL && artificial_count > 0
            return DualRunResult{T}(run.status, run.objective_value,
                                    run.primal[1:size(problem.A, 2)],
                                    run.iterations, run.refactorizations, run.message)
        end
        return run
    catch exception
        exception === stop_requested.exception && rethrow()
        _is_numerical_exception(exception) || rethrow()
        return DualRunResult{T}(NUMERICAL_ERROR, nothing, nothing,
                                isnothing(workspace) ? 0 : workspace.iterations,
                                isnothing(workspace) ? 0 : workspace.refactorizations,
                                sprint(showerror, exception))
    end
end

struct DualTermination
    status::TerminationStatus
    message::String
end

struct DualRunResult{T<:Real}
    status::TerminationStatus
    objective_value::Union{Nothing,T}
    primal::Union{Nothing,Vector{T}}
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

function _finite_workspace(workspace::SimplexWorkspace{T}) where {T}
    return all(isfinite, workspace.primal) && all(isfinite, workspace.reduced_costs) &&
           all(isfinite, workspace.costs) &&
           all(weight -> isfinite(weight) && weight > zero(T), workspace.pricing_weights)
end

function dual_edge_selection(workspace::SimplexWorkspace{T})::Int where {T}
    leaving_row = -1
    best_score = zero(T)
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

function _dual_pivot_eligible(workspace::SimplexWorkspace{T}, index::Int,
                              coefficient::T, tolerance::T) where {T}
    state = workspace.basis.states[index]
    _is_fixed(workspace.lower[index], workspace.upper[index]) && return false
    return (state == AT_LOWER && coefficient > tolerance) ||
           (state == AT_UPPER && coefficient < -tolerance) ||
           (state == FREE_NONBASIC && abs(coefficient) > tolerance)
end

# The row is oriented so that a positive dual step repairs the leaving bound.
function dual_ratio_test(workspace::SimplexWorkspace{T}, tableau_row::Vector{T})::Int where {T}
    candidates = Int[]
    maximum_step = _unbounded_bound(T)
    tolerance = workspace.options.dual_tolerance
    cutoff = _is_exact(T) === Val(true) ? zero(T) : _positive_tolerance(T, 1 // 10^7)
    for index in eachindex(tableau_row)
        coefficient = tableau_row[index]
        _dual_pivot_eligible(workspace, index, coefficient, cutoff) || continue
        push!(candidates, index)
        relaxed_step = (workspace.reduced_costs[index] +
                        ifelse(coefficient < zero(T), -tolerance, tolerance)) / coefficient
        # An overflowed positive relaxation imposes no finite step limit.
        # The selected pivot's actual step is checked before any update.
        if isfinite(relaxed_step) &&
           (!isfinite(maximum_step) || relaxed_step < bound_value(maximum_step))
            maximum_step = Bound(relaxed_step)
        end
    end

    entering_index = -1
    largest_pivot = zero(T)
    for index in candidates
        coefficient = tableau_row[index]
        step = workspace.reduced_costs[index] / coefficient
        within_limit = !isfinite(maximum_step) || step <= bound_value(maximum_step)
        if within_limit && abs(coefficient) > largest_pivot
            entering_index = index
            largest_pivot = abs(coefficient)
        end
    end
    return entering_index
end

function price!(tableau_row::Vector{T}, workspace::SimplexWorkspace{T},
                rho::Vector{T})::Nothing where {T}
    A = workspace.problem.A
    row_count, column_count = size(A)
    for column in 1:column_count
        value = zero(T)
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

function update_duals!(workspace::SimplexWorkspace{T}, tableau_row::Vector{T},
                      leaving_index::Int, entering_index::Int, dual_step::T)::Nothing where {T}
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
                reduced_cost = zero(T)
            end
        end
        workspace.reduced_costs[index] = reduced_cost
    end
    workspace.reduced_costs[leaving_index] = -dual_step
    workspace.reduced_costs[entering_index] = zero(T)
    return nothing
end

function update_primals!(workspace::SimplexWorkspace{T}, tableau_column::Vector{T},
                        entering_index::Int, leaving_row::Int, primal_step::T)::Nothing where {T}
    for (row, index) in enumerate(workspace.basis.basic_indices)
        workspace.primal[index] -= primal_step * tableau_column[row]
    end
    workspace.primal[entering_index] += primal_step
    return nothing
end

function update_dse!(workspace::SimplexWorkspace{T}, rho::Vector{T}, tableau_column::Vector{T},
                    entering_index::Int, pivot::T)::Nothing where {T}
    entering_weight = dot(rho, rho) / pivot^2
    tau = forward_solve(workspace.factorization, rho)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        coefficient = tableau_column[row]
        workspace.pricing_weights[index] = max(
            _typed_ratio(T, 1, 10^4), workspace.pricing_weights[index] + coefficient *
            (coefficient * entering_weight - T(2) * tau[row] / pivot),
        )
    end
    workspace.pricing_weights[entering_index] = entering_weight
    return nothing
end

function dual_iteration!(workspace::SimplexWorkspace{T}, stop_requested)::Union{Nothing,DualTermination} where {T}
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

function _add_product_bounds(lower::T, upper::T, left::T, right::T) where {T<:AbstractFloat}
    (iszero(left) || iszero(right)) && return lower, upper
    product = left * right
    return prevfloat(lower + prevfloat(product)), nextfloat(upper + nextfloat(product))
end

function _floating_infeasibility_certified(workspace::SimplexWorkspace{T},
                                          rho::Vector{T}, below::Bool) where {T<:AbstractFloat}
    # Every feasible working vector satisfies [A -I] * x == 0. A row
    # combination whose minimum over the bounds is strictly positive proves
    # a contradiction without relying on the computed basic primal values.
    A = workspace.problem.A
    column_count = size(A, 2)
    orientation = below ? one(T) : -one(T)
    minimum_value = zero(T)
    for index in eachindex(workspace.lower)
        coefficient_lower = coefficient_upper = zero(T)
        if index <= column_count
            for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                coefficient_lower, coefficient_upper = _add_product_bounds(
                    coefficient_lower, coefficient_upper,
                    orientation * rho[A.rowval[position]], A.nzval[position],
                )
            end
        else
            coefficient_lower = coefficient_upper = -orientation * rho[index - column_count]
        end
        isfinite(coefficient_lower) && isfinite(coefficient_upper) || return false
        iszero(coefficient_lower) && iszero(coefficient_upper) && continue

        lower, upper = workspace.lower[index], workspace.upper[index]
        !isfinite(lower) && coefficient_upper > zero(T) && return false
        !isfinite(upper) && coefficient_lower < zero(T) && return false
        isfinite(lower) || isfinite(upper) || return false
        endpoint = isfinite(lower) ? bound_value(lower) : bound_value(upper)
        term = min(coefficient_lower * endpoint, coefficient_upper * endpoint)
        if isfinite(lower) && isfinite(upper)
            endpoint = bound_value(upper)
            term = min(term, coefficient_lower * endpoint, coefficient_upper * endpoint)
        end
        isfinite(term) || return false
        total = minimum_value + prevfloat(term)
        isfinite(total) || return false
        minimum_value = prevfloat(total)
    end
    return minimum_value > zero(T)
end

function _dual_iteration!(workspace::SimplexWorkspace{T}, stop_requested,
                          basis_refreshed::Bool=false) where {T}
    leaving_row = dual_edge_selection(workspace)
    leaving_row == -1 && return DualTermination(OPTIMAL, "optimal solution found")
    leaving_index = workspace.basis.basic_indices[leaving_row]
    below = _lower_violation(workspace.lower[leaving_index], workspace.primal[leaving_index]) > zero(T)
    bound = below ? workspace.lower[leaving_index] : workspace.upper[leaving_index]
    delta = workspace.primal[leaving_index] - bound_value(bound)

    row_count, column_count = size(workspace.problem.A)
    unit = zeros(T, row_count)
    unit[leaving_row] = one(T)
    rho = transpose_solve(workspace.factorization, unit)
    tableau_row = zeros(T, row_count + column_count)
    price!(tableau_row, workspace, rho)
    all(isfinite, rho) && all(isfinite, tableau_row) || return _numerical_failure()
    oriented_row = below ? -tableau_row : tableau_row
    entering_index = dual_ratio_test(workspace, oriented_row)
    if entering_index == -1
        # A tolerance cannot turn a nonzero, sign-eligible coefficient into a
        # mathematical infeasibility proof.
        if any(index -> _dual_pivot_eligible(workspace, index, oriented_row[index],
                                             zero(T)), eachindex(oriented_row))
            return DualTermination(NUMERICAL_ERROR, "eligible pivots are below the Harris safety cutoff")
        end
        if _is_exact(T) === Val(false) && !basis_refreshed
            # Incremental floating updates can drift outside primal tolerance.
            # Rebuild once and repeat the test before certifying infeasibility.
            stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
            recompute!(workspace; refactorize=true, caller_guard=stop_requested)
            stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
            _finite_workspace(workspace) || return _numerical_failure()
            dual_infeasibility(workspace) <= workspace.options.dual_tolerance ||
                return DualTermination(NUMERICAL_ERROR, "dual feasibility lost")
            return _dual_iteration!(workspace, stop_requested, true)
        end
        if _is_exact(T) === Val(false) && !_floating_infeasibility_certified(workspace, rho, below)
            return DualTermination(NUMERICAL_ERROR,
                                   "floating row combination does not certify infeasibility")
        end
        return DualTermination(INFEASIBLE, "no eligible dual pivot")
    end

    column = zeros(T, row_count)
    if entering_index <= column_count
        A = workspace.problem.A
        for position in A.colptr[entering_index]:(A.colptr[entering_index + 1] - 1)
            column[A.rowval[position]] = A.nzval[position]
        end
    else
        column[entering_index - column_count] = -one(T)
    end
    tableau_column = forward_solve(workspace.factorization, column)
    all(isfinite, tableau_column) || return _numerical_failure()
    pivot = tableau_column[leaving_row]
    abs(pivot) > workspace.options.zero_tolerance || throw(ZeroPivotException(leaving_row))
    primal_step = delta / pivot
    dual_step = workspace.reduced_costs[entering_index] / tableau_row[entering_index]
    isfinite(primal_step) && isfinite(dual_step) || return _numerical_failure()
    if dual_step * sign(delta) < zero(T)
        # Harris may accept a reduced cost on the infeasible side of zero,
        # within dual tolerance. Do not move backwards in the dual direction.
        workspace.costs[entering_index] -= workspace.reduced_costs[entering_index]
        workspace.reduced_costs[entering_index] = zero(T)
        workspace.perturbed = true
        dual_step = zero(T)
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

function _within_primal_bounds(values::AbstractVector{T}, lower::AbstractVector{Bound{T}},
                               upper::AbstractVector{Bound{T}}, tolerance::T) where {T}
    all(isfinite, values) || return false
    for index in eachindex(values)
        _lower_violation(lower[index], values[index]) > tolerance && return false
        _upper_violation(upper[index], values[index]) > tolerance && return false
    end
    return true
end

function _original_primal_feasible(workspace::SimplexWorkspace{T}, primal::Vector{T}) where {T}
    problem = workspace.problem
    # Use the configured absolute tolerance in the original constraint units.
    # Scaling it by the sum of absolute products would hide cancellation in A * x.
    tolerance = workspace.options.primal_tolerance
    _within_primal_bounds(primal, problem.column_lower, problem.column_upper, tolerance) || return false
    return _within_primal_bounds(problem.A * primal, problem.row_lower, problem.row_upper, tolerance)
end

function _internal_solution(workspace::SimplexWorkspace{T}, status::TerminationStatus,
                            message::String) where {T}
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
    return DualRunResult{T}(status, objective, primal, workspace.iterations,
                            workspace.refactorizations, message)
end

_internal_solution(workspace::SimplexWorkspace{T}, terminal::DualTermination) where {T} =
    _internal_solution(workspace, terminal.status, terminal.message)

function _flip_bounds!(workspace::SimplexWorkspace{T}) where {T}
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

function _dual_optimize!(workspace::SimplexWorkspace{T}, stop_requested)::DualTermination where {T}
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

function _auxiliary_workspace(workspace::SimplexWorkspace{T}) where {T}
    lower = similar(workspace.lower)
    upper = similar(workspace.upper)
    basis = Basis(workspace.basis.basic_indices, workspace.basis.states)
    for index in eachindex(lower)
        has_lower = isfinite(workspace.lower[index])
        has_upper = isfinite(workspace.upper[index])
        if has_lower && has_upper
            lower[index], upper[index] = Bound(zero(T)), Bound(zero(T))
        elseif has_lower
            lower[index], upper[index] = Bound(zero(T)), Bound(one(T))
        elseif has_upper
            lower[index], upper[index] = Bound(-one(T)), Bound(zero(T))
        else
            lower[index], upper[index] = Bound(-T(1000)), Bound(T(1000))
        end
        if basis.states[index] != BASIC
            basis.states[index] = workspace.reduced_costs[index] < zero(T) ? AT_UPPER : AT_LOWER
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

function _classify_recession!(workspace::SimplexWorkspace{T}, stop_requested) where {T}
    # A negative auxiliary optimum certifies a recession direction. Original
    # feasibility is still required: an infeasible LP can have such a direction.
    feasibility = initialize_workspace(workspace.problem, workspace.options)
    feasibility.iterations = workspace.iterations
    feasibility.refactorizations = workspace.refactorizations
    fill!(feasibility.costs, zero(T))
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

function _recession_row_bounds(A::SparseMatrixCSC{T,Int}, structural::Vector{T},
                                ::Val{true}) where {T<:Rational}
    values = A * structural
    return values, values
end

function _recession_row_bounds(A::SparseMatrixCSC{T,Int}, structural::Vector{T},
                                ::Val{false}) where {T<:AbstractFloat}
    lower = zeros(T, size(A, 1))
    upper = zeros(T, size(A, 1))
    for column in axes(A, 2)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            row = A.rowval[position]
            lower[row], upper[row] = _add_product_bounds(
                lower[row], upper[row], A.nzval[position], structural[column],
            )
        end
    end
    return lower, upper
end

function _recession_objective_bounds(costs::Vector{T}, lower::Vector{T}, upper::Vector{T},
                                      ::Val{true}) where {T<:Rational}
    value = dot(costs, lower)
    return value, value
end

function _recession_objective_bounds(costs::Vector{T}, lower::Vector{T}, upper::Vector{T},
                                      ::Val{false}) where {T<:AbstractFloat}
    minimum_value = maximum_value = zero(T)
    for index in eachindex(costs)
        cost = costs[index]
        minimum_direction, maximum_direction = cost < zero(T) ?
            (upper[index], lower[index]) : (lower[index], upper[index])
        minimum_value, _ = _add_product_bounds(minimum_value, zero(T), cost, minimum_direction)
        _, maximum_value = _add_product_bounds(zero(T), maximum_value, cost, maximum_direction)
    end
    return minimum_value, maximum_value
end

function _recession_direction_status(workspace::SimplexWorkspace{T},
                                     auxiliary::SimplexWorkspace{T}) where {T}
    column_count = size(workspace.problem.A, 2)
    structural = auxiliary.primal[1:column_count]
    row_lower, row_upper = _recession_row_bounds(workspace.problem.A, structural, _is_exact(T))
    lower, upper = vcat(structural, row_lower), vcat(structural, row_upper)
    all(isfinite, lower) && all(isfinite, upper) || return :invalid
    # Each exact row direction must have a valid sign throughout its interval.
    # An interval containing zero does not establish equality, even when the
    # computed residual vanishes or is small relative to the dot-product terms.
    tolerance = workspace.options.zero_tolerance
    ambiguous = false
    for index in eachindex(lower)
        violation = max(isfinite(workspace.lower[index]) ? -lower[index] : zero(T),
                        isfinite(workspace.upper[index]) ? upper[index] : zero(T))
        violation <= zero(T) && continue
        certain_violation = max(isfinite(workspace.lower[index]) ? -upper[index] : zero(T),
                                isfinite(workspace.upper[index]) ? lower[index] : zero(T))
        certain_violation > tolerance && return :invalid
        ambiguous = true
    end
    objective_lower, objective_upper = _recession_objective_bounds(
        workspace.costs, lower, upper, _is_exact(T),
    )
    isfinite(objective_lower) && isfinite(objective_upper) || return :invalid
    objective_lower < -workspace.options.dual_tolerance || return :invalid
    objective_upper < -workspace.options.dual_tolerance || return :ambiguous
    return ambiguous ? :ambiguous : :certified
end

function make_dual_feasible!(workspace::SimplexWorkspace{T}, stop_requested)::Union{Nothing,DualTermination} where {T}
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

function _make_dual_feasible!(workspace::SimplexWorkspace{T}, stop_requested) where {T}
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
            return DualTermination(NUMERICAL_ERROR, "auxiliary direction has uncertain feasibility or objective improvement")
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

function _solve_continuous_dual(problem::LinearProblem{T}, options::SolverOptions{T};
                                stop_requested::Function=() -> false) where {T}
    stop_requested = _guard_stop_callback(stop_requested)
    workspace = nothing
    try
        workspace = initialize_workspace(problem, options)
        return _solve_continuous_dual!(workspace, stop_requested)
    catch exception
        exception === stop_requested.exception && rethrow()
        _is_numerical_exception(exception) || rethrow()
        return DualRunResult{T}(NUMERICAL_ERROR, nothing, nothing,
                                isnothing(workspace) ? 0 : workspace.iterations,
                                isnothing(workspace) ? 0 : workspace.refactorizations,
                                sprint(showerror, exception))
    end
end

function _solve_continuous_dual!(workspace::SimplexWorkspace{T}, stop_requested) where {T}
    problem, options = workspace.problem, workspace.options
    stop_requested() && return _internal_solution(workspace, TIME_LIMIT, "time limit reached")
    _finite_workspace(workspace) || return _internal_solution(workspace, _numerical_failure())
    if iszero(size(problem.A, 1))
        for index in eachindex(workspace.costs)
            cost = workspace.costs[index]
            iszero(cost) && continue
            bound = cost > zero(T) ? workspace.lower[index] : workspace.upper[index]
            isfinite(bound) || return _internal_solution(workspace, UNBOUNDED, "unbounded improving direction")
            workspace.primal[index] = bound_value(bound)
        end
        return _internal_solution(workspace, OPTIMAL, "optimal solution found")
    end
    terminal = make_dual_feasible!(workspace, stop_requested)
    isnothing(terminal) || return _internal_solution(workspace, terminal)
    terminal = _dual_optimize!(workspace, stop_requested)
    terminal.status == OPTIMAL || return _internal_solution(workspace, terminal)
    workspace.costs .= vcat(problem.objective, zeros(T, size(problem.A, 1)))
    workspace.perturbed = false
    recompute!(workspace)
    status = primal_infeasibility(workspace) <= options.primal_tolerance &&
             dual_infeasibility(workspace) <= options.dual_tolerance ? OPTIMAL : NUMERICAL_ERROR
    return _internal_solution(workspace, status,
                              status == OPTIMAL ? "optimal solution found" : "dual feasibility lost")
end

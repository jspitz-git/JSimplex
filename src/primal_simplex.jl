function _primal_direction_weight(direction::AbstractVector{T}) where {T<:AbstractFloat}
    scale = one(T)
    for coefficient in direction
        scale = max(scale, abs(coefficient))
    end
    scaled_square = abs2(inv(scale))
    for coefficient in direction
        scaled_square += abs2(coefficient / scale)
    end
    factor = sqrt(scaled_square)
    scale_mantissa, scale_exponent = frexp(scale)
    factor_mantissa, factor_exponent = frexp(factor)
    mantissa, correction = frexp(scale_mantissa * factor_mantissa)
    # Keep the exponent separately: a finite column can have a norm above floatmax(T).
    scaled_weight = (scale_exponent + factor_exponent + correction, mantissa)
    stored_weight = min(floatmax(T), scale * factor)
    return scaled_weight, stored_weight
end

function _primal_direction_weight(direction::AbstractVector{T}) where {T<:Rational}
    weight = one(Rational{BigInt})
    for coefficient in direction
        weight += abs2(big(coefficient))
    end
    stored_weight = T === Rational{BigInt} ? weight : one(T)
    return weight, stored_weight
end

function _primal_weighted_score(reduced_cost::T,
                                weight::Tuple{I,T}) where {I<:Integer,T<:AbstractFloat}
    cost_mantissa, cost_exponent = frexp(abs(reduced_cost))
    weight_exponent, weight_mantissa = weight
    score_mantissa, correction = frexp(cost_mantissa / weight_mantissa)
    return (cost_exponent - weight_exponent + correction, score_mantissa)
end

function _primal_weighted_score(reduced_cost::T, weight::T) where {T<:AbstractFloat}
    mantissa, exponent = frexp(weight)
    return _primal_weighted_score(reduced_cost, (exponent, mantissa))
end
_primal_weighted_score(reduced_cost::Rational, weight::Rational) =
    big(reduced_cost)^2 / big(weight)

_primal_dantzig_score(reduced_cost::T) where {T<:AbstractFloat} =
    _primal_weighted_score(reduced_cost, one(T))
_primal_dantzig_score(reduced_cost::Rational) = abs(big(reduced_cost))

_primal_devex_leaving_weight(weight::T, pivot::T) where {T<:AbstractFloat} =
    max(one(T), min(floatmax(T), weight / abs(pivot)))
_primal_store_rational_weight(::Type{Rational{BigInt}}, weight::Rational{BigInt}) = weight
function _primal_store_rational_weight(::Type{Rational{I}},
                                       weight::Rational{BigInt}) where {I<:Integer}
    limit = BigInt(typemax(I))
    numerator_value, denominator_value = numerator(weight), denominator(weight)
    if numerator_value <= limit && denominator_value <= limit
        return convert(I, numerator_value) // convert(I, denominator_value)
    end
    # Devex is an estimate; retain a positive, representable integer weight.
    return convert(I, min(limit, div(numerator_value, denominator_value))) // one(I)
end
_primal_devex_leaving_weight(weight::T, pivot::T) where {T<:Rational} =
    _primal_store_rational_weight(T, max(one(Rational{BigInt}),
                                         big(weight) / big(pivot)^2))

_primal_devex_candidate_weight(coefficient::T, leaving_weight::T) where {T<:AbstractFloat} =
    min(floatmax(T), abs(coefficient) * leaving_weight)
_primal_devex_candidate_weight(coefficient::T, leaving_weight::T) where {T<:Rational} =
    _primal_store_rational_weight(T, big(coefficient)^2 * big(leaving_weight))

function _primal_steepest_weight!(workspace::SimplexWorkspace{T}, index::Int) where {T}
    A = workspace.problem.A
    column_count = size(A, 2)
    column = workspace.scratch.row_rhs
    fill!(column, zero(T))
    if index <= column_count
        for position in A.colptr[index]:(A.colptr[index + 1] - 1)
            column[A.rowval[position]] = A.nzval[position]
        end
    else
        column[index - column_count] = -one(T)
    end
    direction = _checked_basis_solve!(workspace.scratch.row_solution,workspace,column)
    scaled_weight, stored_weight = _primal_direction_weight(direction)
    workspace.pricing_weights[index] = stored_weight
    workspace.scratch.steepest_valid[index] = _primal_cacheable_weight(stored_weight)
    return scaled_weight
end

_primal_cacheable_weight(weight::T) where {T<:AbstractFloat} =
    isfinite(weight) && weight < floatmax(T) && isfinite(abs2(weight))
_primal_cacheable_weight(weight::Rational{BigInt}) = true
_primal_cacheable_weight(weight::Rational) = false

function _primal_unit_basis(workspace::SimplexWorkspace{T}) where {T}
    A = workspace.problem.A
    column_count = size(A, 2)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        if index > column_count
            index - column_count == row || return false
        else
            start = A.colptr[index]
            A.colptr[index + 1] == start + 1 || return false
            A.rowval[start] == row || return false
            abs(A.nzval[start]) == one(T) || return false
        end
    end
    return true
end

function _primal_initialize_steepest!(workspace::SimplexWorkspace{T}) where {T}
    scratch = workspace.scratch
    scratch.steepest_initialized && return nothing
    scratch.steepest_initialized = true
    T <: Rational && T !== Rational{BigInt} && return nothing
    _primal_unit_basis(workspace) || return nothing
    A = workspace.problem.A
    row_count, column_count = size(A)
    for index in 1:column_count
        direction = @view A.nzval[A.colptr[index]:(A.colptr[index + 1] - 1)]
        _, weight = _primal_direction_weight(direction)
        workspace.pricing_weights[index] = weight
        scratch.steepest_valid[index] = _primal_cacheable_weight(weight)
    end
    _, row_weight = _primal_direction_weight(T[one(T)])
    for index in (column_count + 1):(column_count + row_count)
        workspace.pricing_weights[index] = row_weight
        scratch.steepest_valid[index] = _primal_cacheable_weight(row_weight)
    end
    return nothing
end

function _primal_updated_weight(weight::T, alpha::T, beta::T,
                                h_norm_squared::T) where {T<:AbstractFloat}
    squared = muladd(alpha * alpha, h_norm_squared,
                     muladd(-2 * alpha, beta, weight * weight))
    isfinite(squared) && squared >= one(T) || return nothing
    updated = sqrt(squared)
    return _primal_cacheable_weight(updated) ? updated : nothing
end

function _primal_updated_weight(weight::Rational{BigInt}, alpha::Rational{BigInt},
                                beta::Rational{BigInt}, h_norm_squared::Rational{BigInt})
    updated = weight - 2 * alpha * beta + alpha^2 * h_norm_squared
    return updated >= 1 ? updated : nothing
end

function _primal_update_steepest!(workspace::SimplexWorkspace{T}, entering::Int,
                                  leaving_row::Int, pivot::T) where {T}
    scratch = workspace.scratch
    # Fixed-width rational weights are priced exactly on demand in BigInt arithmetic.
    T <: Rational && T !== Rational{BigInt} && return nothing
    direction = scratch.row_solution
    h = scratch.row_rhs
    for row in eachindex(h)
        h[row] = (direction[row] - (row == leaving_row ? one(T) : zero(T))) / pivot
    end
    if !all(isfinite, h)
        fill!(scratch.steepest_valid, false)
        return nothing
    end
    h_norm_squared = dot(h, h)
    if !isfinite(h_norm_squared)
        fill!(scratch.steepest_valid, false)
        return nothing
    end
    tau = _checked_basis_solve!(scratch.tau,workspace,h;transposed=true)
    fill!(h, zero(T))
    h[leaving_row] = one(T)
    rho = _checked_basis_solve!(scratch.rho,workspace,h;transposed=true)
    if !all(isfinite, tau) || !all(isfinite, rho)
        fill!(scratch.steepest_valid, false)
        return nothing
    end
    price!(scratch.pricing_row, workspace, tau)
    price!(scratch.tableau_row, workspace, rho)
    leaving = workspace.basis.basic_indices[leaving_row]
    for index in eachindex(workspace.basis.states)
        (index == entering || workspace.basis.states[index] == BASIC && index != leaving) &&
            continue
        scratch.steepest_valid[index] || index == leaving || continue
        weight = index == leaving ?
            (T <: AbstractFloat ? sqrt(T(2)) : T(2)) : workspace.pricing_weights[index]
        updated = _primal_updated_weight(weight, scratch.tableau_row[index],
                                         scratch.pricing_row[index], h_norm_squared)
        if isnothing(updated)
            scratch.steepest_valid[index] = false
        else
            workspace.pricing_weights[index] = updated
            scratch.steepest_valid[index] = true
        end
    end
    scratch.steepest_valid[entering] = false
    return nothing
end

function _primal_entering(workspace::SimplexWorkspace{T}, tolerance::T) where {T}
    workspace.options.pricing == :steepest_edge && _primal_initialize_steepest!(workspace)
    entering = 0
    direction = zero(T)
    best_score = _primal_dantzig_score(one(T))
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        index in workspace.scratch.rejected_entering && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        reduced_cost = workspace.reduced_costs[index]
        improving = (state == AT_LOWER && reduced_cost < -tolerance) ||
                    (state == AT_UPPER && reduced_cost > tolerance) ||
                    (state == FREE_NONBASIC && abs(reduced_cost) > tolerance)
        improving || continue
        pricing = workspace.options.pricing
        score = if pricing == :dantzig
            _primal_dantzig_score(reduced_cost)
        else
            weight = pricing == :steepest_edge && !workspace.scratch.steepest_valid[index] ?
                _primal_steepest_weight!(workspace, index) : workspace.pricing_weights[index]
            _primal_weighted_score(reduced_cost, weight)
        end
        if entering == 0 || score > best_score
            entering = index
            direction = reduced_cost < zero(T) ? one(T) : -one(T)
            best_score = score
        end
    end
    return entering, direction
end

function _primal_update_devex!(workspace::SimplexWorkspace{T}, entering::Int,
                               leaving_row::Int, pivot::T) where {T}
    unit = workspace.scratch.row_rhs
    fill!(unit, zero(T))
    unit[leaving_row] = one(T)
    rho = _checked_basis_solve!(workspace.scratch.rho,workspace,unit;transposed=true)
    tableau_row = workspace.scratch.tableau_row
    price!(tableau_row, workspace, rho)
    leaving = workspace.basis.basic_indices[leaving_row]
    leaving_weight = _primal_devex_leaving_weight(
        workspace.pricing_weights[entering], pivot,
    )
    for index in eachindex(workspace.basis.states)
        (index == entering || workspace.basis.states[index] == BASIC) && continue
        workspace.pricing_weights[index] = max(
            workspace.pricing_weights[index],
            _primal_devex_candidate_weight(tableau_row[index], leaving_weight),
        )
    end
    workspace.pricing_weights[leaving] = leaving_weight
    return nothing
end

_primal_relaxed_step(raw_step::T, tolerance::T, movement::T) where {T<:AbstractFloat} =
    raw_step + tolerance / abs(movement)
_primal_relaxed_step(raw_step::T, tolerance::T, movement::T) where {T<:Rational} =
    big(raw_step) + big(tolerance) / abs(big(movement))

function _primal_ratio(workspace::SimplexWorkspace{T}, entering::Int, direction::T,
                       tableau_column::Vector{T}) where {T}
    opposite = direction > zero(T) ? workspace.upper[entering] : workspace.lower[entering]
    # Keep optionality in flags so numeric loop accumulators stay concrete.
    has_step = isfinite(opposite)
    entering_step = has_step ?
        (bound_value(opposite) - workspace.primal[entering]) / direction : zero(T)
    strict_step = entering_step
    strict_row = 0
    strict_state = BASIC
    relaxed_limit = entering_step
    has_relaxed_limit = has_step
    tolerance = workspace.options.primal_tolerance
    for (row, index) in enumerate(workspace.basis.basic_indices)
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > zero(T) ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        raw_step = (bound_value(bound) - workspace.primal[index]) / movement
        isfinite(raw_step) || return nothing, -1, BASIC
        if raw_step < zero(T)
            violation = movement > zero(T) ?
                _upper_violation(bound, workspace.primal[index]) :
                _lower_violation(bound, workspace.primal[index])
            violation > tolerance && return nothing, -1, BASIC
        end
        candidate = max(zero(T), raw_step)
        if !has_step || candidate < strict_step ||
           (candidate == strict_step && strict_row == 0)
            strict_step = candidate
            strict_row = row
            strict_state = movement > zero(T) ? AT_UPPER : AT_LOWER
            has_step = true
        end
        relaxed = _primal_relaxed_step(raw_step, tolerance, movement)
        if isfinite(relaxed) && (!has_relaxed_limit || relaxed < relaxed_limit)
            relaxed_limit = max(zero(T), relaxed)
            has_relaxed_limit = true
        end
    end
    has_step || return nothing, strict_row, strict_state
    strict_row == 0 && return strict_step, strict_row, strict_state
    has_relaxed_limit || return strict_step, strict_row, strict_state

    leaving_row = 0
    leaving_step = strict_step
    leaving_state = strict_state
    largest_pivot = zero(T)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row in workspace.scratch.rejected_rows && continue
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > zero(T) ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        candidate = max(zero(T),
                        (bound_value(bound) - workspace.primal[index]) / movement)
        candidate <= relaxed_limit || continue
        pivot = abs(tableau_column[row])
        if pivot > largest_pivot
            leaving_row = row
            leaving_step = candidate
            leaving_state = movement > zero(T) ? AT_UPPER : AT_LOWER
            largest_pivot = pivot
        end
    end
    if leaving_row == 0
        strict_row in workspace.scratch.rejected_rows && return nothing,-1,BASIC
        return strict_step,strict_row,strict_state
    end
    violation = zero(T)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        value = workspace.primal[index] - direction * tableau_column[row] * leaving_step
        if !isfinite(value)
            strict_row in workspace.scratch.rejected_rows && return nothing,-1,BASIC
            return strict_step,strict_row,strict_state
        end
        violation += max(zero(T), _lower_violation(workspace.lower[index], value),
                         _upper_violation(workspace.upper[index], value))
        if violation > tolerance
            strict_row in workspace.scratch.rejected_rows && return nothing,-1,BASIC
            return strict_step,strict_row,strict_state
        end
    end
    return leaving_step, leaving_row, leaving_state
end

function _primal_iteration_unchecked!(workspace::SimplexWorkspace{T}, stop_requested,
                            reduced_cost_tolerance::T,
                            basis_refreshed::Bool=false) where {T}
    _simplex_event!(workspace, :pricing)
    entering, direction = _timed_simplex(workspace, :pricing) do
        _primal_entering(workspace, reduced_cost_tolerance)
    end
    if entering == 0
        isempty(workspace.scratch.rejected_entering) || throw(_PivotRejection(0,0,:exhausted))
        return DualTermination(OPTIMAL, "optimal solution found")
    end
    workspace.scratch.selected_entering = entering
    workspace.iterations < workspace.options.iteration_limit ||
        return DualTermination(ITERATION_LIMIT, "iteration limit reached")

    _simplex_event!(workspace, :pivot_proposed)
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
    tableau_column = _timed_simplex(workspace, :ftran) do
        forward_solve!(workspace.scratch.row_solution, workspace.factorization, column)
    end
    all(isfinite, tableau_column) || return _numerical_failure()
    checked_pivot = workspace.progress.numerical_policy.pivot_validation
    if checked_pivot || workspace.progress.numerical_policy.solve_refinement
        quality = refine_basis_solve!(tableau_column,workspace,column,
                                       workspace.progress.numerical_policy,stop_requested)
        if !quality.reliable
            checked_pivot && throw(_PivotRejection(0,entering,:refresh))
            throw(_UnreliableBasisSolve())
        end
    end
    step, leaving_row, leaving_state = _primal_ratio(
        workspace, entering, direction, tableau_column,
    )
    workspace.scratch.selected_row = leaving_row
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
        if _is_staged_workspace(workspace)
            _prepare_primal_candidate!(workspace,entering,direction,step,tableau_column,
                                       leaving_row,leaving_state) || return _numerical_failure()
        end
        workspace.basis.states[entering] = direction > zero(T) ? AT_UPPER : AT_LOWER
    else
        if checked_pivot
            fill!(column,zero(T))
            column[leaving_row] = one(T)
            rho = transpose_solve!(workspace.scratch.rho,workspace.factorization,column)
            refine_basis_solve!(rho,workspace,column,workspace.progress.numerical_policy,
                                 stop_requested;transposed=true)
            price!(workspace.scratch.tableau_row,workspace,rho)
            proposal = PivotCandidate(entering,leaving_row,
                workspace.scratch.tableau_row[entering],tableau_column,rho)
            quality = validate_pivot!(workspace,proposal,workspace.progress.numerical_policy)
            quality == :accept || throw(_PivotRejection(leaving_row,entering,quality))
        end
        if !checked_pivot && abs(tableau_column[leaving_row]) <= workspace.options.zero_tolerance
            if !basis_refreshed
                stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
                recompute!(workspace; refactorize=true, caller_guard=stop_requested,
                           diagnostic_reason=:refactor_pivot)
                stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
                _finite_workspace(workspace) || return _numerical_failure()
                primal_infeasibility(workspace) <= workspace.options.primal_tolerance ||
                    return DualTermination(NUMERICAL_ERROR, "primal feasibility lost")
                fill!(workspace.scratch.steepest_valid, false)
                return _primal_iteration_unchecked!(workspace, stop_requested,
                                          reduced_cost_tolerance, true)
            end
            return DualTermination(NUMERICAL_ERROR, "primal pivot is below the zero tolerance")
        end
        workspace.options.pricing == :devex &&
            _primal_update_devex!(workspace, entering, leaving_row,
                                   tableau_column[leaving_row])
        workspace.options.pricing == :steepest_edge &&
            _primal_update_steepest!(workspace, entering, leaving_row,
                                     tableau_column[leaving_row])
        if _is_staged_workspace(workspace)
            # Check finite candidate values before mutating the factor. The
            # ordinary full recomputation finishes before publishing the step.
            _prepare_primal_candidate!(workspace,entering,direction,step,tableau_column,
                                       leaving_row,leaving_state) || return _numerical_failure()
        end
        _replace_pivot_column!(workspace, tableau_column, leaving_row;
                               stop_requested,
                               zero_tolerance=checked_pivot ? zero(T) : workspace.options.zero_tolerance)
        leaving = workspace.basis.basic_indices[leaving_row]
        workspace.basis.basic_indices[leaving_row] = entering
        workspace.basis.states[entering] = BASIC
        workspace.basis.states[leaving] = leaving_state
    end
    workspace.iterations += 1
    _simplex_event!(workspace, leaving_row == 0 ? :flip_completed : :pivot_completed)
    refactorize = length(workspace.factorization.updates) >=
                  workspace.options.refactorization_interval
    if _is_staged_workspace(workspace)
        workspace.scratch.post_iteration = :primal
        workspace.scratch.post_refactorize = refactorize
        return nothing
    end
    stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
    recompute!(workspace; refactorize, caller_guard=stop_requested,
               diagnostic_reason=:refactor_limit)
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

function _primal_phase_one_matrix(A::SparseMatrixCSC{T,Int}, artificial_rows::Vector{Int},
                                  artificial_signs::Vector{T}) where {T}
    row_count, column_count = size(A)
    artificial_count = length(artificial_rows)
    stored_count = nnz(A)
    # Phase I supplies one valid row/sign pair per artificial column. Append
    # these singleton columns directly, retaining owned CSC result arrays.
    column_pointers = Vector{Int}(undef, column_count + artificial_count + 1)
    rows = Vector{Int}(undef, stored_count + artificial_count)
    values = Vector{T}(undef, stored_count + artificial_count)
    copyto!(column_pointers, 1, A.colptr, 1, column_count + 1)
    copyto!(rows, 1, A.rowval, 1, stored_count)
    copyto!(values, 1, A.nzval, 1, stored_count)
    for column in 1:artificial_count
        column_pointers[column_count + column + 1] = stored_count + column + 1
    end
    copyto!(rows, stored_count + 1, artificial_rows, 1, artificial_count)
    copyto!(values, stored_count + 1, artificial_signs, 1, artificial_count)
    return SparseMatrixCSC(row_count, column_count + artificial_count,
                           column_pointers, rows, values)
end

function _primal_phase_one_vectors(problem::LinearProblem{T}, artificial_count::Int) where {T}
    column_count = size(problem.A, 2)
    total_columns = column_count + artificial_count
    objective = Vector{T}(undef, total_columns)
    fill!(@view(objective[1:column_count]), zero(T))
    fill!(@view(objective[column_count + 1:end]), one(T))
    lower = Vector{Bound{T}}(undef, total_columns)
    upper = Vector{Bound{T}}(undef, total_columns)
    copyto!(lower, 1, problem.column_lower, 1, column_count)
    copyto!(upper, 1, problem.column_upper, 1, column_count)
    fill!(@view(lower[column_count + 1:end]), Bound(zero(T)))
    fill!(@view(upper[column_count + 1:end]), Bound{T}(nothing))
    return objective, lower, upper
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
    objective, column_lower, column_upper = _primal_phase_one_vectors(problem, artificial_count)
    phase_problem = LinearProblem{T}(
        _primal_phase_one_matrix(problem.A, artificial_rows, artificial_signs),
        objective,
        zero(T), MIN_SENSE, problem.row_lower, problem.row_upper,
        column_lower, column_upper,
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

function _primal_original_basis(workspace::SimplexWorkspace, column_count::Int,
                                artificial_count::Int)
    artificial_count == 0 &&
        return Basis(workspace.basis.basic_indices, workspace.basis.states)
    basis = workspace.basis
    row_count = size(workspace.problem.A, 1)
    states = Vector{VariableState}(undef, column_count + row_count)
    copyto!(states, 1, basis.states, 1, column_count)
    copyto!(states, column_count + 1, basis.states,
            column_count + artificial_count + 1, row_count)
    indices = Vector{Int}(undef, row_count)
    for row in 1:row_count
        index = basis.basic_indices[row]
        if column_count < index <= column_count + artificial_count
            position = workspace.problem.A.colptr[index]
            original_row = workspace.problem.A.rowval[position]
            replacement = column_count + original_row
            states[replacement] == BASIC && return nothing
            states[replacement] = BASIC
            indices[row] = replacement
        else
            indices[row] = index <= column_count ? index : index - artificial_count
        end
    end
    return Basis(indices, states, Val(:owned))
end

function _solve_continuous_primal(problem::LinearProblem{T}, options::SolverOptions{T};
                                  stop_requested::Function=() -> false,
                                  progress::SimplexProgressContext{T}=
                                      SimplexProgressContext(problem;
                                          numerical_policy=NumericalPolicy(T,options))) where {T}
    stop_requested = _guard_stop_callback(stop_requested)
    workspace = nothing
    try
        workspace, artificial_count, initial = _primal_phase_one(
            problem, options, progress, stop_requested,
        )
        _simplex_event!(workspace, artificial_count > 0 ? :phase_one : :phase_primal)
        # A small phase-I reduced cost can still remove a large violation when
        # its column is small, so dual_tolerance must not suppress it.
        terminal = _primal_optimize!(workspace, stop_requested,
                                     artificial_count > 0 ? zero(T) : options.dual_tolerance)
        terminal.status == OPTIMAL || return _internal_solution(workspace, terminal)
        if artificial_count > 0
            column_count = size(problem.A, 2)
            phase_primal = workspace.primal[1:column_count + artificial_count]
            _original_optimality_certified(workspace, phase_primal) ||
                return _internal_solution(workspace, NUMERICAL_ERROR,
                                          "phase I optimality certificate is inconclusive")
            artificial_sum = sum(workspace.primal[column_count + 1:column_count + artificial_count])
            isfinite(artificial_sum) || return _internal_solution(workspace, _numerical_failure())
            if artificial_sum > options.primal_tolerance
                basic_costs = workspace.costs[workspace.basis.basic_indices]
                dual = _checked_basis_solve!(zeros(T,length(basic_costs)),workspace,
                                             basic_costs,stop_requested;transposed=true)
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
            _restore_original_costs!(workspace)
            recompute!(workspace)
            _simplex_event!(workspace, :phase_primal)
            terminal = _primal_optimize!(workspace, stop_requested)
            terminal.status == OPTIMAL || return _internal_solution(workspace, terminal)
        end
        run = _internal_solution(workspace, OPTIMAL, "optimal solution found")
        if run.status == OPTIMAL && artificial_count > 0
            basis = _primal_original_basis(workspace, column_count, artificial_count)
            return DualRunResult{T}(run.status, run.objective_value,
                                    run.primal[1:size(problem.A, 2)],
                                    run.iterations, run.refactorizations, run.message, basis)
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

# A pivot can preserve a feasible approximate point even when a floating
# factorization reconstructs an infeasible one. Keep the predicted point only
# after independently certifying both original bounds and row consistency.
_legacy_primal_point_candidate(workspace, entering, leaving_row, step, column) = nothing

function _legacy_primal_point_candidate(workspace::SimplexWorkspace{T}, entering::Int,
                                        leaving_row::Int, step::T, column::AbstractVector{T}) where {T}
    T === Float32 || T === Float64 || return nothing
    workspace.options.algorithm == :primal &&
        workspace.options.simplex_strategy == :legacy || return nothing
    policy = workspace.progress.numerical_policy
    (policy.pivot_validation || policy.solve_refinement || policy.recovery ||
     policy.incremental_primal || policy.incremental_primal_pivots ||
     policy.adaptive_refactor || _is_staged_workspace(workspace)) && return nothing
    candidate = _pivot_quality_buffers(workspace).trial
    for (row, index) in enumerate(workspace.basis.basic_indices)
        candidate[row] = row == leaving_row ? workspace.primal[entering] + step :
            workspace.primal[index] - step * column[row]
    end
    return candidate
end

# Bound-feasible reconstructed values can still violate the equations. Probe
# the full stored point, including nonbasic contributions, in its own precision.
# This only triggers the existing certified fallback; an unavailable native
# residual retains the previous behavior rather than escalating precision.
function _legacy_primal_equation_violation(workspace::SimplexWorkspace{T}) where {T<:Union{Float32,Float64}}
    columns = size(workspace.problem.A, 2)
    scratch = _pivot_quality_buffers(workspace).column
    quality = _compensated_solve_quality!(scratch, workspace.problem.A,
        @view(workspace.primal[1:columns]), @view(workspace.primal[(columns + 1):end]),
        workspace.progress.numerical_policy, false)
    return !isnothing(quality) &&
        (!quality.finite || quality.absolute_error > workspace.options.primal_tolerance)
end

_restore_legacy_primal_point!(workspace, ::Nothing, stop) = false

function _restore_legacy_primal_point!(workspace::SimplexWorkspace{T},
                                          candidate::Vector{T}, stop) where {T}
    T === Float32 || T === Float64 || return false
    tolerance = workspace.options.primal_tolerance
    _legacy_primal_reconstruction_feasible(workspace) && return false
    stop() && return false
    computed = _pivot_quality_buffers(workspace).correction
    for (row, index) in enumerate(workspace.basis.basic_indices)
        computed[row] = workspace.primal[index]
        workspace.primal[index] = candidate[row]
    end
    accepted = false
    try
        _finite_workspace(workspace) && primal_infeasibility(workspace) <= tolerance || return false
        columns = size(workspace.problem.A, 2)
        _original_primal_feasible(workspace.problem, workspace.primal[1:columns], tolerance) || return false
        _legacy_primal_row_consistent(workspace, tolerance) || return false
        stop() && return false
        accepted = true
    finally
        if !accepted
            for (row, index) in enumerate(workspace.basis.basic_indices)
                workspace.primal[index] = computed[row]
            end
        end
    end
    copyto!(workspace.scratch.row_solution, candidate)
    _pipeline_changed!(workspace, workspace.scratch.row_solution)
    _simplex_event!(workspace, :primal_point_preserved)
    return true
end

function _legacy_primal_row_consistent(workspace::SimplexWorkspace{T}, tolerance::T) where {T}
    T === Float32 || T === Float64 || return false
    columns = size(workspace.problem.A, 2)
    primal = workspace.primal[1:columns]
    lower, upper = _primal_row_bounds(workspace.problem.A, primal, Val(false))
    activities = Bound.(workspace.primal[(columns + 1):end])
    rows = Int[]
    for row in eachindex(lower)
        _primal_interval_within_bounds(lower[row], upper[row], activities[row],
                                       activities[row], tolerance) || push!(rows, row)
    end
    isempty(rows) && return true
    # Reuse the original-model certificate's exact fallback only when the
    # native enclosure is inconclusive. Solver values remain in their type.
    return _refined_primal_rows_feasible(workspace.problem, primal, tolerance,
                                         rows, activities, activities)
end

# Match the former reconstruction fast path: no extra matrix scan or basis
# solve is required when the reconstructed point already passes this check.
function _legacy_primal_reconstruction_feasible(workspace)
    return all(index -> isfinite(workspace.primal[index]), workspace.basis.basic_indices) &&
        primal_infeasibility(workspace) <= workspace.options.primal_tolerance &&
        !_legacy_primal_equation_violation(workspace)
end

function _legacy_primal_point_certified(workspace)
    tolerance = workspace.options.primal_tolerance
    _finite_workspace(workspace) || return false
    for index in eachindex(workspace.primal)
        value = workspace.primal[index]
        max(_lower_violation(workspace.lower[index], value),
            _upper_violation(workspace.upper[index], value)) <= tolerance || return false
    end
    columns = size(workspace.problem.A, 2)
    return _original_primal_feasible(workspace.problem, workspace.primal[1:columns], tolerance) &&
        _legacy_primal_row_consistent(workspace, tolerance)
end

# Use the complete stored equations, including nonbasic contributions, rather
# than the rounded RHS assembled for reconstruction. Try exactly one correction
# in the model's hardware floating type; failed trials leave the point untouched.
function _try_native_primal_point_correction!(workspace::SimplexWorkspace{T}, stop) where {T<:Union{Float32,Float64}}
    workspace.options.algorithm == :primal &&
        _legacy_primal_row_validation_enabled(workspace) || return false
    stop() && return false
    buffers = _pivot_quality_buffers(workspace)
    columns = size(workspace.problem.A, 2)
    quality = _compensated_solve_quality!(buffers.column, workspace.problem.A,
        @view(workspace.primal[1:columns]), @view(workspace.primal[(columns+1):end]),
        workspace.progress.numerical_policy, false)
    (isnothing(quality) || !quality.finite) && return false
    _simplex_event!(workspace, :correction_attempt)
    stop() && return false
    try
        _timed_simplex(workspace, :ftran) do
            _ordinary_forward_solve!(buffers.correction, workspace.factorization,
                buffers.column.residual)
        end
    catch exception
        _is_numerical_exception(exception) || rethrow()
        return false
    end
    stop() && return false
    all(isfinite, buffers.correction) || return false
    original = buffers.trial
    for (row, index) in enumerate(workspace.basis.basic_indices)
        original[row] = workspace.primal[index]
    end
    accepted = false
    try
        for (row, index) in enumerate(workspace.basis.basic_indices)
            workspace.primal[index] = original[row] + buffers.correction[row]
        end
        _legacy_primal_point_certified(workspace) || return false
        stop() && return false
        accepted = true
    finally
        if !accepted
            for (row, index) in enumerate(workspace.basis.basic_indices)
                workspace.primal[index] = original[row]
            end
        end
    end
    for (row, index) in enumerate(workspace.basis.basic_indices)
        workspace.scratch.row_solution[row] = workspace.primal[index]
    end
    _pipeline_changed!(workspace, workspace.scratch.row_solution)
    _simplex_event!(workspace, :correction)
    _simplex_event!(workspace, :primal_point_corrected)
    return true
end

_finish_legacy_primal_point!(workspace, ::Nothing, stop) = nothing

# A failed prediction is not permission to continue with a bad reconstruction.
# Return a terminal result to all three callers before they can price again.
function _finish_legacy_primal_point!(workspace::SimplexWorkspace, candidate::Vector, stop)
    stop() && return DualTermination(TIME_LIMIT, "time limit reached during primal point recovery")
    _legacy_primal_reconstruction_feasible(workspace) && return nothing
    _restore_legacy_primal_point!(workspace, candidate, stop) && return nothing
    _try_native_primal_point_correction!(workspace, stop) && return nothing
    stop() && return DualTermination(TIME_LIMIT, "time limit reached during primal point recovery")
    # Candidate retries assume an unchanged, feasible basis point. This failure
    # invalidates that assumption, including after a fresh-factor retry.
    workspace.scratch.selected_row = 0
    return DualTermination(NUMERICAL_ERROR, "primal point could not be certified")
end

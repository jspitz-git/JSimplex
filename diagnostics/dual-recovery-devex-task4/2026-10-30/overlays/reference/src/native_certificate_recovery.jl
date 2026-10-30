# A terminal native point can satisfy stored basic bounds while accumulated
# equation error violates the original model. Try one working-type FTRAN on
# a private full point; the caller must still certify original feasibility,
# optimality and the corrected objective before exporting any result.
_native_terminal_primal_candidate(workspace, stop) = nothing
function _native_terminal_primal_candidate(workspace::SimplexWorkspace{T}, stop) where {T<:Union{Float32,Float64}}
    policy = workspace.progress.numerical_policy
    (workspace.options.algorithm == :dual && _legacy_primal_row_validation_enabled(workspace) &&
     policy.max_refinements > 0 && rounding(T) == RoundNearest && !get_zero_subnormals()) || return nothing
    stop() && return nothing
    rows, columns = size(workspace.problem.A)
    scratch = SolveQualityScratch(T, rows)
    quality = _compensated_solve_quality!(scratch, workspace.problem.A,
        @view(workspace.primal[1:columns]), @view(workspace.primal[(columns+1):end]),
        policy, false)
    (isnothing(quality) || !quality.finite || iszero(quality.absolute_error) || stop()) && return nothing
    # The leading accumulator is dead after residual construction; keep the
    # correction separate from the residual without another vector allocation.
    correction = scratch.work_residual
    try
        _timed_simplex(workspace, :ftran) do
            _ordinary_forward_solve!(correction, workspace.factorization, scratch.residual)
        end
    catch exception
        _is_numerical_exception(exception) || rethrow()
        return nothing
    end
    all(isfinite, correction) && !stop() || return nothing
    trial = copy(workspace.primal)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        trial[index] += correction[row]
    end
    all(isfinite, trial) && _within_primal_bounds(trial, workspace.lower, workspace.upper,
        workspace.options.primal_tolerance) && !stop() || return nothing
    # No observer or callback occurs inside this private correction. In
    # particular, no validity result is carried across new caller code.
    return trial
end

# The terminal certificate is stricter than incremental pricing: basic reduced
# costs must also vanish. Correct a failed native witness without changing the
# basis, working costs, primal point, or the certificate's absolute tolerances.
_try_native_certificate_recovery(workspace, primal, dual, stop) = false
function _try_native_certificate_recovery(workspace::SimplexWorkspace{T},
                                           primal::Vector{T}, dual::Vector{T}, stop) where {T<:Union{Float32,Float64}}
    policy = workspace.progress.numerical_policy
    # The checked solve already used its refinement budget in the witness path.
    (policy.solve_refinement || policy.max_refinements == 0 || stop()) && return false
    B = _basis_matrix!(workspace)
    n = size(workspace.problem.A, 2)
    rhs = T[index <= n ? workspace.problem.objective[index] : zero(T)
            for index in workspace.basis.basic_indices]
    scratch = SolveQualityScratch(T, length(rhs))
    quality = _compensated_solve_quality!(scratch, B, dual, rhs, policy, true)
    (isnothing(quality) || !quality.finite || iszero(quality.absolute_error) || stop()) && return false
    _simplex_event!(workspace, :correction_attempt)
    correction = _timed_simplex(workspace, :btran) do
        transpose_solve(workspace.factorization, scratch.residual)
    end
    all(isfinite, correction) || return false
    trial = dual + correction
    all(isfinite, trial) && !stop() || return false
    # One private working-precision correction is enough to test this repair.
    # The full independent check, including nonbasic complementarity, decides
    # acceptance; neither a small relative residual nor cached prices suffice.
    _original_witness_certified(workspace.problem, workspace.options,
        workspace.basis, primal, trial) && !stop() || return false
    _simplex_event!(workspace, :certificate_corrected)
    return true
end

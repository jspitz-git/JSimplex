# A failed legacy residual check need not discard an otherwise useful updated
# factor. Try bounded corrections in the problem's hardware floating type and
# publish only a vector that passes the original legacy acceptance test.
_try_native_dual_correction!(workspace, destination, index, leaving_row, stop;
                             transposed=false) = false

function _try_native_dual_correction!(workspace::SimplexWorkspace{T}, destination::Vector{T},
                                     index::Int, leaving_row::Int, stop;
                                     transposed::Bool=false) where {T}
    T === Float32 || T === Float64 || return false
    workspace.options.simplex_strategy == :legacy || return false
    policy = workspace.progress.numerical_policy
    (policy.pivot_validation || policy.solve_refinement || policy.recovery ||
     policy.adaptive_refactor) && return false
    policy.max_refinements > 0 || return false
    stop() && return false
    buffers = _pivot_quality_buffers(workspace)
    rhs = buffers.rhs
    fill!(rhs, zero(T))
    if transposed
        rhs[index] = one(T)
    else
        A = workspace.problem.A
        if index <= size(A, 2)
            for p in nzrange(A, index)
                rhs[A.rowval[p]] = A.nzval[p]
            end
        else
            rhs[index - size(A, 2)] = -one(T)
        end
    end
    B = _basis_matrix!(workspace)
    scratch = transposed ? buffers.row : buffers.column
    trial = copyto!(buffers.trial, destination)
    for _ in 1:policy.max_refinements
        stop() && return false
        # Calling the native enclosure directly avoids its arbitrary-precision
        # fallback. An ambiguous or exceptional residual retains refactorization.
        quality = _compensated_solve_quality!(scratch, B, trial, rhs, policy, transposed)
        (isnothing(quality) || !quality.finite) && return false
        _simplex_event!(workspace, :correction_attempt)
        try
            _timed_simplex(workspace, transposed ? :btran : :ftran) do
                transposed ? transpose_solve!(buffers.correction, workspace.factorization, scratch.residual) :
                             forward_solve!(buffers.correction, workspace.factorization, scratch.residual)
            end
        catch exception
            _is_numerical_exception(exception) || rethrow()
            return false
        end
        all(isfinite, buffers.correction) || return false
        for i in eachindex(trial)
            trial[i] += buffers.correction[i]
        end
        all(isfinite, trial) || return false
        accepted = if transposed
            _dual_row_residual_ratio(workspace, trial, leaving_row) <= one(T)
        else
            copyto!(workspace.scratch.row_rhs, rhs)
            _pipeline_changed!(workspace, workspace.scratch.row_rhs)
            pivot = trial[leaving_row]
            tolerance = max(workspace.options.zero_tolerance, sqrt(eps(one(T))) * abs(pivot))
            # Correcting a direction must not silently validate a different
            # ratio decision. A disagreeing row needs the existing full retry.
            abs(pivot) > workspace.options.zero_tolerance &&
                abs(pivot - workspace.scratch.tableau_row[index]) <= tolerance &&
                _dual_direction_residual_ok!(workspace, trial, pivot)
        end
        if accepted
            stop() && return false
            copyto!(destination, trial)
            _pipeline_changed!(workspace, destination)
            workspace.scratch.refactorization.residual_bad = true
            _simplex_event!(workspace, :correction)
            return true
        end
    end
    return false
end

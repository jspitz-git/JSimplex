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

function _presolve_tolerance_model(problem::LinearProblem{T}, tolerance::T) where {T}
    m, n = size(problem.A)
    # Represent x=z+e, with z inside the original column bounds and |e|<=tol.
    # A separate row error allows |A*x-clamp(A*x,row bounds)|<=tol. Keeping
    # these errors separate avoids rounding a tiny allowance into a huge bound.
    negative, _ = _primal_difference_bounds(zero(T), tolerance)
    error_lower = isfinite(negative) ? Bound(negative) : _unbounded_bound(T)
    error_upper = Bound(tolerance)
    matrix = hcat(problem.A, problem.A, spdiagm(0=>ones(T, m)))
    return LinearProblem{T}(
        matrix, zeros(T, 2n+m), zero(T), MIN_SENSE,
        problem.row_lower, problem.row_upper,
        vcat(problem.column_lower, fill(error_lower, n+m)),
        vcat(problem.column_upper, fill(error_upper, n+m)),
        fill(CONTINUOUS, 2n+m), problem.name, problem.row_names, String[])
end

function _presolve_for_solve(problem::LinearProblem{T}, tolerance::T;
                             stop_requested=()->false, verbose::Bool=false) where {T}
    result = presolve_problem(problem)
    (!(result isa PresolveFailure) || result.status != INFEASIBLE || iszero(tolerance)) &&
        return result
    stop_requested() && return identity_presolve(problem)
    # A contradiction in a reduced row has different units after elimination.
    # Recheck only infeasibility on the tolerance envelope of ORIGINAL bounds.
    # This model is never optimized and its reductions never reach postsolve.
    proof = _presolve_tolerance_model(problem, tolerance)
    stop_requested() && return identity_presolve(problem)
    verified = presolve_problem(proof)
    verified isa PresolveFailure && verified.status == INFEASIBLE && return result
    verbose && @info "Presolve infeasibility is inconclusive at primal tolerance; retaining original LP"
    return identity_presolve(problem)
end

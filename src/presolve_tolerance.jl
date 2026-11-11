function _presolve_tolerance_model(problem::LinearProblem{T}, tolerance::T) where {T}
    m, n = size(problem.A)
    # Represent x=z+e, with z inside the original column bounds and |e|<=tol.
    # A separate row error allows |A*x-clamp(A*x,row bounds)|<=tol. Keeping
    # these errors separate avoids rounding a tiny allowance into a huge bound.
    negative, _ = _primal_difference_bounds(zero(T), tolerance)
    error_lower = isfinite(negative) ? Bound(negative) : _unbounded_bound(T)
    error_upper = Bound(tolerance)
    matrix = hcat(problem.A, problem.A, spdiagm(0=>ones(T, m)))
    return _presolve_model(Val(2499),
        matrix, zeros(T, 2n+m), zero(T), MIN_SENSE,
        problem.row_lower, problem.row_upper,
        vcat(problem.column_lower, fill(error_lower, n+m)),
        vcat(problem.column_upper, fill(error_upper, n+m)),
        fill(CONTINUOUS, 2n+m), problem.name, problem.row_names, String[])
end

function _presolve_base_for_solve(problem::LinearProblem{T}, tolerance::T;
                             stop_requested=()->false, verbose::Bool=false,
                             history=nothing, rounded_costs::Bool=false) where {T}
    return _history_transaction(history) do
        result = presolve_problem(problem; directed_bounds=tolerance > zero(T),history,rounded_costs)
        (!(result isa PresolveFailure) || result.status != INFEASIBLE || iszero(tolerance)) &&
            return result
        stop_requested() && return identity_presolve(problem)
        # A contradiction in a reduced row has different units after elimination.
        # Recheck only infeasibility on the tolerance envelope of ORIGINAL bounds.
        # This model is never optimized and its reductions never reach postsolve.
        proof = _presolve_tolerance_model(problem, tolerance)
        stop_requested() && return identity_presolve(problem)
        verified = presolve_problem(proof; directed_bounds=false,strict_objective=true)
        verified isa PresolveFailure && verified.status == INFEASIBLE && return result
        verbose && @info "Presolve infeasibility is inconclusive at primal tolerance; retaining original LP"
        return identity_presolve(problem)
    end
end

function _presolve_for_solve_cached_body(problem::LinearProblem{T}, tolerance::T;
                             stop_requested=()->false, verbose::Bool=false,
                             history=nothing) where T
    rounded_costs = T in (Float32,Float64) && tolerance > zero(T)
    # A callback may signal only once. Preserve that request across the base
    # presolve, its infeasibility proof, and the optional inequality pass.
    stopped = Ref(false)
    poll() = stopped[] || (stopped[] = stop_requested())
    base = _presolve_base_for_solve(problem,tolerance;stop_requested=poll,verbose,history,rounded_costs)
    return _augment_inequalities(base,problem,tolerance,history,poll,verbose;rounded_costs)
end

function _presolve_for_solve(problem::LinearProblem{T},tolerance::T;
                             stop_requested=()->false,verbose::Bool=false,history=nothing) where T
    return _PresolveWork.with_session(T) do
        _presolve_for_solve_cached_body(problem,tolerance;stop_requested,verbose,history)
    end
end

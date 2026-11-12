@enum _PostsolveBasisState begin
    _POSTSOLVE_ACCEPTED
    _POSTSOLVE_PARTIAL
    _POSTSOLVE_REJECTED
    _POSTSOLVE_STOPPED
end

# Installing a completed auxiliary basis is still original-model
# reconstruction, not acceptance of the auxiliary objective or its prices.
function _install_postsolve_basis!(ws,run,stop)
    ws.basis=Basis(run.basis.basic_indices,run.basis.states)
    recompute!(ws;refactorize=true,caller_guard=stop)
    stop() && return false
    _finite_workspace(ws) || return false
    infeasibility=primal_infeasibility(ws)
    if infeasibility>ws.options.primal_tolerance
        _try_native_cleanup_recompute!(ws,stop) || return false
        stop() && return false
        _finite_workspace(ws) || return false
        infeasibility=primal_infeasibility(ws)
    end
    return infeasibility<=ws.options.primal_tolerance &&
        _original_primal_feasible(ws.problem,ws.primal[1:size(ws.problem.A,2)],
                                 ws.options.primal_tolerance)
end

"""Construction outcome, never a certificate for the original objective.

PARTIAL retains valid exchanges but does not assert primal feasibility. Only
ACCEPTED can be exposed through the historical Int/nothing projection wrapper.
The caller must discard a rejected/stopped construction, or explicitly complete
and certify a partial one before optimizing the original objective.
"""
struct _PostsolveBasisResult
    state::_PostsolveBasisState
    exchanges::Int
end

function _postsolve_partial_allowed(ws::SimplexWorkspace{T}) where T
    policy=ws.progress.numerical_policy
    return T <: Union{Float32,Float64} && _native_primal_kernel(policy) &&
        ws.options.simplex_strategy==:legacy && !policy.precision_boosting &&
        !policy.lp_refinement && !_is_staged_workspace(ws)
end

function _postsolve_partial_result(ws,exchanges,stop)
    stop() && return _PostsolveBasisResult(_POSTSOLVE_STOPPED,exchanges)
    state=_postsolve_partial_allowed(ws) && _finite_workspace(ws) &&
        _original_bounds_active(ws) ? _POSTSOLVE_PARTIAL : _POSTSOLVE_REJECTED
    return _PostsolveBasisResult(state,exchanges)
end

function _postsolve_feasibility_problem(p::LinearProblem{T}) where T
    # All arrays are fresh, including each CSC buffer. Unlike the diagnostic
    # prototype, this transfers actual ownership, with no borrowed-matrix tag
    # or constraint on future matrix readers/writers. Exactly one CSC copy.
    return LinearProblem{T}(copy(p.A),zeros(T,length(p.objective)),zero(T),MIN_SENSE,
        copy(p.row_lower),copy(p.row_upper),copy(p.column_lower),copy(p.column_upper),
        copy(p.variable_domains),p.name,copy(p.row_names),copy(p.column_names),Val(:presolve_owned))
end

"""One owned zero-objective feasibility phase, within the owner's total budget.

Never installs an uncertified auxiliary basis in the owner. On every exit,
including observer exceptions, only completed-work counters are inherited.
The caller owns restoration/fallback; this helper never calls cleanup_original.
"""
function _complete_postsolve_basis!(owner::SimplexWorkspace{T},stop) where T
    _postsolve_partial_allowed(owner) ||
        return _phase_result(owner,NUMERICAL_ERROR,"partial postsolve recovery is unsupported by this policy")
    guard=_guard_stop_callback(stop)
    guard() && return _phase_result(owner,TIME_LIMIT,"stopped before postsolve feasibility")
    owner.iterations<owner.options.iteration_limit ||
        return _phase_result(owner,ITERATION_LIMIT,"iteration limit reached before postsolve feasibility")
    _original_bounds_active(owner) ||
        return _phase_result(owner,NUMERICAL_ERROR,"postsolve feasibility requires original bounds")
    auxiliary=_postsolve_feasibility_problem(owner.problem)
    pr=owner.progress
    progress=SimplexProgressContext(auxiliary;start_ns=pr.start_ns,diagnostics=pr.diagnostics,
        numerical_policy=pr.numerical_policy,iteration_offset=pr.iteration_offset,
        refactorization_offset=pr.refactorization_offset)
    phase=nothing
    try
        # Skip reconstruction of the unused default slack point. The state
        # constructor still owns its initial factor; replacement is refactored
        # and checked before the unchanged dual driver may use it.
        phase=_initialize_workspace_state(auxiliary,owner.options;progress)
        phase.basis=Basis(owner.basis.basic_indices,owner.basis.states)
        phase.iterations=owner.iterations
        phase.refactorizations+=owner.refactorizations
        recompute!(phase;refactorize=true,caller_guard=guard)
        finite=_finite_workspace(phase)
        reliable=finite && _recomputed_basis_reliable(phase)
        if finite && !reliable
            _try_native_cleanup_recompute!(phase,guard) ||
                return _phase_result(phase,NUMERICAL_ERROR,"postsolve feasibility basis correction failed")
            finite=_finite_workspace(phase)
            reliable=finite && _recomputed_basis_reliable(phase)
        end
        finite && reliable ||
            return _phase_result(phase,NUMERICAL_ERROR,"postsolve feasibility basis quality rejected")
        run=_solve_continuous_dual!(phase,guard)
        # The real auxiliary driver performs its original certificate. Its
        # OPTIMAL alone is insufficient to accept an original-model point.
        if run.status==OPTIMAL && (isnothing(run.primal) || isnothing(run.basis) ||
           !_original_primal_feasible(owner.problem,run.primal,owner.options.primal_tolerance))
            return _phase_result(phase,NUMERICAL_ERROR,"postsolve feasibility failed original primal validation")
        end
        return run
    finally
        if !isnothing(phase)
            owner.iterations=max(owner.iterations,phase.iterations)
            owner.refactorizations=max(owner.refactorizations,phase.refactorizations)
        end
    end
end

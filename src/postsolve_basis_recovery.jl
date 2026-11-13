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

# A singular provisional hint is not a certificate that the original LP is
# singular. Unsupported arithmetic/backends retain the historical failure path.
_repair_postsolve_hint(owner,target,stop) = nothing

"""Bounded, private replacement of weak columns in a failed postsolve hint.

The unchecked LU only selects proposals; it is never installed in the live
factorization. Acceptance requires the manager's normal refactorization and
the unchanged primal/dual solve-quality checks. This does not certify a point
or the objective: construction, cleanup and original certification follow.
On failure/exception only completed-work counters are inherited by the owner.
"""
function _repair_postsolve_hint(owner::SimplexWorkspace{Float64},target,stop)
    _postsolve_partial_allowed(owner) && owner.options.basis_refactorization==:native &&
        _original_bounds_active(owner) || return nothing
    length(target)==size(owner.problem.A,2) && all(isfinite,target) || return nothing
    guard=_guard_stop_callback(stop)
    guard() && return nothing
    owner.iterations<owner.options.iteration_limit || return nothing
    trial=nothing
    try
        trial=_initialize_workspace_state(owner.problem,owner.options;progress=owner.progress)
        trial.iterations=owner.iterations
        trial.refactorizations=owner.refactorizations
        trial.basis=Basis(owner.basis.basic_indices,owner.basis.states)
        indices=trial.basis.basic_indices
        states=trial.basis.states
        m,n=size(owner.problem.A)
        values=vcat(target,owner.problem.A*target)
        all(isfinite,values) || return nothing
        selected=falses(n+m)
        selected[indices].=true
        factor_ready=false
        for attempt in 1:owner.progress.numerical_policy.max_pivot_candidates
            guard() && return nothing
            _simplex_event!(trial,:postsolve_hint_attempt)
            B=_basis_matrix!(trial)
            f=lu(B;check=false)
            guard() && return nothing
            U=f.U
            weak=Int[]
            # A scale-relative proposal heuristic, never an acceptance tolerance.
            for column in 1:m
                magnitude=0.0
                for k in nzrange(U,column)
                    magnitude=max(magnitude,abs(U.nzval[k]))
                end
                abs(U[column,column])<=sqrt(eps(Float64))*magnitude && push!(weak,column)
            end
            if isempty(weak)
                factor_ready || return nothing
                # Roundoff in a now usable basis can still need the existing
                # terminal native reconstruction. No new refinement budget.
                _try_native_cleanup_recompute!(trial,guard) || return nothing
                guard() && return nothing
                _finite_workspace(trial) && _recomputed_basis_reliable(trial) || return nothing
                guard() && return nothing
                _simplex_event!(trial,:postsolve_hint_repaired)
                guard() && return nothing
                return trial
            end
            rows=f.p
            slots=f.q[weak]
            removed=indices[slots]
            selected[removed].=false
            cursor=1
            for (slot,k) in zip(slots,weak)
                row=rows[k]
                if selected[n+row]
                    while cursor<=m && selected[n+cursor]
                        cursor+=1
                    end
                    cursor<=m || return nothing
                    row=cursor
                end
                indices[slot]=n+row
                selected[n+row]=true
            end
            for index in removed
                selected[index] && continue
                lower,upper=trial.lower[index],trial.upper[index]
                states[index]=if isfinite(lower) && isfinite(upper)
                    abs(values[index]-bound_value(lower))<=abs(values[index]-bound_value(upper)) ? AT_LOWER : AT_UPPER
                elseif isfinite(lower)
                    AT_LOWER
                elseif isfinite(upper)
                    AT_UPPER
                else
                    FREE_NONBASIC
                end
            end
            for slot in slots
                states[indices[slot]]=BASIC
            end
            factor_ready=false
            guard() && return nothing
            try
                recompute!(trial;refactorize=true,caller_guard=guard)
                factor_ready=true
                guard() && return nothing
                if _finite_workspace(trial) && _recomputed_basis_reliable(trial)
                    guard() && return nothing
                    _simplex_event!(trial,:postsolve_hint_repaired)
                    guard() && return nothing
                    return trial
                end
            catch exception
                exception === guard.exception && rethrow()
                _is_numerical_exception(exception) || rethrow()
            end
        end
        return nothing
    finally
        if !isnothing(trial)
            owner.iterations=max(owner.iterations,trial.iterations)
            owner.refactorizations=max(owner.refactorizations,trial.refactorizations)
        end
    end
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

"""Owned column maps for a sum-of-artificials auxiliary problem.

A zero entry in `phase_to_original` identifies an artificial column.
"""
struct PhaseOneMap
    original_to_phase::Vector{Int}
    phase_to_original::Vector{Int}
    artificial_columns::Vector{Int}
end

function _phase_options(o::SolverOptions{T,M,R},algorithm::Symbol) where {T,M,R}
    return SolverOptions{T,M,R}(o.primal_tolerance,o.dual_tolerance,o.zero_tolerance,
        o.iteration_limit,o.time_limit,o.refactorization_interval,o.verbose,o.log_level,
        algorithm,o.pricing,o.basis_update,o.basis_refactorization,o.scaling,o.presolve,
        o.simplex_strategy)
end

function _phase_inherit_work!(destination,source)
    destination.iterations = max(destination.iterations,source.iterations)
    destination.refactorizations = max(destination.refactorizations,source.refactorizations)
    return nothing
end

function _phase_refactor!(ws,owner,stop)
    stop = _guard_stop_callback(stop)
    stop() && throw(_UnreliableBasisSolve())
    before = ws.refactorizations
    try
        recompute!(ws;refactorize=true,caller_guard=stop)
    finally
        ws.refactorizations = max(before+1,ws.refactorizations)
        _phase_inherit_work!(owner,ws)
    end
    return nothing
end

function _phase_one_workspace(ws::SimplexWorkspace{T},policy,stop) where T
    return _with_recovery_precision(ws,ws) do
        m,n = size(ws.problem.A)
        rows,signs,states = Int[],T[],VariableState[]
        for (r,j) in enumerate(ws.basis.basic_indices)
            stop() && throw(_UnreliableBasisSolve())
            if _lower_violation(ws.lower[j],ws.primal[j]) > ws.options.primal_tolerance
                push!(rows,r);push!(signs,-one(T));push!(states,AT_LOWER)
            elseif _upper_violation(ws.upper[j],ws.primal[j]) > ws.options.primal_tolerance
                push!(rows,r);push!(signs,one(T));push!(states,AT_UPPER)
            end
        end
        k = length(rows)
        forward = vcat(collect(1:n),collect(n+k+1:n+k+m))
        backward = vcat(collect(1:n),zeros(Int,k),collect(n+1:n+m))
        map = PhaseOneMap(forward,backward,collect(n+1:n+k))
        # Copy CSC columns directly. No dense m-by-k artificial matrix is needed.
        ptr,indices,values = copy(ws.problem.A.colptr),copy(ws.problem.A.rowval),copy(ws.problem.A.nzval)
        for (i,r) in enumerate(rows)
            stop() && throw(_UnreliableBasisSolve())
            j = ws.basis.basic_indices[r]
            if j <= n
                for p in nzrange(ws.problem.A,j)
                    push!(indices,ws.problem.A.rowval[p]);push!(values,signs[i]*ws.problem.A.nzval[p])
                end
            else
                push!(indices,j-n);push!(values,-signs[i])
            end
            push!(ptr,length(values)+1)
        end
        A = SparseMatrixCSC(m,n+k,ptr,indices,values)
        costs,lower,upper = _primal_phase_one_vectors(ws.problem,k)
        problem = LinearProblem{T}(A,costs,zero(T),MIN_SENSE,
            copy(ws.problem.row_lower),copy(ws.problem.row_upper),lower,upper,
            fill(CONTINUOUS,n+k),ws.problem.name,String[],String[])
        stop() && throw(_UnreliableBasisSolve())
        phase = initialize_workspace(problem,_phase_options(ws.options,:primal);progress=ws.progress)
        _phase_inherit_work!(phase,ws)
        phase.basis = Basis(forward[ws.basis.basic_indices],
            vcat(ws.basis.states[1:n],fill(AT_LOWER,k),ws.basis.states[n+1:end]),Val(:owned))
        for (i,r) in enumerate(rows)
            phase.basis.states[forward[ws.basis.basic_indices[r]]] = states[i]
            phase.basis.states[n+i] = BASIC
            phase.basis.basic_indices[r] = n+i
        end
        _install_driver_policy!(phase,policy)
        _phase_refactor!(phase,ws,stop)
        _finite_workspace(phase) && _recomputed_basis_reliable(phase) && _start_primal_feasible(phase) ||
            throw(_UnreliableBasisSolve())
        reset_devex!(phase)
        return phase,map
    end
end

# Adopt fresh original-dimension numerical state. Progress, model identity,
# options and monotonically consumed work belong to the original caller.
function _adopt_phase_basis!(ws,fresh)
    ws.costs=fresh.costs;ws.lower=fresh.lower;ws.upper=fresh.upper
    ws.basis=fresh.basis;ws.primal=fresh.primal;ws.reduced_costs=fresh.reduced_costs
    ws.pricing_weights=fresh.pricing_weights;ws.devex_reference=fresh.devex_reference
    ws.factorization=fresh.factorization;ws.scratch=fresh.scratch
    ws.perturbed=fresh.perturbed;ws.zero_dual_step_streak=fresh.zero_dual_step_streak
    ws.dual_pricing_fallback=fresh.dual_pricing_fallback
    ws.dual_devex_fallback=fresh.dual_devex_fallback
    ws.dual_refactorization_interval=fresh.dual_refactorization_interval
    ws.dual_recent_repairs=fresh.dual_recent_repairs;ws.dual_bad_update_min=fresh.dual_bad_update_min
    ws.dual_stable_refactorizations=fresh.dual_stable_refactorizations
    ws.dual_nonzero_steps_since_refactorization=fresh.dual_nonzero_steps_since_refactorization
    _phase_inherit_work!(ws,fresh)
    return nothing
end

function _remove_artificials!(phase::SimplexWorkspace{T},map,original,policy,stop) where T
    m = length(phase.basis.basic_indices)
    rhs,column,unit,rho = zeros(T,m),zeros(T,m),zeros(T,m),zeros(T,m)
    prices = zeros(T,length(phase.basis.states))
    for row in 1:m
        leaving = phase.basis.basic_indices[row]
        map.phase_to_original[leaving] != 0 && continue
        stop() && return false
        phase.iterations < phase.options.iteration_limit || return false
        abs(phase.primal[leaving]) <= phase.options.primal_tolerance || return false
        fill!(unit,zero(T));unit[row]=one(T)
        _checked_basis_solve!(rho,phase,unit,stop;transposed=true)
        # One independent sparse column scan avoids an m-vector dot product
        # for every possible original entering column.
        _csc_price!(prices,phase.problem.A,rho)
        # Original fixed and free columns are eligible for a zero-step exchange.
        entering = 0
        strength = zero(T)
        for j in map.original_to_phase
            stop() && return false
            phase.basis.states[j] == BASIC && continue
            candidate = abs(prices[j])
            if candidate > strength
                _pivot_column!(rhs,phase,j)
                _checked_basis_solve!(column,phase,rhs,stop)
                abs(column[row]) > policy.pivot_error_tolerance*maximum(abs,column;init=zero(T)) || continue
                proposal = PivotCandidate(j,row,prices[j],column,rho)
                validate_pivot!(phase,proposal,policy) == :accept || continue
                entering,strength = j,candidate
            end
        end
        entering == 0 && return false
        _pivot_column!(rhs,phase,entering)
        _checked_basis_solve!(column,phase,rhs,stop)
        validate_pivot!(phase,PivotCandidate(entering,row,dot(rho,rhs),column,rho),policy) == :accept || return false
        movement = phase.primal[leaving]/column[row]
        stop() && return false
        replace_column!(phase.factorization,column,row;zero_tolerance=zero(T))
        _finite_updated_factor(phase.factorization) || return false
        _prepare_primal_candidate!(phase,entering,one(T),movement,column,row,AT_LOWER) || return false
        phase.basis.basic_indices[row]=entering
        phase.basis.states[entering]=BASIC;phase.basis.states[leaving]=AT_LOWER
        phase.iterations += 1
        _phase_inherit_work!(original,phase)
        _invalidate_basis_checkpoints!(phase)
        # A tiny artificial is not exactly zero. Recompute the actual exchange
        # and require feasible original bounds before declaring it removable.
        _phase_refactor!(phase,original,stop)
        _finite_workspace(phase) && _recomputed_basis_reliable(phase) && _start_primal_feasible(phase) || return false
        _simplex_event!(phase,:artificial_removed)
    end
    stop() && return false
    states = phase.basis.states[map.original_to_phase]
    indices = map.phase_to_original[phase.basis.basic_indices]
    all(>(0),indices) || return false
    fresh = initialize_workspace(original.problem,original.options;progress=original.progress)
    _phase_inherit_work!(fresh,phase)
    fresh.basis=Basis(indices,states,Val(:owned))
    _phase_refactor!(fresh,original,stop)
    stop() && return false
    _finite_workspace(fresh) && _recomputed_basis_reliable(fresh) && _start_primal_feasible(fresh) || return false
    _original_primal_feasible(fresh,fresh.primal[1:size(fresh.problem.A,2)]) || return false
    reset_devex!(fresh)
    _adopt_phase_basis!(original,fresh)
    return true
end

"""Eliminate basic artificials by validated exchanges before mapping the basis.

Failure leaves the original workspace's numerical state intact and retains all
consumed work. The auxiliary workspace is private and may be discarded.
"""
function remove_artificials!(phase,map,original,policy,stop)::Bool
    guard = _guard_stop_callback(stop)
    try
        return _with_recovery_precision(phase,phase) do
            _remove_artificials!(phase,map,original,policy,guard)
        end
    catch exception
        exception === guard.exception && rethrow()
        _crash_numerical_exception(exception) || rethrow()
        return false
    finally
        _phase_inherit_work!(original,phase)
    end
end

_phase_result(ws::SimplexWorkspace{T},status,message) where T =
    DualRunResult{T}(status,nothing,nothing,ws.iterations,ws.refactorizations,message,
        Basis(ws.basis.basic_indices,ws.basis.states))

function _run_phase_one!(ws::SimplexWorkspace{T},budget::SimplexRunBudget,
                        policy::NumericalPolicy{T},stop)::DualRunResult{T} where T
    stopped = Ref(false)
    guard = _guard_stop_callback(()->(stopped[] = stopped[] || _budget_expired(budget) || stop()))
    original_options = ws.options
    phase = nothing
    try
        _install_driver_policy!(ws,policy;start_ns=budget.start_ns)
        ws.iterations=max(ws.iterations,budget.iterations-ws.progress.iteration_offset)
        ws.refactorizations=max(ws.refactorizations,budget.refactorizations-ws.progress.refactorization_offset)
        limit=max(0,budget.iteration_limit-ws.progress.iteration_offset)
        ws.options=_remaining_options(ws.options;iterations=max(0,ws.options.iteration_limit-limit),
            time_limit=min(ws.options.time_limit,budget.time_limit_seconds))
        guard() && return _phase_result(ws,TIME_LIMIT,"time limit reached before phase I")
        _restore_original_costs!(ws)
        ws.perturbed=false
        _original_bounds_active(ws) || return _phase_result(ws,NUMERICAL_ERROR,"phase I requires original bounds or an owned perturbation journal")
        recompute!(ws;caller_guard=guard)
        guard() && return _phase_result(ws,TIME_LIMIT,"time limit reached during phase I initialization")
        _start_primal_feasible(ws) && _recomputed_basis_reliable(ws) &&
            return _phase_result(ws,OPTIMAL,"original basis is primal feasible")
        ws.iterations < ws.options.iteration_limit || return _phase_result(ws,ITERATION_LIMIT,"iteration limit reached before phase I")
        phase,map = try
            _phase_one_workspace(ws,policy,guard)
        catch exception
            exception === guard.exception && rethrow()
            _crash_numerical_exception(exception) || rethrow()
            guard() && return _phase_result(ws,TIME_LIMIT,"time limit reached during phase I construction")
            # A failed general-basis extension gets one verified slack fallback.
            slack=initialize_workspace(ws.problem,ws.options;progress=ws.progress)
            _phase_inherit_work!(slack,ws)
            try
                _phase_one_workspace(slack,policy,guard)
            finally
                _phase_inherit_work!(ws,slack)
            end
        end
        _simplex_event!(phase,:phase_one)
        terminal=_run_original_objective_terminal!(phase,budget,policy,guard;
            reduced_cost_tolerance=zero(T),allow_auxiliary=Val(false),phase_perturbations=true)
        _phase_inherit_work!(ws,phase)
        guard() && return _phase_result(ws,TIME_LIMIT,"time limit reached during phase I optimization")
        terminal.status == OPTIMAL || return _phase_result(ws,terminal.status,terminal.message)
        n=size(phase.problem.A,2)
        _original_optimality_certified(phase,phase.primal[1:n]) ||
            return _phase_result(ws,NUMERICAL_ERROR,"phase I optimality certificate is inconclusive")
        guard() && return _phase_result(ws,TIME_LIMIT,"time limit reached during phase I certification")
        artificial_sum=sum(phase.primal[map.artificial_columns])
        isfinite(artificial_sum) || return _phase_result(ws,NUMERICAL_ERROR,"non-finite artificial sum")
        if artificial_sum > ws.options.primal_tolerance
            dual=_checked_basis_solve!(zeros(T,length(phase.basis.basic_indices)),phase,
                phase.costs[phase.basis.basic_indices],guard;transposed=true)
            certified=all(isfinite,dual) && _primal_infeasibility_certified(ws,dual)
            guard() && return _phase_result(ws,TIME_LIMIT,"time limit reached during phase I certification")
            return _phase_result(ws,certified ? INFEASIBLE : NUMERICAL_ERROR,
                certified ? "phase I optimum certifies original infeasibility" : "phase I infeasibility certificate is inconclusive")
        end
        removed=remove_artificials!(phase,map,ws,policy,guard)
        guard() && return _phase_result(ws,TIME_LIMIT,"time limit reached during artificial removal")
        if !removed
            status=phase.iterations >= phase.options.iteration_limit ? ITERATION_LIMIT : NUMERICAL_ERROR
            return _phase_result(ws,status,"artificial removal could not be completed")
        end
        _simplex_event!(ws,:phase_primal)
        return _phase_result(ws,OPTIMAL,"phase I established an original-model feasible basis")
    catch exception
        if exception === guard.exception
            stop isa _StopCallback && (stop.exception=exception)
            rethrow()
        end
        _crash_numerical_exception(exception) || rethrow()
        !isnothing(phase) && _phase_inherit_work!(ws,phase)
        return _phase_result(ws,guard() ? TIME_LIMIT : NUMERICAL_ERROR,"phase I numerical construction or removal failed")
    finally
        !isnothing(phase) && _phase_inherit_work!(ws,phase)
        _sync_run_budget!(budget,ws)
        ws.options=original_options
    end
end

"""Find an original-model feasible basis within the caller's shared budget.

OPTIMAL here certifies auxiliary feasibility only: the caller must still solve
and certify the original objective. No original objective/primal result is returned.
"""
function run_phase_one!(ws::SimplexWorkspace{T},budget::SimplexRunBudget,
                        policy::NumericalPolicy{T},stop)::DualRunResult{T} where T
    _install_driver_policy!(ws,policy;start_ns=budget.start_ns)
    return _with_recovery_precision(ws,ws) do
        _run_phase_one!(ws,budget,policy,stop)
    end
end

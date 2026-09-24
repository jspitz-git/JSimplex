struct DualTermination
    status::TerminationStatus
    message::String
end

struct DualRunResult{T<:Real}
    status::TerminationStatus
    objective_value::Union{Nothing,T}
    primal::Union{Nothing,Vector{T}}
    iterations::Int
    refactorizations::Int
    message::String
    basis::Union{Nothing,Basis}
end

DualRunResult{T}(status, objective_value, primal, iterations, refactorizations, message) where {T<:Real} =
    DualRunResult{T}(status, objective_value, primal, iterations, refactorizations, message, nothing)

"""A monotonic clock and completed-work budget shared across simplex phases.

Iteration totals include the outer retry offset. Workspace/result counters stay
local to that retry, so the public solver can add previous work exactly once.
"""
mutable struct SimplexRunBudget
    start_ns::UInt64
    time_limit_seconds::Float64
    iteration_limit::Int
    iterations::Int
    refactorizations::Int
end

function SimplexRunBudget(ws::SimplexWorkspace)
    offset = ws.progress.iteration_offset
    limit = Int(min(big(offset)+ws.options.iteration_limit,typemax(Int)))
    return SimplexRunBudget(ws.progress.start_ns,ws.options.time_limit,limit,
        offset+ws.iterations,ws.progress.refactorization_offset+ws.refactorizations)
end

function _sync_run_budget!(budget,ws)
    budget.iterations = max(budget.iterations,ws.progress.iteration_offset+ws.iterations)
    budget.refactorizations = max(budget.refactorizations,
        ws.progress.refactorization_offset+ws.refactorizations)
    return nothing
end

_budget_expired(budget::SimplexRunBudget) =
    budget.time_limit_seconds != Inf &&
    (time_ns()-budget.start_ns)/1e9 >= budget.time_limit_seconds

feasibility_mode(primal_ok::Bool,dual_ok::Bool)::Symbol =
    primal_ok ? (dual_ok ? :certify : :primal) : (dual_ok ? :dual : :phase_one)

function _install_driver_policy!(ws,policy;start_ns::UInt64=ws.progress.start_ns)
    p = ws.progress
    ws.progress = typeof(p)(start_ns,p.objective,p.objective_constant,p.scaling,
        p.iteration_offset,p.refactorization_offset,p.diagnostics,policy)
    return nothing
end

function _driver_feasibility(ws::SimplexWorkspace{T},tolerance::T) where T
    # Phase I uses zero rather than the user's ordinary pricing tolerance.
    violation = zero(T)
    for j in eachindex(ws.basis.states)
        state = ws.basis.states[j]
        (state == BASIC || _is_fixed(ws.lower[j],ws.upper[j])) && continue
        price = ws.reduced_costs[j]
        error = state == AT_LOWER ? -price : state == AT_UPPER ? price : abs(price)
        error > tolerance && (violation += error)
    end
    return feasibility_mode(primal_infeasibility(ws) <= ws.options.primal_tolerance,
        violation <= tolerance)
end

function _verify_driver_basis!(ws,stop;refactorize::Bool=false)
    stop() && return false
    state = ws.scratch.pricing
    algorithm = isnothing(state) ? ws.options.algorithm : state.algorithm
    _prepare_auto_pricing!(ws,algorithm;stop) || return false
    return _with_recovery_precision(ws,ws) do
        recompute!(ws;refactorize,caller_guard=stop)
        stop() && return false
        _finite_workspace(ws) && _recomputed_basis_reliable(ws)
    end
end

function _driver_signature(ws,mode)
    return hash((ws.basis.basic_indices,ws.basis.states,ws.costs,ws.lower,ws.upper,
        ws.scratch.phase_generation,mode))
end

function _run_basis_terminal!(ws::SimplexWorkspace{T},budget::SimplexRunBudget,
                              policy::NumericalPolicy{T},stop;
                              reduced_cost_tolerance::T=ws.options.dual_tolerance,
                              perturb_degenerate::Bool=true,perturb_primal::Bool=true,
                              allow_auxiliary=Val(true))::DualTermination where T
    return _run_basis_terminal!(ws,budget,policy,stop,allow_auxiliary,
        reduced_cost_tolerance,perturb_degenerate,perturb_primal)
end

function _run_basis_terminal!(ws::SimplexWorkspace{T},budget::SimplexRunBudget,
                              policy::NumericalPolicy{T},stop,::Val{A},
                              reduced_cost_tolerance::T,perturb_degenerate::Bool,
                              perturb_primal::Bool)::DualTermination where {T,A}
    _install_driver_policy!(ws,policy;start_ns=budget.start_ns)
    # A new workspace inherits consumed work rather than receiving a fresh
    # iteration allowance. Offsets belong to the outer retry, not to phases.
    ws.iterations = max(ws.iterations,budget.iterations-ws.progress.iteration_offset)
    ws.refactorizations = max(ws.refactorizations,
        budget.refactorizations-ws.progress.refactorization_offset)
    original_options = ws.options
    # Auxiliary workspaces inherit this exact remaining limit. A custom budget
    # must not be bypassed by a method's own iteration loop.
    local_limit = max(0,budget.iteration_limit-ws.progress.iteration_offset)
    ws.options = _remaining_options(original_options;
        iterations=max(0,original_options.iteration_limit-local_limit),
        time_limit=min(original_options.time_limit,budget.time_limit_seconds))
    guarded = _guard_stop_callback(() -> begin
        _sync_run_budget!(budget,ws)
        _budget_expired(budget) || stop()
    end)
    history = UInt[]
    rounds = 0
    last_progress = ws.iterations
    fresh = false
    try
        if !policy.feasibility_recovery
            return ws.options.algorithm == :dual ? _dual_optimize!(ws,guarded;perturb_degenerate) :
                _primal_optimize!(ws,guarded,reduced_cost_tolerance;
                    perturb_degenerate=perturb_primal)
        end
        while true
            guarded() && return DualTermination(TIME_LIMIT,"time limit reached during feasibility recovery")
            verified = try
                _verify_driver_basis!(ws,guarded;refactorize=fresh)
            catch exception
                exception === guarded.exception && rethrow()
                _is_numerical_exception(exception) || rethrow()
                false
            end
            guarded() && return DualTermination(TIME_LIMIT,"time limit reached during feasibility recovery")
            mode = verified ? _driver_feasibility(ws,reduced_cost_tolerance) : :unreliable
            mode == :certify && return DualTermination(OPTIMAL,"optimal solution found")
            _sync_run_budget!(budget,ws)
            budget.iterations < budget.iteration_limit ||
                return DualTermination(ITERATION_LIMIT,"iteration limit reached")
            terminal = if !verified
                DualTermination(NUMERICAL_ERROR,"basis recomputation could not be verified")
            else
                try
                    if mode == :phase_one
                        A ? make_dual_feasible!(ws,guarded) :
                            DualTermination(NUMERICAL_ERROR,"auxiliary feasibility recovery cannot nest")
                    elseif mode == :primal
                        _simplex_event!(ws,:phase_primal)
                        _primal_optimize!(ws,guarded,reduced_cost_tolerance;
                            perturb_degenerate=perturb_primal)
                    else
                        _simplex_event!(ws,:phase_dual)
                        _dual_optimize!(ws,guarded;perturb_degenerate)
                    end
                catch exception
                    exception === guarded.exception && rethrow()
                    _is_numerical_exception(exception) || rethrow()
                    DualTermination(NUMERICAL_ERROR,sprint(showerror,exception))
                end
            end
            _sync_run_budget!(budget,ws)
            guarded() && return DualTermination(TIME_LIMIT,"time limit reached during feasibility recovery")
            if !isnothing(terminal) && !(terminal.status in (OPTIMAL,NUMERICAL_ERROR))
                return terminal
            end
            if !isnothing(terminal) && terminal.status == NUMERICAL_ERROR
                _simplex_event!(ws,:feasibility_recovery)
            end
            # A successful method still needs a verified recomputation before
            # accepting its feasibility. Repeated phase/basis states are bounded,
            # even when a method reports optimality without completing a step.
            if ws.iterations > last_progress
                rounds = 0
                empty!(history)
                last_progress = ws.iterations
            end
            signature = _driver_signature(ws,mode)
            if rounds >= min(2,policy.max_recovery_rounds) || signature in history
                # Permit one final verified check after a successful method.
                if !isnothing(terminal) && terminal.status == OPTIMAL &&
                   _verify_driver_basis!(ws,guarded) &&
                   _driver_feasibility(ws,reduced_cost_tolerance) == :certify
                    return terminal
                end
                guarded() && return DualTermination(TIME_LIMIT,"time limit reached during feasibility recovery")
                return DualTermination(NUMERICAL_ERROR,"bounded feasibility recovery exhausted")
            end
            push!(history,signature)
            rounds += 1
            fresh = !verified || (!isnothing(terminal) && terminal.status == NUMERICAL_ERROR)
            if fresh && policy.recovery
                # First refresh the current basis. Exchange columns only when
                # it remains unreliable or the failing method's invariant did
                # not change; otherwise dispatch the newly feasible method.
                reliable = try
                    _verify_driver_basis!(ws,guarded;refactorize=true)
                catch exception
                    exception === guarded.exception && rethrow()
                    _is_numerical_exception(exception) || rethrow()
                    false
                end
                guarded() && return DualTermination(TIME_LIMIT,"time limit reached during feasibility recovery")
                if !reliable || _driver_feasibility(ws,reduced_cost_tolerance) == mode
                    repair_basis!(ws,policy,guarded)
                end
                fresh = false
            end
        end
    catch exception
        if exception === guarded.exception
            # The budget adds a callback wrapper. Relay logger/callback
            # provenance to the caller's guard before its numerical handler.
            stop isa _StopCallback && (stop.exception = exception)
            rethrow()
        end
        _is_numerical_exception(exception) || rethrow()
        return DualTermination(NUMERICAL_ERROR,sprint(showerror,exception))
    finally
        _sync_run_budget!(budget,ws)
        ws.options = original_options
    end
end

function _original_costs_active(ws::SimplexWorkspace{T}) where T
    ws.perturbed && return false
    n = length(ws.problem.objective)
    for j in eachindex(ws.costs)
        ws.costs[j] == (j <= n ? ws.problem.objective[j] : zero(T)) || return false
    end
    return true
end

function _original_bounds_active(ws::SimplexWorkspace)
    n = size(ws.problem.A,2)
    for j in eachindex(ws.lower)
        lower = j <= n ? ws.problem.column_lower[j] : ws.problem.row_lower[j-n]
        upper = j <= n ? ws.problem.column_upper[j] : ws.problem.row_upper[j-n]
        ws.lower[j] == lower && ws.upper[j] == upper || return false
    end
    return true
end

function _original_bound_terminal(ws,terminal::DualTermination)
    if terminal.status in (INFEASIBLE,UNBOUNDED) && !_original_bounds_active(ws)
        # Only an owned journal can restore altered working bounds. A proof
        # for unrelated bound changes must not certify the original model.
        return DualTermination(NUMERICAL_ERROR,"terminal proof uses altered working bounds")
    end
    return terminal
end

function _run_original_objective_terminal!(ws::SimplexWorkspace{T},budget,policy,stop;
        reduced_cost_tolerance::T=ws.options.dual_tolerance,
        allow_auxiliary=Val(true),phase_perturbations::Bool=false)::DualTermination where T
    return _run_original_objective_terminal!(ws,budget,policy,stop,allow_auxiliary,
        reduced_cost_tolerance,phase_perturbations)
end

function _run_original_objective_terminal!(ws::SimplexWorkspace{T},budget,policy,stop,
        allow_auxiliary::Val{A},reduced_cost_tolerance::T,
        phase_perturbations::Bool)::DualTermination where {T,A}
    # Repairs may also shift a small price even with degeneracy perturbations
    # disabled. Bound cleanup itself and certify only the original objective.
    for cleanup in 0:2
        perturb = cleanup == 0 && ws.options.algorithm == :dual &&
            (!iszero(reduced_cost_tolerance) || phase_perturbations)
        perturb_primal = cleanup == 0 && ws.options.algorithm == :primal &&
            (!iszero(reduced_cost_tolerance) || phase_perturbations)
        terminal = _run_basis_terminal!(ws,budget,policy,stop,allow_auxiliary,
            reduced_cost_tolerance,perturb,perturb_primal)
        if terminal.status in (OPTIMAL,INFEASIBLE,UNBOUNDED) &&
           _has_active_bound_perturbations(ws.scratch.perturbations)
            # Expanded-bound feasibility or a terminal proof must be checked
            # again after restoring the original LP, within this same budget.
            _restore_original_costs!(ws)
            ws.perturbed = false
            _simplex_event!(ws,:phase_cleanup)
            continue
        end
        terminal = _original_bound_terminal(ws,terminal)
        journal = ws.scratch.perturbations
        adaptive_proof = terminal.status == INFEASIBLE &&
            !isnothing(journal) && journal.active
        # A cost shift does not change primal infeasibility, but retire its
        # working state and verify the terminal proof with the original costs.
        (terminal.status in (OPTIMAL,UNBOUNDED) || adaptive_proof) || return terminal
        _original_costs_active(ws) && return terminal
        _restore_original_costs!(ws)
        ws.perturbed = false
        _simplex_event!(ws,:phase_cleanup)
    end
    (_budget_expired(budget) || stop()) &&
        return DualTermination(TIME_LIMIT,"time limit reached during objective cleanup")
    return DualTermination(NUMERICAL_ERROR,"bounded original-objective cleanup exhausted")
end

function run_from_basis!(ws::SimplexWorkspace{T},budget::SimplexRunBudget,
                         policy::NumericalPolicy{T},stop;
                         reduced_cost_tolerance::T=ws.options.dual_tolerance)::DualRunResult{T} where T
    terminal = _run_original_objective_terminal!(ws,budget,policy,stop;reduced_cost_tolerance)
    return _internal_solution(ws,terminal)
end

"""Owned original costs and active working storage for reversible perturbations.

The active buffer becomes the workspace's cost vector on first publication.
Later pivots and repairs therefore update the same owned working storage.
"""
mutable struct PerturbationJournal{T<:Real}
    workspace_id::UInt
    original_costs::Vector{T}
    active_costs::Vector{T}
    original_perturbed::Bool
    active::Bool
    level::Int
    last_monitor::Union{Nothing,StagnationMonitor{T,T},StagnationMonitor{T,Rational{BigInt}}}
    last_observation::Int
    cooldown_until::Int
end

PerturbationJournal(ws) = PerturbationJournal(objectid(ws),copy(ws.costs),
    copy(ws.costs),ws.perturbed,false,0,nothing,0,0)

_perturbation_stopped(::Nothing) = false
_perturbation_stopped(stop) = stop()

function _check_perturbation_owner(ws,journal)
    journal.workspace_id == objectid(ws) &&
        length(journal.original_costs) == length(ws.costs) ||
        throw(ArgumentError("Perturbation journal belongs to a different workspace"))
    return nothing
end

function _perturbation_cooldown!(ws,journal)
    journal.cooldown_until = Int(min(typemax(Int),big(ws.iterations)+
        2big(ws.progress.numerical_policy.stagnation_window)))
    return nothing
end

"""Restore saved values directly; the caller recomputes before using prices."""
function restore_perturbations!(ws,journal::PerturbationJournal)::Nothing
    _check_perturbation_owner(ws,journal)
    journal.active || return nothing
    copyto!(ws.costs,journal.original_costs)
    copyto!(journal.active_costs,journal.original_costs)
    ws.perturbed = journal.original_perturbed
    journal.active = false
    _perturbation_cooldown!(ws,journal)
    _invalidate_basis_checkpoints!(ws)
    _reset_workspace_stagnation!(ws)
    _simplex_event!(ws,:restore_perturbations)
    return nothing
end

"""Give stalled, near-zero nonbasic prices a bounded dual-feasible margin.

There are at most three attempts in a journal. Their deterministic margins
increase by powers of two, with a total cost displacement cap of 512 dual
feasibility tolerances. Local cost scaling is bounded between one and two;
large unrepresentable shifts are skipped rather than rounded to a distant ulp.
Return -1 for cancellation before publication, zero for no shift, or the count.
"""
function perturb_dual_costs!(ws,monitor::StagnationMonitor,
                            journal::PerturbationJournal{T},policy;
                            stop_requested=nothing)::Int where T
    _check_perturbation_owner(ws,journal)
    _is_exact(T) === Val(true) && return 0
    policy.adaptive_dual_perturbation && ws.scratch.dual_perturbation_allowed || return 0
    monitor.state == :stalled && monitor.window_count == monitor.window || return 0
    (monitor !== journal.last_monitor || monitor.observations > journal.last_observation) &&
        journal.level < 3 || return 0
    ws.iterations >= journal.cooldown_until || return 0
    _perturbation_stopped(stop_requested) && return -1
    return _with_recovery_precision(ws,ws) do
        _perturb_dual_costs_precise!(ws,monitor,journal,policy,stop_requested)
    end
end

function _perturb_dual_costs_precise!(ws,monitor,journal::PerturbationJournal{T},
                                    policy,stop_requested)::Int where T
    tolerance = ws.options.dual_tolerance
    isfinite(tolerance) && tolerance > zero(T) || return 0
    _finite_workspace(ws) && dual_infeasibility(ws) <= tolerance || return 0
    level = journal.level+1
    cap = T(512)*tolerance
    isfinite(cap) || return 0
    costs,prices = copy(ws.costs),copy(ws.reduced_costs)
    shifted = 0
    for j in eachindex(ws.basis.states)
        j % 1024 == 0 && _perturbation_stopped(stop_requested) && return -1
        state = ws.basis.states[j]
        (state == AT_LOWER || state == AT_UPPER) || continue
        _is_fixed(ws.lower[j],ws.upper[j]) && continue
        old_cost,price = ws.costs[j],ws.reduced_costs[j]
        direction = state == AT_LOWER ? one(T) : -one(T)
        local_scale = one(T)+min(abs(old_cost),one(T))
        target = min(cap,tolerance*T(8+j%16)*local_scale*T(1 << (level-1)))
        isfinite(target) && target > tolerance || continue
        previous_shift = !isequal(old_cost,journal.original_costs[j])
        (abs(price) <= tolerance || (journal.active && previous_shift && abs(price) <= target)) || continue
        direction*price < target || continue
        requested = direction*target-price
        new_cost = old_cost+requested
        isfinite(new_cost) && new_cost != old_cost || continue
        actual = new_cost-old_cost
        isfinite(actual) && abs(actual) <= 2abs(requested) || continue
        displacement = new_cost-journal.original_costs[j]
        isfinite(displacement) && abs(displacement) <= cap || continue
        new_price = price+actual
        isfinite(new_price) && direction*new_price > tolerance || continue
        costs[j],prices[j] = new_cost,new_price
        shifted += 1
    end
    _perturbation_stopped(stop_requested) && return -1
    # Even an unrepresentable attempt consumes one level and one observation.
    journal.level = level
    journal.last_monitor = monitor
    journal.last_observation = monitor.observations
    shifted == 0 && return 0
    copyto!(journal.active_costs,costs)
    ws.costs = journal.active_costs
    copyto!(ws.reduced_costs,prices)
    journal.active = true
    ws.perturbed = true
    ws.scratch.perturbations = journal
    _invalidate_basis_checkpoints!(ws)
    _reset_workspace_stagnation!(ws)
    _simplex_event!(ws,:perturbation)
    return shifted
end

# Automatic shifts need the common monitor and original-objective cleanup.
_adaptive_dual_perturbation_enabled(policy) = policy.adaptive_dual_perturbation &&
    policy.adaptive_stalling && policy.feasibility_recovery

function _maybe_perturb_dual_costs!(ws,stop)::Int
    policy = ws.progress.numerical_policy
    _adaptive_dual_perturbation_enabled(policy) &&
        ws.scratch.dual_perturbation_allowed || return 0
    _is_exact(eltype(ws.costs)) === Val(true) && return 0
    state = ws.scratch.stagnation
    isnothing(state) && return 0
    return _maybe_perturb_dual_costs!(ws,state,stop)
end

function _maybe_perturb_dual_costs!(ws,state::WorkspaceStagnation{T,S},stop)::Int where {T,S}
    monitor = state.monitor
    monitor.state == :stalled && monitor.window_count == monitor.window || return 0
    primal_infeasibility(ws) > ws.options.primal_tolerance || return 0
    _perturbation_stopped(stop) && return -1
    journal = ws.scratch.perturbations
    if isnothing(journal)
        journal = PerturbationJournal(ws)
        # Keep unsuccessful bounded attempts too; they must not get fresh levels.
        ws.scratch.perturbations = journal
    end
    return perturb_dual_costs!(ws,monitor,journal,ws.progress.numerical_policy;
        stop_requested=stop)
end

function _restore_active_perturbations!(ws)
    journal = ws.scratch.perturbations
    isnothing(journal) || restore_perturbations!(ws,journal)
    return nothing
end

function _retire_perturbations!(ws)
    _restore_active_perturbations!(ws)
    ws.scratch.perturbations = nothing
    return nothing
end

function _perturbation_recovered!(ws)
    journal = ws.scratch.perturbations
    # The F11 history remains live across a basis restore. Only the perturbation
    # action cools down; a repair must not repeatedly postpone stall detection.
    isnothing(journal) || _perturbation_cooldown!(ws,journal)
    return nothing
end

function _auxiliary_costs_without_perturbation(ws)
    journal = ws.scratch.perturbations
    return isnothing(journal) || !journal.active ? ws.costs : journal.original_costs
end

function _auxiliary_perturbed_without_journal(ws)
    journal = ws.scratch.perturbations
    return isnothing(journal) || !journal.active ? ws.perturbed : journal.original_perturbed
end

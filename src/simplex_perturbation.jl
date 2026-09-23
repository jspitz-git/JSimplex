"""Lazy, independently bounded history and owned storage for bound shifts."""
mutable struct BoundPerturbationState{T<:Real}
    original_lower::Vector{Bound{T}}
    original_upper::Vector{Bound{T}}
    active_lower::Vector{Bound{T}}
    active_upper::Vector{Bound{T}}
    active::Bool
    level::Int
    last_monitor::Union{Nothing,StagnationMonitor{T,T},StagnationMonitor{T,Rational{BigInt}}}
    last_observation::Int
    cooldown_until::Int
end

BoundPerturbationState(ws) = BoundPerturbationState(copy(ws.lower),copy(ws.upper),
    copy(ws.lower),copy(ws.upper),false,0,nothing,0,0)

"""Owned original costs and active working storage for reversible perturbations.

The active buffer becomes the workspace's cost vector on first publication.
Later pivots and repairs therefore update the same owned working storage.
"""
mutable struct PerturbationJournal{T<:Real}
    workspace_id::UInt
    original_costs::Vector{T}
    active_costs::Vector{T}
    original_perturbed::Bool
    active::Bool # Cost activity; bound activity has its own state below.
    level::Int
    last_monitor::Union{Nothing,StagnationMonitor{T,T},StagnationMonitor{T,Rational{BigInt}}}
    last_observation::Int
    cooldown_until::Int
    bounds::Union{Nothing,BoundPerturbationState{T}}
end

PerturbationJournal(ws) = PerturbationJournal(objectid(ws),copy(ws.costs),
    copy(ws.costs),ws.perturbed,false,0,nothing,0,0,nothing)

_active_bounds(::Nothing) = false
_active_bounds(bounds::BoundPerturbationState) = bounds.active
_has_active_perturbations(::Nothing) = false
_has_active_perturbations(journal::PerturbationJournal) =
    journal.active || _active_bounds(journal.bounds)
_has_active_bound_perturbations(::Nothing) = false
_has_active_bound_perturbations(journal::PerturbationJournal) = _active_bounds(journal.bounds)

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

"""Restore saved values directly; recompute before using primal values or prices."""
function restore_perturbations!(ws,journal::PerturbationJournal)::Nothing
    _check_perturbation_owner(ws,journal)
    _has_active_perturbations(journal) || return nothing
    copyto!(ws.costs,journal.original_costs)
    copyto!(journal.active_costs,journal.original_costs)
    _restore_working_bounds!(ws,journal.bounds)
    ws.perturbed = journal.original_perturbed
    journal.active = false
    _perturbation_cooldown!(ws,journal)
    _invalidate_basis_checkpoints!(ws)
    _reset_workspace_stagnation!(ws)
    _simplex_event!(ws,:restore_perturbations)
    return nothing
end

_restore_working_bounds!(ws,::Nothing) = nothing
function _restore_working_bounds!(ws,bounds::BoundPerturbationState)
    bounds.active || return nothing
    copyto!(ws.lower,bounds.original_lower)
    copyto!(ws.upper,bounds.original_upper)
    copyto!(bounds.active_lower,bounds.original_lower)
    copyto!(bounds.active_upper,bounds.original_upper)
    bounds.active = false
    _perturbation_cooldown!(ws,bounds)
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
    if !isnothing(journal) && !isnothing(journal.bounds)
        _perturbation_cooldown!(ws,journal.bounds)
    end
    return nothing
end

function _auxiliary_costs_without_perturbation(ws)
    journal = ws.scratch.perturbations
    return isnothing(journal) || !journal.active ? ws.costs : journal.original_costs
end

function _auxiliary_perturbed_without_journal(ws)
    journal = ws.scratch.perturbations
    return !_has_active_perturbations(journal) ? ws.perturbed : journal.original_perturbed
end

"""Expand near-active basic bounds outward without changing boundedness.

Bounds have independent three-level escalation and cooldown. Each endpoint's
total displacement is capped at 512 primal tolerances. Fixed/free variables,
nonbasic variables, and unrepresentable shifts are skipped. The caller restores
the journal and recomputes before certifying the original problem.
"""
function perturb_primal_bounds!(ws,monitor::StagnationMonitor,
                               journal::PerturbationJournal{T},policy;
                               stop_requested=nothing)::Int where T
    _check_perturbation_owner(ws,journal)
    _is_exact(T) === Val(true) && return 0
    policy.adaptive_primal_perturbation && ws.scratch.primal_perturbation_allowed || return 0
    monitor.state == :stalled && monitor.window_count == monitor.window || return 0
    ws.iterations >= journal.cooldown_until || return 0
    bounds = journal.bounds
    if !isnothing(bounds)
        (monitor !== bounds.last_monitor || monitor.observations > bounds.last_observation) &&
            bounds.level < 3 || return 0
        ws.iterations >= bounds.cooldown_until || return 0
    end
    _perturbation_stopped(stop_requested) && return -1
    return _with_recovery_precision(ws,ws) do
        _perturb_primal_bounds_precise!(ws,monitor,journal,stop_requested)
    end
end

function _expanded_basic_bound(original::Bound{T},current::Bound{T},value::T,
                               direction::T,tolerance::T,cap::T,level::Int,index::Int) where T
    isfinite(current) && isfinite(original) || return current
    abs(value-current.value) <= tolerance || return current
    scale = one(T)+min(abs(original.value),one(T))
    margin = min(cap,tolerance*T(8+index%16)*scale*T(1 << (level-1)))
    isfinite(margin) && margin > tolerance || return current
    requested = original.value+direction*margin
    isfinite(requested) || return current
    change = direction*(requested-current.value)
    change > zero(T) && change <= 2margin || return current
    displacement = direction*(requested-original.value)
    isfinite(displacement) && zero(T) < displacement <= cap || return current
    return Bound(requested)
end

function _perturb_primal_bounds_precise!(ws,monitor,journal::PerturbationJournal{T},
                                       stop_requested)::Int where T
    tolerance = ws.options.primal_tolerance
    isfinite(tolerance) && tolerance > zero(T) || return 0
    _finite_workspace(ws) && primal_infeasibility(ws) <= tolerance || return 0
    cap = T(512)*tolerance
    isfinite(cap) || return 0
    bounds = journal.bounds
    isnothing(bounds) && (bounds = BoundPerturbationState(ws))
    level = bounds.level+1
    lower,upper = copy(ws.lower),copy(ws.upper)
    shifted = 0
    for (row,j) in enumerate(ws.basis.basic_indices)
        row % 1024 == 0 && _perturbation_stopped(stop_requested) && return -1
        _is_fixed(ws.lower[j],ws.upper[j]) && continue
        lo = _expanded_basic_bound(bounds.original_lower[j],ws.lower[j],ws.primal[j],
            -one(T),tolerance,cap,level,j)
        hi = _expanded_basic_bound(bounds.original_upper[j],ws.upper[j],ws.primal[j],
            one(T),tolerance,cap,level,j)
        shifted += !isequal(lo,lower[j]) + !isequal(hi,upper[j])
        lower[j],upper[j] = lo,hi
    end
    _perturbation_stopped(stop_requested) && return -1
    bounds.level = level
    bounds.last_monitor = monitor
    bounds.last_observation = monitor.observations
    journal.bounds = bounds
    shifted == 0 && return 0
    copyto!(bounds.active_lower,lower)
    copyto!(bounds.active_upper,upper)
    ws.lower,ws.upper = bounds.active_lower,bounds.active_upper
    bounds.active = true
    ws.perturbed = true
    ws.scratch.perturbations = journal
    _invalidate_basis_checkpoints!(ws)
    _reset_workspace_stagnation!(ws)
    _simplex_event!(ws,:perturbation)
    return shifted
end

_adaptive_primal_perturbation_enabled(policy) = policy.adaptive_primal_perturbation &&
    policy.adaptive_stalling && policy.feasibility_recovery

function _maybe_perturb_primal_bounds!(ws,stop)::Int
    _adaptive_primal_perturbation_enabled(ws.progress.numerical_policy) &&
        ws.scratch.primal_perturbation_allowed || return 0
    _is_exact(eltype(ws.costs)) === Val(true) && return 0
    state = ws.scratch.stagnation
    isnothing(state) && return 0
    return _maybe_perturb_primal_bounds!(ws,state,stop)
end

function _maybe_perturb_primal_bounds!(ws,state::WorkspaceStagnation{T,S},stop)::Int where {T,S}
    monitor = state.monitor
    monitor.state == :stalled && monitor.window_count == monitor.window || return 0
    dual_infeasibility(ws) > ws.options.dual_tolerance || return 0
    _perturbation_stopped(stop) && return -1
    journal = ws.scratch.perturbations
    if isnothing(journal)
        journal = PerturbationJournal(ws)
        ws.scratch.perturbations = journal
    end
    return perturb_primal_bounds!(ws,monitor,journal,ws.progress.numerical_policy;
        stop_requested=stop)
end

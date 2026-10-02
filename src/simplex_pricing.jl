"""Owned automatic-pricing history, driven by weight quality and progress, not clocks."""
mutable struct PricingState{T<:Real}
    active::Symbol
    algorithm::Symbol
    weight_quality::Symbol
    framework_valid::Bool
    needs_reset::Bool
    cooldown_until::Int
    observations::Int
    last_monitor::Union{Nothing,StagnationMonitor{T,T},StagnationMonitor{T,Rational{BigInt}}}
    last_observation::Int
    pricing_passes::Int
    validated_weights::Int
    rejected_weights::Int
    switches::Int
    resets::Int
    return_mode::Symbol
    temporary::Bool
    trial_until::Int
    progress_windows::Int
    last_transition::Symbol
end

PricingState(::Type{T}) where {T<:Real} = PricingState{T}(
    :steepest_edge,:none,:valid,true,false,0,0,nothing,0,0,0,0,0,0,
    :steepest_edge,false,0,0,:none)

_pricing_add(value::Int, increment::Int) = value + min(increment,typemax(Int)-value)
_pricing_cooldown(state,policy) =
    _pricing_add(state.observations,2min(policy.stagnation_window,typemax(Int)÷2))

function _unreliable_pricing!(state,policy)
    state.active != :devex && (state.switches += 1)
    state.active = :devex
    state.return_mode = :devex
    state.temporary = false
    state.progress_windows = 0
    state.last_transition = :numerical
    state.weight_quality = :pending
    state.framework_valid = false
    state.needs_reset = true
    state.cooldown_until = _pricing_cooldown(state,policy)
    return state.active
end

"""Compare squared edge weights, or stored primal square roots, without overflow."""
function validate_edge_weight(stored::T,actual::T,policy::NumericalPolicy;
                              square_root::Bool=false)::Bool where {T<:Real}
    isfinite(stored) && isfinite(actual) && stored > zero(T) && actual > zero(T) || return false
    ratio = T <: Rational ? min(big(stored),big(actual))/max(big(stored),big(actual)) :
                            min(stored,actual)/max(stored,actual)
    return (square_root ? ratio*ratio : ratio) >= _typed_ratio(typeof(ratio),1,2)
end

function validate_edge_weight(stored::BigFloat,actual::BigFloat,policy::NumericalPolicy;
                              square_root::Bool=false)::Bool
    return setprecision(BigFloat,max(precision(stored),precision(actual),
                                     precision(policy.solve_tolerance))) do
        isfinite(stored) && isfinite(actual) && stored > 0 && actual > 0 || return false
        ratio = min(stored,actual)/max(stored,actual)
        (square_root ? ratio*ratio : ratio) >= BigFloat(1)/2
    end
end

"""Select a mode from one shared progress history; the caller owns framework resets."""
function next_pricing!(state::PricingState{T},monitor::StagnationMonitor{T},
                       policy::NumericalPolicy{T})::Symbol where {T}
    same_monitor = monitor === state.last_monitor
    delta = same_monitor ? max(0,monitor.observations-state.last_observation) :
                           monitor.observations
    same_monitor || (state.progress_windows = 0)
    state.observations = _pricing_add(state.observations,delta)
    state.last_monitor = monitor
    state.last_observation = monitor.observations
    state.last_transition = :none
    if state.weight_quality == :unreliable
        return _unreliable_pricing!(state,policy)
    end
    state.needs_reset && return state.active
    enabled = policy.adaptive_pricing && policy.adaptive_stalling
    closed = delta > 0 && monitor.window_count == monitor.window
    if state.temporary
        if closed
            state.progress_windows = monitor.state == :progress ?
                state.progress_windows + 1 : 0
        end
        reason = !enabled ? :disabled : state.progress_windows >= 2 ? :progress :
            state.observations >= state.trial_until ? :trial_limit : :none
        if reason != :none && state.framework_valid
            state.active = state.return_mode
            state.temporary = false
            state.progress_windows = 0
            state.switches += 1
            state.cooldown_until = _pricing_cooldown(state,policy)
            state.last_transition = reason
        end
    elseif enabled && closed && monitor.state == :stalled &&
           state.active != :dantzig && state.framework_valid &&
           state.observations >= state.cooldown_until
        state.return_mode = state.active
        state.active = :dantzig
        state.temporary = true
        state.progress_windows = 0
        state.trial_until = _pricing_add(state.observations,
            4min(policy.stagnation_window,typemax(Int)÷4))
        state.switches += 1
        state.last_transition = :stalled
    end
    return state.active
end

function _effective_pricing(ws,algorithm::Symbol)
    ws.options.pricing == :dantzig && return :dantzig
    state = ws.scratch.pricing
    if !isnothing(state) && state.algorithm == algorithm
        return state.active
    end
    ws.options.pricing == :auto && return :steepest_edge
    if algorithm == :dual
        ws.dual_pricing_fallback && return :dantzig
        ws.dual_devex_fallback && return :devex
    end
    return ws.options.pricing
end

"""Weight maintenance follows the saved rule during a temporary selection trial."""
function _weight_pricing(ws,algorithm::Symbol)
    state = ws.scratch.pricing
    return !isnothing(state) && state.temporary ? state.return_mode :
        _effective_pricing(ws,algorithm)
end

function _copy_pricing_state!(destination,source)
    state = source.scratch.pricing
    if isnothing(state)
        destination.scratch.pricing = nothing
    else
        _copy_pricing_state!(destination.scratch,state)
    end
    return nothing
end

function _copy_pricing_state!(scratch,source::PricingState{T}) where T
    destination = scratch.pricing
    if isnothing(destination)
        destination = PricingState(T)
        scratch.pricing = destination
    end
    # Explicit fields avoid boxing heterogeneous values in this pivot copy.
    # The monitor is read-only here; all mutable pricing fields are owned.
    destination.active = source.active
    destination.algorithm = source.algorithm
    destination.weight_quality = source.weight_quality
    destination.framework_valid = source.framework_valid
    destination.needs_reset = source.needs_reset
    destination.cooldown_until = source.cooldown_until
    destination.observations = source.observations
    destination.last_monitor = source.last_monitor
    destination.last_observation = source.last_observation
    destination.pricing_passes = source.pricing_passes
    destination.validated_weights = source.validated_weights
    destination.rejected_weights = source.rejected_weights
    destination.switches = source.switches
    destination.resets = source.resets
    destination.return_mode = source.return_mode
    destination.temporary = source.temporary
    destination.trial_until = source.trial_until
    destination.progress_windows = source.progress_windows
    destination.last_transition = source.last_transition
    return nothing
end

function _reset_auto_pricing!(ws)
    # Phase history is owned by the workspace. Do not mutate a monitor shared
    # read-only with an uncommitted candidate.
    ws.scratch.stagnation = nothing
    state = ws.scratch.pricing
    isnothing(state) && return nothing
    if state.temporary
        state.active = state.return_mode
    elseif state.active == :dantzig
        state.active = ws.options.pricing == :auto ? :steepest_edge : ws.options.pricing
    end
    state.temporary = false
    if !state.framework_valid || state.needs_reset
        _unreliable_pricing!(state,ws.progress.numerical_policy)
        reset_devex!(ws)
    end
    state.return_mode = state.active
    state.observations = 0
    state.cooldown_until = 0
    state.trial_until = 0
    state.progress_windows = 0
    state.last_monitor = nothing
    state.last_observation = 0
    state.last_transition = :phase
    ws.dual_pricing_fallback = false
    _simplex_event!(ws,:pricing_phase_reset)
    return nothing
end

"""Carry a safe rule into freshly initialized primal weights of a different phase."""
function _inherit_primal_phase_pricing!(destination,source)
    previous = source.scratch.pricing
    isnothing(previous) && return nothing
    state = PricingState(eltype(destination.costs))
    state.algorithm = :primal
    state.active = state.return_mode = previous.needs_reset || !previous.framework_valid ?
        :devex : _weight_pricing(source,previous.algorithm)
    destination.scratch.pricing = state
    return nothing
end

function _auto_framework_reset!(ws)
    state = ws.scratch.pricing
    isnothing(state) && return nothing
    state.framework_valid = true
    state.needs_reset = false
    state.weight_quality = :valid
    state.resets += 1
    fill!(ws.scratch.steepest_valid,false)
    ws.scratch.steepest_initialized = false
    # A recovery trial publishes its reset counter only with the new basis.
    ws.scratch.recovery_active || _simplex_event!(ws,:pricing_reset)
    return nothing
end

function _reject_auto_weight!(ws)
    state = ws.scratch.pricing
    previous = state.active
    state.rejected_weights += 1
    _invalidate_pricing_pool!(ws;basis=false,costs=false)
    _simplex_event!(ws,:pricing_weight_rejected)
    _unreliable_pricing!(state,ws.progress.numerical_policy)
    reset_devex!(ws)
    previous != :devex && _simplex_event!(ws,:pricing_devex)
    return false
end

function _prepare_auto_pricing!(ws,algorithm::Symbol;stop=()->false)::Bool
    policy = ws.progress.numerical_policy
    controlled = ws.options.pricing == :auto ||
        (ws.options.pricing != :dantzig && policy.adaptive_pricing && policy.adaptive_stalling)
    controlled || !isnothing(ws.scratch.pricing) || return true
    stop() && return false
    algorithm in (:primal,:dual) || throw(ArgumentError("Unknown pricing algorithm"))
    state = ws.scratch.pricing
    if isnothing(state) || state.algorithm != algorithm
        changed_algorithm = !isnothing(state)
        safe_devex = changed_algorithm &&
            (state.temporary ? state.return_mode : state.active) == :devex
        state = PricingState(eltype(ws.costs))
        state.algorithm = algorithm
        state.active = safe_devex || (algorithm == :dual && ws.dual_devex_fallback) ?
            :devex : ws.options.pricing == :auto ? :steepest_edge : ws.options.pricing
        state.return_mode = state.active
        ws.scratch.pricing = state
        ws.dual_pricing_fallback = false
        # Primal and dual weights have different meanings. Retire the previous
        # geometry without introducing a mode change merely for that reason.
        (changed_algorithm || ws.options.pricing == :auto) && reset_devex!(ws)
    end
    if ws.options.pricing == :auto
        all(w -> isfinite(w) && w > zero(w),ws.pricing_weights) || _reject_auto_weight!(ws)
    end
    if state.temporary && !(policy.adaptive_pricing && policy.adaptive_stalling)
        if state.framework_valid && !state.needs_reset
            state.active = state.return_mode
            state.temporary = false
            state.progress_windows = 0
            state.cooldown_until = _pricing_cooldown(state,policy)
            state.switches += 1
            state.last_transition = :disabled
            _simplex_event!(ws,state.active == :devex ? :pricing_devex : :pricing_steepest_edge)
        else
            _reject_auto_weight!(ws)
        end
    end
    return !stop()
end

function _validate_primal_edge!(ws,index::Int,direction::AbstractVector{T})::Bool where T
    ws.options.pricing == :auto && _weight_pricing(ws,:primal) == :steepest_edge || return true
    # Uncacheable norms and fixed-width rationals are already solved exactly
    # on demand by primal pricing, including its scaled-exponent score path.
    ws.scratch.steepest_valid[index] || return true
    ws.scratch.pricing.validated_weights += 1
    _,actual = _primal_direction_weight(direction)
    valid = validate_edge_weight(ws.pricing_weights[index],actual,
        ws.progress.numerical_policy;square_root=T <: AbstractFloat)
    return valid || _reject_auto_weight!(ws)
end

function _validate_dual_edge!(ws,index::Int,rho::AbstractVector{T})::Bool where T
    ws.options.pricing == :auto && _weight_pricing(ws,:dual) == :steepest_edge || return true
    ws.scratch.pricing.validated_weights += 1
    stored = ws.pricing_weights[index]
    if T <: Rational
        # Validation can precede an infeasibility proof with no pivot at all.
        # Widen its squared norm rather than introducing a fixed-width overflow.
        actual = zero(Rational{BigInt})
        for value in rho
            actual += abs2(big(value))
        end
        valid = validate_edge_weight(big(stored),actual,ws.progress.numerical_policy)
    else
        valid = validate_edge_weight(stored,dot(rho,rho),ws.progress.numerical_policy)
    end
    return valid || _reject_auto_weight!(ws)
end

function _observe_auto_pricing!(ws,algorithm::Symbol)
    state = ws.scratch.pricing
    isnothing(state) && return nothing
    history = ws.scratch.stagnation
    isnothing(history) && return nothing
    previous = state.active
    policy = ws.progress.numerical_policy
    next_pricing!(state,history.monitor,policy)
    if state.needs_reset
        reset_devex!(ws)
    end
    if state.active != previous
        _simplex_event!(ws,state.active == :dantzig ? :pricing_dantzig :
            state.active == :devex ? :pricing_devex : :pricing_steepest_edge)
        state.last_transition == :progress && _simplex_event!(ws,:pricing_progress_return)
        state.last_transition == :trial_limit && _simplex_event!(ws,:pricing_trial_expired)
    end
    return nothing
end

"""Owned candidate indices; scores are always recomputed from current state."""
mutable struct CandidatePool
    algorithm::Symbol
    indices::Vector{Int}
    block_size::Int
    scan_position::Int
    basis_generation::UInt
    cost_generation::UInt
    valid::Bool
    full_scan::Bool
    scanned_entries::Int
    scored_entries::Int
    passes::Int
    full_scans::Int
    block_scans::Int
end

function CandidatePool(;algorithm::Symbol=:primal,block_size::Int=64)
    algorithm in (:primal,:dual) || throw(ArgumentError("Unknown pool algorithm"))
    block_size > 0 || throw(ArgumentError("Pricing block size must be positive"))
    return CandidatePool(algorithm,Int[],block_size,1,UInt(0),UInt(0),true,false,0,0,0,0,0)
end

function _pool_best!(pool,eligible,score,initial,accept_first)
    best,best_score,kept = 0,initial,0
    for index in pool.indices
        eligible(index) || continue
        kept += 1
        pool.indices[kept] = index
        value = score(index)
        pool.scored_entries += 1
        if (accept_first && best == 0) || value > best_score ||
           (best != 0 && value == best_score && index < best)
            best,best_score = index,value
        end
    end
    resize!(pool.indices,kept)
    return best
end

function _select_pool!(pool,count,eligible,score,initial,accept_first;force_full=false)
    pool.passes += 1
    pool.full_scan = false
    force_full = force_full || !pool.valid
    if force_full
        empty!(pool.indices)
        pool.scan_position = 1
        pool.valid = true
    else
        best = _pool_best!(pool,eligible,score,initial,accept_first)
        best != 0 && return best
        empty!(pool.indices)
    end
    # Every exhaustion checks the entire current domain, including blocks seen
    # before a pivot. An old empty block is never an optimality certificate.
    visited = 0
    cursor = clamp(pool.scan_position,1,max(1,count))
    while visited < count
        take = min(pool.block_size,count-visited)
        for _ in 1:take
            eligible(cursor) && push!(pool.indices,cursor)
            cursor = cursor == count ? 1 : cursor+1
        end
        pool.block_scans += 1
        visited += take
        pool.scanned_entries += take
        pool.scan_position = cursor
        if visited == count
            pool.full_scan = true
            pool.full_scans += 1
        end
        if !force_full || pool.full_scan
            best = _pool_best!(pool,eligible,score,initial,accept_first)
            best != 0 && return best
        end
    end
    if count == 0
        pool.full_scan = true
        pool.full_scans += 1
    end
    return 0
end

function _pool_primal_eligible(ws,index,tolerance)
    state = ws.basis.states[index]
    state == BASIC && return false
    index in ws.scratch.rejected_entering && return false
    _is_fixed(ws.lower[index],ws.upper[index]) && return false
    value = ws.reduced_costs[index]
    return (state == AT_LOWER && value < -tolerance) ||
           (state == AT_UPPER && value > tolerance) ||
           (state == FREE_NONBASIC && abs(value) > tolerance)
end

function _pool_primal_score(ws,index,pricing)
    value = ws.reduced_costs[index]
    pricing == :dantzig && return _primal_dantzig_score(value)
    weight = pricing == :steepest_edge && !ws.scratch.steepest_valid[index] ?
        _primal_steepest_weight!(ws,index) : ws.pricing_weights[index]
    return _primal_weighted_score(value,weight)
end

function _pool_dual_violation(ws,row)
    index = ws.basis.basic_indices[row]
    return max(_lower_violation(ws.lower[index],ws.primal[index]),
               _upper_violation(ws.upper[index],ws.primal[index]))
end

function _select_dual_pool!(ws,pool,scoring::Val{S};force_full=false) where S
    T = eltype(ws.costs)
    weighted = _effective_pricing(ws,:dual) != :dantzig
    initial = S === :scaled ? _primal_dantzig_score(one(T)) : zero(S)
    eligible = row -> !(row in ws.scratch.rejected_rows) &&
                      _pool_dual_violation(ws,row) > ws.options.primal_tolerance
    score = row -> _dual_pricing_score(_pool_dual_violation(ws,row),
        ws.pricing_weights[ws.basis.basic_indices[row]],weighted,scoring)
    return _select_pool!(pool,length(ws.basis.basic_indices),eligible,score,
                         initial,S === :scaled;force_full)
end

"""Select a current candidate; zero requires a complete scan during this call."""
function select_pricing_candidate!(ws,pool::CandidatePool,policy;
                                   force_full::Bool=false,
                                   tolerance=ws.options.dual_tolerance)::Int
    force_full = force_full || !policy.partial_pricing
    T = eltype(ws.costs)
    _prepare_auto_pricing!(ws,pool.algorithm)
    if pool.algorithm == :primal
        pricing = _effective_pricing(ws,:primal)
        pricing == :steepest_edge && _primal_initialize_steepest!(ws)
        eligible = index -> _pool_primal_eligible(ws,index,tolerance)
        score = index -> _pool_primal_score(ws,index,pricing)
        return _select_pool!(pool,length(ws.basis.states),eligible,score,
                             _primal_dantzig_score(one(T)),true;force_full)
    end
    if ws.options.pricing == :auto && T <: Rational
        return _select_dual_pool!(ws,pool,Val(Rational{BigInt});force_full)
    elseif ws.options.pricing == :auto
        return _select_dual_pool!(ws,pool,Val(:scaled);force_full)
    end
    return _select_dual_pool!(ws,pool,Val(T);force_full)
end

function _pricing_pool!(ws,algorithm::Symbol)
    pool = ws.scratch.pricing_pool
    if isnothing(pool) || pool.algorithm != algorithm
        pool = CandidatePool(;algorithm)
        ws.scratch.pricing_pool = pool
    end
    return pool
end

function _invalidate_pricing_pool!(ws;basis::Bool=true,costs::Bool=true)
    pool = ws.scratch.pricing_pool
    isnothing(pool) && return nothing
    basis && (pool.basis_generation += UInt(1))
    costs && (pool.cost_generation += UInt(1))
    pool.valid = false
    pool.full_scan = false
    empty!(pool.indices)
    return nothing
end

function _advance_pricing_basis!(ws)
    pool = ws.scratch.pricing_pool
    isnothing(pool) && return nothing
    pool.basis_generation += UInt(1)
    pool.full_scan = false
    return nothing
end

function _copy_pricing_pool!(destination,source)
    pool = source.scratch.pricing_pool
    if isnothing(pool)
        destination.scratch.pricing_pool = nothing
        return nothing
    end
    copy_pool = _pricing_pool!(destination,pool.algorithm)
    resize!(copy_pool.indices,length(pool.indices))
    copyto!(copy_pool.indices,pool.indices)
    copy_pool.block_size = pool.block_size
    copy_pool.scan_position = pool.scan_position
    copy_pool.basis_generation = pool.basis_generation
    copy_pool.cost_generation = pool.cost_generation
    copy_pool.valid = pool.valid
    copy_pool.full_scan = pool.full_scan
    copy_pool.scanned_entries = pool.scanned_entries
    copy_pool.scored_entries = pool.scored_entries
    copy_pool.passes = pool.passes
    copy_pool.full_scans = pool.full_scans
    copy_pool.block_scans = pool.block_scans
    return nothing
end

_partial_pricing_enabled(ws,algorithm) = ws.progress.numerical_policy.partial_pricing &&
    (algorithm == :primal ? length(ws.basis.states) : length(ws.basis.basic_indices)) > 128

function _select_workspace_pool!(ws,algorithm;force_full=false,
                                 tolerance=ws.options.dual_tolerance)
    pool = _pricing_pool!(ws,algorithm)
    previous = (pool.scanned_entries,pool.scored_entries,pool.full_scans,pool.block_scans)
    result = select_pricing_candidate!(ws,pool,ws.progress.numerical_policy;force_full,tolerance)
    _record_pricing_work!(ws.progress.diagnostics,pool,previous,result)
    return result
end

_record_pricing_work!(::Nothing,pool,previous,result) = nothing
function _record_pricing_work!(diagnostics,pool,previous,result)
    # Work counters include discarded attempts and share the live diagnostic
    # dictionary in staged pivots. They do not publish solver-state events.
    scanned = pool.scanned_entries-previous[1]
    diagnostics.counts[:pricing_scanned_entries] += scanned
    diagnostics.counts[:pricing_scored_entries] += pool.scored_entries-previous[2]
    diagnostics.counts[:pricing_full_scan] += pool.full_scans-previous[3]
    diagnostics.counts[:pricing_block_scan] += pool.block_scans-previous[4]
    diagnostics.counts[:pricing_pool_hit] += Int(scanned == 0 && result != 0)
    return nothing
end

_record_full_pricing!(::Nothing,count,scored) = nothing
function _record_full_pricing!(diagnostics,count,scored)
    diagnostics.counts[:pricing_scanned_entries] += count
    diagnostics.counts[:pricing_scored_entries] += scored
    diagnostics.counts[:pricing_full_scan] += 1
    return nothing
end

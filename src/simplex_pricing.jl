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
end

PricingState(::Type{T}) where {T<:Real} = PricingState{T}(
    :steepest_edge,:none,:valid,true,false,0,0,nothing,0,0,0,0,0,0)

_pricing_add(value::Int, increment::Int) = value + min(increment,typemax(Int)-value)
_pricing_cooldown(state,policy) =
    _pricing_add(state.observations,2min(policy.stagnation_window,typemax(Int)÷2))

function _unreliable_pricing!(state,policy)
    state.active != :devex && (state.switches += 1)
    state.active = :devex
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
    delta = monitor === state.last_monitor ? max(0,monitor.observations-state.last_observation) :
                                             monitor.observations
    state.observations = _pricing_add(state.observations,delta)
    state.last_monitor = monitor
    state.last_observation = monitor.observations
    if state.weight_quality == :unreliable
        return _unreliable_pricing!(state,policy)
    end
    state.needs_reset && return state.active
    policy.adaptive_pricing || return state.active
    if state.active == :dantzig
        if state.observations >= state.cooldown_until && state.framework_valid
            state.active = :devex
            state.switches += 1
            state.cooldown_until = _pricing_cooldown(state,policy)
        end
    elseif delta > 0 && monitor.state == :stalled && monitor.window_count == monitor.window &&
           state.observations >= state.cooldown_until
        state.active = :dantzig
        state.framework_valid = false
        state.switches += 1
        state.cooldown_until = _pricing_cooldown(state,policy)
    end
    return state.active
end

function _effective_pricing(ws,algorithm::Symbol)
    if ws.options.pricing == :auto
        state = ws.scratch.pricing
        return isnothing(state) ? :steepest_edge : state.active
    end
    ws.options.pricing == :dantzig && return :dantzig
    if algorithm == :dual
        ws.dual_pricing_fallback && return :dantzig
        ws.dual_devex_fallback && return :devex
    end
    return ws.options.pricing
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
    return nothing
end

function _reset_auto_pricing!(ws)
    ws.options.pricing == :auto || return nothing
    ws.scratch.pricing = nothing
    return nothing
end

function _auto_framework_reset!(ws)
    ws.options.pricing == :auto || return nothing
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
    _simplex_event!(ws,:pricing_weight_rejected)
    _unreliable_pricing!(state,ws.progress.numerical_policy)
    reset_devex!(ws)
    previous != :devex && _simplex_event!(ws,:pricing_devex)
    return false
end

function _prepare_auto_pricing!(ws,algorithm::Symbol;stop=()->false)::Bool
    ws.options.pricing == :auto || return true
    stop() && return false
    algorithm in (:primal,:dual) || throw(ArgumentError("Unknown pricing algorithm"))
    state = ws.scratch.pricing
    if isnothing(state) || state.algorithm != algorithm
        state = PricingState(eltype(ws.costs))
        state.algorithm = algorithm
        ws.scratch.pricing = state
        ws.dual_pricing_fallback = false
        ws.dual_devex_fallback = false
        reset_devex!(ws)
    end
    all(w -> isfinite(w) && w > zero(w),ws.pricing_weights) || _reject_auto_weight!(ws)
    return !stop()
end

function _validate_primal_edge!(ws,index::Int,direction::AbstractVector{T})::Bool where T
    ws.options.pricing == :auto && _effective_pricing(ws,:primal) == :steepest_edge || return true
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
    ws.options.pricing == :auto && _effective_pricing(ws,:dual) == :steepest_edge || return true
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
    ws.options.pricing == :auto || return nothing
    state = ws.scratch.pricing
    isnothing(state) && return nothing
    history = ws.scratch.stagnation
    isnothing(history) && return nothing
    previous = state.active
    # No weighted updates run during Dantzig pivots. Its old reference cannot
    # justify a return to weighted pricing after the cooldown.
    previous == :dantzig && (state.framework_valid = false)
    policy = ws.progress.numerical_policy
    next_pricing!(state,history.monitor,policy)
    if policy.adaptive_pricing && state.active == :dantzig &&
       state.observations >= state.cooldown_until
        reset_devex!(ws)
        next_pricing!(state,history.monitor,policy)
    elseif state.needs_reset
        reset_devex!(ws)
    end
    if state.active != previous
        _simplex_event!(ws,state.active == :dantzig ? :pricing_dantzig : :pricing_devex)
    end
    return nothing
end

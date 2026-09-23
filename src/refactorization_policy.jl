# Numerical triggers precede economic heuristics. Timing data never certifies
# a basis and never replaces the finite update ceiling.
_refactor_ceiling(initial::Int, multiplier::Int=8, floor::Int=512) =
    max(initial, min(4096, max(floor, initial > 4096 ÷ multiplier ? 4096 : multiplier*initial)))

mutable struct RefactorizationState{T<:Real}
    nupdates::Int
    productive_updates::Int
    initial_interval::Int
    interval::Int
    hard_ceiling::Int
    fixed::Bool
    timing_enabled::Bool
    residual_bad::Bool
    latest_quality::Union{Nothing,SolveQuality{T}}
    growth_scale::Float64
    base_growth_scale::T
    metrics_update_count::Int
    growth_limit::Float64
    stored_elements::Int
    base_elements::Int
    fill_limit::Float64
    fresh_seconds::Float64
    update_seconds::Float64
    factor_seconds::Float64
    fresh_samples::Int
    update_samples::Int
    factor_samples::Int
    fresh_observed::Float64
    update_observed::Float64
    healthy_cycles::Int
    recent_failures::Int
    earliest_bad_update::Int
    work_attempts::Int
    factor_attempts::Int
    timing_depth::Int
    work_seconds::Float64
    pending_cycle::Symbol
end

function RefactorizationState(::Type{T}=Float64;
    nupdates::Int = 0,
    productive_updates::Int = 0,
    initial_interval::Int = 20,
    interval::Int = initial_interval,
    hard_ceiling::Int = _refactor_ceiling(initial_interval),
    fixed::Bool = T <: Rational,
    timing_enabled::Bool = !fixed,
    residual_bad::Bool = false,
    latest_quality::Union{Nothing,SolveQuality{T}} = nothing,
    growth_scale::Float64 = 1.0,
    base_growth_scale::T = one(T),
    metrics_update_count::Int = -1,
    growth_limit::Float64 = 1e8,
    stored_elements::Int = 1,
    base_elements::Int = 1,
    fill_limit::Float64 = 8.0,
    fresh_seconds::Float64 = 0.0,
    update_seconds::Float64 = 0.0,
    factor_seconds::Float64 = 0.0,
    fresh_samples::Int = 0,
    update_samples::Int = 0,
    factor_samples::Int = 0,
    fresh_observed::Float64 = 0.0,
    update_observed::Float64 = 0.0,
    healthy_cycles::Int = 0,
    recent_failures::Int = 0,
    earliest_bad_update::Int = typemax(Int),
    work_attempts::Int = 0,
    factor_attempts::Int = 0,
    timing_depth::Int = 0,
    work_seconds::Float64 = 0.0,
    pending_cycle::Symbol = :none
) where {T<:Real}
    state = RefactorizationState{T}(
        nupdates, productive_updates, initial_interval, interval, hard_ceiling, fixed,
        timing_enabled, residual_bad, latest_quality, growth_scale, base_growth_scale, metrics_update_count, growth_limit,
        stored_elements, base_elements, fill_limit, fresh_seconds, update_seconds,
        factor_seconds, fresh_samples, update_samples, factor_samples, fresh_observed,
        update_observed, healthy_cycles, recent_failures, earliest_bad_update,
        work_attempts, factor_attempts, timing_depth, work_seconds, pending_cycle,
    )
    1 <= state.initial_interval <= state.hard_ceiling &&
        1 <= state.interval <= state.hard_ceiling && state.nupdates >= 0 ||
        throw(ArgumentError("Invalid refactorization interval or update count"))
    return state
end

function refactor_reason(state::RefactorizationState, policy::NumericalPolicy)::Symbol
    state.residual_bad && return :residual
    !isnothing(state.latest_quality) && !state.latest_quality.reliable && return :residual
    if state.fixed
        return state.nupdates >= state.initial_interval ? :limit : :none
    end
    (!isfinite(state.growth_scale) || state.growth_scale > state.growth_limit) &&
        return :pivot_growth
    state.stored_elements / max(1,state.base_elements) > state.fill_limit && return :fill
    state.nupdates >= state.hard_ceiling && return :limit
    if state.timing_enabled && policy.refactor_timing && state.nupdates >= 4 &&
       state.fresh_samples >= 4 && state.update_samples >= 4 && state.factor_samples > 0 &&
       state.fresh_observed >= 1e-4 && state.update_observed >= 1e-4
        # With approximately linear update overhead, minimizing average cycle
        # work LU/r + fresh + slope*(r+1)/2 gives overhead > 2*LU/r.
        # Divide first to avoid overflowing a cost-times-horizon product.
        overhead = state.update_seconds-state.fresh_seconds
        all(isfinite,(overhead,state.factor_seconds)) && state.factor_seconds > 0 &&
            overhead > (state.factor_seconds/state.nupdates)*2 && return :cost
    end
    return state.nupdates >= state.interval ? :limit : :none
end

_basis_cost_ema(old, value, count) = iszero(count) ? value : 0.75*old+0.25*value
_bounded_observation_sum(old, value) = min(floatmax(Float64),old+value)

"""Record synthetic or measured costs; invalid observations carry no evidence."""
function record_basis_cost!(state::RefactorizationState, operation::Symbol, seconds)::Nothing
    operation in (:fresh,:update,:refactorization) || throw(ArgumentError("Unknown basis cost operation"))
    state.fixed && return nothing
    value = Float64(seconds)
    isfinite(value) && value > 0 || return nothing
    if operation == :fresh
        state.fresh_seconds = _basis_cost_ema(state.fresh_seconds,value,state.fresh_samples)
        state.fresh_samples = min(typemax(Int)-1,state.fresh_samples)+1
        state.fresh_observed = _bounded_observation_sum(state.fresh_observed,value)
    elseif operation == :update
        state.update_seconds = _basis_cost_ema(state.update_seconds,value,state.update_samples)
        state.update_samples = min(typemax(Int)-1,state.update_samples)+1
        state.update_observed = _bounded_observation_sum(state.update_observed,value)
    else
        state.factor_seconds = _basis_cost_ema(state.factor_seconds,value,state.factor_samples)
        state.factor_samples = min(typemax(Int)-1,state.factor_samples)+1
    end
    return nothing
end

"""Adapt only after repeated failures or three reliable, productive cycles."""
function record_refactor_cycle!(state::RefactorizationState;
                               reliable::Bool, productive::Bool)::Nothing
    state.fixed && return nothing
    if !reliable
        state.healthy_cycles = 0
        state.recent_failures = min(2,state.recent_failures+1)
        state.earliest_bad_update = min(state.earliest_bad_update,max(1,state.nupdates))
        if state.recent_failures >= 2
            state.interval = min(state.interval,max(1,state.earliest_bad_update ÷ 2))
            state.recent_failures = 0
            state.earliest_bad_update = typemax(Int)
        end
    elseif !productive
        state.healthy_cycles = 0
    else
        state.healthy_cycles += 1
        if state.healthy_cycles >= 3
            state.interval = state.interval > state.hard_ceiling ÷ 2 ?
                state.hard_ceiling : 2*state.interval
            state.healthy_cycles = 0
            state.recent_failures = 0
            state.earliest_bad_update = typemax(Int)
        end
    end
    return nothing
end

function _configure_refactorization!(ws)
    initial = ws.options.refactorization_interval
    pfi = ws.factorization isa PFIFactorization
    ws.scratch.refactorization = RefactorizationState(eltype(ws.costs);
        initial_interval=initial,
        hard_ceiling=_refactor_ceiling(initial,pfi ? 8 : 4,pfi ? 512 : 128),
        timing_enabled=ws.progress.numerical_policy.adaptive_refactor &&
            ws.progress.numerical_policy.refactor_timing && !(eltype(ws.costs) <: Rational))
    _reset_refactor_metrics!(ws)
    return nothing
end

function _reset_refactor_metrics!(ws)
    state = ws.scratch.refactorization
    state.base_elements = _factor_storage_count(ws.factorization)
    state.stored_elements = state.base_elements
    state.base_growth_scale = _factor_growth_reference(ws.factorization)
    state.metrics_update_count = length(ws.factorization.updates)
    state.growth_scale = 1.0
    return nothing
end

function _refresh_refactor_metrics!(ws;force::Bool=false)
    state = ws.scratch.refactorization
    age = state.nupdates = length(ws.factorization.updates)
    if !force
        age == state.metrics_update_count && return nothing
        age == 1 || iszero(age % 8) || age >= state.interval || return nothing
    end
    state.stored_elements = _factor_storage_count(ws.factorization)
    if !state.fixed
        state.growth_scale = _with_recovery_precision(ws,ws) do
            current = _factor_growth_measure(ws.factorization)
            baseline = state.base_growth_scale
            iszero(baseline) ? (iszero(current) ? 1.0 : Inf) : Float64(current/baseline)
        end
    end
    state.metrics_update_count = age
    return nothing
end

function _record_refactor_quality!(ws, quality)
    if ws.progress.numerical_policy.adaptive_refactor
        state = ws.scratch.refactorization
        state.latest_quality = quality
        state.residual_bad |= !quality.reliable
        quality.reliable || (state.healthy_cycles = 0)
    end
    return quality
end

function _note_refactor_step!(ws, step)
    ws.progress.numerical_policy.adaptive_refactor || return nothing
    state = ws.scratch.refactorization
    updates = length(ws.factorization.updates)
    updates > state.nupdates && !iszero(step) && (state.productive_updates += 1)
    state.nupdates = updates
    return nothing
end

function _scheduled_refactor_reason(ws, algorithm::Symbol)
    if ws.progress.numerical_policy.adaptive_refactor
        state = ws.scratch.refactorization
        state.nupdates = length(ws.factorization.updates)
        state.fixed || _refresh_refactor_metrics!(ws)
        return refactor_reason(state,ws.progress.numerical_policy)
    end
    interval = algorithm == :dual ? ws.dual_refactorization_interval : ws.options.refactorization_interval
    return length(ws.factorization.updates) >= interval ? :limit : :none
end

_refactor_event(reason::Symbol) = reason == :cost ? :refactor_cost :
    reason == :pivot_growth ? :refactor_growth : reason == :fill ? :refactor_fill :
    reason == :residual ? :refactor_residual : :refactor_limit

function _before_basis_refactor!(ws, reason::Symbol)
    ws.progress.numerical_policy.adaptive_refactor || return nothing
    state = ws.scratch.refactorization
    state.nupdates = length(ws.factorization.updates)
    state.pending_cycle = :none
    state.nupdates == 0 && return nothing
    failed = state.residual_bad || reason in (:refactor_pivot,:refactor_residual,:refactor_growth) ||
        (!isnothing(state.latest_quality) && !state.latest_quality.reliable)
    productive = reason != :refactor_fill &&
        state.productive_updates >= state.nupdates-state.nupdates÷4
    state.pending_cycle = failed ? :failed : isnothing(state.latest_quality) ? :unknown :
        productive ? :healthy : :unproductive
    state.pending_cycle == :healthy || (state.healthy_cycles = 0)
    return nothing
end

function _abort_basis_refactor!(ws)
    ws.progress.numerical_policy.adaptive_refactor || return nothing
    state = ws.scratch.refactorization
    state.nupdates > 0 && record_refactor_cycle!(state;reliable=false,productive=false)
    state.pending_cycle = :none
    state.healthy_cycles = 0
    state.residual_bad = true
    return nothing
end

function _after_basis_refactor!(ws)
    ws.progress.numerical_policy.adaptive_refactor || return nothing
    state = ws.scratch.refactorization
    if state.pending_cycle in (:healthy,:failed,:unproductive)
        record_refactor_cycle!(state;reliable=state.pending_cycle != :failed,
            productive=state.pending_cycle == :healthy)
    end
    state.pending_cycle = :none
    state.nupdates = 0
    state.productive_updates = 0
    state.residual_bad = false
    state.latest_quality = nothing
    state.growth_scale = 1.0
    _reset_refactor_metrics!(ws)
    return nothing
end

# Measure the whole attempted step, including validation, refinement, pricing,
# and BFRT RHS work. A step containing a factor rebuild cannot enter the solve
# EMA: its LU work has a separate estimate. Nested iteration scopes do not
# produce duplicate observations. Samples are heuristic, never safety evidence.
function _measure_basis_iteration!(f, ws; clock=time_ns)
    state = ws.scratch.refactorization
    state.timing_enabled && !state.fixed || return f()
    state.timing_depth == 0 || return f()
    state.work_attempts = min(typemax(Int)-1,state.work_attempts)+1
    age = length(ws.factorization.updates)
    sample = age == 0 || iszero(state.work_attempts % 4)
    state.timing_depth += 1
    if !sample
        try
            return f()
        finally
            state.timing_depth -= 1
        end
    end
    iterations, refactors = ws.iterations, ws.refactorizations
    started = clock()
    finished = false
    try
        result = f()
        finished = true
        return result
    finally
        seconds = Float64(clock()-started)/1e9
        state.timing_depth -= 1
        if isfinite(seconds) && seconds > 0
            state.work_seconds = _bounded_observation_sum(state.work_seconds,seconds)
            if finished && ws.scratch.refactorization === state &&
               ws.refactorizations == refactors && ws.iterations == iterations+1
                record_basis_cost!(state,age == 0 ? :fresh : :update,seconds)
            end
        end
    end
end

# This wrapper forwards its callables. Specialize them explicitly so that the
# factorization closure does not escape and allocate on every rebuild.
function _measure_basis_factorization!(f::F, ws; clock::C=time_ns) where {F,C}
    try
        return _measure_basis_factorization_cost!(f,ws;clock)
    catch
        _abort_basis_refactor!(ws)
        rethrow()
    end
end

function _measure_basis_factorization_cost!(f, ws; clock=time_ns)
    state = ws.scratch.refactorization
    state.timing_enabled && !state.fixed || return f()
    state.factor_attempts = min(typemax(Int)-1,state.factor_attempts)+1
    state.factor_attempts <= 4 || iszero(state.factor_attempts % 4) || return f()
    started = clock()
    result = f()
    record_basis_cost!(state,:refactorization,Float64(clock()-started)/1e9)
    return result
end

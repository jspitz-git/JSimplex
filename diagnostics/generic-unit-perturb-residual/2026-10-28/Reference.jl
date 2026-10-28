module UPRReference
import JSimplex
using SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,Bound,bound_value,PerturbationJournal,BoundPerturbationState,StagnationMonitor,LPResiduals,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,
    _is_exact,_is_fixed,_primal_direction_magnitude,_prepare_auto_pricing!,_partial_pricing_enabled,_select_workspace_pool!,_effective_pricing,_primal_initialize_steepest!,_primal_steepest_weight!,_primal_dantzig_score,_record_full_pricing!,
    _check_perturbation_owner,_perturbation_stopped,_with_recovery_precision,_finite_workspace,dual_infeasibility,primal_infeasibility,_invalidate_basis_checkpoints!,_reset_workspace_stagnation!,_simplex_event!,_copy_working_values,_working_value_bits,_lp_residual_bits
function _primal_weighted_score(reduced_cost::T,
                                weight::Tuple{I,T}) where {I<:Integer,T<:AbstractFloat}
    cost_mantissa, cost_exponent = frexp(abs(reduced_cost))
    weight_exponent, weight_mantissa = weight
    score_mantissa, correction = frexp(cost_mantissa / weight_mantissa)
    return (cost_exponent - weight_exponent + correction, score_mantissa)
end

# Positive scores keep the original owner without a discarded negation.
function _primal_weighted_score(reduced_cost::BigFloat,
                                weight::Tuple{I,BigFloat}) where {I<:Integer}
    cost_mantissa, cost_exponent = frexp(_primal_direction_magnitude(reduced_cost))
    weight_exponent, weight_mantissa = weight
    score_mantissa, correction = frexp(cost_mantissa / weight_mantissa)
    return (cost_exponent - weight_exponent + correction, score_mantissa)
end


function _primal_weighted_score(reduced_cost::T, weight::T) where {T<:AbstractFloat}
    mantissa, exponent = frexp(weight)
    return _primal_weighted_score(reduced_cost, (exponent, mantissa))
end
_primal_weighted_score(reduced_cost::Rational, weight::Rational) =
    big(reduced_cost)^2 / big(weight)

function _primal_entering(workspace::SimplexWorkspace{T}, tolerance::T) where {T}
    _prepare_auto_pricing!(workspace,:primal)
    state = workspace.scratch.pricing
    isnothing(state) || (state.pricing_passes += 1)
    if _partial_pricing_enabled(workspace,:primal)
        entering = _select_workspace_pool!(workspace,:primal;tolerance)
        direction = entering == 0 ? zero(T) :
            (workspace.reduced_costs[entering] < zero(T) ? one(T) : -one(T))
        return entering,direction
    end
    pricing = _effective_pricing(workspace,:primal)
    pricing == :steepest_edge && _primal_initialize_steepest!(workspace)
    entering = 0
    scored = 0
    direction = zero(T)
    best_score = _primal_dantzig_score(one(T))
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        index in workspace.scratch.rejected_entering && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        reduced_cost = workspace.reduced_costs[index]
        improving = (state == AT_LOWER && reduced_cost < -tolerance) ||
                    (state == AT_UPPER && reduced_cost > tolerance) ||
                    (state == FREE_NONBASIC && abs(reduced_cost) > tolerance)
        improving || continue
        scored += 1
        score = if pricing == :dantzig
            _primal_dantzig_score(reduced_cost)
        else
            weight = pricing == :steepest_edge && !workspace.scratch.steepest_valid[index] ?
                _primal_steepest_weight!(workspace, index) : workspace.pricing_weights[index]
            _primal_weighted_score(reduced_cost, weight)
        end
        if entering == 0 || score > best_score
            entering = index
            direction = reduced_cost < zero(T) ? one(T) : -one(T)
            best_score = score
        end
    end
    _record_full_pricing!(workspace.progress.diagnostics,length(workspace.basis.states),scored)
    return entering, direction
end

function _primal_entering(workspace::SimplexWorkspace{T}, tolerance::T) where {T<:Union{BigFloat,Rational{BigInt}}}
    _prepare_auto_pricing!(workspace,:primal)
    state = workspace.scratch.pricing
    isnothing(state) || (state.pricing_passes += 1)
    if _partial_pricing_enabled(workspace,:primal)
        entering = _select_workspace_pool!(workspace,:primal;tolerance)
        direction = entering == 0 ? zero(T) :
            (workspace.reduced_costs[entering] < 0 ? one(T) : -one(T))
        return entering,direction
    end
    pricing = _effective_pricing(workspace,:primal)
    pricing == :steepest_edge && _primal_initialize_steepest!(workspace)
    entering = 0
    scored = 0
    direction = zero(T)
    best_score = _primal_dantzig_score(one(T))
    negative_tolerance = tolerance
    negative_ready = false
    reuse_negative = pricing === :dantzig || pricing === :devex
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        index in workspace.scratch.rejected_entering && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        reduced_cost = workspace.reduced_costs[index]
        improving = if state == AT_LOWER
            if reuse_negative
                if !negative_ready
                    negative_tolerance = -tolerance
                    negative_ready = true
                end
                reduced_cost < negative_tolerance
            else
                reduced_cost < -tolerance
            end
        else
            (state == AT_UPPER && reduced_cost > tolerance) ||
            (state == FREE_NONBASIC && _primal_direction_magnitude(reduced_cost) > tolerance)
        end
        improving || continue
        scored += 1
        score = if pricing == :dantzig
            _primal_dantzig_score(reduced_cost)
        else
            weight = pricing == :steepest_edge && !workspace.scratch.steepest_valid[index] ?
                _primal_steepest_weight!(workspace, index) : workspace.pricing_weights[index]
            _primal_weighted_score(reduced_cost, weight)
        end
        if entering == 0 || score > best_score
            entering = index
            direction = reduced_cost < 0 ? one(T) : -one(T)
            best_score = score
        end
    end
    _record_full_pricing!(workspace.progress.diagnostics,length(workspace.basis.states),scored)
    return entering, direction
end


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

function _lp_residual_values(::Type{R}, ws, values, multipliers) where R
    m, n = size(ws.problem.A)
    length(values) == n+m && length(multipliers) == m ||
        throw(DimensionMismatch("LP residual coordinates do not match the original model"))
    v, y = _copy_working_values(R, values), _copy_working_values(R, multipliers)
    all(isfinite, v) && all(isfinite, y) || throw(ArgumentError("Nonfinite LP residual candidate"))
    primal = copy(v[n+1:end])
    dual = vcat(_copy_working_values(R, ws.problem.objective), copy(y))
    for j in 1:n, k in nzrange(ws.problem.A, j)
        i, a = ws.problem.A.rowval[k], R(ws.problem.A.nzval[k])
        primal[i] -= a*v[j]
        dual[j] -= a*y[i]
    end
    return LPResiduals(v, y, primal, dual)
end

function _lp_residuals(ws::SimplexWorkspace{T}, values, multipliers;
                       bits::Int=_lp_residual_bits(ws)) where T
    if _is_exact(T) === Val(true)
        return _lp_residual_values(T, ws, values, multipliers)
    end
    actual = max(bits, _working_value_bits(values), _working_value_bits(multipliers))
    return setprecision(BigFloat, actual) do
        _lp_residual_values(BigFloat, ws, values, multipliers)
    end
end


end

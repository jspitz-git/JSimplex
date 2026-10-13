function isolated_pricing_policy(::Type{T}=Float64; enabled=true, window=2) where T
    # All unrelated adaptive mechanisms remain disabled.
    return JSimplex.NumericalPolicy(T; adaptive_stalling=true, adaptive_pricing=enabled,
        stagnation_window=window, refactor_timing=false)
end

function pricing_window!(state, monitor, policy; objective=1)
    for _ in 1:monitor.window
        JSimplex.observe_progress!(monitor; objective, primal_violation=1,
            dual_violation=0, primal_step=0, dual_step=0)
        JSimplex.next_pricing!(state, monitor, policy)
    end
    return state.active
end

function force_pricing_trial!(ws,algorithm)
    JSimplex._prepare_auto_pricing!(ws,algorithm)
    state = ws.scratch.pricing
    state.return_mode = state.active
    state.active = :dantzig
    state.temporary = true
    state.trial_until = 8
    return state
end

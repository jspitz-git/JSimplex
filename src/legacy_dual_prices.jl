# A recomputed working price can cross the feasibility boundary by roundoff
# after a sequence of cost shifts. Maintain that working objective in its own
# type; original-cost restoration and certification still determine the result.
function _shift_marginal_dual_prices!(ws::SimplexWorkspace{T}, stop) where T
    T === Float32 || T === Float64 || return false
    policy = ws.progress.numerical_policy
    (policy.pivot_validation || policy.solve_refinement || policy.recovery) && return false
    _has_active_perturbations(ws.scratch.perturbations) && return false
    ws.perturbed || return false
    isempty(ws.factorization.updates) || return false
    stop() && return false
    tolerance = ws.options.dual_tolerance
    cap = T(4) * tolerance
    zero(T) < tolerance && isfinite(cap) || return false
    margin = tolerance / T(4)
    indices = Int[]
    costs, prices = T[], T[]
    for index in eachindex(ws.basis.states)
        index % 1024 == 0 && stop() && return false
        state = ws.basis.states[index]
        state == BASIC && continue
        _is_fixed(ws.lower[index], ws.upper[index]) && continue
        price = ws.reduced_costs[index]
        isfinite(price) || return false
        _dual_price_feasible(state, price, tolerance) && continue
        abs(price) <= T(2) * tolerance || return false
        target = state == AT_LOWER ? tolerance : state == AT_UPPER ? -tolerance : zero(T)
        old_cost = ws.costs[index]
        new_cost = old_cost + (target - price)
        isfinite(new_cost) || return false
        actual_shift = new_cost - old_cost
        isfinite(actual_shift) && abs(actual_shift) <= cap || return false
        new_price = price + actual_shift
        isfinite(new_price) || return false
        # A large cost may not represent a sufficiently small shift. Require
        # the actual rounded price to have a margin, rather than writing zero.
        feasible = state == AT_LOWER ? new_price >= margin :
                   state == AT_UPPER ? new_price <= -margin : abs(new_price) <= margin
        feasible || return false
        push!(indices, index)
        push!(costs, new_cost)
        push!(prices, new_price)
    end
    isempty(indices) && return false
    stop() && return false
    ws.costs[indices] .= costs
    ws.reduced_costs[indices] .= prices
    _invalidate_pricing_pool!(ws; basis=false)
    _simplex_event!(ws, :perturbation)
    try
        @logmsg ws.options.log_level "Shifted marginal working reduced costs" iterations=ws.iterations shifted=length(indices)
    catch exception
        stop isa _StopCallback && (stop.exception = exception)
        rethrow()
    end
    return true
end

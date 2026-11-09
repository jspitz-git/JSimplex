"""A dual step in the oriented row; `flips` is borrowed until the next proposal."""
struct DualPivotProposal{T}
    entering::Int
    flips::Vector{Int}
    dual_step::T
    outcome::Symbol
end

_ratio_boxed(ws, i) = isfinite(ws.lower[i]) && isfinite(ws.upper[i])

# Rebuild flips at this candidate's actual step. Tolerated price deviations do
# not force a flip. Optional flips are used only to supply displacement that
# the entering variable cannot supply on its own.
function _validate_dual_ratio_candidate!(ws::SimplexWorkspace{T}, row, orientation,
                                        violation, entering, tolerance,
                                        primal_tolerance) where {T}
    flips, optional = ws.scratch.flips, ws.scratch.ratio_optional
    empty!(flips)
    empty!(optional)
    step = ws.scratch.ratio_steps[entering]
    remaining = violation
    for i in eachindex(row)
        state = ws.basis.states[i]
        (state == BASIC || _is_fixed(ws.lower[i], ws.upper[i])) && continue
        coefficient = orientation * row[i]
        price = ws.reduced_costs[i] - step * coefficient
        isfinite(price) || return false
        if i == entering
            abs(price) <= tolerance || return false
            continue
        end
        feasible = _dual_price_feasible(state, price, tolerance)
        can_flip = _ratio_boxed(ws, i) &&
            _dual_pivot_eligible(ws, i, coefficient, zero(T))
        opposite = state == AT_LOWER ? AT_UPPER : AT_LOWER
        can_flip &= _dual_price_feasible(opposite, price, tolerance)
        if !feasible
            can_flip || return false
            gain = ws.scratch.ratio_gains[i]
            remaining -= gain
            isfinite(remaining) && remaining >= -primal_tolerance || return false
            push!(flips, i)
        elseif can_flip
            push!(optional, i)
        end
    end
    remaining >= -primal_tolerance || return false
    if _ratio_boxed(ws, entering)
        capacity = ws.scratch.ratio_gains[entering]
        sort!(optional; by=i -> (ws.scratch.ratio_steps[i],i))
        for i in optional
            remaining <= capacity + primal_tolerance && break
            gain = ws.scratch.ratio_gains[i]
            gain <= remaining + primal_tolerance || continue
            remaining -= gain
            push!(flips, i)
        end
        remaining <= capacity + primal_tolerance || return false
    end
    return remaining >= -primal_tolerance
end

"""
    propose_dual_step!(ws, row, orientation, violation, policy)

Harris bound-flipping ratio test without mutations to prices, primal values,
states or the basis. Breakpoint groups share a relaxed upper step; strong
pivots are tried first within each group. Exact arithmetic uses zero relaxation.
An unsafe coefficient, overflow or exhausted candidate budget yields
`:uncertain`, never an infeasibility certificate.
"""
function propose_dual_step!(ws::SimplexWorkspace{T}, row::Vector{T}, orientation::T,
                            violation::T, policy::NumericalPolicy{T}) where {T}
    length(row) == length(ws.basis.states) || throw(DimensionMismatch("dual tableau row"))
    abs(orientation) == one(T) || throw(ArgumentError("dual orientation must be +1 or -1"))
    isfinite(violation) && violation >= zero(T) || throw(ArgumentError("invalid primal violation"))
    candidates, flips = ws.scratch.candidates, ws.scratch.flips
    empty!(candidates)
    empty!(flips)
    uncertain() = (empty!(flips); DualPivotProposal(-1, flips, zero(T), :uncertain))
    steps, gains = ws.scratch.ratio_steps, ws.scratch.ratio_gains
    resize!(steps, length(row))
    resize!(gains, length(row))
    fill!(gains, zero(T))
    exact = _is_exact(T) === Val(true)
    tolerance = exact ? zero(T) : ws.options.dual_tolerance
    primal_tolerance = exact ? zero(T) : ws.options.primal_tolerance
    cutoff = policy.pivot_validation ? zero(T) : _dual_pivot_cutoff(T)
    rejected = false
    for i in eachindex(row)
        coefficient = orientation * row[i]
        price = ws.reduced_costs[i]
        isfinite(coefficient) && isfinite(price) || return uncertain()
        state = ws.basis.states[i]
        (state == BASIC || _is_fixed(ws.lower[i], ws.upper[i])) && continue
        _dual_price_feasible(state, price, tolerance) || return uncertain()
        _dual_pivot_eligible(ws, i, coefficient, zero(T)) || continue
        if _ratio_boxed(ws, i)
            width = bound_value(ws.upper[i]) - bound_value(ws.lower[i])
            gains[i] = abs(coefficient) * width
            isfinite(width) && isfinite(gains[i]) || return uncertain()
            width > zero(T) && iszero(gains[i]) && return uncertain()
        end
        steps[i] = price / coefficient
        isfinite(steps[i]) || return uncertain()
        if !_dual_pivot_eligible(ws, i, coefficient, cutoff)
            rejected = true
            continue
        end
        push!(candidates, i)
    end
    sort!(candidates; by=i -> (steps[i],i))
    capacity = zero(T)
    unbounded = false
    attempts = 0
    first = 1
    while first <= length(candidates)
        i = candidates[first]
        limit = steps[i] + tolerance / abs(row[i])
        isfinite(limit) || return uncertain()
        last = first
        while last < length(candidates) && steps[candidates[last+1]] <= limit
            last += 1
            j = candidates[last]
            limit = min(limit, steps[j] + tolerance / abs(row[j]))
        end
        for k in first:last
            j = candidates[k]
            if _ratio_boxed(ws, j)
                capacity += gains[j]
                isfinite(capacity) || return uncertain()
            else
                unbounded = true
            end
        end
        if unbounded || capacity + primal_tolerance >= violation
            group = view(candidates, first:last)
            sort!(group; by=j -> (-abs(row[j]),j))
            for j in group
                j in ws.scratch.rejected_entering && continue
                attempts += 1
                attempts <= policy.max_pivot_candidates || return uncertain()
                if _validate_dual_ratio_candidate!(ws, row, orientation, violation,
                                                   j, tolerance, primal_tolerance)
                    return DualPivotProposal(j, flips, steps[j], :pivot)
                end
            end
            # Later steps cannot relax an unbounded variable's restriction.
            unbounded && return uncertain()
        end
        first = last + 1
    end
    (rejected || capacity + primal_tolerance >= violation) && return uncertain()
    empty!(flips)
    return DualPivotProposal(-1, flips, zero(T), :exhausted)
end

# Keep the legacy path unchanged and use the same selection after row refinement.
function _configured_dual_ratio_test(ws::SimplexWorkspace{T}, row::Vector{T},
                                     orientation::T, violation::T) where {T}
    policy = ws.progress.numerical_policy
    result = if policy.stable_ratio
        proposal = propose_dual_step!(ws, row, orientation, violation, policy)
        (proposal.entering, proposal.flips, proposal.outcome == :exhausted)
    else
        _bound_flipping_ratio_test(ws, row, orientation, violation)
    end
    if result[1] == -1 && !isempty(ws.scratch.rejected_entering)
        throw(_PivotRejection(ws.scratch.selected_row,0,:next_row))
    end
    return result
end

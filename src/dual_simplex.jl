_is_numerical_exception(exception) =
    exception isa SingularException || exception isa ZeroPivotException ||
    exception isa _UnreliableBasisSolve

mutable struct _StopCallback{F}
    callback::F
    exception::Any
end

function (stop::_StopCallback)()
    stop.exception = nothing
    try
        return stop.callback()
    catch exception
        stop.exception = exception
        rethrow()
    end
end

# Share provenance across nested numerical catches while rethrowing the
# caller's original callback or logger exception, including
# SingularException/ZeroPivotException. Refactorization logging shares this guard.
_guard_stop_callback(stop::_StopCallback) = stop
_guard_stop_callback(stop) = _StopCallback(stop, nothing)

_numerical_failure() = DualTermination(NUMERICAL_ERROR, "non-finite simplex iterate")

function _finite_workspace(workspace::SimplexWorkspace{T}) where {T}
    return all(isfinite, workspace.primal) && all(isfinite, workspace.reduced_costs) &&
           all(isfinite, workspace.costs) &&
           (_effective_pricing(workspace,:dual) == :dantzig ||
            all(weight -> isfinite(weight) && weight > zero(T), workspace.pricing_weights))
end

# A fresh Float64 LU can produce reduced costs with the wrong sign when the
# basis is ill-conditioned. Refine Bᵀy = c_B using the stored binary64 matrix
# entries, and accept the prices only when two precisions agree well within
# the dual tolerance. This is used only after the ordinary feasibility check
# fails; other numeric types retain their existing behavior.
function _refined_dual_prices(workspace::SimplexWorkspace{Float64}, factor, B,
                              bits::Int, stop_requested)
    return setprecision(BigFloat,bits) do
        basic_costs = workspace.costs[workspace.basis.basic_indices]
        dual = _refined_basis_solution(factor,B,basic_costs,bits,stop_requested;transposed=true)
        isnothing(dual) && return nothing
        A = workspace.problem.A
        row_count,column_count = size(A)
        matrix_values = BigFloat.(A.nzval)
        prices = Vector{BigFloat}(undef,column_count+row_count)
        for column in 1:column_count
            column % 1024 == 0 && stop_requested() && return nothing
            total = zero(BigFloat)
            for position in A.colptr[column]:(A.colptr[column+1]-1)
                total += matrix_values[position]*dual[A.rowval[position]]
            end
            prices[column] = BigFloat(workspace.costs[column])-total
        end
        for row in 1:row_count
            prices[column_count+row] = BigFloat(workspace.costs[column_count+row])+dual[row]
        end
        return prices
    end
end

function _dual_price_feasible(state::VariableState, price, tolerance)
    if state == AT_LOWER
        return price >= -tolerance
    elseif state == AT_UPPER
        return price <= tolerance
    end
    return abs(price) <= tolerance
end

function _try_refine_dual_prices!(workspace::SimplexWorkspace{Float64}, stop_requested)
    isempty(workspace.factorization.updates) || return false
    _simplex_event!(workspace, :correction_attempt)
    B = basis_matrix(workspace)
    factor = try
        lu(B)
    catch exception
        _is_numerical_exception(exception) || rethrow()
        return false
    end
    low = _refined_dual_prices(workspace, factor, B, 256, stop_requested)
    isnothing(low) && return false
    high = _refined_dual_prices(workspace, factor, B, 512, stop_requested)
    isnothing(high) && return false

    tolerance = BigFloat(workspace.options.dual_tolerance)
    agreement = tolerance / 8
    states = workspace.basis.states
    original_column_count = size(workspace.problem.A, 2)
    restored = Int[]
    adjusted_high = copy(high)
    for index in eachindex(low)
        index % 1024 == 0 && stop_requested() && return false
        isfinite(low[index]) && isfinite(high[index]) || return false
        abs(low[index] - high[index]) <= agreement || return false
        state = states[index]
        state == BASIC && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        if !_dual_price_feasible(state, low[index], tolerance) ||
           !_dual_price_feasible(state, high[index], tolerance)
            # A prior cost shift can become harmful after a bound flip.
            # Release it only if both independent price calculations then
            # regain dual feasibility with a margin.
            workspace.perturbed || return false
            original_cost = index <= original_column_count ?
                workspace.problem.objective[index] : 0.0
            original_cost == workspace.costs[index] && return false
            delta = setprecision(BigFloat, 512) do
                BigFloat(original_cost) - BigFloat(workspace.costs[index])
            end
            setprecision(BigFloat, 512) do
                _dual_price_feasible(state, low[index] + delta, agreement) &&
                _dual_price_feasible(state, high[index] + delta, agreement)
            end || return false
            adjusted_high[index] = setprecision(BigFloat, 512) do
                high[index] + delta
            end
            push!(restored, index)
        end
    end

    replacement = Float64.(adjusted_high)
    all(isfinite, replacement) || return false
    replacement[workspace.basis.basic_indices] .= 0.0
    old_prices = copy(workspace.reduced_costs)
    old_costs = workspace.costs[restored]
    for index in restored
        workspace.costs[index] = index <= original_column_count ?
            workspace.problem.objective[index] : 0.0
    end
    workspace.reduced_costs .= replacement
    if dual_infeasibility(workspace) > workspace.options.dual_tolerance
        workspace.costs[restored] .= old_costs
        workspace.reduced_costs .= old_prices
        return false
    end
    _invalidate_pricing_pool!(workspace;basis=false)
    try
        @logmsg workspace.options.log_level "Refined reduced costs after dual feasibility loss" iterations=workspace.iterations restored_costs=length(restored)
    catch exception
        stop_requested isa _StopCallback && (stop_requested.exception = exception)
        rethrow()
    end
    _simplex_event!(workspace, :correction)
    return true
end

_try_refine_dual_prices!(::SimplexWorkspace, stop_requested) = false

# An entering price hidden by Float64 cancellation can become a much larger
# infeasibility when divided by a small pivot. Check the price independently
# before the basis changes and, for a backward Harris step, shift its working
# cost only if binary64 can represent a sufficiently accurate correction.
function _stabilize_small_dual_pivot!(workspace::SimplexWorkspace{Float64},
                                       entering_index::Int, pivot::Float64,
                                       tableau_coefficient::Float64, delta::Float64,
                                       stop_requested)
    abs(pivot) > 10 * _dual_pivot_cutoff(Float64) && return true
    stop_requested() && return false
    B = basis_matrix(workspace)
    factor = try
        lu(B)
    catch exception
        _is_numerical_exception(exception) || rethrow()
        return false
    end
    low = _refined_dual_prices(workspace, factor, B, 256, stop_requested)
    isnothing(low) && return false
    high = _refined_dual_prices(workspace, factor, B, 512, stop_requested)
    isnothing(high) && return false
    tolerance = BigFloat(workspace.options.dual_tolerance)
    margin = tolerance * abs(BigFloat(pivot)) / 8
    for index in eachindex(low)
        index % 1024 == 0 && stop_requested() && return false
        isfinite(low[index]) && isfinite(high[index]) || return false
        abs(low[index] - high[index]) <= tolerance / 8 || return false
        state = workspace.basis.states[index]
        (state == BASIC || _is_fixed(workspace.lower[index], workspace.upper[index])) &&
            continue
        _dual_price_feasible(state, low[index], tolerance) &&
            _dual_price_feasible(state, high[index], tolerance) || return false
    end
    exact_price = high[entering_index]
    abs(low[entering_index] - exact_price) <= margin || return false
    stored_price = workspace.reduced_costs[entering_index]
    old_cost = workspace.costs[entering_index]
    stored_step = stored_price / tableau_coefficient
    isfinite(stored_step) || return false
    # Mirror the existing backward-step shift, including its Float64 rounding,
    # to check whether the outgoing variable would really violate tolerance.
    predicted_cost = stored_step * sign(delta) < 0 ? old_cost - stored_price : old_cost
    isfinite(predicted_cost) || return false
    predicted_price = exact_price + BigFloat(predicted_cost) - BigFloat(old_cost)
    predicted_step = predicted_price / BigFloat(pivot)
    predicted_step * sign(delta) >= -tolerance && return true

    abs(exact_price) <= tolerance || return false
    new_cost = Float64(BigFloat(old_cost) - exact_price)
    isfinite(new_cost) || return false
    residual_price = exact_price + BigFloat(new_cost) - BigFloat(old_cost)
    abs(residual_price) <= margin || return false
    workspace.costs[entering_index] = new_cost
    _invalidate_pricing_pool!(workspace;basis=false)
    workspace.reduced_costs[entering_index] = 0.0
    workspace.perturbed = true
    return true
end

_stabilize_small_dual_pivot!(::SimplexWorkspace, ::Int, pivot, tableau_coefficient, delta,
                             stop_requested) = true

function _dual_prices_feasible_or_refined!(workspace::SimplexWorkspace, stop_requested)
    dual_infeasibility(workspace) <= workspace.options.dual_tolerance && return true
    stop_requested() && return false
    return _try_refine_dual_prices!(workspace, stop_requested)
end

function dual_edge_selection(workspace::SimplexWorkspace{T};force_full::Bool=false)::Int where {T}
    _prepare_auto_pricing!(workspace,:dual)
    state = workspace.scratch.pricing
    isnothing(state) || (state.pricing_passes += 1)
    if _partial_pricing_enabled(workspace,:dual)
        row = _select_workspace_pool!(workspace,:dual;force_full)
        return row == 0 ? -1 : row
    end
    if workspace.options.pricing == :auto && T <: Rational
        return _dual_edge_selection(workspace,Val(Rational{BigInt}))
    elseif workspace.options.pricing == :auto
        return _dual_edge_selection(workspace,Val(:scaled))
    end
    return _dual_edge_selection(workspace,Val(T))
end

function _dual_pricing_score(violation,weight,weighted,::Val{S}) where S
    if S === :scaled
        isfinite(violation) || return (typemax(Int),one(violation))
        # Comparing v/sqrt(w) preserves the order of v^2/w while the existing
        # exponent score avoids overflow and the loss of tiny eligible rows.
        return weighted ? _primal_weighted_score(violation,sqrt(weight)) :
                          _primal_dantzig_score(violation)
    end
    return weighted ? S(violation)^2/S(weight) : S(violation)
end

function _dual_edge_selection(workspace::SimplexWorkspace{T},scoring::Val{S})::Int where {T,S}
    leaving_row = -1
    scored = 0
    best_score = S === :scaled ? _primal_dantzig_score(one(T)) : zero(S)
    weighted = _effective_pricing(workspace,:dual) != :dantzig
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row in workspace.scratch.rejected_rows && continue
        violation = max(_lower_violation(workspace.lower[index], workspace.primal[index]),
                        _upper_violation(workspace.upper[index], workspace.primal[index]))
        violation > workspace.options.primal_tolerance || continue
        scored += 1
        score = _dual_pricing_score(violation,workspace.pricing_weights[index],weighted,scoring)
        if (S === :scaled && leaving_row == -1) || score > best_score
            leaving_row = row
            best_score = score
        end
    end
    _record_full_pricing!(workspace.progress.diagnostics,length(workspace.basis.basic_indices),scored)
    return leaving_row
end

function _dual_pivot_eligible(workspace::SimplexWorkspace{T}, index::Int,
                              coefficient::T, tolerance::T) where {T}
    state = workspace.basis.states[index]
    _is_fixed(workspace.lower[index], workspace.upper[index]) && return false
    return (state == AT_LOWER && coefficient > tolerance) ||
           (state == AT_UPPER && coefficient < -tolerance) ||
           (state == FREE_NONBASIC && abs(coefficient) > tolerance)
end

_dual_pivot_cutoff(::Type{T}) where {T} =
    _is_exact(T) === Val(true) ? zero(T) : _positive_tolerance(T, 1 // 10^7)

# The row is oriented so that a positive dual step repairs the leaving bound.
function dual_ratio_test(workspace::SimplexWorkspace{T}, tableau_row::Vector{T},
                         orientation::T=one(T))::Int where {T}
    candidates = workspace.scratch.candidates
    empty!(candidates)
    maximum_step = _unbounded_bound(T)
    tolerance = workspace.options.dual_tolerance
    cutoff = workspace.progress.numerical_policy.pivot_validation ? zero(T) : _dual_pivot_cutoff(T)
    for index in eachindex(tableau_row)
        coefficient = orientation * tableau_row[index]
        _dual_pivot_eligible(workspace, index, coefficient, cutoff) || continue
        push!(candidates, index)
        relaxed_step = (workspace.reduced_costs[index] +
                        ifelse(coefficient < zero(T), -tolerance, tolerance)) / coefficient
        # An overflowed positive relaxation imposes no finite step limit.
        # The selected pivot's actual step is checked before any update.
        if isfinite(relaxed_step) &&
           (!isfinite(maximum_step) || relaxed_step < bound_value(maximum_step))
            maximum_step = Bound(relaxed_step)
        end
    end

    entering_index = -1
    largest_pivot = zero(T)
    for index in candidates
        index in workspace.scratch.rejected_entering && continue
        coefficient = orientation * tableau_row[index]
        step = workspace.reduced_costs[index] / coefficient
        within_limit = !isfinite(maximum_step) || step <= bound_value(maximum_step)
        if within_limit && abs(coefficient) > largest_pivot
            entering_index = index
            largest_pivot = abs(coefficient)
        end
    end
    return entering_index
end

# Traverse dual breakpoints until the remaining primal violation fits in the
# entering variable's range. Earlier boxed variables may cross to their other
# bound without changing the basis.
function _bound_flipping_ratio_test(workspace::SimplexWorkspace{T}, tableau_row::Vector{T},
                                    orientation::T, violation::T) where {T}
    flips = workspace.scratch.flips
    empty!(flips)
    cutoff = workspace.progress.numerical_policy.pivot_validation ? zero(T) : _dual_pivot_cutoff(T)
    # A boxed variable matters only when it can move in this tableau row.
    # Otherwise keep the linear Harris pass and its stronger pivot choice.
    has_boxed = false
    for index in eachindex(workspace.basis.states)
        if isfinite(workspace.lower[index]) && isfinite(workspace.upper[index]) &&
           _dual_pivot_eligible(workspace, index, orientation * tableau_row[index], cutoff)
            has_boxed = true
            break
        end
    end
    has_boxed || return dual_ratio_test(workspace, tableau_row, orientation), flips, false

    candidates = workspace.scratch.candidates
    empty!(candidates)
    steps = workspace.scratch.ratio_steps
    length(steps) < length(tableau_row) && resize!(steps, length(tableau_row))
    for index in eachindex(tableau_row)
        coefficient = orientation * tableau_row[index]
        _dual_pivot_eligible(workspace, index, coefficient, cutoff) || continue
        step = workspace.reduced_costs[index] / coefficient
        if !isfinite(step) || step < zero(T)
            return dual_ratio_test(workspace, tableau_row, orientation), flips, false
        end
        steps[index] = step
        push!(candidates, index)
    end
    isempty(candidates) && return -1, flips, false
    # Keep the stable ordering (including signed zeros and equal breakpoints),
    # but do not repeat multiplication/division at every sorting comparison.
    sort!(candidates; by=index -> steps[index])

    remaining = violation
    for index in candidates
        state = workspace.basis.states[index]
        opposite = state == AT_LOWER ? workspace.upper[index] : workspace.lower[index]
        if state == FREE_NONBASIC || !isfinite(opposite)
            index in workspace.scratch.rejected_entering && return -1, flips, false
            return index, flips, false
        end
        width = bound_value(workspace.upper[index]) - bound_value(workspace.lower[index])
        gain = abs(tableau_row[index]) * width
        if !isfinite(width) || !isfinite(gain)
            empty!(flips)
            return dual_ratio_test(workspace, tableau_row, orientation), flips, false
        end
        if remaining <= gain + workspace.options.primal_tolerance
            index in workspace.scratch.rejected_entering && return -1, flips, false
            return index, flips, false
        end
        push!(flips, index)
        remaining -= gain
    end
    return -1, flips, true
end

function _apply_bound_flips!(workspace::SimplexWorkspace{T}, flips::Vector{Int}, stop=nothing) where {T}
    isempty(flips) && return true
    A = workspace.problem.A
    column_count = size(A, 2)
    rhs = workspace.scratch.row_rhs
    fill!(rhs, zero(T))
    for index in flips
        state = workspace.basis.states[index]
        change = state == AT_LOWER ?
            bound_value(workspace.upper[index]) - bound_value(workspace.lower[index]) :
            bound_value(workspace.lower[index]) - bound_value(workspace.upper[index])
        if index <= column_count
            for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                rhs[A.rowval[position]] += A.nzval[position] * change
            end
        else
            rhs[index - column_count] -= change
        end
    end
    all(isfinite, rhs) || return false
    # The entering direction may already occupy row_solution.
    basic_change = forward_solve!(workspace.scratch.tau, workspace.factorization, rhs)
    all(isfinite, basic_change) || return false
    _maybe_refine_basis_solve!(basic_change,workspace,rhs,stop) || return false
    for (row, index) in enumerate(workspace.basis.basic_indices)
        isfinite(workspace.primal[index] - basic_change[row]) || return false
    end
    for index in flips
        state = workspace.basis.states[index]
        workspace.basis.states[index] = state == AT_LOWER ? AT_UPPER : AT_LOWER
        workspace.primal[index] = state == AT_LOWER ?
            bound_value(workspace.upper[index]) : bound_value(workspace.lower[index])
    end
    for (row, index) in enumerate(workspace.basis.basic_indices)
        workspace.primal[index] -= basic_change[row]
    end
    if !isnothing(workspace.progress.diagnostics)
        for _ in flips
            _simplex_event!(workspace, :bound_flipped)
        end
    end
    return true
end

function price!(tableau_row::Vector{T}, workspace::SimplexWorkspace{T},
                rho::Vector{T})::Nothing where {T}
    A = workspace.problem.A
    row_count, column_count = size(A)
    for column in 1:column_count
        value = zero(T)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            value += rho[A.rowval[position]] * A.nzval[position]
        end
        tableau_row[column] = value
    end
    for row in 1:row_count
        tableau_row[column_count + row] = -rho[row]
    end
    return nothing
end

function update_duals!(workspace::SimplexWorkspace{T}, tableau_row::Vector{T},
                      leaving_index::Int, entering_index::Int, dual_step::T)::Nothing where {T}
    changed_costs = false
    for index in eachindex(workspace.reduced_costs)
        state = workspace.basis.states[index]
        (state == BASIC || index == entering_index) && continue
        reduced_cost = workspace.reduced_costs[index] - dual_step * tableau_row[index]
        if !_is_fixed(workspace.lower[index], workspace.upper[index])
            tolerance = workspace.options.dual_tolerance
            violated = ((state == AT_LOWER || state == FREE_NONBASIC) && reduced_cost < -tolerance) ||
                       ((state == AT_UPPER || state == FREE_NONBASIC) && reduced_cost > tolerance)
            if violated
                # Shift to zero to leave room for recomputation roundoff.
                workspace.costs[index] -= reduced_cost
                changed_costs = true
                workspace.perturbed = true
                reduced_cost = zero(T)
            end
        end
        workspace.reduced_costs[index] = reduced_cost
    end
    workspace.reduced_costs[leaving_index] = -dual_step
    workspace.reduced_costs[entering_index] = zero(T)
    changed_costs && _invalidate_pricing_pool!(workspace;basis=false)
    return nothing
end

function update_primals!(workspace::SimplexWorkspace{T}, tableau_column::Vector{T},
                        entering_index::Int, leaving_row::Int, primal_step::T)::Nothing where {T}
    for (row, index) in enumerate(workspace.basis.basic_indices)
        workspace.primal[index] -= primal_step * tableau_column[row]
    end
    workspace.primal[entering_index] += primal_step
    return nothing
end

function update_dse!(workspace::SimplexWorkspace{T}, rho::Vector{T}, tableau_column::Vector{T},
                    entering_index::Int, pivot::T, squared_norm::T)::Nothing where {T}
    entering_weight = squared_norm / pivot^2
    tau = _checked_basis_solve!(workspace.scratch.tau,workspace,rho)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        coefficient = tableau_column[row]
        workspace.pricing_weights[index] = max(
            _typed_ratio(T, 1, 10^4), workspace.pricing_weights[index] + coefficient *
            (coefficient * entering_weight - T(2) * tau[row] / pivot),
        )
    end
    workspace.pricing_weights[entering_index] = entering_weight
    return nothing
end

function _switch_dual_pricing_to_devex!(workspace::SimplexWorkspace{T},
                                        stop_requested, reason::String;
                                        stored_weight::Union{Nothing,T}=nothing,
                                        actual_weight::Union{Nothing,T}=nothing) where {T}
    if workspace.options.pricing == :auto
        _reject_auto_weight!(workspace)
    else
        workspace.dual_devex_fallback = true
        reset_devex!(workspace)
    end
    try
        @logmsg workspace.options.log_level "Switching dual pricing to Devex" iteration=workspace.iterations reason stored_weight actual_weight
    catch exception
        stop_requested isa _StopCallback && (stop_requested.exception = exception)
        rethrow()
    end
    return nothing
end

function _recover_invalid_dse_weights!(workspace::SimplexWorkspace{T},
                                       stop_requested) where {T}
    if (_is_exact(T) === Val(false) || workspace.options.pricing == :auto) &&
       _effective_pricing(workspace,:dual) == :steepest_edge &&
       any(weight -> !isfinite(weight) || weight <= zero(T), workspace.pricing_weights)
        _switch_dual_pricing_to_devex!(workspace, stop_requested,
                                       "invalid steepest-edge weight")
        return true
    end
    return false
end

_dse_weight_unreliable(stored::T, actual::T) where {T} =
    !isfinite(actual) || actual <= zero(T) ||
    min(stored, actual) < _typed_ratio(T, 1, 2) * max(stored, actual)

function update_devex!(workspace::SimplexWorkspace{T}, tableau_row::Vector{T},
                       tableau_column::Vector{T}, entering_index::Int,
                       pivot::T)::Nothing where {T}
    reference_weight = zero(T)
    for index in eachindex(tableau_row)
        workspace.devex_reference[index] || continue
        reference_weight += tableau_row[index]^2
    end
    entering_weight = max(one(T), reference_weight / pivot^2)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        candidate = tableau_column[row]^2 * entering_weight
        workspace.pricing_weights[index] = max(workspace.pricing_weights[index], candidate)
    end
    workspace.pricing_weights[entering_index] = entering_weight
    return nothing
end

function update_dual_pricing_weights!(workspace::SimplexWorkspace{T},
                                      rho::Vector{T}, tableau_row::Vector{T},
                                      tableau_column::Vector{T}, entering_index::Int,
                                      pivot::T, dse_weight::T, stop_requested) where {T}
    if _effective_pricing(workspace,:dual) == :steepest_edge
        update_dse!(workspace, rho, tableau_column, entering_index, pivot,
                    dse_weight)
        if !_finite_workspace(workspace)
            _recover_invalid_dse_weights!(workspace, stop_requested) || return false
            _finite_workspace(workspace) || return false
            # The Devex reference is the pre-pivot basis. Account for this
            # pivot before replacing its basis column.
            update_devex!(workspace, tableau_row, tableau_column, entering_index, pivot)
        end
    elseif _effective_pricing(workspace,:dual) == :devex
        update_devex!(workspace, tableau_row, tableau_column, entering_index, pivot)
    end
    return _finite_workspace(workspace)
end

# Give nearly zero nonbasic reduced costs a small, reproducible margin in the
# dual-feasible direction. Only nonbasic costs move, so the current basis dual
# multipliers and every other reduced cost stay unchanged. Original costs are
# restored before the final optimality check.
function _perturb_degenerate_dual_costs!(workspace::SimplexWorkspace{T},
                                         stop_requested) where {T<:AbstractFloat}
    tolerance = workspace.options.dual_tolerance
    indices = Int[]
    costs = T[]
    prices = T[]
    for index in eachindex(workspace.basis.states)
        index % 1024 == 0 && stop_requested() && return -1
        state = workspace.basis.states[index]
        (state == AT_LOWER || state == AT_UPPER) || continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        price = workspace.reduced_costs[index]
        abs(price) <= tolerance || continue
        direction = state == AT_LOWER ? one(T) : -one(T)
        target = tolerance * T(8 + index % 16)
        isfinite(target) || continue
        old_cost = workspace.costs[index]
        requested_shift = direction * target - price
        new_cost = old_cost + requested_shift
        new_cost == old_cost && continue
        isfinite(new_cost) || continue
        actual_shift = new_cost - old_cost
        # A single ulp of a large cost can dwarf the intended margin.
        abs(actual_shift) <= 2abs(requested_shift) || continue
        new_price = price + actual_shift
        isfinite(new_price) && direction * new_price > tolerance || continue
        push!(indices, index)
        push!(costs, new_cost)
        push!(prices, new_price)
    end
    isempty(indices) && return 0
    previous_costs = workspace.costs[indices]
    previous_prices = workspace.reduced_costs[indices]
    previous_perturbed = workspace.perturbed
    workspace.costs[indices] .= costs
    workspace.reduced_costs[indices] .= prices
    if !_finite_workspace(workspace) ||
       dual_infeasibility(workspace) > tolerance
        workspace.costs[indices] .= previous_costs
        workspace.reduced_costs[indices] .= previous_prices
        workspace.perturbed = previous_perturbed
        return 0
    end
    workspace.perturbed = true
    _invalidate_pricing_pool!(workspace;basis=false)
    try
        @logmsg workspace.options.log_level "Perturbed dual costs after zero-step stall" iteration=workspace.iterations shifted=length(indices)
    catch exception
        stop_requested isa _StopCallback && (stop_requested.exception = exception)
        rethrow()
    end
    isempty(indices) || _simplex_event!(workspace, :perturbation)
    return length(indices)
end

function dual_iteration!(workspace::SimplexWorkspace{T}, stop_requested;
                         perturb_degenerate::Bool=true)::Union{Nothing,DualTermination} where {T}
    stop_requested = _guard_stop_callback(stop_requested)
    stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
    _prepare_auto_pricing!(workspace,:dual;stop=stop_requested) ||
        return DualTermination(TIME_LIMIT,"time limit reached during pricing recovery")
    try
        if !_finite_workspace(workspace)
            _recover_invalid_dse_weights!(workspace, stop_requested) ||
                return _numerical_failure()
            _finite_workspace(workspace) || return _numerical_failure()
        end
        return _dual_iteration!(workspace, stop_requested, false, perturb_degenerate)
    catch exception
        exception === stop_requested.exception && rethrow()
        _is_numerical_exception(exception) || rethrow()
        return DualTermination(NUMERICAL_ERROR, sprint(showerror, exception))
    end
end

function _add_product_bounds(lower::T, upper::T, left::T, right::T) where {T<:AbstractFloat}
    (iszero(left) || iszero(right)) && return lower, upper
    product = left * right
    return prevfloat(lower + prevfloat(product)), nextfloat(upper + nextfloat(product))
end

function _floating_infeasibility_certified(workspace::SimplexWorkspace{T},
                                          rho::Vector{T}, below::Bool) where {T<:AbstractFloat}
    # Every feasible working vector satisfies [A -I] * x == 0. A row
    # combination whose minimum over the bounds is strictly positive proves
    # a contradiction without relying on the computed basic primal values.
    A = workspace.problem.A
    column_count = size(A, 2)
    orientation = below ? one(T) : -one(T)
    minimum_value = zero(T)
    for index in eachindex(workspace.lower)
        coefficient_lower = coefficient_upper = zero(T)
        if index <= column_count
            for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                coefficient_lower, coefficient_upper = _add_product_bounds(
                    coefficient_lower, coefficient_upper,
                    orientation * rho[A.rowval[position]], A.nzval[position],
                )
            end
        else
            coefficient_lower = coefficient_upper = -orientation * rho[index - column_count]
        end
        isfinite(coefficient_lower) && isfinite(coefficient_upper) || return false
        iszero(coefficient_lower) && iszero(coefficient_upper) && continue

        lower, upper = workspace.lower[index], workspace.upper[index]
        !isfinite(lower) && coefficient_upper > zero(T) && return false
        !isfinite(upper) && coefficient_lower < zero(T) && return false
        isfinite(lower) || isfinite(upper) || return false
        endpoint = isfinite(lower) ? bound_value(lower) : bound_value(upper)
        term = min(coefficient_lower * endpoint, coefficient_upper * endpoint)
        if isfinite(lower) && isfinite(upper)
            endpoint = bound_value(upper)
            term = min(term, coefficient_lower * endpoint, coefficient_upper * endpoint)
        end
        isfinite(term) || return false
        total = minimum_value + prevfloat(term)
        isfinite(total) || return false
        minimum_value = prevfloat(total)
    end
    return minimum_value > zero(T)
end

function _dual_direction_residual_ok!(workspace::SimplexWorkspace{T},
                                      direction::Vector{T}, pivot::T) where {T<:AbstractFloat}
    A = workspace.problem.A
    column_count = size(A, 2)
    residual = workspace.scratch.tau
    scale = workspace.scratch.row_rhs
    for row in eachindex(residual)
        rhs = scale[row]
        residual[row] = -rhs
        scale[row] = abs(rhs)
    end
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        value = direction[basis_row]
        if index <= column_count
            for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                row = A.rowval[position]
                term = A.nzval[position] * value
                residual[row] += term
                scale[row] += abs(term)
            end
        else
            row = index - column_count
            residual[row] -= value
            scale[row] += abs(value)
        end
    end
    roundoff = T(256) * eps(one(T))
    pivot_tolerance = sqrt(eps(one(T))) * abs(pivot)
    for row in eachindex(residual)
        isfinite(residual[row]) && isfinite(scale[row]) || return false
        tolerance = max(workspace.options.zero_tolerance, pivot_tolerance,
                        roundoff * (scale[row] + one(T)))
        abs(residual[row]) <= tolerance || return false
    end
    return true
end

# The entering direction can be accurate even when an updated factorization
# gives an inaccurate tableau row and therefore the wrong ratio-test choice.
# Check Bᵀ*rho = e_leaving against the current basis before the ratio test.
function _dual_row_residual_ratio(workspace::SimplexWorkspace{T},
                                  rho::Vector{T}, leaving_row::Int) where {T<:AbstractFloat}
    A = workspace.problem.A
    column_count = size(A, 2)
    roundoff = T(256) * eps(one(T))
    worst_ratio = zero(T)
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        expected = basis_row == leaving_row ? one(T) : zero(T)
        residual = -expected
        scale = expected
        if index <= column_count
            for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                term = A.nzval[position] * rho[A.rowval[position]]
                residual += term
                scale += abs(term)
            end
        else
            term = -rho[index - column_count]
            residual += term
            scale += abs(term)
        end
        isfinite(residual) && isfinite(scale) || return T(Inf)
        tolerance = max(workspace.options.zero_tolerance,
                        roundoff * (scale + one(T)))
        isfinite(tolerance) || return T(Inf)
        worst_ratio = max(worst_ratio, abs(residual) / tolerance)
    end
    return worst_ratio
end

# A second inaccurate updated solve within three clean factorization cycles
# lowers the update limit to at most half the earliest observed failure count,
# with a minimum of one. Each clean cycle doubles a shortened interval back
# toward the user's configured value; growth above it remains more cautious.
function _note_dual_updated_basis_repair!(workspace::SimplexWorkspace)
    _simplex_event!(workspace, :repair)
    if workspace.progress.numerical_policy.adaptive_refactor
        workspace.scratch.refactorization.residual_bad = true
        return nothing
    end
    updates = length(workspace.factorization.updates)
    updates > 0 || return nothing
    workspace.dual_recent_repairs += 1
    workspace.dual_bad_update_min = min(workspace.dual_bad_update_min, updates)
    workspace.dual_stable_refactorizations = 0
    if workspace.dual_recent_repairs >= 2
        workspace.dual_refactorization_interval = min(
            workspace.dual_refactorization_interval,
            max(1, workspace.dual_bad_update_min ÷ 2),
        )
        workspace.dual_recent_repairs = 0
        workspace.dual_bad_update_min = typemax(Int)
    end
    return nothing
end

function _dual_refactorization_growth_ceiling(workspace::SimplexWorkspace)
    configured = workspace.options.refactorization_interval
    # The measured runtime.mps prefix favored longer product-form chains
    # than triangular chains; keep the initial growth ceilings conservative.
    floor, multiplier = workspace.factorization isa PFIFactorization ? (512, 8) : (128, 4)
    scaled = configured > 4096 ÷ multiplier ? 4096 : multiplier * configured
    return max(configured, min(4096, max(floor, scaled)))
end

function _note_stable_dual_refactorization!(workspace::SimplexWorkspace,
                                             productive::Bool)
    configured = workspace.options.refactorization_interval
    interval = workspace.dual_refactorization_interval
    if interval < configured
        workspace.dual_recent_repairs = 0
        workspace.dual_bad_update_min = typemax(Int)
        workspace.dual_refactorization_interval = interval > configured ÷ 2 ?
            configured : 2 * interval
        workspace.dual_stable_refactorizations = 0
        return nothing
    end
    if workspace.dual_recent_repairs > 0
        workspace.dual_stable_refactorizations += 1
        if workspace.dual_stable_refactorizations >= 3
            workspace.dual_recent_repairs = 0
            workspace.dual_bad_update_min = typemax(Int)
            workspace.dual_stable_refactorizations = 0
        end
        return nothing
    end
    ceiling = _dual_refactorization_growth_ceiling(workspace)
    if !productive || workspace.dual_pricing_fallback || interval >= ceiling
        workspace.dual_stable_refactorizations = 0
        return nothing
    end
    workspace.dual_stable_refactorizations += 1
    if workspace.dual_stable_refactorizations >= 3
        workspace.dual_refactorization_interval = interval > ceiling ÷ 2 ?
            ceiling : 2 * interval
        workspace.dual_stable_refactorizations = 0
    end
    return nothing
end

# A fresh floating LU can still give an inaccurate direction for an
# ill-conditioned basis. Correct B*d = a in higher precision using the same
# binary64 matrix entries; this path runs only after the ordinary solve and
# a refactorized retry have both failed their residual checks.
function _refined_primal_direction(factor,B,rhs::Vector{Float64},bits::Int,stop_requested)
    return _refined_basis_solution(factor,B,rhs,bits,stop_requested)
end

function _refined_tableau_row(workspace::SimplexWorkspace{Float64},factor,B,
                              leaving_row::Int,bits::Int,stop_requested)
    return setprecision(BigFloat,bits) do
        unit = zeros(Float64,size(B,1))
        unit[leaving_row] = 1.0
        rho = _refined_basis_solution(factor,B,unit,bits,stop_requested;transposed=true)
        isnothing(rho) && return nothing
        A = workspace.problem.A
        row_count,column_count = size(A)
        matrix_values = BigFloat.(A.nzval)
        tableau = Vector{BigFloat}(undef,column_count+row_count)
        for column in 1:column_count
            column % 1024 == 0 && stop_requested() && return nothing
            total = zero(BigFloat)
            for position in A.colptr[column]:(A.colptr[column+1]-1)
                total += matrix_values[position]*rho[A.rowval[position]]
            end
            tableau[column] = total
        end
        for row in 1:row_count
            tableau[column_count+row] = -rho[row]
        end
        return (rho=rho,tableau=tableau)
    end
end

function _try_refine_dual_direction!(workspace::SimplexWorkspace{Float64},
                                      entering_index::Int, leaving_row::Int,
                                      original_pivot::Float64,
                                      tableau_coefficient::Float64,
                                      stop_requested)
    isempty(workspace.factorization.updates) || return false
    stop_requested() && return false
    B = basis_matrix(workspace)
    factor = try
        lu(B)
    catch exception
        _is_numerical_exception(exception) || rethrow()
        return false
    end
    rhs = zeros(Float64, size(B, 1))
    A = workspace.problem.A
    column_count = size(A, 2)
    if entering_index <= column_count
        for position in A.colptr[entering_index]:(A.colptr[entering_index + 1] - 1)
            rhs[A.rowval[position]] = A.nzval[position]
        end
    else
        rhs[entering_index - column_count] = -1.0
    end
    low, high = try
        low = _refined_primal_direction(factor, B, rhs, 256, stop_requested)
        isnothing(low) && return false
        high = _refined_primal_direction(factor, B, rhs, 512, stop_requested)
        low, high
    catch exception
        _is_numerical_exception(exception) || rethrow()
        return false
    end
    isnothing(high) && return false
    agreement = BigFloat(1e-24)
    for index in eachindex(low)
        index % 1024 == 0 && stop_requested() && return false
        isfinite(low[index]) && isfinite(high[index]) || return false
        abs(low[index] - high[index]) <= agreement * max(one(BigFloat), abs(high[index])) ||
            return false
    end
    replacement = Float64.(high)
    all(isfinite, replacement) || return false
    refined_pivot = replacement[leaving_row]
    abs(refined_pivot) > max(workspace.options.zero_tolerance,
                             _dual_pivot_cutoff(Float64)) || return false
    tolerance = max(workspace.options.zero_tolerance, 1e-8 * abs(refined_pivot))
    abs(refined_pivot - original_pivot) <= tolerance || return false
    abs(refined_pivot - tableau_coefficient) <= tolerance || return false
    copyto!(workspace.scratch.row_rhs, rhs)
    _dual_direction_residual_ok!(workspace, replacement, refined_pivot) || return false
    copyto!(workspace.scratch.row_solution, replacement)
    return true
end

_try_refine_dual_direction!(::SimplexWorkspace, ::Int, ::Int, pivot,
                            tableau_coefficient, stop_requested) = false

# When the corrected direction disagrees with the floating tableau row,
# rebuild the complete pivot decision from the same basis. A more accurate
# dual price can select a different entering variable, so the direction must
# be solved for the newly chosen column.
function _try_refine_dual_pivot!(workspace::SimplexWorkspace{Float64},
                                  leaving_row::Int,
                                  orientation::Float64, violation::Float64,
                                  stop_requested)
    isempty(workspace.factorization.updates) || return nothing
    stop_requested() && return nothing
    B = basis_matrix(workspace)
    factor = try
        lu(B)
    catch exception
        _is_numerical_exception(exception) || rethrow()
        return nothing
    end
    refined = try
        low_row = _refined_tableau_row(workspace, factor, B, leaving_row, 256,
                                        stop_requested)
        isnothing(low_row) && return nothing
        high_row = _refined_tableau_row(workspace, factor, B, leaving_row, 512,
                                         stop_requested)
        isnothing(high_row) && return nothing
        low_prices = _refined_dual_prices(workspace, factor, B, 256, stop_requested)
        isnothing(low_prices) && return nothing
        high_prices = _refined_dual_prices(workspace, factor, B, 512, stop_requested)
        isnothing(high_prices) && return nothing
        (low_row, high_row, low_prices, high_prices)
    catch exception
        _is_numerical_exception(exception) || rethrow()
        return nothing
    end
    low_row, high_row, low_prices, high_prices = refined
    agreement = BigFloat(1e-24)
    for (low, high) in ((low_row.rho, high_row.rho),
                        (low_row.tableau, high_row.tableau))
        for index in eachindex(low)
            index % 1024 == 0 && stop_requested() && return nothing
            isfinite(low[index]) && isfinite(high[index]) || return nothing
            abs(low[index] - high[index]) <= agreement *
                max(one(BigFloat), abs(high[index])) || return nothing
        end
    end
    price_tolerance = BigFloat(workspace.options.dual_tolerance)
    for index in eachindex(low_prices)
        index % 1024 == 0 && stop_requested() && return nothing
        isfinite(low_prices[index]) && isfinite(high_prices[index]) || return nothing
        abs(low_prices[index] - high_prices[index]) <= price_tolerance / 8 ||
            return nothing
        state = workspace.basis.states[index]
        (state == BASIC || _is_fixed(workspace.lower[index], workspace.upper[index])) &&
            continue
        _dual_price_feasible(state, low_prices[index], price_tolerance) &&
            _dual_price_feasible(state, high_prices[index], price_tolerance) ||
            return nothing
    end
    rho = Float64.(high_row.rho)
    tableau = Float64.(high_row.tableau)
    prices = Float64.(high_prices)
    all(isfinite, rho) && all(isfinite, tableau) && all(isfinite, prices) ||
        return nothing
    prices[workspace.basis.basic_indices] .= 0.0
    previous_prices = copy(workspace.reduced_costs)
    accepted = false
    try
        copyto!(workspace.reduced_costs, prices)
        dual_infeasibility(workspace) <= workspace.options.dual_tolerance || return nothing
        entering_index, flips, exhausted = _configured_dual_ratio_test(
            workspace, tableau, orientation, violation)
        entering_index != -1 && !exhausted || return nothing
        stop_requested() && return nothing
        rhs = zeros(Float64, size(B, 1))
        A = workspace.problem.A
        column_count = size(A, 2)
        if entering_index <= column_count
            for position in A.colptr[entering_index]:(A.colptr[entering_index + 1] - 1)
                rhs[A.rowval[position]] = A.nzval[position]
            end
        else
            rhs[entering_index - column_count] = -1.0
        end
        directions = try
            low = _refined_primal_direction(factor, B, rhs, 256, stop_requested)
            isnothing(low) && return nothing
            high = _refined_primal_direction(factor, B, rhs, 512, stop_requested)
            isnothing(high) && return nothing
            (low, high)
        catch exception
            _is_numerical_exception(exception) || rethrow()
            return nothing
        end
        low_direction, high_direction = directions
        for index in eachindex(low_direction)
            index % 1024 == 0 && stop_requested() && return nothing
            isfinite(low_direction[index]) && isfinite(high_direction[index]) ||
                return nothing
            abs(low_direction[index] - high_direction[index]) <= agreement *
                max(one(BigFloat), abs(high_direction[index])) || return nothing
        end
        direction = Float64.(high_direction)
        all(isfinite, direction) || return nothing
        pivot = direction[leaving_row]
        abs(pivot) > max(workspace.options.zero_tolerance,
                         _dual_pivot_cutoff(Float64)) || return nothing
        abs(pivot - tableau[entering_index]) <=
            max(workspace.options.zero_tolerance, 1e-8 * abs(pivot)) || return nothing
        copyto!(workspace.scratch.row_rhs, rhs)
        _dual_direction_residual_ok!(workspace, direction, pivot) || return nothing
        copyto!(workspace.scratch.row_solution, direction)
        copyto!(workspace.scratch.tableau_row, tableau)
        copyto!(workspace.scratch.rho, rho)
        accepted = true
        return (entering_index=entering_index, flips=flips, pivot=pivot)
    finally
        accepted || copyto!(workspace.reduced_costs, previous_prices)
    end
end

_try_refine_dual_pivot!(::SimplexWorkspace, ::Int, orientation, violation,
                        stop_requested) = nothing

function _dual_iteration_unchecked!(workspace::SimplexWorkspace{T}, stop_requested,
                          basis_refreshed::Bool=false,
                          perturb_degenerate::Bool=true;
                          force_full_pricing::Bool=false) where {T}
    _simplex_event!(workspace, :pricing)
    leaving_row = _timed_simplex(workspace, :pricing) do
        dual_edge_selection(workspace;force_full=force_full_pricing)
    end
    if leaving_row == -1
        isempty(workspace.scratch.rejected_rows) || throw(_PivotRejection(0,0,:exhausted))
        return DualTermination(OPTIMAL, "optimal solution found")
    end
    workspace.scratch.selected_row = leaving_row
    _simplex_event!(workspace, :pivot_proposed)
    leaving_index = workspace.basis.basic_indices[leaving_row]
    below = _lower_violation(workspace.lower[leaving_index], workspace.primal[leaving_index]) > zero(T)
    bound = below ? workspace.lower[leaving_index] : workspace.upper[leaving_index]
    delta = workspace.primal[leaving_index] - bound_value(bound)

    row_count, column_count = size(workspace.problem.A)
    unit = workspace.scratch.row_rhs
    fill!(unit, zero(T))
    unit[leaving_row] = one(T)
    rho = _timed_simplex(workspace, :btran) do
        transpose_solve!(workspace.scratch.rho, workspace.factorization, unit)
    end
    policy = workspace.progress.numerical_policy
    if policy.pivot_validation || policy.solve_refinement
        quality = refine_basis_solve!(rho,workspace,unit,policy,stop_requested;transposed=true)
        policy.solve_refinement && !quality.reliable && throw(_UnreliableBasisSolve())
    end
    tableau_row = workspace.scratch.tableau_row
    _timed_simplex(workspace, :pricing) do
        price!(tableau_row, workspace, rho)
    end
    all(isfinite, rho) && all(isfinite, tableau_row) || return _numerical_failure()
    if _is_exact(T) === Val(false) && !isempty(workspace.factorization.updates)
        row_residual_ratio = _dual_row_residual_ratio(workspace, rho, leaving_row)
        if row_residual_ratio > one(T)
            basis_refreshed &&
                return DualTermination(NUMERICAL_ERROR, "basis transpose solve residual too large")
            stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
            _note_dual_updated_basis_repair!(workspace)
            try
                @logmsg workspace.options.log_level "Refactorizing inaccurate dual tableau row" iteration=workspace.iterations updates=length(workspace.factorization.updates) row_residual_ratio
            catch exception
                stop_requested isa _StopCallback && (stop_requested.exception = exception)
                rethrow()
            end
            recompute!(workspace; refactorize=true, caller_guard=stop_requested,
                       diagnostic_reason=:refactor_residual)
            stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
            _finite_workspace(workspace) || return _numerical_failure()
            if !_dual_prices_feasible_or_refined!(workspace, stop_requested)
                stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
                return DualTermination(NUMERICAL_ERROR, "dual feasibility lost")
            end
            return _dual_iteration_unchecked!(workspace, stop_requested, true, perturb_degenerate)
        end
    end
    dse_weight = zero(T)
    if !_validate_dual_edge!(workspace,leaving_index,rho)
        stop_requested() && return DualTermination(TIME_LIMIT,"time limit reached during pricing recovery")
        return _dual_iteration_unchecked!(workspace,stop_requested,basis_refreshed,perturb_degenerate)
    end
    if _effective_pricing(workspace,:dual) == :steepest_edge &&
       _is_exact(T) === Val(false)
        dse_weight = dot(rho, rho)
        stored_weight = workspace.pricing_weights[leaving_index]
        if workspace.options.pricing != :auto && _dse_weight_unreliable(stored_weight, dse_weight)
            _switch_dual_pricing_to_devex!(workspace, stop_requested,
                                           "steepest-edge weight disagrees with basis solve";
                                           stored_weight, actual_weight=dse_weight)
            return _dual_iteration_unchecked!(workspace, stop_requested, basis_refreshed,
                                    perturb_degenerate)
        end
    end
    orientation = below ? -one(T) : one(T)
    entering_index, flips, exhausted = _configured_dual_ratio_test(
        workspace, tableau_row, orientation, abs(delta),
    )
    workspace.scratch.selected_entering = entering_index
    if entering_index == -1
        if workspace.progress.numerical_policy.stable_ratio && !exhausted
            return DualTermination(NUMERICAL_ERROR, "stable dual ratio test is numerically uncertain")
        end
        # A tolerance cannot turn a nonzero, sign-eligible coefficient into a
        # mathematical infeasibility proof.
        if any(index -> begin
                   coefficient = orientation * tableau_row[index]
                   _dual_pivot_eligible(workspace, index, coefficient, zero(T)) &&
                       (!exhausted || !_dual_pivot_eligible(workspace, index, coefficient,
                                                             _dual_pivot_cutoff(T)))
               end, eachindex(tableau_row))
            return DualTermination(NUMERICAL_ERROR, "eligible pivots are below the Harris safety cutoff")
        end
        if _is_exact(T) === Val(false) && !basis_refreshed
            # Incremental floating updates can drift outside primal tolerance.
            # Rebuild once and repeat the test before certifying infeasibility.
            stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
            recompute!(workspace; refactorize=true, caller_guard=stop_requested)
            stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
            _finite_workspace(workspace) || return _numerical_failure()
            if !_dual_prices_feasible_or_refined!(workspace, stop_requested)
                stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
                return DualTermination(NUMERICAL_ERROR, "dual feasibility lost")
            end
            return _dual_iteration_unchecked!(workspace, stop_requested, true, perturb_degenerate)
        end
        pool = workspace.scratch.pricing_pool
        if _partial_pricing_enabled(workspace,:dual) && !isnothing(pool) && !pool.full_scan
            full_row = dual_edge_selection(workspace;force_full=true)
            if full_row != leaving_row
                return _dual_iteration_unchecked!(workspace,stop_requested,basis_refreshed,
                    perturb_degenerate;force_full_pricing=true)
            end
        end
        if _is_exact(T) === Val(false) && !_floating_infeasibility_certified(workspace, rho, below)
            return DualTermination(NUMERICAL_ERROR,
                                   "floating row combination does not certify infeasibility")
        end
        return DualTermination(INFEASIBLE, "no eligible dual pivot")
    end

    column = workspace.scratch.row_rhs
    fill!(column, zero(T))
    if entering_index <= column_count
        A = workspace.problem.A
        for position in A.colptr[entering_index]:(A.colptr[entering_index + 1] - 1)
            column[A.rowval[position]] = A.nzval[position]
        end
    else
        column[entering_index - column_count] = -one(T)
    end
    tableau_column = _timed_simplex(workspace, :ftran) do
        forward_solve!(workspace.scratch.row_solution, workspace.factorization, column)
    end
    if policy.pivot_validation || policy.solve_refinement
        quality = refine_basis_solve!(tableau_column,workspace,column,policy,stop_requested)
        policy.solve_refinement && !quality.reliable && throw(_UnreliableBasisSolve())
    end
    all(isfinite, tableau_column) || return _numerical_failure()
    pivot = tableau_column[leaving_row]
    refined_row = false
    # An updated factorization can invent a nonzero pivot even when its
    # magnitude is well above the ratio-test cutoff. Check every floating
    # direction against the current basis before accepting it.
    if _is_exact(T) === Val(false) &&
       !_dual_direction_residual_ok!(workspace, tableau_column, pivot)
        if !basis_refreshed
            stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
            _note_dual_updated_basis_repair!(workspace)
            recompute!(workspace; refactorize=true, caller_guard=stop_requested,
                       diagnostic_reason=:refactor_residual)
            stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
            _finite_workspace(workspace) || return _numerical_failure()
            if !_dual_prices_feasible_or_refined!(workspace, stop_requested)
                stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
                return DualTermination(NUMERICAL_ERROR, "dual feasibility lost")
            end
            return _dual_iteration_unchecked!(workspace, stop_requested, true, perturb_degenerate)
        end
        if _try_refine_dual_direction!(workspace, entering_index, leaving_row,
                                       pivot, tableau_row[entering_index],
                                       stop_requested)
            refined_pivot = tableau_column[leaving_row]
            try
                @info "Refined dual pivot direction" iteration=workspace.iterations leaving_row entering_index old_pivot=pivot refined_pivot
            catch exception
                stop_requested isa _StopCallback && (stop_requested.exception = exception)
                rethrow()
            end
            pivot = refined_pivot
        elseif (decision = _try_refine_dual_pivot!(
                    workspace, leaving_row, orientation, abs(delta), stop_requested)) !== nothing
            original_entering_index = entering_index
            entering_index = decision.entering_index
            flips = decision.flips
            refined_pivot = decision.pivot
            try
                @info "Refined dual pivot row, direction, and prices" iteration=workspace.iterations leaving_row original_entering_index entering_index old_pivot=pivot refined_pivot
            catch exception
                stop_requested isa _StopCallback && (stop_requested.exception = exception)
                rethrow()
            end
            pivot = refined_pivot
            refined_row = true
        else
            stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
            residual = workspace.scratch.tau
            scale = workspace.scratch.row_rhs
            roundoff = T(256) * eps(one(T))
            pivot_tolerance = sqrt(eps(one(T))) * abs(pivot)
            worst_row = firstindex(residual)
            worst_ratio = zero(T)
            for row in eachindex(residual)
                tolerance = max(workspace.options.zero_tolerance, pivot_tolerance,
                                roundoff * (scale[row] + one(T)))
                ratio = abs(residual[row]) / tolerance
                if !isfinite(ratio) || ratio > worst_ratio
                    worst_row = row
                    worst_ratio = ratio
                end
            end
            try
                @info "Rejected dual pivot after basis refresh" iteration=workspace.iterations leaving_row entering_index pivot tableau_coefficient=tableau_row[entering_index] worst_row worst_ratio residual=residual[worst_row]
            catch exception
                stop_requested isa _StopCallback && (stop_requested.exception = exception)
                rethrow()
            end
            return DualTermination(NUMERICAL_ERROR, "basis solve residual too large")
        end
    end
    checked_pivot = workspace.progress.numerical_policy.pivot_validation
    if checked_pivot
        proposal = PivotCandidate(entering_index,leaving_row,
                                  tableau_row[entering_index],tableau_column,rho)
        quality = validate_pivot!(workspace,proposal,workspace.progress.numerical_policy)
        quality == :accept || throw(_PivotRejection(leaving_row,entering_index,quality))
    end
    if !checked_pivot && abs(pivot) <= workspace.options.zero_tolerance &&
       _is_exact(T) === Val(false) && !basis_refreshed
        # A small pivot can result from drift in the updated factorization.
        # Rebuild the current basis and repeat the iteration once.
        stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
        recompute!(workspace; refactorize=true, caller_guard=stop_requested)
        stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
        _finite_workspace(workspace) || return _numerical_failure()
        if !_dual_prices_feasible_or_refined!(workspace, stop_requested)
            stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
            return DualTermination(NUMERICAL_ERROR, "dual feasibility lost")
        end
        return _dual_iteration_unchecked!(workspace, stop_requested, true, perturb_degenerate)
    end
    (checked_pivot || abs(pivot) > workspace.options.zero_tolerance) || throw(ZeroPivotException(leaving_row))
    if !_stabilize_small_dual_pivot!(workspace, entering_index, pivot,
                                     tableau_row[entering_index], delta, stop_requested)
        stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
        return DualTermination(NUMERICAL_ERROR, "small pivot dual price could not be certified")
    end
    if refined_row && _effective_pricing(workspace,:dual) == :steepest_edge
        dse_weight = dot(rho, rho)
        stored_weight = workspace.pricing_weights[leaving_index]
        if workspace.options.pricing == :auto
            _validate_dual_edge!(workspace,leaving_index,rho)
        elseif _dse_weight_unreliable(stored_weight, dse_weight)
            _switch_dual_pricing_to_devex!(workspace, stop_requested,
                                           "refined steepest-edge weight disagrees with basis solve";
                                           stored_weight, actual_weight=dse_weight)
        end
    end
    # A refresh can retry the ratio test. Keep the proposed flips pending
    # until the entering direction has passed its numerical checks.
    _apply_bound_flips!(workspace, flips, stop_requested) || return _numerical_failure()
    delta = workspace.primal[leaving_index] - bound_value(bound)
    primal_step = delta / pivot
    dual_step = workspace.reduced_costs[entering_index] / tableau_row[entering_index]
    isfinite(primal_step) && isfinite(dual_step) || return _numerical_failure()
    if dual_step * sign(delta) < zero(T)
        # Harris may accept a reduced cost on the infeasible side of zero,
        # within dual tolerance. Do not move backwards in the dual direction.
        workspace.costs[entering_index] -= workspace.reduced_costs[entering_index]
        _invalidate_pricing_pool!(workspace;basis=false)
        workspace.reduced_costs[entering_index] = zero(T)
        workspace.perturbed = true
        dual_step = zero(T)
    end
    update_duals!(workspace, tableau_row, leaving_index, entering_index, dual_step)
    update_primals!(workspace, tableau_column, entering_index, leaving_row, primal_step)
    if _effective_pricing(workspace,:dual) == :steepest_edge &&
       _is_exact(T) === Val(true)
        dse_weight = dot(rho, rho)
    end
    update_dual_pricing_weights!(workspace, rho, tableau_row, tableau_column,
                                 entering_index, pivot, dse_weight, stop_requested) ||
        return _numerical_failure()
    _replace_pivot_column!(workspace, tableau_column, leaving_row;
                           stop_requested,
                           zero_tolerance=checked_pivot ? zero(T) : workspace.options.zero_tolerance)
    workspace.basis.basic_indices[leaving_row] = entering_index
    workspace.basis.states[entering_index] = BASIC
    workspace.basis.states[leaving_index] = below ? AT_LOWER : AT_UPPER
    _advance_pricing_basis!(workspace)
    workspace.primal[leaving_index] = bound_value(bound)
    # Count the completed pivot even when its subsequent refactorization times out.
    _note_refactor_step!(workspace,dual_step)
    workspace.scratch.last_primal_step = primal_step
    workspace.scratch.last_dual_step = dual_step
    workspace.iterations += 1
    _simplex_event!(workspace, :pivot_completed)
    if _is_staged_workspace(workspace)
        workspace.scratch.post_iteration = :dual
        workspace.scratch.post_dual_step = dual_step
        workspace.scratch.post_basis_refreshed = basis_refreshed
        workspace.scratch.post_perturb_degenerate = perturb_degenerate
        return nothing
    end
    return _dual_after_iteration!(workspace,stop_requested,dual_step,basis_refreshed,perturb_degenerate)
end

function _dual_after_iteration!(workspace::SimplexWorkspace{T},stop_requested,dual_step::T,
                                basis_refreshed::Bool,perturb_degenerate::Bool) where {T}
    if _is_exact(T) === Val(false) && !iszero(dual_step)
        workspace.dual_nonzero_steps_since_refactorization += 1
    end
    if _is_exact(T) === Val(false)
        workspace.zero_dual_step_streak = iszero(dual_step) ?
            workspace.zero_dual_step_streak + 1 : 0
        if !workspace.progress.numerical_policy.adaptive_stalling &&
           workspace.options.pricing == :steepest_edge &&
           !workspace.dual_pricing_fallback &&
           workspace.zero_dual_step_streak >= 256 &&
           primal_infeasibility(workspace) > workspace.options.primal_tolerance
            workspace.dual_pricing_fallback = true
            try
                @logmsg workspace.options.log_level "Switching dual pricing to Dantzig after zero dual steps" iteration=workspace.iterations streak=workspace.zero_dual_step_streak
            catch exception
                stop_requested isa _StopCallback && (stop_requested.exception = exception)
                rethrow()
            end
        end
    end
    refactor_reason = _scheduled_refactor_reason(workspace,:dual)
    if refactor_reason != :none
        stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
        updates = length(workspace.factorization.updates)
        productive = _is_exact(T) === Val(false) &&
                     workspace.dual_nonzero_steps_since_refactorization >=
                     updates - updates ÷ 4
        recompute!(workspace; refactorize=true, caller_guard=stop_requested,
                   diagnostic_reason=_refactor_event(refactor_reason))
        if !workspace.progress.numerical_policy.adaptive_refactor
            basis_refreshed || _note_stable_dual_refactorization!(workspace, productive)
        end
    end
    if perturb_degenerate && _is_exact(T) === Val(false) &&
       !_adaptive_dual_perturbation_enabled(workspace.progress.numerical_policy) &&
       workspace.zero_dual_step_streak >= 1024 &&
       primal_infeasibility(workspace) > workspace.options.primal_tolerance
        stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
        if !isempty(workspace.factorization.updates)
            recompute!(workspace; refactorize=true, caller_guard=stop_requested)
            stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
            _finite_workspace(workspace) || return _numerical_failure()
            if !_dual_prices_feasible_or_refined!(workspace, stop_requested)
                stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
                return DualTermination(NUMERICAL_ERROR, "dual feasibility lost")
            end
        end
        if primal_infeasibility(workspace) > workspace.options.primal_tolerance
            shifted = _perturb_degenerate_dual_costs!(workspace, stop_requested)
            shifted < 0 && return DualTermination(TIME_LIMIT, "time limit reached")
        end
        workspace.zero_dual_step_streak = 0
    end
    _finite_workspace(workspace) || return _numerical_failure()
    return nothing
end

_primal_nearest_rounding(::Type{<:AbstractFloat}) = false
_primal_nearest_rounding(::Type{Float16}) = rounding(Float32) == RoundNearest
_primal_nearest_rounding(::Type{T}) where {T<:Union{Float32,Float64,BigFloat}} =
    rounding(T) == RoundNearest

function _primal_sum_bounds(left::T, right::T) where {T<:Rational}
    value = left + right
    return value, value
end

function _primal_sum_bounds(left::T, right::T) where {T<:AbstractFloat}
    iszero(left) && return right, right
    iszero(right) && return left, left
    isfinite(left) && precision(right) == precision(T) && left == -right &&
        return zero(T), zero(T)
    value = left + right
    # FastTwoSum is exact when intermediate residuals cannot underflow.
    # Other rounding modes and mixed BigFloat precisions use the enclosure.
    if isfinite(value) && _primal_nearest_rounding(T) &&
       precision(left) == precision(right) == precision(T) &&
       min(abs(left), abs(right)) >= ldexp(nextfloat(zero(T)), precision(T))
        large, small = abs(left) >= abs(right) ? (left, right) : (right, left)
        error = (large - value) + small
        if isfinite(error)
            return error < zero(T) ? (prevfloat(value), value) :
                   error > zero(T) ? (value, nextfloat(value)) : (value, value)
        end
    end
    return prevfloat(value), nextfloat(value)
end

_primal_difference_bounds(left::T, right::T) where {T<:Rational} =
    _primal_sum_bounds(left, -right)

function _primal_difference_bounds(left::T, right::T) where {T<:AbstractFloat}
    precision(right) == precision(T) && return _primal_sum_bounds(left, -right)
    # Negating an older, higher-precision tolerance can round before the sum.
    value = left - right
    return prevfloat(value), nextfloat(value)
end

function _primal_product_bounds(left::T, right::T) where {T<:AbstractFloat}
    (iszero(left) || iszero(right)) && return zero(T), zero(T)
    left == one(T) && return right, right
    right == one(T) && return left, left
    left == -one(T) && precision(right) == precision(T) && return -right, -right
    right == -one(T) && precision(left) == precision(T) && return -left, -left
    value = left * right
    if isfinite(value) && _primal_nearest_rounding(T)
        error = fma(left, right, -value)
        # A nonzero fused residual has a conclusive sign. Zero only proves
        # exactness when the product's finest possible bit cannot underflow.
        if isfinite(error) && (!iszero(error) ||
           abs(value) >= ldexp(nextfloat(zero(T)), precision(left) + precision(right)))
            return error < zero(T) ? (prevfloat(value), value) :
                   error > zero(T) ? (value, nextfloat(value)) : (value, value)
        end
    end
    return prevfloat(value), nextfloat(value)
end

function _primal_product_bounds(left::T, right::T) where {T<:Rational}
    value = left * right
    return value, value
end

function _primal_row_bounds(A::SparseMatrixCSC{T,Int}, primal::Vector{T},
                            ::Val{true}) where {T<:Rational}
    values = A * primal
    return values, values
end

function _primal_row_bounds(A::SparseMatrixCSC{T,Int}, primal::Vector{T},
                            ::Val{false}) where {T<:AbstractFloat}
    lower, upper = zeros(T, size(A, 1)), zeros(T, size(A, 1))
    for column in axes(A, 2)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            row = A.rowval[position]
            product_lower, product_upper = _primal_product_bounds(A.nzval[position], primal[column])
            lower[row], _ = _primal_sum_bounds(lower[row], product_lower)
            _, upper[row] = _primal_sum_bounds(upper[row], product_upper)
        end
    end
    return lower, upper
end

function _primal_interval_within_bounds(value_lower::T, value_upper::T,
                                        lower::Bound{T}, upper::Bound{T},
                                        tolerance::T) where {T}
    isfinite(value_lower) && isfinite(value_upper) || return false
    if isfinite(lower) && value_lower < bound_value(lower)
        _, threshold = _primal_difference_bounds(bound_value(lower), tolerance)
        value_lower >= threshold || return false
    end
    if isfinite(upper) && value_upper > bound_value(upper)
        threshold, _ = _primal_sum_bounds(bound_value(upper), tolerance)
        value_upper <= threshold || return false
    end
    return true
end

function _within_primal_intervals(values_lower::AbstractVector{T}, values_upper::AbstractVector{T},
                                  lower::AbstractVector{Bound{T}}, upper::AbstractVector{Bound{T}},
                                  tolerance::T) where {T}
    for index in eachindex(values_lower)
        _primal_interval_within_bounds(values_lower[index], values_upper[index],
                                       lower[index], upper[index], tolerance) || return false
    end
    return true
end

_within_primal_bounds(values::AbstractVector{T}, lower::AbstractVector{Bound{T}},
                      upper::AbstractVector{Bound{T}}, tolerance::T) where {T} =
    _within_primal_intervals(values, values, lower, upper, tolerance)

function _refined_primal_rows_feasible(problem::LinearProblem{T}, primal::Vector{T},
                                       tolerance::T, rows::Vector{Int}) where {T<:Union{Float32,Float64}}
    A = problem.A
    row_slot = zeros(Int, size(A, 1))
    for (slot, row) in enumerate(rows)
        row_slot[row] = slot
    end
    activities = zeros(Rational{BigInt}, length(rows))
    for column in axes(A, 2)
        value = Rational{BigInt}(primal[column])
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            slot = row_slot[A.rowval[position]]
            slot == 0 && continue
            coefficient = A.nzval[position]
            isfinite(coefficient) || return false
            activities[slot] += Rational{BigInt}(coefficient) * value
        end
    end
    exact_tolerance = Rational{BigInt}(tolerance)
    for (slot, row) in enumerate(rows)
        lower = problem.row_lower[row]
        upper = problem.row_upper[row]
        if isfinite(lower)
            activities[slot] >= Rational{BigInt}(bound_value(lower)) - exact_tolerance ||
                return false
        end
        if isfinite(upper)
            activities[slot] <= Rational{BigInt}(bound_value(upper)) + exact_tolerance ||
                return false
        end
    end
    return true
end

_refined_primal_rows_feasible(::LinearProblem, ::Vector, tolerance, rows) = false

function _original_primal_feasible(problem::LinearProblem{T}, primal::Vector{T}, tolerance::T) where {T}
    _within_primal_bounds(primal, problem.column_lower, problem.column_upper, tolerance) || return false
    row_lower, row_upper = _primal_row_bounds(problem.A, primal, _is_exact(T))
    # Certify the entire activity interval in the original absolute units.
    # Cancellation uncertainty must not enlarge the configured tolerance.
    _within_primal_intervals(row_lower, row_upper, problem.row_lower,
                             problem.row_upper, tolerance) && return true
    all(isfinite, row_lower) && all(isfinite, row_upper) || return false
    # A long floating sum can have a wider enclosure than the absolute
    # tolerance even when its exact stored-coefficient activity is feasible.
    T <: Union{Float32,Float64} || return false
    rows = Int[]
    for row in eachindex(row_lower)
        _primal_interval_within_bounds(row_lower[row], row_upper[row],
                                       problem.row_lower[row], problem.row_upper[row],
                                       tolerance) || push!(rows, row)
    end
    return _refined_primal_rows_feasible(problem, primal, tolerance, rows)
end

_original_primal_feasible(workspace::SimplexWorkspace{T}, primal::Vector{T}) where {T} =
    _original_primal_feasible(workspace.problem, primal, workspace.options.primal_tolerance)

function _original_reduced_cost_bounds(problem::LinearProblem{T}, dual::Vector{T}) where {T}
    A = problem.A
    column_count = size(A, 2)
    lower = Vector{T}(undef, column_count + length(dual))
    upper = Vector{T}(undef, column_count + length(dual))
    copyto!(lower, column_count + 1, dual, 1, length(dual))
    copyto!(upper, column_count + 1, dual, 1, length(dual))
    for column in 1:column_count
        minimum_dot = maximum_dot = zero(T)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            product_lower, product_upper = _primal_product_bounds(A.nzval[position], dual[A.rowval[position]])
            minimum_dot, _ = _primal_sum_bounds(minimum_dot, product_lower)
            _, maximum_dot = _primal_sum_bounds(maximum_dot, product_upper)
        end
        lower[column], _ = _primal_difference_bounds(problem.objective[column], maximum_dot)
        _, upper[column] = _primal_difference_bounds(problem.objective[column], minimum_dot)
    end
    # Working row-activity columns are -I and have zero original cost.
    return lower, upper
end

function _primal_interval_at_bound(lower::T, upper::T, bound::Bound{T}, tolerance::T) where {T}
    isfinite(bound) && isfinite(lower) && isfinite(upper) || return false
    value = bound_value(bound)
    if lower < value
        _, threshold = _primal_difference_bounds(value, tolerance)
        lower >= threshold || return false
    end
    if upper > value
        threshold, _ = _primal_sum_bounds(value, tolerance)
        upper <= threshold || return false
    end
    return true
end

function _original_optimality_certified(workspace::SimplexWorkspace{T}, primal::Vector{T}) where {T}
    problem, options = workspace.problem, workspace.options
    column_count, row_count = size(problem.A, 2), size(problem.A, 1)
    basic_costs = zeros(T, length(workspace.basis.basic_indices))
    for (row, index) in enumerate(workspace.basis.basic_indices)
        checkbounds(Base.OneTo(column_count + row_count), index)
        if index <= column_count
            basic_costs[row] = problem.objective[index]
        end
    end
    # The factorization supplies only a candidate witness. Certify the original
    # c - [A -I]' * dual independently, including every basic entry that the
    # incremental algorithm overwrites with zero. Shifted costs are irrelevant.
    dual = transpose_solve(workspace.factorization, basic_costs)
    all(isfinite, dual) || return false
    _maybe_refine_basis_solve!(dual,workspace,basic_costs;transposed=true) || return false
    reduced_lower, reduced_upper = _original_reduced_cost_bounds(problem, dual)
    all(isfinite, reduced_lower) && all(isfinite, reduced_upper) || return false
    row_lower, row_upper = _primal_row_bounds(problem.A, primal, _is_exact(T))
    _, negative_tolerance = _primal_difference_bounds(zero(T), options.dual_tolerance)
    for index in eachindex(reduced_lower)
        stationary = reduced_lower[index] >= negative_tolerance &&
                     reduced_upper[index] <= options.dual_tolerance
        workspace.basis.states[index] == BASIC && !stationary && return false
        stationary && continue
        lower = index <= column_count ? problem.column_lower[index] : problem.row_lower[index - column_count]
        upper = index <= column_count ? problem.column_upper[index] : problem.row_upper[index - column_count]
        _is_fixed(lower, upper) && continue
        # Use actual structural values and certified original row activities,
        # not stored slack values or a possibly stale nonbasic bound label.
        value_lower = index <= column_count ? primal[index] : row_lower[index - column_count]
        value_upper = index <= column_count ? primal[index] : row_upper[index - column_count]
        at_lower = reduced_lower[index] >= negative_tolerance &&
                   _primal_interval_at_bound(value_lower, value_upper, lower,
                                             options.primal_tolerance)
        at_upper = reduced_upper[index] <= options.dual_tolerance &&
                   _primal_interval_at_bound(value_lower, value_upper, upper,
                                             options.primal_tolerance)
        at_lower || at_upper || return false
    end
    return true
end

function _internal_solution(workspace::SimplexWorkspace{T}, status::TerminationStatus,
                            message::String) where {T}
    _simplex_event!(workspace, status == OPTIMAL ? :certification :
                              status == NUMERICAL_ERROR ? :certification_failed : :checkpoint)
    primal = status == OPTIMAL ? workspace.primal[1:size(workspace.problem.A, 2)] : nothing
    objective = isnothing(primal) ? nothing :
                dot(workspace.problem.objective, primal) + workspace.problem.objective_constant
    if status == OPTIMAL && (!_finite_workspace(workspace) || !isfinite(objective))
        return _internal_solution(workspace, _numerical_failure())
    end
    if status == OPTIMAL && !_original_primal_feasible(workspace, primal)
        return _internal_solution(workspace, NUMERICAL_ERROR,
                                  "structural primal failed original-model feasibility checks")
    end
    if status == OPTIMAL && !_original_optimality_certified(workspace, primal)
        return _internal_solution(workspace, NUMERICAL_ERROR,
                                  "original-objective optimality certificate is inconclusive")
    end
    basis = status == OPTIMAL ? Basis(workspace.basis.basic_indices, workspace.basis.states) : nothing
    return DualRunResult{T}(status, objective, primal, workspace.iterations,
                            workspace.refactorizations, message, basis)
end

_internal_solution(workspace::SimplexWorkspace{T}, terminal::DualTermination) where {T} =
    _internal_solution(workspace, terminal.status, terminal.message)

function _flip_bounds!(workspace::SimplexWorkspace{T}) where {T}
    flipped = false
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        isfinite(workspace.lower[index]) && isfinite(workspace.upper[index]) || continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        reduced_cost = workspace.reduced_costs[index]
        if state == AT_LOWER && reduced_cost < -workspace.options.dual_tolerance
            workspace.basis.states[index] = AT_UPPER
            flipped = true
        elseif state == AT_UPPER && reduced_cost > workspace.options.dual_tolerance
            workspace.basis.states[index] = AT_LOWER
            flipped = true
        end
    end
    flipped && recompute!(workspace)
    return nothing
end

function _dual_optimize!(workspace::SimplexWorkspace{T}, stop_requested;
                         perturb_degenerate::Bool=true)::DualTermination where {T}
    while true
        stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
        _prepare_auto_pricing!(workspace,:dual;stop=stop_requested) ||
            return DualTermination(TIME_LIMIT,"time limit reached during pricing recovery")
        _finite_workspace(workspace) || return _numerical_failure()
        if dual_infeasibility(workspace) > workspace.options.dual_tolerance
            if _is_exact(T) === Val(false) && !isempty(workspace.factorization.updates)
                # Updated factors and reduced costs can drift between rebuilds.
                # Confirm the failure against the current basis before stopping.
                recompute!(workspace; refactorize=true, caller_guard=stop_requested)
                stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
                _finite_workspace(workspace) || return _numerical_failure()
            end
            if !_dual_prices_feasible_or_refined!(workspace, stop_requested)
                stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
                return DualTermination(NUMERICAL_ERROR, "dual feasibility lost")
            end
        end
        if primal_infeasibility(workspace) <= workspace.options.primal_tolerance
            return DualTermination(OPTIMAL, "optimal solution found")
        end
        workspace.iterations < workspace.options.iteration_limit ||
            return DualTermination(ITERATION_LIMIT, "iteration limit reached")
        terminal = dual_iteration!(workspace, stop_requested; perturb_degenerate)
        isnothing(terminal) && _observe_stagnation!(workspace,:dual,
            workspace.scratch.last_primal_step,workspace.scratch.last_dual_step)
        isnothing(terminal) && _observe_auto_pricing!(workspace,:dual)
        if isnothing(terminal) && perturb_degenerate &&
           _maybe_perturb_dual_costs!(workspace,stop_requested) < 0
            return DualTermination(TIME_LIMIT,"time limit reached before dual perturbation")
        end
        isnothing(terminal) || return terminal
    end
end

function _auxiliary_workspace(workspace::SimplexWorkspace{T}) where {T}
    lower = similar(workspace.lower)
    upper = similar(workspace.upper)
    basis = Basis(workspace.basis.basic_indices, workspace.basis.states)
    for index in eachindex(lower)
        has_lower = isfinite(workspace.lower[index])
        has_upper = isfinite(workspace.upper[index])
        if has_lower && has_upper
            lower[index], upper[index] = Bound(zero(T)), Bound(zero(T))
        elseif has_lower
            lower[index], upper[index] = Bound(zero(T)), Bound(one(T))
        elseif has_upper
            lower[index], upper[index] = Bound(-one(T)), Bound(zero(T))
        else
            lower[index], upper[index] = Bound(-T(1000)), Bound(T(1000))
        end
        if basis.states[index] != BASIC
            basis.states[index] = workspace.reduced_costs[index] < zero(T) ? AT_UPPER : AT_LOWER
        end
    end
    # The base LU is only read by solves. Each workspace owns its mutable
    # update state; refactorization replaces its own base factorization.
    factorization = copy_basis_factorization(workspace.factorization)
    row_count, column_count = size(workspace.problem.A)
    scratch = SimplexScratch(T, row_count, row_count + column_count)
    auxiliary = SimplexWorkspace(
        workspace.problem, workspace.options, workspace.progress,
        copy(_auxiliary_costs_without_perturbation(workspace)), lower, upper,
        basis, copy(workspace.primal), copy(workspace.reduced_costs),
        copy(workspace.pricing_weights), copy(workspace.devex_reference),
        factorization, scratch, workspace.iterations,
        workspace.refactorizations, _auxiliary_perturbed_without_journal(workspace),
        workspace.zero_dual_step_streak, workspace.dual_pricing_fallback,
        workspace.dual_devex_fallback,
        workspace.dual_refactorization_interval, workspace.dual_recent_repairs,
        workspace.dual_bad_update_min, workspace.dual_stable_refactorizations,
        workspace.dual_nonzero_steps_since_refactorization,
    )
    auxiliary.scratch.refactorization = deepcopy(workspace.scratch.refactorization)
    auxiliary.scratch.refactorization.timing_depth = 0
    auxiliary.scratch.dual_perturbation_allowed = false
    auxiliary.scratch.primal_perturbation_allowed = false
    recompute!(auxiliary)
    _simplex_event!(auxiliary, :phase_auxiliary)
    return auxiliary
end

function _classify_recession!(workspace::SimplexWorkspace{T}, stop_requested) where {T}
    # A negative auxiliary optimum certifies a recession direction. Original
    # feasibility is still required: an infeasible LP can have such a direction.
    feasibility = initialize_workspace(
        workspace.problem,
        workspace.options;
        progress=workspace.progress,
    )
    feasibility.iterations = workspace.iterations
    feasibility.scratch.primal_perturbation_allowed = false
    feasibility.refactorizations = workspace.refactorizations
    fill!(feasibility.costs, zero(T))
    recompute!(feasibility)
    terminal = try
        _dual_optimize!(feasibility, stop_requested)
    finally
        workspace.iterations = feasibility.iterations
        workspace.refactorizations = feasibility.refactorizations
    end
    terminal.status == OPTIMAL || return terminal
    primal = feasibility.primal[1:size(workspace.problem.A, 2)]
    _original_primal_feasible(feasibility, primal) ||
        return DualTermination(NUMERICAL_ERROR,
                               "recession feasibility primal failed original-model feasibility checks")
    return DualTermination(UNBOUNDED, "unbounded improving direction")
end

function _recession_row_bounds(A::SparseMatrixCSC{T,Int}, structural::Vector{T},
                                ::Val{true}) where {T<:Rational}
    values = A * structural
    return values, values
end

function _recession_row_bounds(A::SparseMatrixCSC{T,Int}, structural::Vector{T},
                                ::Val{false}) where {T<:AbstractFloat}
    lower = zeros(T, size(A, 1))
    upper = zeros(T, size(A, 1))
    for column in axes(A, 2)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            row = A.rowval[position]
            lower[row], upper[row] = _add_product_bounds(
                lower[row], upper[row], A.nzval[position], structural[column],
            )
        end
    end
    return lower, upper
end

function _recession_objective_bounds(costs::Vector{T}, lower::Vector{T}, upper::Vector{T},
                                      ::Val{true}) where {T<:Rational}
    value = dot(costs, lower)
    return value, value
end

function _recession_objective_bounds(costs::Vector{T}, lower::Vector{T}, upper::Vector{T},
                                      ::Val{false}) where {T<:AbstractFloat}
    minimum_value = maximum_value = zero(T)
    for index in eachindex(costs)
        cost = costs[index]
        minimum_direction, maximum_direction = cost < zero(T) ?
            (upper[index], lower[index]) : (lower[index], upper[index])
        minimum_value, _ = _add_product_bounds(minimum_value, zero(T), cost, minimum_direction)
        _, maximum_value = _add_product_bounds(zero(T), maximum_value, cost, maximum_direction)
    end
    return minimum_value, maximum_value
end

function _recession_direction_status(workspace::SimplexWorkspace{T},
                                     auxiliary::SimplexWorkspace{T}) where {T}
    column_count = size(workspace.problem.A, 2)
    return _recession_direction_status(workspace, auxiliary.primal[1:column_count])
end

function _recession_direction_status(workspace::SimplexWorkspace{T},
                                     structural::Vector{T}) where {T}
    row_lower, row_upper = _recession_row_bounds(workspace.problem.A, structural, _is_exact(T))
    lower, upper = vcat(structural, row_lower), vcat(structural, row_upper)
    all(isfinite, lower) && all(isfinite, upper) || return :invalid
    # Each exact row direction must have a valid sign throughout its interval.
    # An interval containing zero does not establish equality, even when the
    # computed residual vanishes or is small relative to the dot-product terms.
    tolerance = workspace.options.zero_tolerance
    ambiguous = false
    for index in eachindex(lower)
        violation = max(isfinite(workspace.lower[index]) ? -lower[index] : zero(T),
                        isfinite(workspace.upper[index]) ? upper[index] : zero(T))
        violation <= zero(T) && continue
        certain_violation = max(isfinite(workspace.lower[index]) ? -upper[index] : zero(T),
                                isfinite(workspace.upper[index]) ? lower[index] : zero(T))
        certain_violation > tolerance && return :invalid
        ambiguous = true
    end
    objective_lower, objective_upper = _recession_objective_bounds(
        workspace.costs, lower, upper, _is_exact(T),
    )
    isfinite(objective_lower) && isfinite(objective_upper) || return :invalid
    objective_lower < -workspace.options.dual_tolerance || return :invalid
    objective_upper < -workspace.options.dual_tolerance || return :ambiguous
    return ambiguous ? :ambiguous : :certified
end

function make_dual_feasible!(workspace::SimplexWorkspace{T}, stop_requested)::Union{Nothing,DualTermination} where {T}
    stop_requested = _guard_stop_callback(stop_requested)
    stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
    _finite_workspace(workspace) || return _numerical_failure()
    try
        return _make_dual_feasible!(workspace, stop_requested)
    catch exception
        exception === stop_requested.exception && rethrow()
        _is_numerical_exception(exception) || rethrow()
        return DualTermination(NUMERICAL_ERROR, sprint(showerror, exception))
    end
end

function _make_dual_feasible!(workspace::SimplexWorkspace{T}, stop_requested) where {T}
    _restore_active_perturbations!(workspace)
    recompute!(workspace)
    _flip_bounds!(workspace)
    _finite_workspace(workspace) || return _numerical_failure()
    dual_infeasibility(workspace) <= workspace.options.dual_tolerance && return nothing

    auxiliary = _auxiliary_workspace(workspace)
    _reset_workspace_stagnation!(workspace)
    # Artificial auxiliary bounds can reverse a nonbasic state when the basis
    # returns to the original LP. Keep anti-degeneracy cost shifts out of this
    # phase so a shifted price cannot become infeasible after that remapping.
    terminal = try
        _dual_optimize!(auxiliary, stop_requested; perturb_degenerate=false)
    finally
        workspace.iterations = auxiliary.iterations
        workspace.refactorizations = auxiliary.refactorizations
    end
    terminal.status == OPTIMAL || return terminal
    if dot(workspace.costs, auxiliary.primal) < -workspace.options.dual_tolerance
        direction_status = _recession_direction_status(workspace, auxiliary)
        direction_status == :ambiguous &&
            return DualTermination(NUMERICAL_ERROR, "auxiliary direction has uncertain feasibility or objective improvement")
        direction_status == :certified ||
            return DualTermination(NUMERICAL_ERROR, "auxiliary vector does not certify an improving direction")
        return _classify_recession!(workspace, stop_requested)
    end

    basis = Basis(auxiliary.basis.basic_indices, auxiliary.basis.states)
    for index in eachindex(basis.states)
        basis.states[index] == BASIC && continue
        if !isfinite(workspace.lower[index]) && !isfinite(workspace.upper[index])
            basis.states[index] = FREE_NONBASIC
        elseif !isfinite(workspace.lower[index])
            basis.states[index] = AT_UPPER
        elseif !isfinite(workspace.upper[index])
            basis.states[index] = AT_LOWER
        end
    end
    stop_requested() && return DualTermination(TIME_LIMIT, "time limit reached")
    _invalidate_basis_checkpoints!(workspace)
    workspace.basis = basis
    _reset_auto_pricing!(workspace)
    workspace.pricing_weights .= auxiliary.pricing_weights
    workspace.costs .= auxiliary.costs
    workspace.perturbed = auxiliary.perturbed
    # Start the stall count on the original bounds and objective.
    workspace.zero_dual_step_streak = 0
    workspace.dual_pricing_fallback = auxiliary.dual_pricing_fallback
    workspace.dual_devex_fallback = auxiliary.dual_devex_fallback
    workspace.dual_refactorization_interval = auxiliary.dual_refactorization_interval
    workspace.dual_recent_repairs = auxiliary.dual_recent_repairs
    workspace.dual_bad_update_min = auxiliary.dual_bad_update_min
    workspace.dual_stable_refactorizations = auxiliary.dual_stable_refactorizations
    workspace.dual_nonzero_steps_since_refactorization =
        auxiliary.dual_nonzero_steps_since_refactorization
    recompute!(workspace; refactorize=true, caller_guard=stop_requested)
    _flip_bounds!(workspace)
    _finite_workspace(workspace) || return _numerical_failure()
    if dual_infeasibility(workspace) > workspace.options.dual_tolerance
        return DualTermination(NUMERICAL_ERROR, "auxiliary basis is not dual feasible")
    end
    return nothing
end

function _solve_continuous_dual(problem::LinearProblem{T}, options::SolverOptions{T};
                                stop_requested::Function=() -> false,
                                progress::SimplexProgressContext{T}=
                                    SimplexProgressContext(problem;
                                        numerical_policy=NumericalPolicy(T,options))) where {T}
    stop_requested = _guard_stop_callback(stop_requested)
    workspace = nothing
    try
        workspace = initialize_workspace(problem, options; progress)
        return _solve_continuous_dual!(workspace, stop_requested)
    catch exception
        exception === stop_requested.exception && rethrow()
        _is_numerical_exception(exception) || rethrow()
        return DualRunResult{T}(NUMERICAL_ERROR, nothing, nothing,
                                isnothing(workspace) ? 0 : workspace.iterations,
                                isnothing(workspace) ? 0 : workspace.refactorizations,
                                sprint(showerror, exception))
    end
end

function _solve_continuous_dual!(workspace::SimplexWorkspace{T}, stop_requested) where {T}
    _simplex_event!(workspace, :phase_dual)
    problem, options = workspace.problem, workspace.options
    stop_requested() && return _internal_solution(workspace, TIME_LIMIT, "time limit reached")
    _finite_workspace(workspace) || return _internal_solution(workspace, _numerical_failure())
    policy = workspace.progress.numerical_policy
    if policy.feasibility_recovery &&
       (!_original_costs_active(workspace) || !_original_bounds_active(workspace))
        # A resumed working problem needs original-model terminal checks even
        # when the zero-row shortcut or dual initialization finds a ray.
        return run_from_basis!(workspace,SimplexRunBudget(workspace),policy,stop_requested)
    end
    if iszero(size(problem.A, 1))
        for index in eachindex(workspace.costs)
            cost = workspace.costs[index]
            iszero(cost) && continue
            bound = cost > zero(T) ? workspace.lower[index] : workspace.upper[index]
            isfinite(bound) || return _internal_solution(workspace, UNBOUNDED, "unbounded improving direction")
            workspace.primal[index] = bound_value(bound)
        end
        return _internal_solution(workspace, OPTIMAL, "optimal solution found")
    end
    terminal = make_dual_feasible!(workspace, stop_requested)
    if policy.feasibility_recovery
        # Keep the explicitly selected dual initialization, then let verified
        # feasibility determine how to continue from a recovered basis.
        if !isnothing(terminal) && terminal.status != NUMERICAL_ERROR
            terminal = _original_bound_terminal(workspace,terminal)
            if terminal.status != UNBOUNDED || _original_costs_active(workspace)
                return _internal_solution(workspace,terminal)
            end
        end
        return run_from_basis!(workspace,SimplexRunBudget(workspace),policy,stop_requested)
    end
    isnothing(terminal) || return _internal_solution(workspace, terminal)
    terminal = _dual_optimize!(workspace, stop_requested)
    terminal.status == OPTIMAL || return _internal_solution(workspace, terminal)
    _restore_original_costs!(workspace)
    workspace.perturbed = false
    recompute!(workspace)
    if dual_infeasibility(workspace) > options.dual_tolerance && _is_exact(T) === Val(false)
        stop_requested() && return _internal_solution(workspace, TIME_LIMIT, "time limit reached")
        recompute!(workspace; refactorize=true, caller_guard=stop_requested)
        stop_requested() && return _internal_solution(workspace, TIME_LIMIT, "time limit reached")
        _dual_prices_feasible_or_refined!(workspace, stop_requested)
    end
    # Restoring the original costs keeps the basis primal feasible, but can
    # expose an improving direction that was hidden by a working-cost shift.
    if dual_infeasibility(workspace) > options.dual_tolerance &&
       primal_infeasibility(workspace) <= options.primal_tolerance
        options.verbose && @info "Starting primal cleanup after restoring original costs"
        workspace.dual_devex_fallback = false
        terminal = _primal_optimize!(workspace, stop_requested;perturb_degenerate=false)
        terminal.status == OPTIMAL || return _internal_solution(workspace, terminal)
    end
    stop_requested() && return _internal_solution(workspace, TIME_LIMIT, "time limit reached")
    status = primal_infeasibility(workspace) <= options.primal_tolerance &&
             dual_infeasibility(workspace) <= options.dual_tolerance ? OPTIMAL : NUMERICAL_ERROR
    return _internal_solution(workspace, status,
                              status == OPTIMAL ? "optimal solution found" : "dual feasibility lost")
end

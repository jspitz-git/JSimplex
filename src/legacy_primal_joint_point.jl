# A bounded feasibility recovery in the current floating type. Nonbasic values,
# basis metadata, tolerances and perturbation journals remain fixed throughout.
function _joint_primal_interval(lower::Bound{T}, upper::Bound{T}, tolerance::T) where T
    lo = isfinite(lower) ? last(_primal_difference_bounds(bound_value(lower), tolerance)) : T(-Inf)
    hi = isfinite(upper) ? first(_primal_sum_bounds(bound_value(upper), tolerance)) : T(Inf)
    return lo, hi
end

# Compensated row dot product; the complete certificate still decides acceptance.
function _joint_primal_activity(rows, row, primal::Vector{T}) where T
    total = correction = zero(T)
    for k in nzrange(rows, row)
        a, x = rows.nzval[k], primal[rows.rowval[k]]
        product = a*x
        error = fma(a, x, -product)
        next = total+product
        part = next-total
        correction += (total-(next-part))+(product-part)+error
        total = next
    end
    return total+correction
end

function _try_joint_primal_point_recovery!(workspace::SimplexWorkspace{T}, stop,
                                          prediction::Union{Nothing,Vector{T}}=nothing) where {T<:Union{Float32,Float64}}
    workspace.options.algorithm == :primal &&
        _legacy_primal_row_validation_enabled(workspace) || return false
    rounding(T) == RoundNearest && !get_zero_subnormals() || return false
    tolerance = workspace.options.primal_tolerance
    isfinite(tolerance) && tolerance > zero(T) || return false
    stop() && return false
    _finite_workspace(workspace) || return false
    all(isfinite, workspace.problem.A.nzval) || return false
    journal = workspace.scratch.perturbations
    working = _has_active_bound_perturbations(journal)
    working && _check_perturbation_owner(workspace, journal)
    original = copy(workspace.primal)
    basic = workspace.basis.states .== BASIC
    anchor = original
    if !isnothing(prediction)
        length(prediction) == length(workspace.basis.basic_indices) || return false
        all(isfinite,prediction) || return false
        # A row-consistent reconstruction can lie far outside the bounds while
        # the pivot prediction still has a nearby feasible point.
        # If the reconstruction has no admissible local box, use the prediction
        # as the anchor without increasing the radius or projection budget.
        for (row,index) in enumerate(workspace.basis.basic_indices)
            row % 256 == 0 && stop() && return false
            lo,hi = _joint_primal_interval(workspace.lower[index],workspace.upper[index],tolerance)
            radius = T(8)*max(tolerance,eps(T)*max(one(T),abs(original[index])))
            if max(lo,original[index]-radius) > min(hi,original[index]+radius)
                anchor = copy(original)
                for (slot,basic_index) in enumerate(workspace.basis.basic_indices)
                    anchor[basic_index] = prediction[slot]
                end
                break
            end
        end
    end
    columns = size(workspace.problem.A, 2)
    lower, upper = similar(anchor), similar(anchor)
    for index in eachindex(anchor)
        index % 256 == 0 && stop() && return false
        lo, hi = _joint_primal_interval(workspace.lower[index], workspace.upper[index], tolerance)
        if basic[index]
            # Keep the recovery near its anchor, also at magnitudes
            # where a single representable step is larger than the absolute tolerance.
            radius = T(8)*max(tolerance, eps(T)*max(one(T), abs(anchor[index])))
            isfinite(radius) || return false
            lo, hi = max(lo, anchor[index]-radius), min(hi, anchor[index]+radius)
        else
            max(_lower_violation(workspace.lower[index], anchor[index]),
                _upper_violation(workspace.upper[index], anchor[index])) <= tolerance || return false
        end
        if index <= columns && !working
            ml, mh = _joint_primal_interval(workspace.problem.column_lower[index],
                workspace.problem.column_upper[index], tolerance)
            lo, hi = max(lo, ml), min(hi, mh)
        end
        lo <= hi || return false
        lower[index], upper[index] = lo, hi
    end
    rows = sparse(transpose(workspace.problem.A))
    row_lower, row_upper = zeros(T, size(rows,2)), zeros(T, size(rows,2))
    scales = similar(row_lower)
    for row in axes(rows,2)
        row % 256 == 0 && stop() && return false
        activity = columns+row
        ml = working ? workspace.lower[activity] : workspace.problem.row_lower[row]
        mh = working ? workspace.upper[activity] : workspace.problem.row_upper[row]
        lo, hi = _joint_primal_interval(ml, mh, tolerance)
        # Eliminate a basic row activity by retaining its admissible interval.
        # A nonbasic activity is a singleton and may never be resynchronized.
        activity_lo = basic[activity] ? lower[activity] : anchor[activity]
        activity_hi = basic[activity] ? upper[activity] : anchor[activity]
        lo = max(lo, last(_primal_difference_bounds(activity_lo, tolerance)))
        hi = min(hi, first(_primal_sum_bounds(activity_hi, tolerance)))
        lo <= hi || return false
        row_lower[row], row_upper[row] = lo, hi
        scale = zero(T)
        for k in nzrange(rows,row)
            basic[rows.rowval[k]] || continue
            scale = max(scale,abs(rows.nzval[k]))
        end
        scales[row] = scale
    end
    stop() && return false
    _simplex_event!(workspace, :primal_projection_attempt)
    accepted = false
    try
        workspace.primal .= anchor
        # Reserve native roundoff room, capped by tolerance and interval width.
        # A fixed fraction of tolerance can destroy a thin feasible intersection.
        # The final certificate always retains its original tolerance.
        for _ in 1:8
            stop() && return false
            for index in 1:columns
                index % 256 == 0 && stop() && return false
                basic[index] || continue
                lo, hi = lower[index], upper[index]
                margin = min(T(8)*eps(T)*max(tolerance,abs(clamp(workspace.primal[index],lo,hi))),
                    tolerance/T(4), (hi-lo)/T(4))
                workspace.primal[index] = clamp(workspace.primal[index], lo+margin, hi-margin)
            end
            for row in axes(rows,2)
                row % 256 == 0 && stop() && return false
                value = _joint_primal_activity(rows,row,workspace.primal)
                isfinite(value) || return false
                lo, hi = row_lower[row], row_upper[row]
                margin = min(T(8)*eps(T)*max(tolerance,abs(clamp(value,lo,hi))),
                    tolerance/T(4), (hi-lo)/T(4))
                target = clamp(value,lo+margin,hi-margin)
                # Immutable rows are checked by the full certificate, even if
                # their current value cannot reach the stricter interior target.
                (target == value || iszero(scales[row])) && continue
                # Redistribute corrections lost when a coordinate reaches a bound.
                # Every clipped pass fixes at least one coordinate in this direction.
                sense = sign(target-value)
                for pass in 1:length(nzrange(rows,row))+1
                    stop() && return false
                    residual = target-_joint_primal_activity(rows,row,workspace.primal)
                    isfinite(residual) || return false
                    sign(residual) == sense || break
                    norm = zero(T)
                    for k in nzrange(rows,row)
                        k % 256 == 0 && stop() && return false
                        index = rows.rowval[k]
                        basic[index] || continue
                        coefficient = rows.nzval[k]/scales[row]
                        direction = sense*sign(coefficient)
                        iszero(direction) && continue
                        movable = direction > zero(T) ? workspace.primal[index] < upper[index] : workspace.primal[index] > lower[index]
                        movable || continue
                        norm += coefficient^2
                    end
                    iszero(norm) && break
                    multiplier = (residual/scales[row])/norm
                    isfinite(multiplier) || return false
                    clipped = false
                    for k in nzrange(rows,row)
                        k % 256 == 0 && stop() && return false
                        index = rows.rowval[k]
                        basic[index] || continue
                        coefficient = rows.nzval[k]/scales[row]
                        direction = sense*sign(coefficient)
                        iszero(direction) && continue
                        movable = direction > zero(T) ? workspace.primal[index] < upper[index] : workspace.primal[index] > lower[index]
                        movable || continue
                        value = workspace.primal[index]+multiplier*coefficient
                        isfinite(value) || return false
                        # A sub-ulp correction must not round back to the same point.
                        # The full certificate decides whether the representable move
                        # also respects every other row and the original tolerance.
                        value = direction > zero(T) ? nextfloat(value) : prevfloat(value)
                        projected = clamp(value,lower[index],upper[index])
                        isfinite(projected) || return false
                        clipped |= value != projected
                        workspace.primal[index] = projected
                    end
                    clipped || break
                end
            end
            for row in axes(rows,2)
                row % 256 == 0 && stop() && return false
                activity = columns+row
                basic[activity] || continue
                value = _joint_primal_activity(rows,row,workspace.primal)
                isfinite(value) || return false
                workspace.primal[activity] = clamp(value,lower[activity],upper[activity])
            end
            if _legacy_primal_point_certified(workspace)
                stop() && return false
                accepted = true
                break
            end
        end
    finally
        if !accepted
            workspace.primal .= original
        end
    end
    accepted || return false
    for (row,index) in enumerate(workspace.basis.basic_indices)
        workspace.scratch.row_solution[row] = workspace.primal[index]
    end
    _pipeline_changed!(workspace,workspace.scratch.row_solution)
    _simplex_event!(workspace,:primal_point_projected)
    return true
end

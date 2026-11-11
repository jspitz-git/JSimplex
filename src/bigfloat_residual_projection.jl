module _ResidualProjection
using SparseArrays
const JS = parentmodule(@__MODULE__)
const Q = Rational{BigInt}
function allowed(w)
 p=w.progress.numerical_policy
 !(p.pivot_validation || p.solve_refinement || p.recovery || p.incremental_primal || p.incremental_primal_pivots || JS._is_staged_workspace(w))
end
q(x)=JS._exact_rational(x)
function rounded(x::Q)
 out=BigFloat(;precision=precision(BigFloat));owner=Base.GMP.MPQ._MPQ(x)
 ccall((:mpfr_set_q,Base.MPFR.libmpfr),Cint,
       (Ref{BigFloat},Base.GMP.MPQ.mpq_t,Base.MPFR.MPFRRoundingMode),out,owner,Base.MPFR.MPFRRoundNearest)
 out
end
function parts(rows,row,primal::Vector{BigFloat})
 total=zero(Q)
 for k in nzrange(rows,row)
  total+=q(rows.nzval[k])*q(primal[rows.rowval[k]])
 end
 total,zero(Q)
end
function activity(rows,row,primal::Vector{BigFloat})
 total,_=parts(rows,row,primal);rounded(total)
end
function difference(target::BigFloat,total::Q,correction::Q,offset::BigFloat)
 isfinite(target) || return target
 rounded(q(target)-total-correction+q(offset))
end
difference(target::BigFloat,total::BigFloat,correction::BigFloat,offset::BigFloat)=difference(target,q(total),q(correction),offset)
function center_difference(lo::BigFloat,hi::BigFloat,total::Q)
 if isfinite(lo) && isfinite(hi) && q(lo)>q(hi)
  return rounded((q(lo)+q(hi))/2-total)
 elseif isfinite(lo) && total<q(lo)
  return rounded(q(lo)-total)
 elseif isfinite(hi) && total>q(hi)
  return rounded(q(hi)-total)
 end
 zero(BigFloat)
end
# A conservative precheck of the existing preparation's row-domain test.
# Drop radius/anchor restrictions only for basic activities, so this interval
# contains every candidate the original preparation could admit. Prediction
# changes only basic values. Nonbasic activities keep their original value.
# This is rejection only; all successful points still require certified().
@noinline function row_domains_compatible(w::JS.SimplexWorkspace{BigFloat},stop,working::Bool)
 working && return true # the owned journal makes working row bounds authoritative
 n=size(w.problem.A,2);t=w.options.primal_tolerance
 band_hi=nothing # invariant, prepared lazily only for separated domains
 for row in axes(w.problem.A,1)
  row % 256 == 0 && stop() && return false
  index=n+row
  wl,wu=w.lower[index],w.upper[index]
  ml,mu=w.problem.row_lower[row],w.problem.row_upper[row]
  wl==ml && wu==mu && continue
  if w.basis.states[index]==JS.BASIC
   lo,hi=JS._joint_primal_interval(wl,wu,t)
  else
   lo=hi=w.primal[index]
  end
  isfinite(ml) && (lo=max(lo,JS.bound_value(ml)))
  isfinite(mu) && (hi=min(hi,JS.bound_value(mu)))
  lo<=hi && continue
  # Bound the original residual test from above at the existing precision.
  # Summing the stored tolerance encloses both exact 2*t and its rounded
  # preparation value, including mixed-precision tolerances. Never introduce
  # exact-rational conversion (whose memory can scale with exponent magnitude).
  isfinite(lo) && isfinite(hi) || continue
  if isnothing(band_hi)
   _,band_hi=JS._primal_sum_bounds(t,t)
   isfinite(band_hi) || return true # unresolved: full certificate/preparation
  end
  _,difference_hi=JS._primal_difference_bounds(hi,lo)
  _,gap_hi=JS._primal_sum_bounds(difference_hi,band_hi)
  isfinite(gap_hi) && gap_hi<0 && return false
 end
 true
end
# Keep both original checks: model/owned working bounds and equality to the
# stored logical activities. The latter uses the same generic interval checker;
# do not enable the unrelated native legacy pivot machinery globally.
function certified(w::JS.SimplexWorkspace{BigFloat})
 JS._finite_workspace(w) || return false
 t=w.options.primal_tolerance
 JS._within_primal_bounds(w.primal,w.lower,w.upper,t) || return false
 n=size(w.problem.A,2);x=w.primal[1:n]
 # Select exactly the same bound authority as _legacy_primal_model_feasible.
 # Check columns before allocating/scanning row enclosures, as the old helper did.
 journal=w.scratch.perturbations
 working=JS._has_active_bound_perturbations(journal)
 working && JS._check_perturbation_owner(w,journal)
 column_lower=working ? @view(w.lower[1:n]) : w.problem.column_lower
 column_upper=working ? @view(w.upper[1:n]) : w.problem.column_upper
 JS._within_primal_bounds(x,column_lower,column_upper,t) || return false
 row_lower=working ? @view(w.lower[n+1:end]) : w.problem.row_lower
 row_upper=working ? @view(w.upper[n+1:end]) : w.problem.row_upper
 row_bounds=JS._primal_row_bounds(w.problem.A,x,JS._is_exact(BigFloat))
 JS._within_primal_intervals(row_bounds[1],row_bounds[2],row_lower,row_upper,t) || return false
 acts=JS._PrimalActivityBounds(w.primal,n)
 JS._primal_feasible_with_bounds(w.problem,x,t,@view(w.lower[1:n]),@view(w.upper[1:n]),acts,acts,row_bounds)
end
end

function _try_joint_primal_point_recovery!(workspace::SimplexWorkspace{T}, stop,
                                          prediction::Union{Nothing,Vector{T}}=nothing) where {T<:BigFloat}
    workspace.options.algorithm == :primal &&
        _ResidualProjection.allowed(workspace) || return false
    rounding(T) == RoundNearest && !get_zero_subnormals() || return false
    tolerance = workspace.options.primal_tolerance
    isfinite(tolerance) && tolerance > zero(T) || return false
    stop() && return false
    _finite_workspace(workspace) || return false
    all(isfinite, workspace.problem.A.nzval) || return false
    journal = workspace.scratch.perturbations
    working = _has_active_bound_perturbations(journal)
    working && _check_perturbation_owner(workspace, journal)
    if !isnothing(prediction)
        length(prediction) == length(workspace.basis.basic_indices) || return false
        all(isfinite,prediction) || return false
    end
    _ResidualProjection.row_domains_compatible(workspace,stop,working) || return false
    if _ResidualProjection.certified(workspace)
        stop() && return false
        _simplex_event!(workspace, :primal_projection_attempt)
        for (row,index) in enumerate(workspace.basis.basic_indices)
            workspace.scratch.row_solution[row] = workspace.primal[index]
        end
        _pipeline_changed!(workspace,workspace.scratch.row_solution)
        _simplex_event!(workspace,:primal_point_projected)
        return true
    end
    original = copy(workspace.primal)
    basic = workspace.basis.states .== BASIC
    anchor = original
    if !isnothing(prediction)
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
        # Both intervals have the same tolerance. Intersect their unexpanded
        # bases first, then apply tolerance only after subtracting the activity.
        activity_lo = basic[activity] ? lower[activity] : anchor[activity]
        activity_hi = basic[activity] ? upper[activity] : anchor[activity]
        lo = max(isfinite(ml) ? bound_value(ml) : T(-Inf), activity_lo)
        hi = min(isfinite(mh) ? bound_value(mh) : T(Inf), activity_hi)
        _ResidualProjection.difference(hi,lo,zero(T),T(2)*tolerance) >= zero(T) || return false
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
                iszero(scales[row]) && continue
                # Keep the original degree+1 redistribution cap and eight sweeps.
                for pass in 1:length(nzrange(rows,row))+1
                    stop() && return false
                    total, compensation = _ResidualProjection.parts(rows,row,workspace.primal)
                    all(isfinite,(total,compensation)) || return false
                    lo = _ResidualProjection.difference(row_lower[row],total,compensation,-tolerance)
                    hi = _ResidualProjection.difference(row_upper[row],total,compensation,tolerance)
                    all(isfinite,(lo,hi)) && lo <= hi || return false
                    distance = max(lo,-hi,zero(T))
                    if iszero(distance)
                        # The original interval certificate can be inconclusive
                        # at a large activity. Seek its unexpanded center only as
                        # a proposal, preserving the full acceptance band.
                        residual=_ResidualProjection.center_difference(row_lower[row],row_upper[row],total)
                        iszero(residual) && break
                        distance=abs(residual)
                    else
                    # An interior target is chosen in residual units; the full
                    # band, not this interior target, decides when to stop.
                    margin = min(T(8)*eps(T)*max(tolerance,abs(total+compensation)),
                        tolerance/T(4), (hi-lo)/T(4))
                    residual = lo > zero(T) ? min(lo+margin,hi) : max(hi-margin,lo)
                    end
                    isfinite(residual) || return false
                    sense = sign(residual)
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
                    progressed = false
                    for k in nzrange(rows,row)
                        k % 256 == 0 && stop() && return false
                        index = rows.rowval[k]
                        basic[index] || continue
                        coefficient = rows.nzval[k]/scales[row]
                        direction = sense*sign(coefficient)
                        iszero(direction) && continue
                        current = workspace.primal[index]
                        movable = direction > zero(T) ? current < upper[index] : current > lower[index]
                        movable || continue
                        value = current+multiplier*coefficient
                        isfinite(value) || return false
                        # Only supply the smallest representable move if rounding
                        # erased the proposed correction. Coarse moves may still
                        # be rejected below if they overshoot the full band.
                        value == current && (value = direction > zero(T) ? nextfloat(value) : prevfloat(value))
                        projected = clamp(value,lower[index],upper[index])
                        isfinite(projected) || return false
                        movement = projected-current
                        remaining_lo = fma(-rows.nzval[k],movement,lo)
                        remaining_hi = fma(-rows.nzval[k],movement,hi)
                        all(isfinite,(remaining_lo,remaining_hi)) || return false
                        remaining_distance = max(remaining_lo,-remaining_hi,zero(T))
                        remaining_distance < distance || continue
                        clipped |= value != projected
                        progressed = true
                        workspace.primal[index] = projected
                        lo, hi, distance = remaining_lo, remaining_hi, remaining_distance
                        iszero(distance) && break
                    end
                    (iszero(distance) || !progressed || !clipped) && break
                end
            end
            for row in axes(rows,2)
                row % 256 == 0 && stop() && return false
                activity = columns+row
                basic[activity] || continue
                value = _ResidualProjection.activity(rows,row,workspace.primal)
                isfinite(value) || return false
                workspace.primal[activity] = clamp(value,lower[activity],upper[activity])
            end
            if _ResidualProjection.certified(workspace)
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

_legacy_primal_row_validation_enabled(workspace) = false

function _legacy_primal_row_validation_enabled(workspace::SimplexWorkspace{T}) where {T}
    T === Float32 || T === Float64 || return false
    policy = workspace.progress.numerical_policy
    return !(policy.pivot_validation || policy.solve_refinement || policy.recovery ||
             policy.incremental_primal || policy.incremental_primal_pivots ||
             _is_staged_workspace(workspace))
end

# The selected direction supplies a second estimate of c_j - c_B' B^-1 a_j.
# A badly cancelled transpose price can otherwise sustain an improving-looking
# cycle even when the pivot itself passes the forward/transpose row check.
function _legacy_primal_direction_price_ok(workspace::SimplexWorkspace{T}, entering::Int,
                                            column::Vector{T}, price_tolerance::T) where {T<:Union{Float32,Float64}}
    rounding(T)==RoundNearest && !get_zero_subnormals() || return true
    cached=workspace.reduced_costs[entering]
    isfinite(cached) || return false
    implied=workspace.costs[entering]
    scale=abs(implied)
    terms=0
    for (row,index) in enumerate(workspace.basis.basic_indices)
        cost=workspace.costs[index]
        (iszero(cost) || iszero(column[row])) && continue
        product=cost*column[row]
        implied-=product
        scale+=abs(product)
        terms+=1
    end
    # An unrepresentable probe must not reject a direction whose existing
    # checks can still handle the exceptional range.
    isfinite(implied) && isfinite(scale) || return true
    k=T(4terms+2)*eps(T)
    k<T(1)/4 || return true
    accumulation=terms==0 ? zero(T) :
        (k*scale+T(2terms+1)*nextfloat(zero(T)))/(one(T)-k)^2
    tolerance=price_tolerance+accumulation+
        sqrt(eps(T))*max(abs(cached),abs(implied))
    return abs(cached-implied)<=tolerance
end

# Repair only a demonstrated native BTRAN price discrepancy. A direction-price
# disagreement can require more accuracy even below the ordinary solve tolerance.
# The fresh solve and all prices stay private; scratch.rho may hold a pivot row,
# so it is not a reusable copy of the current objective's dual solution.
_try_native_primal_price_recovery!(workspace,stop) = false
function _try_native_primal_price_recovery!(workspace::SimplexWorkspace{T},stop) where {T<:Union{Float32,Float64}}
    workspace.options.algorithm == :primal &&
        _legacy_primal_row_validation_enabled(workspace) || return false
    policy=workspace.progress.numerical_policy
    policy.max_refinements>0 && !stop() || return false
    B=_basis_matrix!(workspace)
    rhs=workspace.costs[workspace.basis.basic_indices]
    dual=similar(rhs)
    _timed_simplex(workspace,:btran) do
        transpose_solve!(dual,workspace.factorization,rhs)
    end
    scratch=SolveQualityScratch(T,length(rhs))
    quality=_compensated_solve_quality!(scratch,B,dual,rhs,policy,true)
    (isnothing(quality) || !quality.finite || iszero(quality.absolute_error) || stop()) && return false
    _native_cleanup_solve!(dual,workspace,B,rhs,stop;transposed=true,
        force_refinement=quality.reliable) || return false
    prices=similar(workspace.reduced_costs)
    _recompute_reduced_costs!(prices,workspace,dual)
    all(isfinite,prices) && prices!=workspace.reduced_costs && !stop() || return false
    copyto!(workspace.scratch.rho,dual)
    copyto!(workspace.reduced_costs,prices)
    _pipeline_changed!(workspace,workspace.scratch.rho)
    _invalidate_pricing_pool!(workspace;basis=false)
    _simplex_event!(workspace,:primal_prices_corrected)
    return true
end

# A forward residual alone can miss a spurious pivot in an ill-conditioned
# basis. Check its transpose row before changing the basis, then share that row
# with pricing updates instead of computing another BTRAN for the weights.
function _legacy_primal_pivot_row_status!(workspace::SimplexWorkspace{T}, entering::Int,
                                      leaving_row::Int, pivot::T, stop; column=nothing) where {T}
    T === Float32 || T === Float64 || return :pivot
    stop() && return :pivot
    unit = _pipeline_unit_rhs!(workspace, leaving_row)
    rho = _timed_simplex(workspace, :btran) do
        _pipeline_basis_solve!(workspace.scratch.rho, workspace, unit; transposed=true)
    end
    all(isfinite, rho) || return :residual
    if _dual_row_residual_ratio(workspace, rho, leaving_row) > one(T)
        _try_native_dual_correction!(workspace, rho, leaving_row, leaving_row, stop;
                                     transposed=true) || return :residual
    end
    price!(workspace.scratch.tableau_row, workspace, rho)
    all(isfinite, workspace.scratch.tableau_row) || return :pivot
    row_pivot = workspace.scratch.tableau_row[entering]
    # The absolute zero cutoff must not become an agreement floor: two tiny
    # pivots can differ by a large fraction while both pass that cutoff.
    tolerance = sqrt(eps(one(T))) * max(abs(pivot), abs(row_pivot))
    sign(row_pivot) == sign(pivot) && abs(row_pivot - pivot) <= tolerance || return :pivot
    isnothing(column) && return :accept
    return _legacy_primal_direction_pivot_ok!(workspace, entering, leaving_row, column, stop) ?
        :accept : :pivot
end

# A pivot can be sensitive even when both solves pass their residual checks.
# Only a failed solve check is evidence for shortening the update chain.
function _legacy_primal_pivot_row_ok!(workspace::SimplexWorkspace{T}, entering::Int,
                                      leaving_row::Int, pivot::T, stop; column=nothing) where {T}
    return _legacy_primal_pivot_row_status!(workspace, entering, leaving_row, pivot, stop;
        column) == :accept
end

# Fresh forward and transpose solves can share the same false tiny pivot.
# Probe its sensitivity using a compensated residual against the actual basis,
# even when the ordinary backward error is small. Keep all arithmetic native
# and leave the chosen direction unchanged; rejection uses the existing retry.
function _legacy_primal_direction_pivot_ok!(workspace::SimplexWorkspace{T}, entering::Int,
                                            leaving_row::Int, column::Vector{T}, stop) where {T<:Union{Float32,Float64}}
    pivot = column[leaving_row]
    relative = sqrt(eps(one(T)))
    abs(pivot) > relative * maximum(abs, column) && return true
    stop() && return false
    buffers = _pivot_quality_buffers(workspace)
    rhs = _pivot_column!(buffers.rhs, workspace, entering)
    B = _basis_matrix!(workspace)
    quality = _compensated_solve_quality!(buffers.column, B, column, rhs,
                                          workspace.progress.numerical_policy, false)
    # Reliability describes the input direction, not the residual's usability.
    # Tiny homogeneous rows can have relative error one from harmless roundoff.
    # Let the native correction test the selected pivot before rejecting it.
    (isnothing(quality) || !quality.finite) && return false
    _simplex_event!(workspace, :correction_attempt)
    try
        _timed_simplex(workspace, :ftran) do
            _ordinary_forward_solve!(buffers.correction, workspace.factorization,
                                      buffers.column.residual)
        end
    catch exception
        _is_numerical_exception(exception) || rethrow()
        return false
    end
    stop() && return false
    all(isfinite, buffers.correction) || return false
    return abs(buffers.correction[leaving_row]) <= relative * abs(pivot)
end

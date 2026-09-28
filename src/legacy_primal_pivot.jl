_legacy_primal_row_validation_enabled(workspace) = false

function _legacy_primal_row_validation_enabled(workspace::SimplexWorkspace{T}) where {T}
    T === Float32 || T === Float64 || return false
    workspace.options.simplex_strategy == :legacy || return false
    policy = workspace.progress.numerical_policy
    return !(policy.pivot_validation || policy.solve_refinement || policy.recovery ||
             policy.incremental_primal || policy.incremental_primal_pivots ||
             policy.adaptive_refactor || _is_staged_workspace(workspace))
end

# A forward residual alone can miss a spurious pivot in an ill-conditioned
# basis. Check its transpose row before changing the basis, then share that row
# with pricing updates instead of computing another BTRAN for the weights.
function _legacy_primal_pivot_row_ok!(workspace::SimplexWorkspace{T}, entering::Int,
                                      leaving_row::Int, pivot::T, stop; column=nothing) where {T}
    T === Float32 || T === Float64 || return false
    stop() && return false
    unit = _pipeline_unit_rhs!(workspace, leaving_row)
    rho = _timed_simplex(workspace, :btran) do
        _pipeline_basis_solve!(workspace.scratch.rho, workspace, unit; transposed=true)
    end
    all(isfinite, rho) || return false
    if _dual_row_residual_ratio(workspace, rho, leaving_row) > one(T)
        _try_native_dual_correction!(workspace, rho, leaving_row, leaving_row, stop;
                                     transposed=true) || return false
    end
    price!(workspace.scratch.tableau_row, workspace, rho)
    all(isfinite, workspace.scratch.tableau_row) || return false
    row_pivot = workspace.scratch.tableau_row[entering]
    # The absolute zero cutoff must not become an agreement floor: two tiny
    # pivots can differ by a large fraction while both pass that cutoff.
    tolerance = sqrt(eps(one(T))) * max(abs(pivot), abs(row_pivot))
    sign(row_pivot) == sign(pivot) && abs(row_pivot - pivot) <= tolerance || return false
    isnothing(column) && return true
    return _legacy_primal_direction_pivot_ok!(workspace, entering, leaving_row, column, stop)
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
    (isnothing(quality) || !quality.finite || !quality.reliable) && return false
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

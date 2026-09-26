_legacy_primal_row_validation_enabled(workspace) = false

function _legacy_primal_row_validation_enabled(workspace::SimplexWorkspace{T}) where {T<:Union{Float32,Float64}}
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
                                      leaving_row::Int, pivot::T, stop) where {T<:Union{Float32,Float64}}
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
    tolerance = max(workspace.options.zero_tolerance, sqrt(eps(one(T))) * abs(pivot))
    return sign(row_pivot) == sign(pivot) &&
           abs(row_pivot - pivot) <= tolerance
end

# Frozen implementation from d1978a1; evaluated inside JSimplex for diagnostics.
function _guard_reference_weights!(workspace::SimplexWorkspace{T},
                                      rho::Vector{T}, tableau_row::Vector{T},
                                      tableau_column::Vector{T}, entering_index::Int,
                                      pivot::T, dse_weight::T, stop_requested) where {T}
    if _weight_pricing(workspace,:dual) == :steepest_edge
        update_dse!(workspace, rho, tableau_column, entering_index, pivot,
                    dse_weight)
        if !_finite_workspace(workspace)
            _recover_invalid_dse_weights!(workspace, stop_requested) || return false
            _finite_workspace(workspace) || return false
            # The Devex reference is the pre-pivot basis. Account for this
            # pivot before replacing its basis column.
            update_devex!(workspace, tableau_row, tableau_column, entering_index, pivot)
        end
    elseif _weight_pricing(workspace,:dual) == :devex
        update_devex!(workspace, tableau_row, tableau_column, entering_index, pivot)
    end
    return _finite_workspace(workspace)
end

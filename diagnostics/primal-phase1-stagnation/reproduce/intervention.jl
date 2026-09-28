# Diagnostic intervention only. Keep the existing row-variable behavior intact.
function install_intervention(mode)
if mode == "preserve_structural"
    @eval JSimplex function _can_preserve_primal_row_value(ws::SimplexWorkspace{T}, index::Int,
            state::VariableState, bound::Bound{T}) where {T}
        T === Float32 || T === Float64 || return false
        ws.options.algorithm == :primal && ws.options.simplex_strategy == :legacy || return false
        policy=ws.progress.numerical_policy
        (policy.pivot_validation || policy.recovery || policy.incremental_primal ||
         policy.incremental_primal_pivots || _is_staged_workspace(ws)) && return false
        columns=size(ws.problem.A,2)
        index <= columns && _is_fixed(ws.lower[index],ws.upper[index]) && return false
        value=ws.primal[index]
        isfinite(value) && isfinite(bound) || return false
        outside=state == AT_LOWER ? value < bound_value(bound) : state == AT_UPPER && value > bound_value(bound)
        outside || return false
        original=if index <= columns
            state == AT_LOWER ? ws.problem.column_lower[index] : ws.problem.column_upper[index]
        else
            state == AT_LOWER ? ws.problem.row_lower[index-columns] : ws.problem.row_upper[index-columns]
        end
        return _primal_interval_at_bound(value,value,original,ws.options.primal_tolerance)
    end
elseif mode != "baseline"
    error("Expected baseline or preserve_structural")
end
end

function point_certificate(ws)
    columns=size(ws.problem.A,2)
    max_violation=maximum(eachindex(ws.primal)) do i
        max(zero(eltype(ws.primal)),JSimplex._lower_violation(ws.lower[i],ws.primal[i]),
            JSimplex._upper_violation(ws.upper[i],ws.primal[i]))
    end
    finite=JSimplex._finite_workspace(ws)
    phase=finite && JSimplex._original_primal_feasible(ws.problem,ws.primal[1:columns],ws.options.primal_tolerance)
    rows=finite && JSimplex._legacy_primal_row_consistent(ws,ws.options.primal_tolerance)
    return (finite=finite,max_bound_violation=max_violation,phase_primal=phase,row_consistent=rows)
end
point_certified(ws,c)=c.finite && c.max_bound_violation<=ws.options.primal_tolerance && c.phase_primal && c.row_consistent

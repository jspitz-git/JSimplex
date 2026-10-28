module EBAA
import JSimplex
using SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,LPResiduals,Basis,AT_LOWER,OPTIMAL,
 _pipeline_changed!,_primal_direction_magnitude,bound_value,_is_fixed,
 _lp_child_diagnostics,_lp_auxiliary_options,SimplexProgressContext,_lp_auxiliary_policy,
 _lp_workspace,_precision_current_bits,_simplex_event!,_dispatch_lp_auxiliary,
 _original_dual_witness,_sync_run_budget!,_merge_lp_diagnostics!,_with_transfer_precision
function _dual_direction_residual_ok!(workspace::SimplexWorkspace{T},
                                      direction::Vector{T}, pivot::T) where {T<:AbstractFloat}
    A = workspace.problem.A
    row_count, column_count = size(A)
    length(direction) == length(workspace.basis.basic_indices) == row_count &&
        length(workspace.scratch.tau) == length(workspace.scratch.row_rhs) == row_count ||
        throw(DimensionMismatch("direction residual vectors must match the row count"))
    residual = workspace.scratch.tau
    scale = workspace.scratch.row_rhs
    _pipeline_changed!(workspace,residual)
    _pipeline_changed!(workspace,scale)
    @inbounds for row in eachindex(residual)
        rhs = scale[row]
        residual[row] = -rhs
        scale[row] = abs(rhs)
    end
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        1 <= index <= column_count + row_count || throw(BoundsError(workspace.primal, index))
        value = @inbounds direction[basis_row]
        if index <= column_count
            @inbounds for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                row = A.rowval[position]
                term = A.nzval[position] * value
                residual[row] += term
                scale[row] += abs(term)
            end
        else
            row = index - column_count
            @inbounds residual[row] -= value
            @inbounds scale[row] += abs(value)
        end
    end
    roundoff = T(256) * eps(one(T))
    pivot_tolerance = sqrt(eps(one(T))) * abs(pivot)
    @inbounds for row in eachindex(residual)
        isfinite(residual[row]) && isfinite(scale[row]) || return false
        tolerance = max(workspace.options.zero_tolerance, pivot_tolerance,
                        roundoff * (scale[row] + one(T)))
        abs(residual[row]) <= tolerance || return false
    end
    return true
end

function _dual_direction_residual_ok!(workspace::SimplexWorkspace{T},
                                      direction::Vector{T}, pivot::T) where {T<:BigFloat}
    A = workspace.problem.A
    row_count, column_count = size(A)
    length(direction) == length(workspace.basis.basic_indices) == row_count &&
        length(workspace.scratch.tau) == length(workspace.scratch.row_rhs) == row_count ||
        throw(DimensionMismatch("direction residual vectors must match the row count"))
    residual = workspace.scratch.tau
    scale = workspace.scratch.row_rhs
    _pipeline_changed!(workspace,residual)
    _pipeline_changed!(workspace,scale)
    @inbounds for row in eachindex(residual)
        rhs = scale[row]
        residual[row] = -rhs
        scale[row] = _primal_direction_magnitude(rhs)
    end
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        1 <= index <= column_count + row_count || throw(BoundsError(workspace.primal, index))
        value = @inbounds direction[basis_row]
        if index <= column_count
            @inbounds for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                row = A.rowval[position]
                term = A.nzval[position] * value
                residual[row] += term
                scale[row] += _primal_direction_magnitude(term)
            end
        else
            row = index - column_count
            @inbounds residual[row] -= value
            @inbounds scale[row] += _primal_direction_magnitude(value)
        end
    end
    roundoff_multiplier = T(256)
    epsilon = eps(one(T))
    roundoff = roundoff_multiplier * epsilon
    pivot_tolerance = sqrt(epsilon) * _primal_direction_magnitude(pivot)
    @inbounds for row in eachindex(residual)
        isfinite(residual[row]) && isfinite(scale[row]) || return false
        tolerance = max(workspace.options.zero_tolerance, pivot_tolerance,
                        roundoff * (scale[row] + Clong(1)))
        _primal_direction_magnitude(residual[row]) <= tolerance || return false
    end
    return true
end

function _lp_errors(ws,residuals::LPResiduals{R}) where R
    n = size(ws.problem.A,2)
    primal = maximum(abs,residuals.primal;init=zero(R))
    dual,complementarity = zero(R),zero(R)
    tolerance = R(ws.options.primal_tolerance)
    for j in eachindex(residuals.values)
        value,price = residuals.values[j],residuals.dual[j]
        lower = j <= n ? ws.problem.column_lower[j] : ws.problem.row_lower[j-n]
        upper = j <= n ? ws.problem.column_upper[j] : ws.problem.row_upper[j-n]
        has_lower,has_upper = isfinite(lower),isfinite(upper)
        lo = has_lower ? R(bound_value(lower)) : zero(R)
        hi = has_upper ? R(bound_value(upper)) : zero(R)
        has_lower && (primal=max(primal,lo-value))
        has_upper && (primal=max(primal,value-hi))
        _is_fixed(lower,upper) && continue
        at_lower = has_lower && abs(value-lo) <= tolerance
        at_upper = has_upper && abs(value-hi) <= tolerance
        dual = max(dual,at_lower ? max(-price,zero(R)) : at_upper ? max(price,zero(R)) : abs(price))
        if price > 0
            complementarity=max(complementarity,has_lower ? abs(price*(value-lo)) : abs(price))
        elseif price < 0
            complementarity=max(complementarity,has_upper ? abs(price*(hi-value)) : abs(price))
        end
    end
    return primal,dual,complementarity
end

function _lp_auxiliary_run(ws,problem,map,budget,policy,stop)
    diagnostics = _lp_child_diagnostics(ws.progress.diagnostics)
    auxiliary = nothing
    try
        options = _lp_auxiliary_options(ws.options,budget)
        progress = SimplexProgressContext(problem;start_ns=budget.start_ns,
            iteration_offset=budget.iterations,refactorization_offset=budget.refactorizations,
            diagnostics,numerical_policy=_lp_auxiliary_policy(policy))
        basis = Basis(copy(ws.basis.basic_indices),vcat(ws.basis.states,fill(AT_LOWER,length(map.fixed_activities))))
        auxiliary = _lp_workspace(problem,basis,options,progress,budget,stop;factor_bits=_precision_current_bits(ws))
        isnothing(auxiliary) && return nothing,nothing,nothing
        _simplex_event!(auxiliary,:phase_lp_refinement)
        run = _dispatch_lp_auxiliary(auxiliary,budget,progress.numerical_policy,stop)
        witness = run.status == OPTIMAL ? _original_dual_witness(auxiliary) : nothing
        return auxiliary,run,witness
    finally
        isnothing(auxiliary) || _sync_run_budget!(budget,auxiliary)
        _merge_lp_diagnostics!(ws.progress.diagnostics,diagnostics)
    end
end

function _lp_auxiliary_run_at_working_precision(ws::SimplexWorkspace{T},problem,map,budget,policy,stop) where T
    return _with_transfer_precision(T,_precision_current_bits(ws)) do
        _lp_auxiliary_run(ws,problem,map,budget,policy,stop)
    end
end


end

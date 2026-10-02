# Mandatory original-model cleanup must also work with the native kernel.
# Its relative residual test can reject a feasible point because homogeneous
# equations contain tiny roundoff artifacts. Correct only after that test fails;
# ordinary iterations and the separately selected checked implementation keep
# their existing solve paths. A demonstrated price/direction disagreement may
# request one correction of a reliable solve, but must improve its residual.
function _native_cleanup_solve!(x::Vector{T}, ws, B, rhs, stop;
                                transposed::Bool=false,
                                force_refinement::Bool=false,
                                local_reconstruction::Bool=false) where {T<:Union{Float32,Float64}}
    policy = ws.progress.numerical_policy
    scratch = SolveQualityScratch(T,length(rhs))
    quality = _compensated_solve_quality!(scratch,B,x,rhs,policy,transposed)
    isnothing(quality) && return false
    quality.reliable && (!force_refinement || iszero(quality.absolute_error)) && return true
    require_improvement=force_refinement && quality.reliable
    initial_error=quality.absolute_error
    stop() && return false
    _simplex_event!(ws,:correction_attempt)
    correction = similar(x)
    _timed_simplex(ws,transposed ? :btran : :ftran) do
        transposed ? transpose_solve!(correction,ws.factorization,scratch.residual) :
            _ordinary_forward_solve!(correction,ws.factorization,scratch.residual)
    end
    all(isfinite,correction) || return false
    trial = x + correction
    all(isfinite,trial) || return false
    quality = _compensated_solve_quality!(scratch,B,trial,rhs,policy,transposed)
    isnothing(quality) && return false
    if !quality.reliable
        # Scale a proposed zero cleanup by the correction's rounding error,
        # not the full solution norm, which may include large unrelated values.
        # Accept it only if every equation passes the unchanged residual test.
        cutoff = policy.solve_tolerance*maximum(abs,correction;init=zero(T))
        _clean_homogeneous_terms!(trial,B,rhs,transposed,zeros(Int,length(rhs)),policy;cutoff)
        quality = _compensated_solve_quality!(scratch,B,trial,rhs,policy,transposed)
        isnothing(quality) && return false
        if !quality.reliable
            # Driver cleanup may need a reliable but bound-infeasible basis.
            # Recover tiny terms lost in x + correction using the same budget
            # and cutoff, then certify every equation before publication.
            local_reconstruction && !transposed || return false
            # Failed homogeneous cleanup may have erased coupled tiny terms.
            # Reconstruct from the original corrected candidate instead.
            @. trial = x + correction
            _native_phase_local_rows!(trial,B,rhs,policy,cutoff,stop) || return false
            quality = _compensated_solve_quality!(scratch,B,trial,rhs,policy,false)
            (isnothing(quality) || !quality.reliable) && return false
        end
    end
    require_improvement && !(quality.absolute_error<initial_error) && return false
    stop() && return false
    copyto!(x,trial)
    return true
end

_try_native_cleanup_recompute!(ws,stop) = false
function _try_native_cleanup_recompute!(ws::SimplexWorkspace{T},stop) where {T<:Union{Float32,Float64}}
    policy = ws.progress.numerical_policy
    (policy.solve_refinement || policy.max_refinements == 0 || stop()) && return false
    B = _basis_matrix!(ws)
    rhs = _basis_primal_rhs(ws)
    basic = ws.primal[ws.basis.basic_indices]
    dual = copy(ws.scratch.rho)
    # Keep both corrections private until the complete state is verified.
    _native_cleanup_solve!(basic,ws,B,rhs,stop;local_reconstruction=true) || return false
    _native_cleanup_solve!(dual,ws,B,ws.costs[ws.basis.basic_indices],stop;
        transposed=true) || return false
    prices = similar(ws.reduced_costs)
    _recompute_reduced_costs!(prices,ws,dual)
    all(isfinite,prices) || return false
    stop() && return false
    for (row,index) in enumerate(ws.basis.basic_indices)
        ws.primal[index] = basic[row]
    end
    copyto!(ws.scratch.row_solution,basic)
    copyto!(ws.scratch.rho,dual)
    copyto!(ws.reduced_costs,prices)
    _pipeline_changed!(ws,ws.scratch.row_solution)
    _pipeline_changed!(ws,ws.scratch.rho)
    _invalidate_pricing_pool!(ws;basis=false)
    _simplex_event!(ws,:correction)
    return true
end

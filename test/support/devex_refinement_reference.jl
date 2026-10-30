module RefinementReference
using JSimplex
const JS=JSimplex
function refine_basis_solve!(destination::AbstractVector{T},ws::JS.SimplexWorkspace{T},
                             rhs::AbstractVector{T},policy::JS.NumericalPolicy{T},stop;
                             transposed::Bool=false)::JS.SolveQuality{T} where {T}
    m = size(ws.problem.A,1)
    length(destination) == length(rhs) == m || throw(DimensionMismatch("basis solve dimensions"))
    Base.mightalias(destination,rhs) && throw(ArgumentError("basis solve destination aliases RHS"))
    buffers = JS._pivot_quality_buffers(ws)
    arrays = (buffers.rhs,buffers.unit,buffers.correction,buffers.trial,buffers.singletons,
        buffers.column.residual,buffers.column.work_residual,buffers.column.work_scale,
        buffers.column.compensation,buffers.column.error_sum,
        buffers.row.residual,buffers.row.work_residual,buffers.row.work_scale,
        buffers.row.compensation,buffers.row.error_sum,
        ws.problem.A.nzval)
    any(a -> Base.mightalias(a,destination) || Base.mightalias(a,rhs),arrays) &&
        throw(ArgumentError("basis solve arguments overlap private or model storage"))
    storage = ws.scratch.basis_matrix
    if !isnothing(storage) &&
       (Base.mightalias(storage.nzval,destination) || Base.mightalias(storage.nzval,rhs))
        throw(ArgumentError("basis solve arguments overlap basis assembly storage"))
    end
    B = JS._basis_matrix!(ws)
    if T === BigFloat
        bits = JS._stored_quality_bits(T,B,destination,rhs,policy)
        return setprecision(BigFloat,bits) do
            JS._record_refactor_quality!(ws,_refine_basis_solve!(destination,ws,B,rhs,policy,stop,buffers,transposed))
        end
    end
    return JS._record_refactor_quality!(ws,_refine_basis_solve!(destination,ws,B,rhs,policy,stop,buffers,transposed))
end

function _refine_basis_solve!(destination::AbstractVector{T},ws,B,rhs,policy,stop,buffers,transposed) where T
    quality_scratch = transposed ? buffers.row : buffers.column
    saved_rhs = copyto!(buffers.rhs,rhs)
    quality = JS.solve_quality!(quality_scratch,B,destination,saved_rhs,policy;transposed)
    quality.finite || return quality
    wide = policy.solve_refinement && T === Float64 && !quality.reliable
    if wide && policy.max_refinements > 0
        stop() && return quality
        quality = JS._refinement_quality!(quality_scratch,B,destination,saved_rhs,policy,transposed,wide)
    end
    for _ in 1:policy.max_refinements
        (quality.reliable || !quality.finite || stop()) && return quality
        JS._simplex_event!(ws,:correction_attempt)
        correction = JS._timed_simplex(ws,transposed ? :btran : :ftran) do
            transposed ? JS.transpose_solve!(buffers.correction,ws.factorization,quality_scratch.residual) :
                         JS._ordinary_forward_solve!(buffers.correction,ws.factorization,quality_scratch.residual)
        end
        all(isfinite,correction) || return quality
        changed = false
        for i in eachindex(destination)
            buffers.trial[i] = destination[i]+correction[i]
            changed |= buffers.trial[i] != destination[i]
        end
        all(isfinite,buffers.trial) || return quality
        !changed && !policy.solve_refinement && return quality
        trial_quality = JS._refinement_quality!(quality_scratch,B,buffers.trial,saved_rhs,policy,transposed,wide)
        trial_quality.finite || return quality
        if policy.solve_refinement && !trial_quality.reliable
            # The correction is no longer needed; reuse its storage to retain
            # the ordinary candidate if homogeneous cleanup does not help.
            copyto!(buffers.correction,buffers.trial)
            if JS._clean_homogeneous_terms!(buffers.trial,B,saved_rhs,transposed,buffers.singletons,policy)
                cleaned = JS._refinement_quality!(quality_scratch,B,buffers.trial,saved_rhs,policy,transposed,wide)
                if cleaned.finite && (cleaned.reliable || JS._refinement_error(cleaned) < JS._refinement_error(trial_quality))
                    trial_quality = cleaned
                else
                    copyto!(buffers.trial,buffers.correction)
                    trial_quality = JS._refinement_quality!(quality_scratch,B,buffers.trial,saved_rhs,policy,transposed,wide)
                end
            end
        end
        (trial_quality.reliable || JS._refinement_error(trial_quality) < JS._refinement_error(quality)) || return quality
        stop() && return quality
        copyto!(destination,buffers.trial)
        JS._pipeline_changed!(ws,destination)
        quality = trial_quality
        JS._simplex_event!(ws,:correction)
    end
    return quality
end
end # module

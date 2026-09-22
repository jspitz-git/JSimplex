"""Refine a basis solve using bounded corrections and an owned RHS copy.

A reliable result certifies componentwise backward error, not forward error or
pivot safety. The destination retains the last accepted finite improvement.
Arguments must not overlap each other, the model, or private refinement storage.
"""
function refine_basis_solve!(destination::AbstractVector{T},ws::SimplexWorkspace{T},
                             rhs::AbstractVector{T},policy::NumericalPolicy{T},stop;
                             transposed::Bool=false)::SolveQuality{T} where {T}
    m = size(ws.problem.A,1)
    length(destination) == length(rhs) == m || throw(DimensionMismatch("basis solve dimensions"))
    Base.mightalias(destination,rhs) && throw(ArgumentError("basis solve destination aliases RHS"))
    buffers = _pivot_quality_buffers(ws)
    arrays = (buffers.rhs,buffers.unit,buffers.correction,buffers.trial,buffers.singletons,
        buffers.column.residual,buffers.column.work_residual,buffers.column.work_scale,
        buffers.row.residual,buffers.row.work_residual,buffers.row.work_scale,
        ws.problem.A.nzval)
    any(a -> Base.mightalias(a,destination) || Base.mightalias(a,rhs),arrays) &&
        throw(ArgumentError("basis solve arguments overlap private or model storage"))
    storage = ws.scratch.basis_matrix
    if !isnothing(storage) &&
       (Base.mightalias(storage.nzval,destination) || Base.mightalias(storage.nzval,rhs))
        throw(ArgumentError("basis solve arguments overlap basis assembly storage"))
    end
    B = _basis_matrix!(ws)
    if T === BigFloat
        bits = _stored_quality_bits(T,B,destination,rhs,policy)
        return setprecision(BigFloat,bits) do
            _refine_basis_solve!(destination,ws,B,rhs,policy,stop,buffers,transposed)
        end
    end
    return _refine_basis_solve!(destination,ws,B,rhs,policy,stop,buffers,transposed)
end

_refinement_error(q) = isnothing(q.relative_error) ? q.absolute_error : q.relative_error

function _refinement_quality!(scratch::SolveQualityScratch{T},B,x,rhs,policy,transposed,wide) where T
    if T === Float64 && wide
        return _wide_solve_quality!(scratch,B,x,rhs,policy,transposed)
    end
    return solve_quality!(scratch,B,x,rhs,policy;transposed)
end

# A homogeneous row with a single active term can be satisfied exactly by
# clearing that term. This is only a proposed cleanup: the whole system must
# still pass the same independent error test before accepting the candidate.
function _clean_homogeneous_terms!(x::AbstractVector{T},B,rhs,transposed,singletons,policy) where T
    changed = false
    if transposed
        for column in axes(B,2)
            iszero(rhs[column]) || continue
            active = 0
            for p in nzrange(B,column)
                row = B.rowval[p]
                (iszero(B.nzval[p]) || iszero(x[row])) && continue
                active = active == 0 ? row : -1
                active == -1 && break
            end
            if active > 0
                x[active] = zero(eltype(x))
                changed = true
            end
        end
    else
        fill!(singletons,0)
        for column in axes(B,2)
            iszero(x[column]) && continue
            for p in nzrange(B,column)
                iszero(B.nzval[p]) && continue
                row = B.rowval[p]
                singletons[row] = singletons[row] == 0 ? column : -1
            end
        end
        for row in eachindex(rhs)
            column = singletons[row]
            if iszero(rhs[row]) && column > 0 && !iszero(x[column])
                x[column] = zero(eltype(x))
                changed = true
            end
        end
    end
    if T <: AbstractFloat
        cutoff = policy.solve_tolerance*maximum(abs,x;init=zero(T))
        # Coupled roundoff terms may prevent a homogeneous row from having a
        # lone active term. Propose their joint removal only in such rows.
        # The caller still tests the entire system and restores a worse trial.
        if transposed
            for column in axes(B,2)
                iszero(rhs[column]) || continue
                for p in nzrange(B,column)
                    row = B.rowval[p]
                    if !iszero(B.nzval[p]) && zero(T) < abs(x[row]) <= cutoff
                        x[row] = zero(T)
                        changed = true
                    end
                end
            end
        else
            for column in axes(B,2)
                zero(T) < abs(x[column]) <= cutoff || continue
                for p in nzrange(B,column)
                    if !iszero(B.nzval[p]) && iszero(rhs[B.rowval[p]])
                        x[column] = zero(T)
                        changed = true
                        break
                    end
                end
            end
        end
    end
    return changed
end

function _refine_basis_solve!(destination::AbstractVector{T},ws,B,rhs,policy,stop,buffers,transposed) where T
    quality_scratch = transposed ? buffers.row : buffers.column
    saved_rhs = copyto!(buffers.rhs,rhs)
    quality = solve_quality!(quality_scratch,B,destination,saved_rhs,policy;transposed)
    quality.finite || return quality
    wide = policy.solve_refinement && T === Float64 && !quality.reliable
    if wide && policy.max_refinements > 0
        stop() && return quality
        quality = _refinement_quality!(quality_scratch,B,destination,saved_rhs,policy,transposed,wide)
    end
    for _ in 1:policy.max_refinements
        (quality.reliable || !quality.finite || stop()) && return quality
        _simplex_event!(ws,:correction_attempt)
        correction = _timed_simplex(ws,transposed ? :btran : :ftran) do
            transposed ? transpose_solve!(buffers.correction,ws.factorization,quality_scratch.residual) :
                         forward_solve!(buffers.correction,ws.factorization,quality_scratch.residual)
        end
        all(isfinite,correction) || return quality
        changed = false
        for i in eachindex(destination)
            buffers.trial[i] = destination[i]+correction[i]
            changed |= buffers.trial[i] != destination[i]
        end
        all(isfinite,buffers.trial) || return quality
        !changed && !policy.solve_refinement && return quality
        trial_quality = _refinement_quality!(quality_scratch,B,buffers.trial,saved_rhs,policy,transposed,wide)
        trial_quality.finite || return quality
        if policy.solve_refinement && !trial_quality.reliable
            # The correction is no longer needed; reuse its storage to retain
            # the ordinary candidate if homogeneous cleanup does not help.
            copyto!(buffers.correction,buffers.trial)
            if _clean_homogeneous_terms!(buffers.trial,B,saved_rhs,transposed,buffers.singletons,policy)
                cleaned = _refinement_quality!(quality_scratch,B,buffers.trial,saved_rhs,policy,transposed,wide)
                if cleaned.finite && (cleaned.reliable || _refinement_error(cleaned) < _refinement_error(trial_quality))
                    trial_quality = cleaned
                else
                    copyto!(buffers.trial,buffers.correction)
                    trial_quality = _refinement_quality!(quality_scratch,B,buffers.trial,saved_rhs,policy,transposed,wide)
                end
            end
        end
        (trial_quality.reliable || _refinement_error(trial_quality) < _refinement_error(quality)) || return quality
        stop() && return quality
        copyto!(destination,buffers.trial)
        quality = trial_quality
        _simplex_event!(ws,:correction)
    end
    return quality
end

# A clock-only guard also works inside the callback-free pivot commit window.
struct _BasisSolveClock
    start_ns::UInt64
    limit_seconds::Float64
end
(stop::_BasisSolveClock)() = stop.limit_seconds != Inf &&
    (time_ns()-stop.start_ns)/1e9 >= stop.limit_seconds
_basis_solve_stop(ws,::Nothing) = _BasisSolveClock(ws.progress.start_ns,ws.options.time_limit)
_basis_solve_stop(ws,stop) = stop

function _maybe_refine_basis_solve!(destination,ws,rhs,stop=nothing;transposed=false)
    policy = ws.progress.numerical_policy
    policy.solve_refinement || return true
    return refine_basis_solve!(destination,ws,rhs,policy,_basis_solve_stop(ws,stop);transposed).reliable
end

function _checked_basis_solve!(destination,ws,rhs,stop=nothing;transposed=false)
    if transposed
        transpose_solve!(destination,ws.factorization,rhs)
    else
        forward_solve!(destination,ws.factorization,rhs)
    end
    _maybe_refine_basis_solve!(destination,ws,rhs,stop;transposed) || throw(_UnreliableBasisSolve())
    return destination
end

# Precision-specialized repair retains the legacy absolute residual targets,
# 32-correction budget and independent 256/512-bit agreement checks in callers.
# These stronger repairs are separate from ordinary backward-error acceptance.
function _refined_basis_solution(factor,B,rhs::Vector{Float64},bits::Int,stop;
                                  transposed::Bool=false)
    return setprecision(BigFloat,bits) do
        rhs_big = BigFloat.(rhs)
        values = BigFloat.(B.nzval)
        solution = BigFloat.(transposed ? transpose(factor) \ rhs : factor \ rhs)
        all(isfinite,solution) || return nothing
        residual = similar(rhs_big)
        scale = max(one(BigFloat),maximum(abs,rhs_big;init=zero(BigFloat)))
        target = BigFloat(10)^(-(bits == 256 ? 40 : 90))
        for correction in 0:32
            stop() && return nothing
            if transposed
                for column in eachindex(rhs_big)
                    column % 1024 == 0 && stop() && return nothing
                    total = zero(BigFloat)
                    for position in B.colptr[column]:(B.colptr[column+1]-1)
                        total += values[position]*solution[B.rowval[position]]
                    end
                    residual[column] = total-rhs_big[column]
                end
            else
                residual .= -rhs_big
                for column in eachindex(solution)
                    column % 1024 == 0 && stop() && return nothing
                    value = solution[column]
                    for position in B.colptr[column]:(B.colptr[column+1]-1)
                        residual[B.rowval[position]] += values[position]*value
                    end
                end
            end
            error = maximum(abs,residual;init=zero(BigFloat))/scale
            isfinite(error) || return nothing
            error <= target && return solution
            correction == 32 && return nothing
            narrow_residual = Float64.(residual)
            all(isfinite,narrow_residual) || return nothing
            step = transposed ? transpose(factor) \ narrow_residual : factor \ narrow_residual
            all(isfinite,step) || return nothing
            changed = false
            for i in eachindex(solution)
                value = solution[i]-BigFloat(step[i])
                changed |= value != solution[i]
                solution[i] = value
            end
            changed || return nothing
        end
        return nothing
    end
end

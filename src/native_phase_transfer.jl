# Phase export owns a fresh workspace. Preserve its native primal point and
# repair reconstruction only with bounded, independently certified operations.
_native_phase_transfer_enabled(ws) =
    ws.options.algorithm == :primal && _legacy_primal_row_validation_enabled(ws)

# Propose clearing a coupled roundoff component only after local reconstruction
# stalls. Follow homogeneous rows whose active coordinates are all below the
# correction-based cutoff; do not spread through rows containing larger values
# or a nonzero RHS. The caller still certifies every equation, including those
# outside the component, before publishing the candidate.
function _native_phase_homogeneous_component!(x,B,rows,rhs,policy,cutoff,scratch,stop)
    seen=falses(length(rhs))
    selected=falses(length(x))
    pending=Int[]
    for row in eachindex(rhs)
        stop() && return false
        if abs(scratch.residual[row]) > policy.solve_tolerance*scratch.work_scale[row]
            push!(pending,row)
            seen[row]=true
        end
    end
    head=1
    changed=false
    while head<=length(pending)
        stop() && return false
        row=pending[head];head+=1
        iszero(rhs[row]) || continue
        small=true
        for p in nzrange(rows,row)
            stop() && return false
            iszero(rows.nzval[p]) && continue
            if !(abs(x[rows.rowval[p]])<=cutoff)
                small=false
                break
            end
        end
        small || continue
        for p in nzrange(rows,row)
            stop() && return false
            column=rows.rowval[p]
            (iszero(rows.nzval[p]) || iszero(x[column]) || selected[column]) && continue
            selected[column]=true
            changed=true
            for q in nzrange(B,column)
                stop() && return false
                neighbor=B.rowval[q]
                (iszero(B.nzval[q]) || seen[neighbor]) && continue
                seen[neighbor]=true
                push!(pending,neighbor)
            end
        end
    end
    changed && !stop() || return false
    for column in eachindex(x)
        stop() && return false
        selected[column] && (x[column]=zero(eltype(x)))
    end
    return true
end

_native_phase_local_rows!(x,B,rhs,policy,cutoff,stop) = false
function _native_phase_local_rows!(x::Vector{T}, B::SparseMatrixCSC{T}, rhs,
                                    policy, cutoff::T, stop) where {T<:Union{Float32,Float64}}
    stop() && return false
    trial=copy(x)
    rows=copy(transpose(B))
    scratch=SolveQualityScratch(T,length(rhs))
    for sweep in 1:8
        stop() && return false
        quality=_compensated_solve_quality!(scratch,B,trial,rhs,policy,false)
        isnothing(quality) && return false
        if quality.reliable
            stop() && return false
            copyto!(x,trial)
            return true
        end
        changed=false
        for row in eachindex(rhs)
            stop() && return false
            abs(scratch.residual[row]) > policy.solve_tolerance*scratch.work_scale[row] || continue
            chosen=largest=0
            product_scale=coefficient_scale=zero(T)
            for p in nzrange(rows,row)
                stop() && return false
                coefficient=rows.nzval[p]
                magnitude=abs(coefficient*trial[rows.rowval[p]])
                if magnitude > product_scale
                    chosen=p;product_scale=magnitude
                end
                if abs(coefficient) > coefficient_scale
                    largest=p;coefficient_scale=abs(coefficient)
                end
            end
            chosen==0 && (chosen=largest)
            chosen==0 && continue
            # Direct reconstruction retains contributions too small to survive
            # cancellation in x + correction. Final full-system checks decide.
            total=rhs[row]
            compensation=zero(T)
            for p in nzrange(rows,row)
                stop() && return false
                p==chosen && continue
                a=rows.nzval[p];value=trial[rows.rowval[p]]
                product=-a*value
                product_error=fma(-a,value,-product)
                next=total+product
                part=next-total
                compensation+=(total-(next-part))+(product-part)+product_error
                total=next
            end
            value=(total+compensation)/rows.nzval[chosen]
            index=rows.rowval[chosen]
            isfinite(value) && abs(value-trial[index])<=cutoff || continue
            if value!=trial[index]
                trial[index]=value
                changed=true
            end
        end
        changed || break
    end
    quality=_compensated_solve_quality!(scratch,B,trial,rhs,policy,false)
    (isnothing(quality) || stop()) && return false
    if !quality.reliable
        _native_phase_homogeneous_component!(trial,B,rows,rhs,policy,cutoff,scratch,stop) || return false
        quality=_compensated_solve_quality!(scratch,B,trial,rhs,policy,false)
        (isnothing(quality) || !quality.reliable || stop()) && return false
    end
    copyto!(x,trial)
    return true
end

function _native_phase_primal_solve!(x::Vector{T},ws,B,rhs,stop) where {T<:Union{Float32,Float64}}
    policy=ws.progress.numerical_policy
    scratch=SolveQualityScratch(T,length(rhs))
    stop() && return false
    quality=_compensated_solve_quality!(scratch,B,x,rhs,policy,false)
    isnothing(quality) && return false
    quality.reliable && return true
    policy.max_refinements>0 || return false
    _simplex_event!(ws,:correction_attempt)
    stop() && return false
    correction=similar(x)
    _timed_simplex(ws,:ftran) do
        _ordinary_forward_solve!(correction,ws.factorization,scratch.residual)
    end
    all(isfinite,correction) || return false
    trial=x+correction
    all(isfinite,trial) || return false
    cutoff=policy.solve_tolerance*maximum(abs,correction;init=zero(T))
    _native_phase_local_rows!(trial,B,rhs,policy,cutoff,stop) || return false
    stop() && return false
    copyto!(x,trial)
    return true
end

_complete_native_phase_transfer!(ws,stop) = false
function _complete_native_phase_transfer!(ws::SimplexWorkspace{T},stop) where {T<:Union{Float32,Float64}}
    _native_phase_transfer_enabled(ws) && !stop() && _finite_workspace(ws) || return false
    if _recomputed_basis_reliable(ws)
        return _legacy_primal_point_certified(ws) && !stop()
    end
    ws.progress.numerical_policy.max_refinements>0 || return false
    B=_basis_matrix!(ws)
    rhs=_basis_primal_rhs(ws)
    before=ws.primal[ws.basis.basic_indices]
    basic=copy(before)
    dual=copy(ws.scratch.rho)
    _native_phase_primal_solve!(basic,ws,B,rhs,stop) || return false
    _native_cleanup_solve!(dual,ws,B,ws.costs[ws.basis.basic_indices],stop;transposed=true) || return false
    prices=similar(ws.reduced_costs)
    _recompute_reduced_costs!(prices,ws,dual)
    all(isfinite,prices) && !stop() || return false
    accepted=false
    try
        for (row,index) in enumerate(ws.basis.basic_indices)
            ws.primal[index]=basic[row]
        end
        _legacy_primal_point_certified(ws) && !stop() || return false
        accepted=true
    finally
        if !accepted
            for (row,index) in enumerate(ws.basis.basic_indices)
                ws.primal[index]=before[row]
            end
        end
    end
    copyto!(ws.scratch.row_solution,basic)
    copyto!(ws.scratch.rho,dual)
    copyto!(ws.reduced_costs,prices)
    _pipeline_changed!(ws,ws.scratch.row_solution)
    _pipeline_changed!(ws,ws.scratch.rho)
    _invalidate_pricing_pool!(ws;basis=false)
    return true
end

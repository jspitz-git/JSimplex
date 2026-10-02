# A failed legacy residual check need not discard an otherwise useful updated
# factor. Try bounded corrections in the problem's hardware floating type and
# publish only a vector that passes the original legacy acceptance test.
_try_native_dual_correction!(workspace, destination, index, leaving_row, stop;
                             transposed=false) = false

function _try_native_dual_correction!(workspace::SimplexWorkspace{T}, destination::Vector{T},
                                     index::Int, leaving_row::Int, stop;
                                     transposed::Bool=false) where {T}
    T === Float32 || T === Float64 || return false
    policy = workspace.progress.numerical_policy
    (policy.pivot_validation || policy.solve_refinement || policy.recovery) && return false
    policy.max_refinements > 0 || return false
    stop() && return false
    buffers = _pivot_quality_buffers(workspace)
    rhs = buffers.rhs
    fill!(rhs, zero(T))
    if transposed
        rhs[index] = one(T)
    else
        A = workspace.problem.A
        if index <= size(A, 2)
            for p in nzrange(A, index)
                rhs[A.rowval[p]] = A.nzval[p]
            end
        else
            rhs[index - size(A, 2)] = -one(T)
        end
    end
    B = _basis_matrix!(workspace)
    scratch = transposed ? buffers.row : buffers.column
    trial = copyto!(buffers.trial, destination)
    for _ in 1:policy.max_refinements
        stop() && return false
        # Calling the native enclosure directly avoids its arbitrary-precision
        # fallback. An ambiguous or exceptional residual retains refactorization.
        quality = _compensated_solve_quality!(scratch, B, trial, rhs, policy, transposed)
        (isnothing(quality) || !quality.finite) && return false
        _simplex_event!(workspace, :correction_attempt)
        try
            _timed_simplex(workspace, transposed ? :btran : :ftran) do
                transposed ? transpose_solve!(buffers.correction, workspace.factorization, scratch.residual) :
                             _ordinary_forward_solve!(buffers.correction, workspace.factorization, scratch.residual)
            end
        catch exception
            _is_numerical_exception(exception) || rethrow()
            return false
        end
        all(isfinite, buffers.correction) || return false
        for i in eachindex(trial)
            trial[i] += buffers.correction[i]
        end
        all(isfinite, trial) || return false
        accepted = if transposed
            _dual_row_residual_ratio(workspace, trial, leaving_row) <= one(T)
        else
            copyto!(workspace.scratch.row_rhs, rhs)
            _pipeline_changed!(workspace, workspace.scratch.row_rhs)
            pivot = trial[leaving_row]
            tolerance = max(workspace.options.zero_tolerance, sqrt(eps(one(T))) * abs(pivot))
            # Correcting a direction must not silently validate a different
            # ratio decision. A disagreeing row needs the existing full retry.
            abs(pivot) > workspace.options.zero_tolerance &&
                abs(pivot - workspace.scratch.tableau_row[index]) <= tolerance &&
                _dual_direction_residual_ok!(workspace, trial, pivot)
        end
        if accepted
            stop() && return false
            copyto!(destination, trial)
            _pipeline_changed!(workspace, destination)
            workspace.scratch.refactorization.residual_bad = true
            _simplex_event!(workspace, :correction)
            return true
        end
    end
    return false
end

# Retain the low BTRAN correction while pricing. Rounding rho + correction
# first can erase the very information needed by a small tableau coefficient.
function _native_corrected_tableau!(out,A,rho,correction,stop)
    T=eltype(out)
    for column in axes(A,2)
        column%1024==0 && stop() && return false
        total=error=zero(T)
        for p in nzrange(A,column)
            row=A.rowval[p];coefficient=A.nzval[p]
            for value in (rho[row],correction[row])
                product=coefficient*value
                product_error=fma(coefficient,value,-product)
                next=total+product;part=next-total
                error+=(total-(next-part))+(product-part)+product_error
                total=next
            end
        end
        out[column]=total+error
    end
    n=size(A,2)
    for row in eachindex(rho)
        row%1024==0 && stop() && return false
        out[n+row]=-(rho[row]+correction[row])
    end
    return all(isfinite,out) && !stop()
end

_try_native_dual_tableau!(ws,row,entering,orientation,violation,flips,stop) = false
function _try_native_dual_tableau!(ws::SimplexWorkspace{T},row,entering,orientation,
                                  violation,flips,stop) where {T<:Union{Float32,Float64}}
    policy=ws.progress.numerical_policy
    (policy.pivot_validation || policy.solve_refinement || policy.recovery) && return false
    policy.max_refinements>0 && _is_staged_workspace(ws) &&
        isempty(ws.factorization.updates) && !stop() || return false
    B=_basis_matrix!(ws)
    unit=zeros(T,length(ws.scratch.rho));unit[row]=one(T)
    scratch=SolveQualityScratch(T,length(unit))
    quality=_compensated_solve_quality!(scratch,B,ws.scratch.rho,unit,policy,true)
    (isnothing(quality) || !quality.finite || stop()) && return false
    correction=similar(unit)
    _simplex_event!(ws,:correction_attempt)
    _timed_simplex(ws,:btran) do
        transpose_solve!(correction,ws.factorization,scratch.residual)
    end
    all(isfinite,correction) && !stop() || return false
    rho=ws.scratch.rho+correction
    all(isfinite,rho) && _dual_row_residual_ratio(ws,rho,row)<=one(T) || return false
    tableau=similar(ws.scratch.tableau_row)
    _native_corrected_tableau!(tableau,ws.problem.A,ws.scratch.rho,correction,stop) || return false
    direction=copy(ws.scratch.row_solution)
    old_tableau=copy(ws.scratch.tableau_row)
    old_flips=copy(flips)
    accepted=false
    try
        # The existing direction correction verifies its pivot against this row.
        copyto!(ws.scratch.tableau_row,tableau)
        _pipeline_changed!(ws,ws.scratch.tableau_row)
        _try_native_dual_correction!(ws,direction,entering,row,stop) || return false
        pivot=direction[row];row_pivot=tableau[entering]
        agreement=sqrt(eps(one(T)))*max(abs(pivot),abs(row_pivot))
        _pivot_agrees(row_pivot,pivot,agreement) && !stop() || return false
        next_entering,next_flips,_=_configured_dual_ratio_test(ws,tableau,orientation,violation)
        # Refinement must not silently accept a different ratio decision.
        next_entering==entering && next_flips==old_flips && !stop() || return false
        copyto!(ws.scratch.rho,rho)
        copyto!(ws.scratch.row_solution,direction)
        _pipeline_changed!(ws,ws.scratch.rho)
        _pipeline_changed!(ws,ws.scratch.row_solution)
        accepted=true
        return true
    finally
        if !accepted
            copyto!(ws.scratch.tableau_row,old_tableau)
            copyto!(resize!(flips,length(old_flips)),old_flips)
            _pipeline_changed!(ws,ws.scratch.tableau_row)
        end
    end
end

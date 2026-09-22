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

_checkpoint_model(ws) = (objectid(ws.problem.A),size(ws.problem.A)...)
_checkpoint_phase(ws) = (objectid(ws.costs),ws.scratch.phase_generation)

_with_recovery_precision(f,ws,c) = f()
function _with_recovery_precision(f,ws::SimplexWorkspace{BigFloat},c)
    bits = max(precision(BigFloat),precision(ws.progress.numerical_policy.solve_tolerance),
        maximum(precision,ws.problem.A.nzval;init=2),maximum(precision,c.costs;init=2))
    for bounds in (c.lower,c.upper), bound in bounds
        isfinite(bound) && (bits = max(bits,precision(bound_value(bound))))
    end
    return setprecision(f,BigFloat,bits)
end

"""Own the working basis and perturbations, without time or consumed work."""
function checkpoint_basis(ws::SimplexWorkspace{T})::BasisCheckpoint{T} where T
    _validate_basis(ws)
    return BasisCheckpoint(Basis(ws.basis.basic_indices,ws.basis.states),
        copy(ws.costs),copy(ws.lower),copy(ws.upper),_checkpoint_model(ws),
        _checkpoint_phase(ws),ws.perturbed)
end

function _invalidate_basis_checkpoints!(ws)
    empty!(ws.scratch.checkpoints)
    empty!(ws.scratch.recovery_rejections)
    ws.scratch.phase_generation += UInt(1)
    return nothing
end

function _checkpoint_matches(ws,c)
    m,n = size(ws.problem.A)
    return c.working_model == _checkpoint_model(ws) && c.phase == _checkpoint_phase(ws) &&
        length(c.basis.basic_indices) == m && length(c.basis.states) == m+n &&
        length(c.costs) == length(c.lower) == length(c.upper) == m+n
end

# Observers run before publication; event counts record only a committed change.
function _recovery_observer!(::Nothing,reason,trial)
    return nothing
end
function _recovery_observer!(diagnostics::SimplexDiagnostics,reason,trial)
    isnothing(diagnostics.observer) && return nothing
    try
        diagnostics.observer(reason,trial)
    catch exception
        throw(DiagnosticObserverFailure(exception))
    end
    return nothing
end
_record_recovery!(::Nothing,reason) = nothing
_record_recovery!(diagnostics::SimplexDiagnostics,reason) = record_event!(diagnostics,reason)

function _recovery_trial(ws::SimplexWorkspace{T},c::BasisCheckpoint{T},stop) where T
    stop() && return nothing
    m,n = size(ws.problem.A)
    trial = SimplexWorkspace(ws.problem,ws.options,ws.progress,
        copy(c.costs),copy(c.lower),copy(c.upper),Basis(c.basis.basic_indices,c.basis.states),
        zeros(T,m+n),zeros(T,m+n),ones(T,m+n),falses(m+n),ws.factorization,
        SimplexScratch(T,m,m+n),(getfield(ws,key) for key in _PIVOT_STATE_SCALARS)...)
    _validate_basis(trial)
    trial.perturbed = c.perturbed
    trial.scratch.recovery_active = true
    B = _basis_matrix!(trial)
    try
        @logmsg ws.options.log_level "Rebuilding recovery basis" iterations=ws.iterations refactorizations=ws.refactorizations+1
    catch exception
        stop.exception = exception
        rethrow()
    end
    stop() && return nothing
    # Construction cannot mutate any backend or LU scratch owned by the live solve.
    try
        trial.factorization = _timed_simplex(ws,:refactorization) do
            _basis_factorization(B,ws.options)
        end
    finally
        ws.refactorizations += 1
    end
    trial.refactorizations = ws.refactorizations
    stop() && return nothing
    reset_devex!(trial)
    recompute!(trial;caller_guard=stop)
    _finite_workspace(trial) && _recomputed_basis_reliable(trial) || return nothing
    _rebuild_recovery_weights!(trial,stop) || return nothing
    stop() && return nothing
    return trial
end

function _rebuild_recovery_weights!(trial::SimplexWorkspace{T},stop) where T
    # Primal weights remain invalid and are computed on demand. Dual steepest
    # edge weights belong to basic rows and must match the rebuilt inverse.
    trial.options.pricing == :steepest_edge && !trial.dual_pricing_fallback &&
        !trial.dual_devex_fallback || return true
    m = length(trial.basis.basic_indices)
    rhs,direction = zeros(T,m),zeros(T,m)
    policy = trial.progress.numerical_policy
    for row in 1:m
        stop() && return false
        fill!(rhs,zero(T))
        rhs[row] = one(T)
        transpose_solve!(direction,trial.factorization,rhs)
        refine_basis_solve!(direction,trial,rhs,policy,stop;transposed=true).reliable || return false
        weight = dot(direction,direction)
        isfinite(weight) && weight > zero(T) || return false
        trial.pricing_weights[trial.basis.basic_indices[row]] = max(_typed_ratio(T,1,10^4),weight)
    end
    return true
end

# Only call immediately after recompute!, while rho still holds dual prices.
function _recomputed_basis_reliable(ws::SimplexWorkspace{T}) where T
    B = _basis_matrix!(ws)
    m,n = size(ws.problem.A)
    rhs = zeros(T,m)
    for j in eachindex(ws.basis.states)
        ws.basis.states[j] == BASIC && continue
        value = _nonbasic_value(ws,j)
        if j <= n
            for p in nzrange(ws.problem.A,j)
                rhs[ws.problem.A.rowval[p]] -= ws.problem.A.nzval[p]*value
            end
        else
            rhs[j-n] += value
        end
    end
    policy = ws.progress.numerical_policy
    scratch = SolveQualityScratch(T,m)
    solve_quality!(scratch,B,ws.primal[ws.basis.basic_indices],rhs,policy).reliable || return false
    return solve_quality!(scratch,B,ws.scratch.rho,ws.costs[ws.basis.basic_indices],
        policy;transposed=true).reliable
end

function _publish_recovery!(ws,trial,reason,stop)
    data = checkpoint_basis(trial)
    checkpoint = BasisCheckpoint(data.basis,data.costs,data.lower,data.upper,
        _checkpoint_model(ws),_checkpoint_phase(ws),data.perturbed)
    _recovery_observer!(ws.progress.diagnostics,reason,trial)
    _recovery_observer!(ws.progress.diagnostics,:checkpoint,trial)
    stop() && return false
    _copy_pivot_state!(ws,trial)
    ws.factorization = trial.factorization
    ws.scratch.pending_factor_update = false
    ws.scratch.post_iteration = :none
    ws.scratch.recovery_restored = reason == :restore_checkpoint
    _store_basis_checkpoint!(ws,checkpoint)
    _record_recovery!(ws.progress.diagnostics,reason)
    _record_recovery!(ws.progress.diagnostics,:checkpoint)
    return true
end

"""Rebuild a checkpoint privately; publication never rolls back consumed work."""
function restore_checkpoint!(ws::SimplexWorkspace{T},c::BasisCheckpoint{T},stop)::Bool where T
    _checkpoint_matches(ws,c) || return false
    guard = _guard_stop_callback(stop)
    try
        return _with_recovery_precision(ws,c) do
            trial = _recovery_trial(ws,c,guard)
            isnothing(trial) && return false
            _publish_recovery!(ws,trial,:restore_checkpoint,guard)
        end
    catch exception
        exception === guard.exception && rethrow()
        _is_numerical_exception(exception) && return false
        rethrow()
    end
end

function _remember_verified_basis!(ws,stop)::Bool
    stop() && return false
    _recomputed_basis_reliable(ws) || return false
    checkpoint = checkpoint_basis(ws)
    _recovery_observer!(ws.progress.diagnostics,:checkpoint,ws)
    stop() && return false
    _store_basis_checkpoint!(ws,checkpoint)
    _record_recovery!(ws.progress.diagnostics,:checkpoint)
    return true
end

function _store_basis_checkpoint!(ws,checkpoint)
    history = ws.scratch.checkpoints
    length(history) == 2 && popfirst!(history)
    push!(history,checkpoint)
    return nothing
end

function _sync_recovery_rejections!(ws)
    key = hash(ws.basis.states,hash(ws.basis.basic_indices))
    if key != ws.scratch.recovery_basis_key
        empty!(ws.scratch.recovery_rejections)
        ws.scratch.recovery_basis_key = key
    end
    return nothing
end

function _recovery_nonbasic_state(ws,index)
    isfinite(ws.lower[index]) && return AT_LOWER
    isfinite(ws.upper[index]) && return AT_UPPER
    return FREE_NONBASIC
end

function _reject_recovery_pair!(ws,row,entering,policy)
    _sync_recovery_rejections!(ws)
    row > 0 && entering > 0 || return nothing
    rejected = ws.scratch.recovery_rejections
    pair = (row,entering)
    pair in rejected && return nothing
    length(rejected) >= policy.max_pivot_candidates && popfirst!(rejected)
    push!(rejected,pair)
    return nothing
end

"""Try bounded column exchanges; numerical recovery does not certify feasibility."""
function repair_basis!(ws::SimplexWorkspace{T},policy::NumericalPolicy{T},stop)::Bool where T
    ws.scratch.recovery_restored = false
    guard = _guard_stop_callback(stop)
    guard() && return false
    policy.max_recovery_rounds == 0 && return false
    original = checkpoint_basis(ws)
    return _with_recovery_precision(ws,original) do
        _repair_basis!(ws,policy,guard,original)
    end
end

function _repair_basis!(ws,policy,guard,original)
    _sync_recovery_rejections!(ws)
    m,n = size(ws.problem.A)
    m == 0 && return false
    trigger = (ws.scratch.selected_row,ws.scratch.selected_entering)
    rows = collect(1:m)
    if 1 <= trigger[1] <= m
        deleteat!(rows,trigger[1])
        pushfirst!(rows,trigger[1])
    end
    # Stable ordering favors the row's slack, other slacks, then structural columns.
    candidates = [j for j in (n+1):(n+m) if ws.basis.states[j] != BASIC]
    append!(candidates,[j for j in 1:n if ws.basis.states[j] != BASIC])
    limit = Int(min(big(policy.max_pivot_candidates)^2,typemax(Int)))
    attempts = 0
    for row in Iterators.take(rows,policy.max_pivot_candidates)
        order = copy(candidates)
        own_slack = findfirst(==(n+row),order)
        if !isnothing(own_slack)
            deleteat!(order,own_slack)
            pushfirst!(order,n+row)
        end
        for entering in order
            attempts >= limit && break
            guard() && return false
            (row,entering) in ws.scratch.recovery_rejections && continue
            attempts += 1
            proposed = Basis(original.basis.basic_indices,original.basis.states)
            leaving = proposed.basic_indices[row]
            proposed.basic_indices[row] = entering
            proposed.states[leaving] = _recovery_nonbasic_state(ws,leaving)
            proposed.states[entering] = BASIC
            candidate = BasisCheckpoint(proposed,original.costs,original.lower,original.upper,
                original.working_model,original.phase,original.perturbed)
            try
                trial = _recovery_trial(ws,candidate,guard)
                if !isnothing(trial)
                    if _publish_recovery!(ws,trial,:repair,guard)
                        empty!(ws.scratch.recovery_rejections)
                        return true
                    end
                    return false
                end
            catch exception
                exception === guard.exception && rethrow()
                _is_numerical_exception(exception) || rethrow()
            end
            _reject_recovery_pair!(ws,row,entering,policy)
        end
        attempts >= limit && break
    end
    # An exhausted repair restores a verified state when available, but reports
    # failure so a caller cannot mistake restoration for a successful exchange.
    for checkpoint in Iterators.reverse(ws.scratch.checkpoints)
        guard() && return false
        if restore_checkpoint!(ws,checkpoint,guard)
            break
        end
    end
    _reject_recovery_pair!(ws,trigger...,policy)
    return false
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

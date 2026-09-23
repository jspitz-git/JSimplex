# Both estimates must have the same sign and be separated from their error.
function _pivot_agrees(row_pivot, column_pivot, error_bound)::Bool
    all(isfinite, (row_pivot,column_pivot,error_bound)) || return false
    error_bound >= zero(error_bound) || return false
    sign(row_pivot) == sign(column_pivot) || return false
    min(abs(row_pivot),abs(column_pivot)) > error_bound || return false
    return abs(row_pivot-column_pivot) <= error_bound
end

struct _StageObserver{W}
    live::W
    pending::Vector{Symbol}
end

_is_staged_workspace(ws) = !isnothing(ws.progress.diagnostics) &&
                           ws.progress.diagnostics.observer isa _StageObserver

struct _PivotDeadline <: Exception end

function (observer::_StageObserver)(reason::Symbol, candidate)
    isnothing(observer.live.progress.diagnostics) && return nothing
    if candidate.scratch.pending_factor_update || candidate.scratch.post_iteration != :none ||
       reason in (:pivot_completed,:flip_completed,:bound_flipped)
        push!(observer.pending,reason)
    else
        _diagnostic_event!(observer.live.progress.diagnostics,reason,candidate)
    end
    return nothing
end

# Internal staging already forwards user observers through the guarded live
# observer. Buffering completion events itself is not a user callback.
function _diagnostic_event!(d::SimplexDiagnostics{F},reason::Symbol,state=nothing) where {F<:_StageObserver}
    d.observer(reason,state)
    return nothing
end

const _PIVOT_STATE_SCALARS = (:iterations,:refactorizations,:perturbed,
    :zero_dual_step_streak,:dual_pricing_fallback,:dual_devex_fallback,
    :dual_refactorization_interval,:dual_recent_repairs,:dual_bad_update_min,
    :dual_stable_refactorizations,:dual_nonzero_steps_since_refactorization)

function _new_candidate_workspace(ws::SimplexWorkspace{T}) where {T}
    if isnothing(ws.scratch.stage_values)
        ws.scratch.stage_values = _PivotStageValues(copy(ws.costs),copy(ws.lower),copy(ws.upper),
            Basis(ws.basis.basic_indices,ws.basis.states),copy(ws.primal),copy(ws.reduced_costs),
            copy(ws.pricing_weights),copy(ws.devex_reference),Symbol[],SimplexDiagnostics())
        ws.scratch.stage_scratch = SimplexScratch(T,size(ws.problem.A,1),length(ws.costs))
    end
    values = ws.scratch.stage_values::_PivotStageValues{T}
    scratch = ws.scratch.stage_scratch::SimplexScratch{T}
    empty!(values.pending_events)
    observer = _StageObserver(ws,values.pending_events)
    base = isnothing(ws.progress.diagnostics) ? values.diagnostics : ws.progress.diagnostics
    # Counts and timers belong to the live solve. The internal observer delays
    # only completion events, so failed attempts still retain actual kernel work.
    diagnostics = SimplexDiagnostics(base.counts,base.events,base.next_event,observer,
        base.kernel_timing,base.kernel_calls,base.kernel_nanoseconds)
    old = ws.progress
    progress = SimplexProgressContext{T,typeof(diagnostics)}(old.start_ns,
        old.objective,old.objective_constant,old.scaling,old.iteration_offset,old.refactorization_offset,
        diagnostics,old.numerical_policy)
    return SimplexWorkspace(ws.problem,ws.options,progress,
        values.costs,values.lower,values.upper,values.basis,values.primal,
        values.reduced_costs,values.pricing_weights,values.devex_reference,
        ws.factorization,scratch,
        (getfield(ws,key) for key in _PIVOT_STATE_SCALARS)...)
end

# Explicit fields keep array element types concrete in this inner-loop copy.
function _copy_pivot_state!(destination,source)
    copyto!(destination.costs,source.costs)
    copyto!(destination.lower,source.lower)
    copyto!(destination.upper,source.upper)
    copyto!(destination.primal,source.primal)
    copyto!(destination.reduced_costs,source.reduced_costs)
    copyto!(destination.pricing_weights,source.pricing_weights)
    copyto!(destination.devex_reference,source.devex_reference)
    copyto!(destination.basis.basic_indices,source.basis.basic_indices)
    copyto!(destination.basis.states,source.basis.states)
    destination.iterations = source.iterations
    destination.refactorizations = source.refactorizations
    destination.perturbed = source.perturbed
    destination.zero_dual_step_streak = source.zero_dual_step_streak
    destination.dual_pricing_fallback = source.dual_pricing_fallback
    destination.dual_devex_fallback = source.dual_devex_fallback
    destination.dual_refactorization_interval = source.dual_refactorization_interval
    destination.dual_recent_repairs = source.dual_recent_repairs
    destination.dual_bad_update_min = source.dual_bad_update_min
    destination.dual_stable_refactorizations = source.dual_stable_refactorizations
    destination.dual_nonzero_steps_since_refactorization = source.dual_nonzero_steps_since_refactorization
    destination.scratch.refactorization = source.scratch.refactorization
    copyto!(destination.scratch.basic_mask,source.scratch.basic_mask)
    copyto!(destination.scratch.steepest_valid,source.scratch.steepest_valid)
    copyto!(destination.scratch.row_rhs,source.scratch.row_rhs)
    copyto!(destination.scratch.row_solution,source.scratch.row_solution)
    copyto!(destination.scratch.rho,source.scratch.rho)
    copyto!(destination.scratch.tau,source.scratch.tau)
    copyto!(destination.scratch.tableau_row,source.scratch.tableau_row)
    copyto!(destination.scratch.pricing_row,source.scratch.pricing_row)
    destination.scratch.steepest_initialized = source.scratch.steepest_initialized
    copyto!(resize!(destination.scratch.recovery_rejections,length(source.scratch.recovery_rejections)),
        source.scratch.recovery_rejections)
    destination.scratch.recovery_basis_key = source.scratch.recovery_basis_key
    return destination
end

function _candidate_workspace(ws::SimplexWorkspace{T,F,M,R,D}) where {T,F,M,R,D}
    candidate = _new_candidate_workspace(ws)
    _copy_pivot_state!(candidate,ws)
    candidate.scratch.pending_factor_update = false
    candidate.scratch.post_iteration = :none
    return candidate
end

function _prepare_primal_candidate!(ws::SimplexWorkspace{T},entering,direction,step,
                                    column,leaving_row,leaving_state) where {T}
    movement = direction*step
    for (row,index) in enumerate(ws.basis.basic_indices)
        ws.primal[index] -= movement*column[row]
    end
    ws.primal[entering] += movement
    if leaving_row > 0
        leaving = ws.basis.basic_indices[leaving_row]
        target = leaving_state == AT_LOWER ? ws.lower[leaving] : ws.upper[leaving]
        ws.primal[leaving] = bound_value(target)
    else
        target = direction > zero(T) ? ws.upper[entering] : ws.lower[entering]
        ws.primal[entering] = bound_value(target)
    end
    return all(isfinite,ws.primal)
end

_finite_pivot_update(update::PackedEta) = all(isfinite,update.values)
_finite_pivot_update(update::Union{ForrestTomlinUpdate,SuhlSuhlUpdate}) =
    all(isfinite,update.multipliers)
_finite_pivot_update(update::BartelsGolubUpdate) =
    all(step -> isfinite(step.multiplier),update.steps)
_finite_updated_factor(factor::PFIFactorization) =
    isempty(factor.updates) || _finite_pivot_update(last(factor.updates))
function _finite_updated_factor(factor::AbstractTriangularBasisFactorization)
    for (i,column) in enumerate(factor.upper)
        all(isfinite,column.values) && !iszero(_upper_value(column,i)) || return false
    end
    return isempty(factor.updates) || _finite_pivot_update(last(factor.updates))
end

function _replace_pivot_column!(ws, column, row; zero_tolerance,stop_requested=nothing)
    if _is_staged_workspace(ws) && !isnothing(stop_requested)
        stop_requested() && throw(_PivotDeadline())
    end
    # A triangular backend may mutate before throwing. Mark it before the call.
    ws.scratch.pending_factor_update = true
    try
        replace_column!(ws.factorization,column,row;zero_tolerance)
    catch exception
        if _is_staged_workspace(ws) && _is_numerical_exception(exception)
            throw(_PivotRejection(row,ws.scratch.selected_entering,:refresh))
        end
        rethrow()
    end
    if _is_staged_workspace(ws) && !_finite_updated_factor(ws.factorization)
        throw(_PivotRejection(row,ws.scratch.selected_entering,:refresh))
    end
    return ws.factorization
end

function _discard_candidate!(ws,candidate)
    if ws.progress.numerical_policy.recovery
        if candidate.scratch.selected_row > 0 || candidate.scratch.selected_entering > 0
            ws.scratch.selected_row = candidate.scratch.selected_row
            ws.scratch.selected_entering = candidate.scratch.selected_entering
        end
    end
    ws.refactorizations = max(ws.refactorizations,candidate.refactorizations)
    if candidate.scratch.pending_factor_update
        # The live arrays still describe the old basis. Rebuild it without a
        # callback, even if the caller's deadline has just expired.
        _before_basis_refactor!(ws,:refactor_pivot)
        _measure_basis_factorization!(ws) do
            _timed_simplex(ws,:refactorization) do
                refactorize!(ws.factorization,basis_matrix(ws))
            end
        end
        _after_basis_refactor!(ws)
        ws.refactorizations += 1
        candidate.scratch.pending_factor_update = false
    end
    # Numerical work happened even when its candidate was discarded. Retain
    # those counts without calling observers with an uncommitted state.
    pending = candidate.progress.diagnostics.observer.pending
    if !isnothing(ws.progress.diagnostics)
        for reason in pending
            reason in (:pivot_completed,:flip_completed,:bound_flipped) && continue
            record_event!(ws.progress.diagnostics,reason)
        end
    end
    empty!(pending)
    return nothing
end

function _transactional_simplex_step!(perform,ws::SimplexWorkspace,stop_requested)
    stop_requested() && return DualTermination(TIME_LIMIT,"time limit reached")
    candidate = _candidate_workspace(ws)
    result = try
        result = perform(candidate,stop_requested)
        if isnothing(result) && candidate.scratch.post_iteration == :primal
            # Finish the ordinary primal recomputation before publishing the
            # new basis. This path has no logger, observer or stop callback.
            recompute!(candidate;refactorize=false)
            _finite_workspace(candidate) || throw(_PivotRejection(
                candidate.scratch.selected_row,candidate.scratch.selected_entering,:refresh))
        elseif isnothing(result) && candidate.scratch.post_iteration in (:primal_flip, :primal_pivot)
            if iszero(candidate.iterations % 20)
                audit = _audit_primal_values!(candidate)
                incremental_pivots = candidate.progress.numerical_policy.incremental_primal_pivots
                verified = audit != :unreliable && (audit == :accurate || incremental_pivots)
                if incremental_pivots
                    verified &= primal_infeasibility(candidate) <= candidate.options.primal_tolerance
                end
                verified || throw(_PivotRejection(
                    candidate.scratch.selected_row, candidate.scratch.selected_entering, :refresh))
            end
        end
        if !candidate.scratch.pending_factor_update && stop_requested()
            _discard_candidate!(ws,candidate)
            return DualTermination(TIME_LIMIT,"time limit reached before pivot application")
        end
        if !isnothing(result) && result.status in (TIME_LIMIT,ITERATION_LIMIT,NUMERICAL_ERROR)
            _discard_candidate!(ws,candidate)
            return result
        end
        result
    catch exception
        _discard_candidate!(ws,candidate)
        exception isa _PivotDeadline && return DualTermination(TIME_LIMIT,"time limit reached before pivot application")
        rethrow()
    end
    # No callback is permitted between these copies. Completion observers run
    # only after the live values, basis, factor and completed-step count agree.
    _copy_pivot_state!(ws,candidate)
    ws.factorization = candidate.factorization
    ws.scratch.pending_factor_update = false
    for reason in candidate.progress.diagnostics.observer.pending
        _simplex_event!(ws,reason)
    end
    scratch = candidate.scratch
    if scratch.post_iteration == :dual
        return _dual_after_iteration!(ws,stop_requested,scratch.post_dual_step,
                                      scratch.post_basis_refreshed,scratch.post_perturb_degenerate)
    elseif scratch.post_iteration in (:primal, :primal_flip, :primal_pivot)
        stop_requested() && return DualTermination(TIME_LIMIT,"time limit reached")
        if scratch.post_refactorize
            recompute!(ws;refactorize=true,caller_guard=stop_requested,
                       diagnostic_reason=_refactor_event(scratch.post_refactor_reason))
        end
    end
    return result
end

"""Independent row and column estimates, borrowed until their scratch is reused."""
struct PivotCandidate{T}
    entering::Int
    leaving_row::Int
    row_pivot::T
    column::Vector{T}
    rho::Vector{T}
end

function _pivot_quality_buffers(ws::SimplexWorkspace{T}) where {T}
    W = T === Float32 ? Float64 : T
    C = _PivotQualityBuffers{T,W}
    if !(ws.scratch.pivot_quality_cache isa C)
        m = size(ws.problem.A,1)
        ws.scratch.pivot_quality_cache = C(zeros(T,m),zeros(T,m),zeros(T,m),zeros(T,m),zeros(Int,m),
                                          SolveQualityScratch(T,m),SolveQualityScratch(T,m))
    end
    return ws.scratch.pivot_quality_cache::C
end

# Retained for internal F04 callers; all correction work now shares one API.
_refine_pivot_solve!(destination,ws,rhs,policy,stop_requested;transposed=false) =
    refine_basis_solve!(destination,ws,rhs,policy,stop_requested;transposed)

struct _PivotRejection <: Exception
    row::Int
    entering::Int
    action::Symbol
end

function _retry_simplex_step!(ws::SimplexWorkspace,stop_requested,algorithm::Symbol,
                              reduced_cost_tolerance,basis_refreshed,perturb_degenerate;
                              recovery_rounds::Int=0)
    policy = ws.progress.numerical_policy
    rejected_entering = ws.scratch.rejected_entering
    rejected_rows = ws.scratch.rejected_rows
    empty!(rejected_entering)
    empty!(rejected_rows)
    refreshes = 0
    refresh_pending = false
    # The lists are valid only within this invocation and the current basis.
    # A refresh clears both lists. Every attempt also checks the common clock.
    limit = Int(min(big(policy.max_pivot_candidates)^2*(big(policy.max_recovery_rounds)+1),typemax(Int)))
    attempts = 0
    try
        while attempts < limit
            stop_requested() && return DualTermination(TIME_LIMIT,"time limit reached")
            attempts += 1
            rejection = try
                result = let refresh_now=refresh_pending, refreshed=basis_refreshed || refreshes > 0
                    _transactional_simplex_step!(ws,stop_requested) do candidate,candidate_stop
                        append!(empty!(candidate.scratch.rejected_entering),rejected_entering)
                        append!(empty!(candidate.scratch.rejected_rows),rejected_rows)
                        candidate.scratch.selected_entering = 0
                        candidate.scratch.selected_row = 0
                        if refresh_now
                            recompute!(candidate;refactorize=true,caller_guard=candidate_stop,
                                       diagnostic_reason=:refactor_pivot)
                            candidate_stop() && return DualTermination(TIME_LIMIT,"time limit reached")
                        end
                        terminal = algorithm == :dual ?
                            _dual_iteration_unchecked!(candidate,candidate_stop,
                                refreshed,perturb_degenerate) :
                            _primal_iteration_unchecked!(candidate,candidate_stop,
                                reduced_cost_tolerance,refreshed)
                        if !isnothing(terminal) && terminal.status == NUMERICAL_ERROR
                            throw(_PivotRejection(candidate.scratch.selected_row,
                                candidate.scratch.selected_entering,:refresh))
                        end
                        return terminal
                    end
                end
                return result
            catch exception
                stop_requested isa _StopCallback && exception === stop_requested.exception && rethrow()
                if exception isa _UnreliableBasisSolve ||
                   (policy.recovery && _is_numerical_exception(exception))
                    _PivotRejection(0,0,:refresh)
                else
                    exception isa _PivotRejection || rethrow()
                    exception
                end
            end
            refresh_pending = false
            if rejection.row > 0 || rejection.entering > 0
                ws.scratch.selected_row = rejection.row
                ws.scratch.selected_entering = rejection.entering
            end
            _simplex_event!(ws,:pivot_rejected)
            if rejection.action in (:refresh,:exhausted) && refreshes < policy.max_recovery_rounds
                refreshes += 1
                refresh_pending = true
                empty!(rejected_entering)
                empty!(rejected_rows)
                continue
            end
            rejection.action == :exhausted && break
            if algorithm == :dual
                if rejection.entering > 0
                    rejection.entering in rejected_entering || push!(rejected_entering,rejection.entering)
                end
                if rejection.entering <= 0 || length(rejected_entering) >= policy.max_pivot_candidates
                    rejection.row > 0 || break
                    rejection.row in rejected_rows || push!(rejected_rows,rejection.row)
                    empty!(rejected_entering)
                end
                length(rejected_rows) >= policy.max_pivot_candidates && break
            else
                if rejection.row > 0
                    rejection.row in rejected_rows || push!(rejected_rows,rejection.row)
                end
                if rejection.row <= 0 || length(rejected_rows) >= policy.max_pivot_candidates
                    rejection.entering > 0 || break
                    rejection.entering in rejected_entering || push!(rejected_entering,rejection.entering)
                    empty!(rejected_rows)
                end
                length(rejected_entering) >= policy.max_pivot_candidates && break
            end
        end
        if policy.recovery && recovery_rounds < policy.max_recovery_rounds
            repaired = repair_basis!(ws,policy,stop_requested)
            stop_requested() && return DualTermination(TIME_LIMIT,"time limit reached during basis recovery")
            if repaired || ws.scratch.recovery_restored
                ready = algorithm == :dual ?
                    dual_infeasibility(ws) <= ws.options.dual_tolerance :
                    primal_infeasibility(ws) <= ws.options.primal_tolerance
                ready || return DualTermination(NUMERICAL_ERROR,"recovered basis requires feasibility restoration")
                return _retry_simplex_step!(ws,stop_requested,algorithm,reduced_cost_tolerance,
                    true,perturb_degenerate;recovery_rounds=recovery_rounds+1)
            end
        end
        return DualTermination(NUMERICAL_ERROR,"bounded pivot validation and basis recovery attempts exhausted")
    finally
        empty!(rejected_entering)
        empty!(rejected_rows)
    end
end

function _dual_iteration!(ws::SimplexWorkspace,stop_requested,basis_refreshed::Bool=false,
                          perturb_degenerate::Bool=true)
    return _measure_basis_iteration!(ws) do
        _dual_iteration_core!(ws,stop_requested,basis_refreshed,perturb_degenerate)
    end
end

function _dual_iteration_core!(ws::SimplexWorkspace,stop_requested,basis_refreshed::Bool,
                               perturb_degenerate::Bool)
    (ws.progress.numerical_policy.pivot_validation || ws.progress.numerical_policy.recovery) ||
        return _dual_iteration_unchecked!(ws,stop_requested,basis_refreshed,perturb_degenerate)
    return _retry_simplex_step!(ws,stop_requested,:dual,ws.options.dual_tolerance,
                                basis_refreshed,perturb_degenerate)
end

function _primal_iteration!(ws::SimplexWorkspace,stop_requested,reduced_cost_tolerance,
                            basis_refreshed::Bool=false)
    return _measure_basis_iteration!(ws) do
        _primal_iteration_core!(ws,stop_requested,reduced_cost_tolerance,basis_refreshed)
    end
end

function _primal_iteration_core!(ws::SimplexWorkspace,stop_requested,reduced_cost_tolerance,
                                 basis_refreshed::Bool)
    policy = ws.progress.numerical_policy
    if policy.incremental_primal_pivots
        return _with_recovery_precision(ws,ws) do
            _retry_simplex_step!(ws,stop_requested,:primal,reduced_cost_tolerance,
                                basis_refreshed,false)
        end
    end
    (policy.pivot_validation || policy.recovery || policy.incremental_primal) ||
        return _primal_iteration_unchecked!(ws,stop_requested,reduced_cost_tolerance,basis_refreshed)
    return _retry_simplex_step!(ws,stop_requested,:primal,reduced_cost_tolerance,
                                basis_refreshed,false)
end

function _pivot_column!(rhs::Vector{T}, ws::SimplexWorkspace{T}, entering::Int) where {T}
    fill!(rhs,zero(T))
    A = ws.problem.A
    if entering <= size(A,2)
        for k in nzrange(A,entering)
            rhs[A.rowval[k]] = A.nzval[k]
        end
    else
        rhs[entering-size(A,2)] = -one(T)
    end
    return rhs
end

function validate_pivot!(ws::SimplexWorkspace{T}, proposal::PivotCandidate{T},
                         policy::NumericalPolicy{T})::Symbol where {T}
    if policy.recovery && !isempty(ws.scratch.recovery_rejections)
        _sync_recovery_rejections!(ws)
        (proposal.leaving_row,proposal.entering) in ws.scratch.recovery_rejections &&
            return :reject_candidate
    end
    B = _basis_matrix!(ws)
    m = size(B,1)
    length(proposal.column) == length(proposal.rho) == m ||
        throw(DimensionMismatch("pivot solve dimensions"))
    checkbounds(proposal.column,proposal.leaving_row)
    checkbounds(ws.basis.states,proposal.entering)
    buffers = _pivot_quality_buffers(ws)
    rhs = _pivot_column!(buffers.rhs,ws,proposal.entering)
    unit = fill!(buffers.unit,zero(T))
    unit[proposal.leaving_row] = one(T)
    column_quality = buffers.column
    row_quality = buffers.row
    cq = solve_quality!(column_quality,B,proposal.column,rhs,policy)
    rq = solve_quality!(row_quality,B,proposal.rho,unit,policy;transposed=true)
    cq.reliable && rq.reliable || return :refresh
    row_pivot = proposal.row_pivot
    column_pivot = proposal.column[proposal.leaving_row]
    independently_priced = dot(proposal.rho,rhs)
    all(isfinite,(row_pivot,column_pivot,independently_priced)) || return :reject_candidate
    sign(row_pivot) == sign(column_pivot) || return :reject_candidate
    iszero(column_pivot) && return :reject_candidate
    isfinite(inv(column_pivot)) || return :reject_candidate
    all(value -> isfinite(value/column_pivot),proposal.column) || return :reject_candidate
    if _is_exact(T) === Val(true)
        return row_pivot == independently_priced &&
               _pivot_agrees(row_pivot,column_pivot,zero(T)) ? :accept : :reject_candidate
    end
    # e_r = B' * rho + row_residual and rhs = B * column + column_residual.
    # Their contractions bound disagreement, not forward error in an arbitrary
    # ill-conditioned basis. Cap the allowed error separately and require an
    # independently accumulated row estimate to agree as well.
    contraction = zero(T)
    dot_scale = zero(T)
    for i in eachindex(rhs)
        contraction += abs(row_quality.residual[i]*proposal.column[i]) +
                       abs(column_quality.residual[i]*proposal.rho[i])
        dot_scale += abs(proposal.rho[i]*rhs[i])
    end
    gamma = T(4m+8)*eps(T)
    gamma < one(T) || return :refresh
    roundoff = gamma/(one(T)-gamma) *
        (dot_scale+abs(row_pivot)+abs(column_pivot))
    error_bound = contraction + roundoff
    isfinite(error_bound) || return :refresh
    error_bound <= policy.pivot_error_tolerance *
                   min(abs(row_pivot),abs(column_pivot)) || return :refresh
    return _pivot_agrees(row_pivot,column_pivot,error_bound) &&
           _pivot_agrees(row_pivot,independently_priced,error_bound) ?
           :accept : :reject_candidate
end

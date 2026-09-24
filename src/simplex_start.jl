_start_time_expired(progress, options) = options.time_limit != Inf &&
    (time_ns()-progress.start_ns)/1e9 >= options.time_limit

_with_start_precision(f, problem, policy) = f()
function _with_start_precision(f, problem::LinearProblem{BigFloat}, policy)
    bits = max(precision(BigFloat),precision(policy.solve_tolerance),
        maximum(precision,problem.A.nzval;init=2),
        maximum(precision,problem.objective;init=2))
    for bounds in (problem.column_lower,problem.column_upper,problem.row_lower,problem.row_upper), b in bounds
        isfinite(b) && (bits=max(bits,precision(bound_value(b))))
    end
    return setprecision(f,BigFloat,bits)
end

function _initialize_crash_workspace(problem,options,progress)
    return _with_start_precision(problem,progress.numerical_policy) do
        initialize_workspace(problem,options;progress)
    end
end

function _start_primal_feasible(ws)
    tolerance = ws.options.primal_tolerance
    for j in ws.basis.basic_indices
        value = ws.primal[j]
        isfinite(value) && _lower_violation(ws.lower[j],value) <= tolerance &&
            _upper_violation(ws.upper[j],value) <= tolerance || return false
    end
    return true
end

function _start_nonbasic_state(lower,upper,cost)
    _is_fixed(lower,upper) && return AT_LOWER
    cost < zero(cost) && isfinite(upper) && return AT_UPPER
    isfinite(lower) && return AT_LOWER
    isfinite(upper) && return AT_UPPER
    return FREE_NONBASIC
end

function _slack_start_basis(problem)
    m,n = size(problem.A)
    states = Vector{VariableState}(undef,m+n)
    for j in 1:n
        states[j] = isfinite(problem.column_lower[j]) ? AT_LOWER :
            isfinite(problem.column_upper[j]) ? AT_UPPER : FREE_NONBASIC
    end
    states[n+1:end] .= BASIC
    return Basis(collect(n+1:n+m),states,Val(:owned))
end

"""Construct an owned workspace and verify a fresh factor for the supplied basis.

This checks numerical solve quality, not primal or dual feasibility. The caller's
progress context retains its original clock and outer retry offsets.
"""
function initialize_from_basis(problem::LinearProblem{T},basis::Basis,options::SolverOptions;
    policy::NumericalPolicy{T}=NumericalPolicy(T,options),
    progress::SimplexProgressContext{T}=SimplexProgressContext(problem;numerical_policy=policy),
    stop=()->false) where T
    guard = _guard_stop_callback(stop)
    return _with_start_precision(problem,policy) do
        ws = initialize_workspace(problem,options;progress)
        _install_driver_policy!(ws,policy)
        ws.basis = Basis(basis.basic_indices,basis.states)
        _validate_basis(ws)
        for j in eachindex(ws.basis.states)
            state = ws.basis.states[j]
            state == BASIC && continue
            state == FREE_NONBASIC && (isfinite(ws.lower[j]) || isfinite(ws.upper[j])) &&
                throw(ArgumentError("A free nonbasic variable must have no finite bounds"))
            _nonbasic_value(ws,j) # Reject states referring to absent bounds.
        end
        _invalidate_basis_checkpoints!(ws)
        recompute!(ws;refactorize=true,caller_guard=guard)
        _finite_workspace(ws) && _recomputed_basis_reliable(ws) ||
            throw(_UnreliableBasisSolve())
        reset_devex!(ws)
        return ws
    end
end

_crash_numerical_exception(e) = _is_numerical_exception(e) ||
    e isa OverflowError || e isa DivideError || e isa InexactError

function _crash_fallback(initial,trial,expired)
    if !isnothing(trial)
        initial.iterations = max(initial.iterations,trial.iterations)
        initial.refactorizations = max(initial.refactorizations,trial.refactorizations)
    end
    _simplex_event!(initial,:crash_fallback)
    return initial,expired
end

function _crash_refactor!(ws,guard)
    before = ws.refactorizations
    try
        recompute!(ws;refactorize=true,caller_guard=guard)
    finally
        # Failed factorization attempts are work too; fallback must retain them.
        ws.refactorizations = max(ws.refactorizations,before+1)
    end
    return nothing
end

function _crash_violation(value,lower,upper,tolerance)
    v = max(_lower_violation(lower,value),_upper_violation(upper,value))
    return v > tolerance ? v : zero(value)
end

function _crash_candidate_score(ws,column,entering,row,target)
    movement = (ws.primal[ws.basis.basic_indices[row]]-target)/column[row]
    value = ws.primal[entering]+movement
    isfinite(value) || return nothing
    tolerance = ws.options.primal_tolerance
    _crash_violation(value,ws.lower[entering],ws.upper[entering],tolerance) > 0 && return nothing
    score = zero(value)
    for (r,j) in enumerate(ws.basis.basic_indices)
        r == row && continue
        predicted = ws.primal[j]-movement*column[r]
        isfinite(predicted) || return nothing
        score += _crash_violation(predicted,ws.lower[j],ws.upper[j],tolerance)
    end
    return isfinite(score) ? (score,movement) : nothing
end

function _crash_rows!(rows,ws,column,policy)
    empty!(rows)
    scale = maximum(abs,column;init=zero(eltype(column)))
    iszero(scale) && return rows
    cutoff = policy.pivot_error_tolerance*scale
    for (row,j) in enumerate(ws.basis.basic_indices)
        abs(column[row]) > cutoff || continue
        _crash_violation(ws.primal[j],ws.lower[j],ws.upper[j],ws.options.primal_tolerance) > 0 || continue
        # Keep only a bounded number of strongest eligible pivots. Checking all
        # row scores would turn each column's selection into quadratic work.
        position = findfirst(r->abs(column[row])>abs(column[r]),rows)
        if isnothing(position)
            length(rows)<policy.max_pivot_candidates && push!(rows,row)
        else
            insert!(rows,position,row)
            length(rows)>policy.max_pivot_candidates && pop!(rows)
        end
    end
    return rows
end

function _crash_workspace_impl(initial::SimplexWorkspace{T},stop,fill_limit) where T
    stopped = Ref(false)
    guard = _guard_stop_callback(()->(stopped[] = stopped[] ||
        _start_time_expired(initial.progress,initial.options) || stop()))
    trial = nothing
    guard() && return _crash_fallback(initial,trial,true)
    initial.iterations >= initial.options.iteration_limit && return initial,false
    policy = initial.progress.numerical_policy
    try
        # Even a sum of individually representable exact violations can overflow.
        # Scoring is optional work: retain the slack start if it cannot be formed.
        baseline = primal_infeasibility(initial)
        storage_limit = fill_limit*max(1,_factor_storage_count(initial.factorization))
        # Keep the verified slack workspace untouched. This second slack LU is
        # inexpensive and avoids sharing a mutable update chain with fallback.
        initial.refactorizations += 1
        trial = initialize_workspace(initial.problem,initial.options;progress=initial.progress)
        trial.iterations = initial.iterations
        trial.refactorizations = initial.refactorizations
        trial.scratch.recovery_active = true
        guard() && return _crash_fallback(initial,trial,true)
        m,n = size(trial.problem.A)
        sense = trial.problem.objective_sense == MAX_SENSE ? -one(T) : one(T)
        for j in 1:n
            trial.basis.states[j] = _start_nonbasic_state(trial.lower[j],trial.upper[j],sense*trial.costs[j])
        end
        recompute!(trial;caller_guard=guard)
        columns = collect(1:n)
        counts = zeros(Int,n)
        for j in columns
            guard() && return _crash_fallback(initial,trial,true)
            for k in nzrange(trial.problem.A,j)
                counts[j] += !iszero(trial.problem.A.nzval[k])
            end
        end
        sort!(columns;by=j->(counts[j],j))
        rhs,column,unit,rho = zeros(T,m),zeros(T,m),zeros(T,m),zeros(T,m)
        rows = Int[]
        current = primal_infeasibility(trial)
        for entering in columns
            guard() && return _crash_fallback(initial,trial,true)
            (iszero(current) || trial.iterations >= trial.options.iteration_limit) && break
            (counts[entering] == 0 || _is_fixed(trial.lower[entering],trial.upper[entering])) && continue
            _pivot_column!(rhs,trial,entering)
            _checked_basis_solve!(column,trial,rhs,guard)
            _crash_rows!(rows,trial,column,policy)
            selected = 0
            selected_state = AT_LOWER
            best,movement = current,zero(T)
            for row in rows
                leaving = trial.basis.basic_indices[row]
                state = _lower_violation(trial.lower[leaving],trial.primal[leaving]) >
                    trial.options.primal_tolerance ? AT_LOWER : AT_UPPER
                target = bound_value(state == AT_LOWER ? trial.lower[leaving] : trial.upper[leaving])
                candidate = _crash_candidate_score(trial,column,entering,row,target)
                if !isnothing(candidate) && candidate[1] < best
                    best,movement = candidate
                    selected,selected_state = row,state
                end
            end
            selected == 0 && continue
            if _factor_storage_count(trial.factorization)+count(!iszero,column) > storage_limit
                _simplex_event!(trial,:crash_rejected_fill)
                continue
            end
            fill!(unit,zero(T));unit[selected]=one(T)
            _checked_basis_solve!(rho,trial,unit,guard;transposed=true)
            proposal = PivotCandidate(entering,selected,dot(rho,rhs),column,rho)
            if validate_pivot!(trial,proposal,policy) != :accept
                _simplex_event!(trial,:crash_rejected_quality)
                continue
            end
            guard() && return _crash_fallback(initial,trial,true)
            replace_column!(trial.factorization,column,selected;zero_tolerance=zero(T))
            _finite_updated_factor(trial.factorization) || return _crash_fallback(initial,trial,false)
            _prepare_primal_candidate!(trial,entering,one(T),movement,column,selected,selected_state) ||
                return _crash_fallback(initial,trial,false)
            leaving = trial.basis.basic_indices[selected]
            trial.basis.basic_indices[selected] = entering
            trial.basis.states[leaving] = selected_state
            trial.basis.states[entering] = BASIC
            trial.iterations += 1
            _simplex_event!(trial,:crash_pivot)
            _factor_storage_count(trial.factorization) <= storage_limit ||
                return _crash_fallback(initial,trial,false)
            current = best
            if length(trial.factorization.updates) >= min(64,trial.options.refactorization_interval)
                guard() && return _crash_fallback(initial,trial,true)
                _crash_refactor!(trial,guard)
                _recomputed_basis_reliable(trial) || return _crash_fallback(initial,trial,false)
                current = primal_infeasibility(trial)
            end
        end
        guard() && return _crash_fallback(initial,trial,true)
        _invalidate_basis_checkpoints!(trial)
        _crash_refactor!(trial,guard)
        guard() && return _crash_fallback(initial,trial,true)
        final_violation = primal_infeasibility(trial)
        accepted = _finite_workspace(trial) && _recomputed_basis_reliable(trial) &&
            final_violation <= baseline && _factor_storage_count(trial.factorization) <= storage_limit
        # The modern phase-I builder can extend a partially feasible basis.
        accepted &= policy.phase_one || trial.options.algorithm != :primal || iszero(final_violation)
        accepted || return _crash_fallback(initial,trial,false)
        reset_devex!(trial)
        trial.scratch.recovery_active = false
        _simplex_event!(trial,:crash_accepted)
        return trial,false
    catch exception
        if exception === guard.exception
            stop isa _StopCallback && (stop.exception=exception)
            rethrow()
        end
        _crash_numerical_exception(exception) || rethrow()
        return _crash_fallback(initial,trial,guard())
    end
end

function _crash_workspace(initial,stop;fill_limit::Real=8)
    isfinite(fill_limit) && fill_limit >= 1 || throw(ArgumentError("Invalid crash fill limit"))
    _simplex_event!(initial,:phase_crash)
    diagnostics = initial.progress.diagnostics
    timed = !isnothing(diagnostics) && diagnostics.kernel_timing
    started = timed ? time_ns() : UInt64(0)
    try
        return _with_start_precision(initial.problem,initial.progress.numerical_policy) do
            _crash_workspace_impl(initial,stop,fill_limit)
        end
    finally
        if timed
            diagnostics.kernel_calls[:crash] += 1
            diagnostics.kernel_nanoseconds[:crash] += time_ns()-started
        end
    end
end

"""Return an owned guarded crash basis, or the valid slack fallback on interruption."""
function crash_basis(problem::LinearProblem{T},options::SolverOptions,
                     policy::NumericalPolicy{T},stop)::Basis where T
    guard = _guard_stop_callback(stop)
    guard() && return _slack_start_basis(problem)
    return _with_start_precision(problem,policy) do
        progress = SimplexProgressContext(problem;numerical_policy=policy)
        initial = initialize_workspace(problem,options;progress)
        workspace,_ = _crash_workspace(initial,guard)
        return Basis(workspace.basis.basic_indices,workspace.basis.states)
    end
end

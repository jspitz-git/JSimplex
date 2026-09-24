"""Select a strictly higher canonical working precision within the policy ceiling."""
function next_working_precision(::Type{T},current_bits::Integer,policy)::Union{Nothing,Int} where T
    _is_exact(T) === Val(true) && return nothing
    current_bits >= 2 || throw(ArgumentError("Invalid current working precision"))
    policy.precision_boosting || return nothing
    current = T === BigFloat ? current_bits : max(current_bits,precision(T))
    if T === Float32 && current < 53
        return policy.max_precision_bits >= 53 ? 53 : nothing
    end
    candidate = 128
    while candidate <= current
        candidate <= typemax(Int) ÷ 2 || return nothing
        candidate *= 2
    end
    return candidate <= policy.max_precision_bits ? candidate : nothing
end

_precision_current_bits(ws::SimplexWorkspace{T}) where T = precision(T)
_precision_current_bits(ws::SimplexWorkspace{BigFloat}) =
    _transfer_bits(ws,ws.progress.numerical_policy,2)

function _precision_memory_estimate(ws,::Type{S},bits) where S
    m,n = size(ws.problem.A)
    variables,entries = big(m)+n,big(nnz(ws.problem.A))
    # Markowitz can allocate a dense trailing Schur core. Include independently
    # owned models, scratch, multiple factor buffers and BigFloat limb storage.
    dense = !(S === Float64 && ws.options.basis_refactorization == :native)
    square = dense ? big(m)*m : big(0)
    scalar_bytes = S === BigFloat ? big(128)+cld(bits,8) : big(sizeof(S))
    return (64+32variables+4entries+8square)*scalar_bytes +
        8*(32variables+4entries+8square)
end

_precision_stopped(budget,stop) = _budget_expired(budget) || stop()

function _precision_restore_original!(ws)
    if !_original_costs_active(ws) || _has_active_bound_perturbations(ws.scratch.perturbations)
        _restore_original_costs!(ws)
        ws.perturbed = false
    end
    return nothing
end

function _precision_inherit_work!(origin,budget)
    origin.iterations = max(origin.iterations,budget.iterations-origin.progress.iteration_offset)
    origin.refactorizations = max(origin.refactorizations,
        budget.refactorizations-origin.progress.refactorization_offset)
    return nothing
end

function _precision_initial_workspace(problem,options,progress)
    return _with_start_precision(problem,progress.numerical_policy) do
        _initialize_workspace_state(problem,options;progress)
    end
end

function _precision_finish_initialization!(ws)
    return _with_start_precision(ws.problem,ws.progress.numerical_policy) do
        _finish_workspace_initialization!(ws)
    end
end

_recover_original_failure(::Nothing,run,stop) = run
function _recover_original_failure(ws::SimplexWorkspace{T},run::DualRunResult{T},stop) where T
    policy = ws.progress.numerical_policy
    if run.status != NUMERICAL_ERROR || !policy.precision_boosting || _is_exact(T) === Val(true)
        return run
    end
    ws.iterations = max(ws.iterations,run.iterations)
    ws.refactorizations = max(ws.refactorizations,run.refactorizations)
    return _dispatch_precision_recovery(ws,SimplexRunBudget(ws),policy,stop)
end

function _precision_result(origin::SimplexWorkspace{T},budget,status,message;
                           primal=nothing,objective=nothing,basis=nothing) where T
    return DualRunResult{T}(status,objective,primal,
        budget.iterations-origin.progress.iteration_offset,
        budget.refactorizations-origin.progress.refactorization_offset,message,basis)
end

function _precision_bases(ws)
    candidates = Basis[]
    for checkpoint in Iterators.reverse(ws.scratch.checkpoints)
        _checkpoint_matches(ws,checkpoint) || continue
        push!(candidates,Basis(checkpoint.basis.basic_indices,checkpoint.basis.states))
        break
    end
    if isempty(candidates) || candidates[1].basic_indices != ws.basis.basic_indices ||
       candidates[1].states != ws.basis.states
        push!(candidates,Basis(ws.basis.basic_indices,ws.basis.states))
    end
    return candidates
end

function _precision_transfer_attempt(source,::Type{S},bits,budget,stop) where S
    policy = source.progress.numerical_policy
    _precision_stopped(budget,stop) && return nothing,:stopped,"time limit reached during precision recovery"
    required = _precision_memory_estimate(source,S,bits)
    required <= policy.max_precision_memory_bytes || return nothing,:memory,
        "working precision memory estimate $required exceeds limit $(policy.max_precision_memory_bytes) bytes"
    candidates = _precision_bases(source)
    _precision_restore_original!(source)
    _original_bounds_active(source) || return nothing,:bounds,"precision recovery requires original working bounds"
    message = "higher-precision basis reconstruction failed"
    for basis in candidates
        _precision_stopped(budget,stop) && return nothing,:stopped,"time limit reached during precision recovery"
        fresh = try
            transfer_precision(source,S,bits,budget,policy;stop,basis)
        catch exception
            exception === stop.exception && rethrow()
            _crash_numerical_exception(exception) || rethrow()
            message = sprint(showerror,exception)
            nothing
        end
        isnothing(fresh) || return fresh,:success,""
    end
    return nothing,:numerical,message
end

function _run_precision_level!(ws,budget,stop)
    policy = ws.progress.numerical_policy
    _simplex_event!(ws,:precision_boost)
    _precision_stopped(budget,stop) && return _precision_result(ws,budget,TIME_LIMIT,
        "time limit reached during precision recovery")
    try
        # A legacy failure may leave an infeasible original start. Initialize it
        # at the new precision before entering its configured optimization loop.
        if !policy.feasibility_recovery
            if ws.options.algorithm == :primal && !_start_primal_feasible(ws)
                phase = run_phase_one!(ws,budget,policy,stop)
                phase.status == OPTIMAL || return phase
            elseif ws.options.algorithm == :dual
                terminal = make_dual_feasible!(ws,stop)
                isnothing(terminal) || return _internal_solution(ws,terminal)
            end
        end
        return _run_from_basis_once!(ws,budget,policy,stop)
    catch exception
        exception === stop.exception && rethrow()
        _crash_numerical_exception(exception) || rethrow()
        return _precision_result(ws,budget,NUMERICAL_ERROR,sprint(showerror,exception))
    finally
        _sync_run_budget!(budget,ws)
    end
end

function _convert_precision_run(origin::SimplexWorkspace{T},working,run,budget,stop) where T
    _precision_stopped(budget,stop) && return _precision_result(origin,budget,TIME_LIMIT,
        "time limit reached during precision certification")
    if run.status != OPTIMAL
        # The higher-precision model contains exactly the original binary data;
        # its existing original-model terminal proofs therefore still apply.
        return _precision_result(origin,budget,run.status,run.message)
    end
    _original_costs_active(working) && _original_bounds_active(working) ||
        return _precision_result(origin,budget,NUMERICAL_ERROR,"precision result uses altered working data")
    isnothing(run.primal) && return _precision_result(origin,budget,NUMERICAL_ERROR,
        "precision result has no optimal primal candidate")
    witness = _original_dual_witness(working)
    isnothing(witness) && return _precision_result(origin,budget,NUMERICAL_ERROR,
        "higher-precision dual witness could not be verified")
    primal,dual = T.(run.primal),T.(witness)
    objective = dot(origin.problem.objective,primal)+origin.problem.objective_constant
    certified = all(isfinite,primal) && all(isfinite,dual) && isfinite(objective) &&
        _original_primal_feasible(origin.problem,primal,origin.options.primal_tolerance) &&
        _original_witness_certified(origin.problem,origin.options,working.basis,primal,dual)
    _precision_stopped(budget,stop) && return _precision_result(origin,budget,TIME_LIMIT,
        "time limit reached during precision certification")
    if !certified
        _simplex_event!(working,:certification_failed)
        return _precision_result(origin,budget,NUMERICAL_ERROR,
            "rounded original-type solution failed original-model certification")
    end
    _simplex_event!(working,:certification)
    _precision_stopped(budget,stop) && return _precision_result(origin,budget,TIME_LIMIT,
        "time limit reached during precision certification")
    return _precision_result(origin,budget,OPTIMAL,"optimal solution found after working precision recovery";
        primal,objective,basis=Basis(working.basis.basic_indices,working.basis.states))
end

function _next_bigfloat_workspace(source,bits::Int,budget,stop)
    while true
        fresh,reason,message = _precision_transfer_attempt(source,BigFloat,bits,budget,stop)
        !isnothing(fresh) && return fresh,bits,message
        reason == :numerical || return nothing,bits,message
        next = next_working_precision(BigFloat,bits,source.progress.numerical_policy)
        isnothing(next) && return nothing,bits,message
        bits = next
    end
end

function _run_bigfloat_levels(origin,active::SimplexWorkspace{BigFloat},bits,budget,stop)
    try
        while true
            run = let current = active
                _with_transfer_precision(BigFloat,bits) do
                    result = _run_precision_level!(current,budget,stop)
                    _convert_precision_run(origin,current,result,budget,stop)
                end
            end
            run.status == NUMERICAL_ERROR || return run
            next = next_working_precision(BigFloat,_precision_current_bits(active),active.progress.numerical_policy)
            isnothing(next) && return run
            fresh,new_bits,message = _next_bigfloat_workspace(active,next,budget,stop)
            if isnothing(fresh)
                status = _precision_stopped(budget,stop) ? TIME_LIMIT : NUMERICAL_ERROR
                return _precision_result(origin,budget,status,message)
            end
            active,bits = fresh,new_bits
        end
    finally
        _sync_run_budget!(budget,active)
        _precision_restore_original!(active)
    end
end

function _begin_bigfloat_recovery(origin,source,bits,budget,stop)
    fresh,actual_bits,message = _next_bigfloat_workspace(source,bits,budget,stop)
    if isnothing(fresh)
        status = _precision_stopped(budget,stop) ? TIME_LIMIT : NUMERICAL_ERROR
        return _precision_result(origin,budget,status,message)
    end
    return _run_bigfloat_levels(origin,fresh,actual_bits,budget,stop)
end

function _recover_float32(origin,budget,stop)
    fresh,reason,message = _precision_transfer_attempt(origin,Float64,53,budget,stop)
    if isnothing(fresh)
        next = next_working_precision(Float64,53,origin.progress.numerical_policy)
        if reason == :numerical && !isnothing(next)
            return _begin_bigfloat_recovery(origin,origin,next,budget,stop)
        end
        return _precision_result(origin,budget,
            _precision_stopped(budget,stop) ? TIME_LIMIT : NUMERICAL_ERROR,message)
    end
    try
        run = _convert_precision_run(origin,fresh,_run_precision_level!(fresh,budget,stop),budget,stop)
        run.status == NUMERICAL_ERROR || return run
        next = next_working_precision(Float64,53,fresh.progress.numerical_policy)
        isnothing(next) && return run
        return _begin_bigfloat_recovery(origin,fresh,next,budget,stop)
    finally
        _sync_run_budget!(budget,fresh)
        _precision_restore_original!(fresh)
    end
end

"""Recover a failed original-model solve using actual higher-precision work.

The caller first exhausts cheaper recovery. All levels retain the same clock and
completed-work budget. Returned primal/dual candidates are rounded to the original
scalar type and independently certified against its unchanged tolerances.
"""
function solve_with_precision_recovery(ws::SimplexWorkspace{T},budget::SimplexRunBudget,
                                      policy::NumericalPolicy{T},stop)::DualRunResult{T} where T
    guard = _guard_stop_callback(stop)
    _install_driver_policy!(ws,policy;start_ns=budget.start_ns)
    _precision_inherit_work!(ws,budget)
    try
        _precision_stopped(budget,guard) && return _precision_result(ws,budget,TIME_LIMIT,
            "time limit reached during precision recovery")
        if !policy.precision_boosting || _is_exact(T) === Val(true)
            return _precision_result(ws,budget,NUMERICAL_ERROR,"working precision recovery is disabled")
        end
        next = next_working_precision(T,_precision_current_bits(ws),policy)
        isnothing(next) && return _precision_result(ws,budget,NUMERICAL_ERROR,
            "working precision ceiling reached")
        return T === Float32 ? _recover_float32(ws,budget,guard) :
            _begin_bigfloat_recovery(ws,ws,next,budget,guard)
    catch exception
        exception === guard.exception && rethrow()
        _crash_numerical_exception(exception) || rethrow()
        return _precision_result(ws,budget,_precision_stopped(budget,guard) ? TIME_LIMIT : NUMERICAL_ERROR,
            sprint(showerror,exception))
    finally
        _sync_run_budget!(budget,ws)
        _precision_inherit_work!(ws,budget)
        _precision_restore_original!(ws)
    end
end

# Isolate inference of rarely entered scalar-changing recovery from normal solves.
# The cold dynamic call preserves the concrete public result type; all workspace
# storage and higher-precision simplex kernels retain their concrete types.
@noinline function _dispatch_precision_recovery(ws::SimplexWorkspace{T},budget::SimplexRunBudget,
                                               policy::NumericalPolicy{T},stop)::DualRunResult{T} where T
    return Base.inferencebarrier(solve_with_precision_recovery)(ws,budget,policy,stop)::DualRunResult{T}
end

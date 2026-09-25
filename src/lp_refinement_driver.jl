struct _LPRefinementObserver{D}
    parent::D
end

function _lp_event_reason(reason)
    reason in (:phase_primal,:phase_dual,:phase_one,:phase_auxiliary,:phase_cleanup,:phase_crash) &&
        return :phase_lp_refinement
    reason == :certification && return :lp_correction_certification
    return reason
end

function (observer::_LPRefinementObserver)(reason,ws)
    # The child diagnostic context wraps callback exceptions exactly once.
    callback = observer.parent.observer
    isnothing(callback) || callback(_lp_event_reason(reason),ws)
    return nothing
end

_lp_child_diagnostics(::Nothing) = nothing
_lp_child_diagnostics(parent::SimplexDiagnostics) =
    SimplexDiagnostics(;observer=_LPRefinementObserver(parent),kernel_timing=parent.kernel_timing)

_merge_lp_diagnostics!(::Nothing,::Nothing) = nothing
function _merge_lp_diagnostics!(parent::SimplexDiagnostics,child::SimplexDiagnostics)
    for (reason,count) in child.counts
        parent.counts[_lp_event_reason(reason)] += count
    end
    for reason in recent_events(child)
        mapped = _lp_event_reason(reason)
        if length(parent.events) < 64
            push!(parent.events,mapped)
        else
            parent.events[parent.next_event] = mapped
        end
        parent.next_event = mod1(parent.next_event+1,64)
    end
    for key in keys(child.kernel_calls)
        parent.kernel_calls[key] += child.kernel_calls[key]
        parent.kernel_nanoseconds[key] += child.kernel_nanoseconds[key]
    end
    return nothing
end

function _lp_auxiliary_policy(policy::NumericalPolicy{T}) where T
    names = fieldnames(typeof(policy))
    values = ntuple(Val(length(names))) do i
        name = names[i]
        name in (:lp_refinement,:precision_boosting,:crash) ? false :
            name in (:feasibility_recovery,:phase_one) ? true : getfield(policy,i)
    end
    return NumericalPolicy(T;NamedTuple{names}(values)...)
end

function _lp_auxiliary_options(o::SolverOptions{T,M,R},budget) where {T,M,R}
    return SolverOptions{T,M,R}(o.primal_tolerance,o.dual_tolerance,o.zero_tolerance,
        max(0,budget.iteration_limit-budget.iterations),budget.time_limit_seconds,
        o.refactorization_interval,o.verbose,o.log_level,o.algorithm,o.pricing,
        o.basis_update,o.basis_refactorization,:off,false,o.simplex_strategy)
end

function _lp_memory_estimate(ws::SimplexWorkspace{T},bits) where T
    m,n = size(ws.problem.A)
    N,entries = big(n)+2m,big(nnz(ws.problem.A))+m
    dense = !(T === Float64 && ws.options.basis_refactorization == :native)
    square = dense ? big(m)*m : big(0)
    bytes = T === BigFloat ? big(128)+cld(_precision_current_bits(ws),8) : big(sizeof(T))
    residual_bytes = big(128)+cld(bits,8)
    return (64+64N+8entries+8square)*(bytes+8)+(16N+4entries)*residual_bytes
end

# Construct only the requested basis. Every attempted factor consumes the shared
# counter, including attempts that throw before a workspace can be returned.
function _lp_workspace(problem::LinearProblem{T},basis,options,progress,budget,stop;
                       factor_bits::Int, recompute::Bool=true) where T
    stop() && return nothing
    lower,upper = vcat(problem.column_lower,problem.row_lower),
        vcat(problem.column_upper,problem.row_upper)
    B = _transfer_basis_matrix(problem,basis,lower,upper,stop)
    (isnothing(B) || stop()) && return nothing
    factor = try
        _diagnostic_kernel(progress.diagnostics,:refactorization) do
            _with_transfer_precision(T,factor_bits) do
                _basis_factorization(B,options)
            end
        end
    finally
        budget.refactorizations += 1
    end
    stop() && return nothing
    m,n = size(problem.A)
    fresh = SimplexWorkspace(problem,options,progress,vcat(problem.objective,zeros(T,m)),
        lower,upper,Basis(basis.basic_indices,basis.states),zeros(T,n+m),zeros(T,n+m),
        ones(T,n+m),falses(n+m),factor,SimplexScratch(T,m,n+m),0,1,false,0,false,false,
        options.refactorization_interval,0,typemax(Int),0,0)
    fresh.scratch.basis_matrix = B
    _configure_refactorization!(fresh)
    if recompute
        recompute!(fresh;caller_guard=stop)
        stop() && return nothing
        _finite_workspace(fresh) && _recomputed_basis_reliable(fresh) || throw(_UnreliableBasisSolve())
        reset_devex!(fresh)
    end
    _simplex_event!(fresh,:refactor_other)
    return fresh
end

# Keep inference of the nested simplex solve separate from the correction
# orchestration, while retaining a concrete workspace and result type.
@noinline function _dispatch_lp_auxiliary(ws::SimplexWorkspace{T},budget,policy,stop)::DualRunResult{T} where T
    return Base.inferencebarrier(_run_from_basis_once!)(ws,budget,policy,stop)::DualRunResult{T}
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

function _lp_improves(before,after,options)
    tolerances = (options.primal_tolerance,options.dual_tolerance,
        max(options.primal_tolerance,options.dual_tolerance))
    return all(isfinite,after) && all(after[i] <= max(before[i],tolerances[i]) for i in 1:3) &&
        any(after[i] < before[i]/2 for i in 1:3)
end

function _lp_basis_at_values(ws,indices,values)
    m,n = size(ws.problem.A)
    length(indices)==m && length(unique(indices))==m && all(j->1<=j<=m+n,indices) || return nothing
    mask = falses(m+n);mask[indices].=true
    states = fill(BASIC,m+n)
    for j in eachindex(states)
        mask[j] && continue
        lower,upper = ws.lower[j],ws.upper[j]
        value,tolerance = values[j],ws.options.primal_tolerance
        if isfinite(lower) && abs(value-bound_value(lower)) <= tolerance
            states[j]=AT_LOWER
        elseif isfinite(upper) && abs(value-bound_value(upper)) <= tolerance
            states[j]=AT_UPPER
        elseif !isfinite(lower) && !isfinite(upper) && abs(value) <= tolerance
            states[j]=FREE_NONBASIC
        else
            return nothing
        end
    end
    return Basis(indices,states)
end

function _lp_project_certificate(ws::SimplexWorkspace{T},auxiliary,map,values,dual,budget,stop) where T
    m,n=size(ws.problem.A);N=m+n
    primal=values[1:n]
    _original_primal_feasible(ws.problem,primal,ws.options.primal_tolerance) || return nothing
    mapped=[j<=N ? j : n+j-N for j in auxiliary.basis.basic_indices]
    candidates=[mapped,copy(ws.basis.basic_indices)]
    for checkpoint in Iterators.reverse(ws.scratch.checkpoints)
        _checkpoint_matches(ws,checkpoint) || continue
        push!(candidates,copy(checkpoint.basis.basic_indices));break
    end
    for indices in candidates
        stop() && return nothing
        basis=_lp_basis_at_values(ws,indices,values)
        isnothing(basis) && continue
        _original_witness_certified(ws.problem,ws.options,basis,primal,dual) || continue
        p=ws.progress
        progress=typeof(p)(budget.start_ns,p.objective,p.objective_constant,p.scaling,
            budget.iterations,budget.refactorizations,p.diagnostics,p.numerical_policy)
        probe = try
            _lp_workspace(ws.problem,basis,ws.options,progress,budget,stop;recompute=false,
                factor_bits=_precision_current_bits(ws))
        catch exception
            exception === stop.exception && rethrow()
            _crash_numerical_exception(exception) || rethrow()
            nothing
        end
        isnothing(probe) && continue
        copyto!(probe.primal,values)
        copyto!(probe.scratch.rho,dual)
        residuals=_lp_residuals(ws,values,dual)
        copyto!(probe.reduced_costs,T.(residuals.dual))
        _finite_workspace(probe) && _recomputed_basis_reliable(probe) || continue
        probe.scratch.lp_dual_witness=copy(dual)
        return probe
    end
    return nothing
end

function _lp_fallback(ws,budget,policy,stop,message)
    _precision_stopped(budget,stop) && return _precision_result(ws,budget,TIME_LIMIT,
        "time limit reached during LP refinement")
    policy.precision_boosting && return _dispatch_precision_recovery(ws,budget,policy,stop)
    return _precision_result(ws,budget,NUMERICAL_ERROR,message)
end

function _refine_lp(ws::SimplexWorkspace{T},budget,policy,stop,bits) where T
    n=size(ws.problem.A,2)
    _precision_restore_original!(ws)
    _original_bounds_active(ws) || return _lp_fallback(ws,budget,policy,stop,
        "LP refinement requires original working bounds")
    basic_costs=[j<=n ? ws.problem.objective[j] : zero(T) for j in ws.basis.basic_indices]
    initial_dual=_with_transfer_precision(T,_precision_current_bits(ws)) do
        transpose_solve(ws.factorization,basic_costs)
    end
    all(isfinite,ws.primal) && all(isfinite,initial_dual) ||
        return _lp_fallback(ws,budget,policy,stop,"nonfinite initial LP correction candidate")
    residuals=_lp_residuals(ws,ws.primal,initial_dual;bits)
    errors=_lp_errors(ws,residuals)
    for _ in 1:policy.max_lp_refinements
        stop() && return _precision_result(ws,budget,TIME_LIMIT,"time limit reached before LP correction")
        _simplex_event!(ws,:lp_refinement)
        _simplex_event!(ws,:phase_lp_refinement)
        sp,sd=_lp_correction_scales(ws,residuals)
        problem,map=build_correction_problem(ws,residuals,sp,sd)
        stop() && return _precision_result(ws,budget,TIME_LIMIT,"time limit reached building LP correction")
        auxiliary,run,multiplier=_lp_auxiliary_run_at_working_precision(ws,problem,map,budget,policy,stop)
        stop() && return _precision_result(ws,budget,TIME_LIMIT,"time limit reached solving LP correction")
        isnothing(run) && break
        if run.status in (TIME_LIMIT,ITERATION_LIMIT)
            return _precision_result(ws,budget,run.status,run.message)
        end
        # An auxiliary infeasibility/unboundedness report proves nothing about
        # the original model after deliberately rounded correction coefficients.
        run.status == OPTIMAL || break
        isnothing(multiplier) && break
        values=Vector{T}(undef,length(residuals.values))
        dual=Vector{T}(undef,length(residuals.multipliers))
        for j in eachindex(values)
            values[j]=_lp_round(T,residuals.values[j]+BigFloat(run.primal[j])/sp,bits)
        end
        for i in eachindex(dual)
            dual[i]=_lp_round(T,residuals.multipliers[i]+BigFloat(multiplier[i])/sd,bits)
        end
        candidate=_lp_residuals(ws,values,dual;bits)
        candidate_errors=_lp_errors(ws,candidate)
        _lp_improves(errors,candidate_errors,ws.options) || break
        _simplex_event!(ws,:phase_cleanup)
        probe=_lp_project_certificate(ws,auxiliary,map,values,dual,budget,stop)
        stop() && return _precision_result(ws,budget,TIME_LIMIT,"time limit reached certifying LP correction")
        if !isnothing(probe)
            primal=values[1:n]
            objective=dot(ws.problem.objective,primal)+ws.problem.objective_constant
            if isfinite(objective)
                _simplex_event!(probe,:certification)
                stop() && return _precision_result(ws,budget,TIME_LIMIT,"time limit reached after LP certification")
                return _precision_result(ws,budget,OPTIMAL,"optimal solution found after LP refinement";
                    primal,objective,basis=Basis(probe.basis.basic_indices,probe.basis.states))
            end
        end
        residuals,errors=candidate,candidate_errors
    end
    return _lp_fallback(ws,budget,policy,stop,"bounded LP refinement did not certify the original model")
end

"""Try bounded correction LPs, then precision boosting with the same remaining budget."""
function refine_lp!(ws::SimplexWorkspace{T},budget::SimplexRunBudget,policy::NumericalPolicy{T},stop)::DualRunResult{T} where T
    guard=_guard_stop_callback(()->_budget_expired(budget)||stop())
    _install_driver_policy!(ws,policy;start_ns=budget.start_ns)
    _precision_inherit_work!(ws,budget)
    try
        guard() && return _precision_result(ws,budget,TIME_LIMIT,"time limit reached before LP refinement")
        (!policy.lp_refinement || _is_exact(T) === Val(true)) && return _lp_fallback(ws,budget,policy,guard,
            "floating LP refinement is disabled")
        bits=_lp_residual_bits(ws)
        _lp_memory_estimate(ws,bits) <= policy.max_precision_memory_bytes ||
            return _lp_fallback(ws,budget,policy,guard,"LP correction memory estimate exceeds the allowed limit")
        return setprecision(BigFloat,bits) do
            _refine_lp(ws,budget,policy,guard,bits)
        end
    catch exception
        exception === guard.exception && rethrow()
        (_crash_numerical_exception(exception) || exception isa ArgumentError) || rethrow()
        return _lp_fallback(ws,budget,policy,guard,sprint(showerror,exception))
    finally
        _precision_inherit_work!(ws,budget)
        _precision_restore_original!(ws)
        _sync_run_budget!(budget,ws)
    end
end

# Automatic entry remains cold for ordinary solves. The pure boosting dispatch
# is separate because an exhausted LP refinement falls back to it directly.
@noinline function _dispatch_numerical_recovery(ws::SimplexWorkspace{T},budget::SimplexRunBudget,
                                               policy::NumericalPolicy{T},stop)::DualRunResult{T} where T
    recovery = policy.lp_refinement ? refine_lp! : solve_with_precision_recovery
    return Base.inferencebarrier(recovery)(ws,budget,policy,stop)::DualRunResult{T}
end

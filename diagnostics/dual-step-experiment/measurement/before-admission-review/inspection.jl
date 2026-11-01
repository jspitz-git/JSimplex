# Diagnostic-only nominal adapter; no existing method is replaced.
# The primary timed arm uses the original E.solve_experimental, never this clone.
@eval E begin
mutable struct Task6Adapter{C,F}
    record::SolveRecord
    clock::C
    events::F
    entered::Bool
    probe::Dict{String,Any}
end
function _task6_capture!(probe,e,label)
    data=Dict{String,Any}("graph_bytes"=>Base.summarysize(e),"m"=>length(e.ws.basis.basic_indices),"N"=>length(e.ws.costs))
    for k in fieldnames(ProposalCounts);data["PC_"*string(k)]=getfield(e.proposal.counts,k);end
    seen=Base.IdSet{Any}();memories=Base.IdSet{Any}()
    function visit(x,path)
        x in seen&&return
        push!(seen,x)
        if x isa Vector
            memory=getfield(getfield(x,:ref),:mem)
            data[path*"_length"]=length(x);data[path*"_capacity"]=length(memory)
            if !(memory in memories)
                push!(memories,memory)
                data["unique_vector_payload_bytes"]=get(data,"unique_vector_payload_bytes",0)+length(memory)*Base.elsize(x)
            end
        elseif x isa Tuple
            for i in eachindex(x);visit(x[i],path*"_"*string(i));end
        elseif parentmodule(typeof(x))===@__MODULE__ || x isa J.RowAccess || x isa J.Basis
            for k in fieldnames(typeof(x));visit(getfield(x,k),path*"_"*string(k));end
        end
    end
    for k in (:proposal,:journal,:invariants,:supports,:kernels,:recovery,:residual_scale,:rows);visit(getfield(e,k),string(k));end
    for k in (:costs,:lower,:upper,:basis,:primal,:reduced_costs,:pricing_weights,:devex_reference);visit(getfield(e.ws,k),"ws_"*string(k));end
    for k in fieldnames(typeof(e.ws.scratch))
        value=getfield(e.ws.scratch,k)
        value isa Vector&&visit(value,"ws_scratch_"*string(k))
    end
    probe[label]=data
    nothing
end
function J._dual_engine_notice!(adapter::Task6Adapter,reason)
    r=adapter.record
    reason==:original_retry&&(r.original_retries+=1)
    reason==:original_cleanup&&(r.original_cleanups+=1)
    reason==:original_recovery&&(r.original_recoveries+=1)
    nothing
end
function (adapter::Task6Adapter)(source,stop)
    r=adapter.record
    adapter.entered&&throw(ArgumentError("experimental main phase may enter only once"))
    adapter.entered=true;r.entries=1
    actual_clock=stop isa J._StopCallback ? stop.callback : stop
    clock_matches=actual_clock isa J._SolveDeadline && actual_clock.start_ns==adapter.clock.start_ns &&
        actual_clock.time_limit_seconds==adapter.clock.time_limit_seconds
    if !clock_matches || !eligible(source,adapter.clock) || source.progress.numerical_policy.adaptive_refactor
        r.reason=:ineligible_phase;return nothing
    end
    if adapter.clock()
        r.reason=:deadline_before_import;r.phase_reason=Stopped
        return J._DualEngineHandoff(source,J.DualTermination(J.TIME_LIMIT,"time limit reached before experimental ownership"),false)
    end
    r.import_attempts+=1
    policy=EnginePolicy(source)
    ceiling=min(policy.refactor_limit,source.dual_refactorization_interval)
    ceiling>=1||throw(ArgumentError("invalid inherited factor safety ceiling"))
    policy=EnginePolicy((k==:refactor_limit ? ceiling : getfield(policy,k) for k in fieldnames(typeof(policy)))...)
    e=try;import_phase(source,adapter.clock,policy)
    catch exception
        J._is_numerical_exception(exception)||rethrow()
        r.import_failures+=1;r.reason=:import_failed
        return J._DualEngineHandoff(source,J.DualTermination(J.NUMERICAL_ERROR,"experimental phase import failed"),false)
    end
    r.imports+=1;r.reason=:active
    _task6_capture!(adapter.probe,e,"setup")
    monitor=_EventMonitor(zero_dual_streak=source.zero_dual_step_streak,
        last_refactorization=Int128(e.ws.progress.refactorization_offset)+e.ws.refactorizations)
    result=try
        run_phase!(e;event_sink=_EventGuard(adapter.events,monitor))
    catch exception
        if exception isa EventFailure;r.reason=:event_exception;rethrow();end
        J._is_numerical_exception(exception)||rethrow()
        e.kernels.factor_valid=false;e.recovery.finished=true
        r.reason=:unsafe_failure
        return J._DualEngineHandoff(e.ws,J.DualTermination(J.NUMERICAL_ERROR,"experimental phase failed without a verified handoff"),false)
    finally
        _task6_capture!(adapter.probe,e,"exit")
        _snapshot_counts!(r,e)
        r.entries=1;r.imports=1;r.import_attempts=1;r.import_failures=0
        for name in fieldnames(_EventMonitor);setfield!(r,name,getfield(monitor,name));end
    end
    r.phase_reason=result.reason
    if result.exportable
        workspace=_legacy_workspace!(result.workspace,source,r)
        if result.reason==PrimalFeasible
            return J._DualEngineHandoff(workspace,J.DualTermination(J.OPTIMAL,"experimental working phase complete"),true)
        end
        r.legacy_fallbacks+=1;r.reason=:legacy_boundary
        return J._DualEngineHandoff(workspace,nothing,true)
    end
    r.reason=:no_payload
    status=result.reason==Stopped ? J.TIME_LIMIT : result.message==:iteration_limit ? J.ITERATION_LIMIT : J.NUMERICAL_ERROR
    J._DualEngineHandoff(e.ws,J.DualTermination(status,"experimental phase: "*String(result.message)),false)
end
end

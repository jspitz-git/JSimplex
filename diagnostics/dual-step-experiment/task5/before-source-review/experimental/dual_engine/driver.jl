# One reusable scalar/counter result per solve; no workspace/engine graph retained.
Base.@kwdef mutable struct SolveRecord
    used::Bool=false
    reason::Symbol=:not_reached
    entries::Int=0
    imports::Int=0
    import_attempts::Int=0
    import_failures::Int=0
    exports::Int=0
    legacy_fallbacks::Int=0
    original_retries::Int=0
    original_cleanups::Int=0
    original_recoveries::Int=0
    export_entries::Int=0
    export_mask_entries::Int=0
    export_metadata_refreshes::Int=0
    zero_dual_streak::Int=0
    nonzero_steps::Int=0
    last_refactorization::Int128=Int128(0)
    last_primal_step::Float64=0.
    last_dual_step::Float64=0.
    start_ns::UInt64=UInt64(0)
    elapsed_seconds::Float64=0.
    phase_reason::StepReason=Ready
    result_status::J.TerminationStatus=J.NUMERICAL_ERROR
    engine_counts::EngineCounters=EngineCounters()
    kernel_counts::KernelCounts=KernelCounts()
    repair_counts::RecoveryCounts=RecoveryCounts()
    legacy_counts::Dict{Symbol,Int}=Dict{Symbol,Int}()
end
function Base.getproperty(r::SolveRecord,s::Symbol)
    s in fieldnames(EngineCounters) && return getfield(getfield(r,:engine_counts),s)
    s in fieldnames(KernelCounts) && return getfield(getfield(r,:kernel_counts),s)
    getfield(r,s)
end
function _snapshot_counts!(r,e)
    for (dest,source) in ((r.engine_counts,e.counters),(r.kernel_counts,e.kernels.counts),(r.repair_counts,e.recovery.counts))
        for i in 1:fieldcount(typeof(dest));setfield!(dest,i,getfield(source,i));end
    end
    nothing
end
struct EventFailure{X} <: Exception
    cause::X
end
Base.@kwdef mutable struct _EventMonitor
    zero_dual_streak::Int=0
    nonzero_steps::Int=0
    last_refactorization::Int128=Int128(0)
    last_primal_step::Float64=0.
    last_dual_step::Float64=0.
end
struct _EventGuard{F}
    sink::F
    monitor::_EventMonitor
end
function (g::_EventGuard)(event)
    r=g.monitor
    if event.global_refactorizations!=r.last_refactorization
        r.nonzero_steps=0;r.last_refactorization=event.global_refactorizations
    end
    r.zero_dual_streak=iszero(event.dual_step) ? r.zero_dual_streak+1 : 0
    !iszero(event.dual_step)&&(r.nonzero_steps+=1)
    r.last_primal_step=event.primal_step;r.last_dual_step=event.dual_step
    try;g.sink(event)
    catch exception;throw(EventFailure(exception))
    end
end
# Logical reset only. Installed1.13 Base._deleteend! retains backing Memory.
# No new numeric scratch, model/value/factor copy or physical capacity reduction.
function _legacy_workspace!(workspace,source,r::SolveRecord)
    for a in (workspace.scratch.candidates,workspace.scratch.ratio_optional,workspace.scratch.flips)
        r.export_entries+=length(a);empty!(a)
    end
    g=workspace.progress
    workspace.zero_dual_step_streak=r.zero_dual_streak
    workspace.dual_nonzero_steps_since_refactorization=r.last_refactorization==Int128(g.refactorization_offset)+workspace.refactorizations ? r.nonzero_steps : 0
    workspace.scratch.last_primal_step=r.last_primal_step;workspace.scratch.last_dual_step=r.last_dual_step
    progress=J.SimplexProgressContext(g.start_ns,g.objective,g.objective_constant,g.scaling,
        g.iteration_offset,g.refactorization_offset,source.progress.diagnostics,g.numerical_policy)
    # A fixed wrapper adopts existing owners while restoring ordinary diagnostics.
    owned=J.SimplexWorkspace((k==:progress ? progress : getfield(workspace,k) for k in fieldnames(typeof(workspace)))...)
    fill!(owned.scratch.basic_mask,false)
    for index in owned.basis.basic_indices;owned.scratch.basic_mask[index]=true;end
    r.export_mask_entries+=length(owned.costs)+length(owned.basis.basic_indices)
    J._configure_refactorization!(owned);r.export_metadata_refreshes+=1;r.exports+=1
    owned
end
mutable struct PhaseAdapter{C,F}
    record::SolveRecord
    clock::C
    events::F
    entered::Bool
end
PhaseAdapter(record,clock,events)=PhaseAdapter(record,clock,events,false)
function J._dual_engine_notice!(adapter::PhaseAdapter,reason)
    r=adapter.record
    reason==:original_retry&&(r.original_retries+=1)
    reason==:original_cleanup&&(r.original_cleanups+=1)
    reason==:original_recovery&&(r.original_recoveries+=1)
    nothing
end
function (adapter::PhaseAdapter)(source,stop)
    r=adapter.record
    adapter.entered&&throw(ArgumentError("experimental main phase may enter only once"))
    adapter.entered=true;r.entries=1
    if !eligible(source,adapter.clock)
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
"""Opt-in complete solve; original cleanup/certificates still decide success."""
function solve_experimental(problem::J.LinearProblem{T};options=nothing,clock=nothing,
        observer=nothing,events=NoEvents(),record=SolveRecord(),relax_integrality=false)::J.Solution{T} where T
    record.used&&throw(ArgumentError("solve record is consumed"));record.used=true
    started=time_ns();o=isnothing(options) ? J.SolverOptions(T) : J.SolverOptions(T,options)
    if !isnothing(clock) && !(clock isa J._SolveDeadline);throw(ArgumentError("requires internal scalar deadline"));end
    deadline=isnothing(clock) ? J._SolveDeadline(started,o.time_limit) : clock
    deadline.time_limit_seconds==o.time_limit||throw(ArgumentError("deadline limit differs from options"))
    record.start_ns=deadline.start_ns
    diagnostics=J.SimplexDiagnostics(;observer);record.legacy_counts=diagnostics.counts
    supported=T===Float64 && o.algorithm==:dual && o.pricing==:devex &&
        o.basis_update==:pfi && o.basis_refactorization==:native && isnothing(observer)
    supported||(record.reason=:unsupported)
    hook=supported ? PhaseAdapter(record,deadline,events) : nothing
    try
        solution=J._solve_diagnosed(problem,diagnostics;options=o,relax_integrality,
            dual_engine=hook,clock=deadline)
        record.result_status=solution.status
        solution
    catch exception
        exception isa EventFailure&&throw(exception.cause)
        rethrow()
    finally
        record.elapsed_seconds=(time_ns()-deadline.start_ns)/1e9
    end
end

using TOML, SparseArrays
const LONG_SECTIONS = (:presolve,:initialization,:ordinary,:recovery,
    :refactorization,:projection,:cleanup_entry,:cleanup_steps,:certification,:instrumentation)
const LONG_REGIONS = (
    (:presolve_problem,:presolve),(:initialize_workspace,:initialization),
    (:refactorize!,:refactorization),(:_project_postsolve_basis!,:projection),
    (:cleanup_original,:cleanup_entry),(:_internal_solution,:certification),
    (:_original_optimality_certified,:certification),
    (:_try_native_dual_correction!,:recovery),(:_try_native_dual_tableau!,:recovery),
    (:_try_native_primal_point_correction!,:recovery),
    (:_try_native_certificate_recovery,:recovery),(:_refined_basis_solution,:recovery),
)
abstract type AbstractLongObserver end
mutable struct LongRecorder{I<:IO} <: AbstractLongObserver
    io::I
    counters::Vector{Int64}
    previous_counts::Vector{Int64}
    metrics::Matrix{Int64} # exclusive nanoseconds, bytes, allocation events, GC ns
    last_ns::UInt64
    last_gc::Base.GC_Num
    window_start::UInt64
    section::Int
    phase::Symbol
    algorithm::Symbol
    cleanup::Bool
    iteration::Int
    offset::Int
    rows::Int
    columns::Int
    nonzeros::Int
    accepted::Int
    previous_accepted::Int
    rejected::Int
    previous_rejected::Int
    windows::Int
    closed::Bool
end
function LongRecorder(io::IO,counters::Vector{Int64})
    length(counters)==length(LONG_COUNTER_LABELS) || throw(DimensionMismatch("counter schema"))
    now=time_ns()
    LongRecorder(io,counters,copy(counters),zeros(Int64,length(LONG_SECTIONS),4),
      now,Base.gc_num(),now,2,:initialization,:none,false,0,0,0,0,0,0,0,0,0,0,false)
end
function reset_long_recorder!(r::LongRecorder)
    fill!(r.counters,0);fill!(r.previous_counts,0);fill!(r.metrics,0)
    r.last_ns=time_ns();r.last_gc=Base.gc_num();r.window_start=r.last_ns
    r.section=2;r.phase=:initialization;r.algorithm=:none;r.cleanup=false
    r.iteration=0;r.offset=0;r.rows=0;r.columns=0;r.nonzeros=0
    r.accepted=0;r.previous_accepted=0;r.rejected=0;r.previous_rejected=0
    r.windows=0;r.closed=false
    return r
end
function long_account!(r::LongRecorder)
    now=time_ns();gc=Base.gc_num();d=Base.GC_Diff(gc,r.last_gc)
    i=r.section
    r.metrics[i,1]+=Int64(now-r.last_ns)
    r.metrics[i,2]+=d.allocd;r.metrics[i,3]+=Base.gc_alloc_count(d);r.metrics[i,4]+=d.total_time
    r.last_ns=now;r.last_gc=gc
    nothing
end
function long_enter!(r::LongRecorder,section::Symbol)
    index=findfirst(==(section),LONG_SECTIONS)
    isnothing(index) && throw(ArgumentError("Unknown chronological section"))
    old=r.section;long_account!(r);r.section=index;old
end
function long_leave!(r::LongRecorder,old::Int)
    long_account!(r);r.section=old;nothing
end
function long_emit!(r::LongRecorder,reason::Symbol)
    r.closed && throw(ArgumentError("Recorder already finished"))
    long_account!(r)
    end_ns=r.last_ns
    row=Dict("reason"=>string(reason),"phase"=>string(r.phase),"algorithm"=>string(r.algorithm),
      "iteration"=>r.iteration,"offset"=>r.offset,"rows"=>r.rows,"columns"=>r.columns,"nnz"=>r.nonzeros,
      "accepted_steps"=>r.accepted-r.previous_accepted,"rejected_candidates"=>r.rejected-r.previous_rejected,
      "seconds"=>Float64(end_ns-r.window_start)/1e9,
      "counter_deltas"=>r.counters-r.previous_counts,
      "exclusive_nanoseconds"=>copy(r.metrics[:,1]),"exclusive_bytes"=>copy(r.metrics[:,2]),
      "exclusive_allocations"=>copy(r.metrics[:,3]),"exclusive_gc_nanoseconds"=>copy(r.metrics[:,4]))
    copyto!(r.previous_counts,r.counters);fill!(r.metrics,0)
    r.previous_accepted=r.accepted;r.previous_rejected=r.rejected
    r.window_start=end_ns;r.windows+=1
    old=r.section;r.section=length(LONG_SECTIONS)
    try
        TOML.print(r.io,Dict("windows"=>[row]));flush(r.io)
    finally
        # Recorder construction/output cost is retained in the next window's
        # instrumentation bucket; the last tail is returned by finish!.
        long_account!(r);r.section=old
    end
    nothing
end
function (r::LongRecorder)(event::Symbol,ws)
    phase_event=event in (:phase_primal,:phase_dual,:phase_one,:phase_auxiliary,:phase_cleanup,:phase_lp_refinement,:phase_crash)
    if phase_event
        long_emit!(r,:phase_transition)
        r.iteration=ws.iterations;r.offset=ws.progress.iteration_offset
        r.rows,r.columns=size(ws.problem.A);r.nonzeros=nnz(ws.problem.A)
        if event==:phase_cleanup
            r.cleanup=true;r.phase=:cleanup;r.algorithm=:primal
        elseif event==:phase_one
            r.phase=:phase_one;r.algorithm=:primal
        elseif event==:phase_auxiliary
            r.phase=:auxiliary;r.algorithm=:dual
        elseif event==:phase_primal || event==:phase_dual
            r.algorithm=event==:phase_primal ? :primal : :dual
            r.phase=r.cleanup ? :cleanup : :phase_two
        else
            r.phase=event
        end
        long_account!(r);r.section=r.cleanup ? 8 : 3
    elseif event in (:pivot_completed,:flip_completed)
        r.accepted+=1;r.iteration=ws.iterations;r.offset=ws.progress.iteration_offset
        r.accepted%1024==0 && long_emit!(r,:periodic)
    elseif event==:pivot_rejected
        r.rejected+=1
    end
    nothing
end
function finish!(r::LongRecorder)
    long_emit!(r,:final_partial)
    r.closed=true
    # Includes the final emitted record's construction/write/flush. This is
    # diagnostic tail work, not another numerical phase or a certificate.
    return Dict("tail_instrumentation_nanoseconds"=>r.metrics[end,1],
      "tail_instrumentation_bytes"=>r.metrics[end,2],"windows"=>r.windows)
end
function install_long_regions!(JS,source_root,recorder::LongRecorder)
    isdefined(JS,:_lc_recorder) && throw(ArgumentError("Long regions already installed"))
    isdefined(JS,:_lc_counts) || throw(ArgumentError("Install count probes first"))
    entries=map(LONG_REGIONS) do (name,section)
        index=findfirst(x->first(x)==name,LONG_HOOKS)
        isnothing(index) && error("Missing counted region $name")
        expression=long_function(source_root,LONG_HOOKS[index][2],"function $(name)(")
        (index,section,expression)
    end
    Core.eval(JS,:(const _lc_recorder=$recorder))
    Core.eval(JS,:(const _lc_enter! = $(long_enter!)))
    Core.eval(JS,:(const _lc_leave! = $(long_leave!)))
    for (index,section,expression) in entries
        body=expression.args[2];token=gensym(:region)
        expression.args[2]=quote
            _lc_counts[$index]+=1
            local $token=_lc_enter!(_lc_recorder,$(QuoteNode(section)))
            try
                $body
            finally
                _lc_leave!(_lc_recorder,$token)
            end
        end
        Core.eval(JS,expression)
    end
    nothing
end

# Verification-only composition: the timed recorder has no trace field/branch.
struct LongTraceObserver{R,F} <: AbstractLongObserver
    recorder::R
    trace::F
end
function (observer::LongTraceObserver)(event,ws)
    observer.recorder(event,ws)
    observer.trace(event,ws)
    nothing
end
function install_long_event_sink!(JS)
    isdefined(JS,:_lc_owned_observer_type) && throw(ArgumentError("Owned event sink already installed"))
    Core.eval(JS,:(const _lc_owned_observer_type=$AbstractLongObserver))
    Core.eval(JS,quote
        # Only this diagnostic script's observers use fixed counters/streamed
        # windows instead of the generic event dictionary and 64-event history.
        # Keep event validation, standard callback exception wrapping, and the
        # distinct _StageObserver dispatch that buffers candidate completions.
        # Direct metadata writes (discarded-candidate work and committed
        # recovery) are also omitted. Operation counters remain, but do not
        # establish complete event/recovery coverage; see S0-LONG.md.
        @inline function record_event!(d::SimplexDiagnostics{F},reason::Symbol)::Nothing where {F<:_lc_owned_observer_type}
            reason in SIMPLEX_EVENT_REASONS || throw(ArgumentError("Unknown simplex diagnostic event: $reason"))
            nothing
        end
    end)
    nothing
end

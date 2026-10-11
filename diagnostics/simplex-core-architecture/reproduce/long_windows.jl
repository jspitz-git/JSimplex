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
    region_stack::Vector{Int}
    region_depth::Int
    base_section::Int
    cleanup_steps::Bool
end
function LongRecorder(io::IO,counters::Vector{Int64})
    length(counters)==length(LONG_COUNTER_LABELS) || throw(DimensionMismatch("counter schema"))
    now=time_ns()
    LongRecorder(io,counters,copy(counters),zeros(Int64,length(LONG_SECTIONS),4),
      now,Base.gc_num(),now,2,:initialization,:none,false,0,0,0,0,0,0,0,0,0,0,false,zeros(Int,32),0,2,false)
end
function reset_long_recorder!(r::LongRecorder)
    length(r.counters)==length(r.previous_counts)==length(LONG_COUNTER_LABELS) ||
        throw(DimensionMismatch("counter schema"))
    fill!(r.counters,0);fill!(r.previous_counts,0);fill!(r.metrics,0)
    r.last_ns=time_ns();r.last_gc=Base.gc_num();r.window_start=r.last_ns
    r.section=2;r.phase=:initialization;r.algorithm=:none;r.cleanup=false
    r.iteration=0;r.offset=0;r.rows=0;r.columns=0;r.nonzeros=0
    r.accepted=0;r.previous_accepted=0;r.rejected=0;r.previous_rejected=0
    r.windows=0;r.closed=false
    fill!(r.region_stack,0);r.region_depth=0;r.base_section=2;r.cleanup_steps=false
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
function long_select_section!(r::LongRecorder)
    r.section=r.base_section
    for i in r.region_depth:-1:1
        candidate=r.region_stack[i]
        candidate==7 && r.cleanup_steps && continue
        r.section=candidate
        break
    end
    nothing
end
function long_enter!(r::LongRecorder,section::Symbol)
    index=findfirst(==(section),LONG_SECTIONS)
    isnothing(index) && throw(ArgumentError("Unknown chronological section"))
    token=r.region_depth
    token<length(r.region_stack) || error("Chronological region nesting overflow")
    long_account!(r)
    r.region_depth+=1;r.region_stack[r.region_depth]=index
    long_select_section!(r)
    token
end
function long_leave!(r::LongRecorder,token::Int)
    r.region_depth==token+1 || error("Unbalanced chronological region nesting")
    long_account!(r);r.region_depth=token
    long_select_section!(r)
    nothing
end
# Schema-specific streaming avoids temporary dictionaries and vector slices for
# numeric arrays. TOML still escapes the three string fields correctly.
function long_write_array!(io,label,values)
    print(io,label," = [")
    first=true
    for value in values
        first || print(io,", ")
        print(io,value)
        first=false
    end
    print(io,"]\n")
    nothing
end
function long_write_window!(io,r::LongRecorder,reason::Symbol,end_ns::UInt64)
    print(io,"[[windows]]\n")
    TOML.print(io,Dict("reason"=>string(reason),"phase"=>string(r.phase),"algorithm"=>string(r.algorithm)))
    for (label,value) in (("iteration",r.iteration),("offset",r.offset),
        ("rows",r.rows),("columns",r.columns),("nnz",r.nonzeros),
        ("accepted_steps",r.accepted-r.previous_accepted),
        ("rejected_candidates",r.rejected-r.previous_rejected))
        print(io,label," = ",value,"\n")
    end
    print(io,"seconds = ",Float64(end_ns-r.window_start)/1e9,"\n")
    long_write_array!(io,"counter_deltas",(r.counters[i]-r.previous_counts[i] for i in eachindex(r.counters)))
    for (column,label) in enumerate(("exclusive_nanoseconds","exclusive_bytes","exclusive_allocations","exclusive_gc_nanoseconds"))
        long_write_array!(io,label,(r.metrics[i,column] for i in axes(r.metrics,1)))
    end
    print(io,"\n")
    nothing
end
function long_emit!(r::LongRecorder,reason::Symbol)
    r.closed && throw(ArgumentError("Recorder already finished"))
    long_account!(r)
    end_ns=r.last_ns
    old=r.section;r.section=length(LONG_SECTIONS)
    try
        long_write_window!(r.io,r,reason,end_ns)
        flush(r.io)
    finally
        # Snapshot/reset after writing; no numerical code runs in between.
        # The next window (or finish! tail) receives all construction/output work.
        copyto!(r.previous_counts,r.counters);fill!(r.metrics,0)
        r.previous_accepted=r.accepted;r.previous_rejected=r.rejected
        r.window_start=end_ns;r.windows+=1
        long_account!(r);r.section=old
    end
    nothing
end

# Cold phase changes must not overwrite an active recovery/refactor region.
function long_set_phase!(r::LongRecorder,phase,algorithm,ws)
    rows,columns=size(ws.problem.A)
    if (r.phase,r.algorithm,r.rows,r.columns,r.offset)!=(phase,algorithm,rows,columns,ws.progress.iteration_offset)
        long_emit!(r,:phase_transition)
    end
    long_account!(r)
    r.phase=phase;r.algorithm=algorithm
    r.iteration=ws.iterations;r.offset=ws.progress.iteration_offset
    r.rows=rows;r.columns=columns;r.nonzeros=nnz(ws.problem.A)
    long_select_section!(r)
    nothing
end
function long_report_phase!(r::LongRecorder,phase::Symbol,algorithm::Symbol,ws)
    name=r.cleanup ? :cleanup : phase==:I ? (algorithm==:dual ? :auxiliary : :phase_one) : :phase_two
    long_set_phase!(r,name,algorithm,ws)
    r.base_section=r.cleanup ? (r.cleanup_steps ? 8 : 7) : 3
    long_select_section!(r)
    nothing
end
function long_algorithm!(r::LongRecorder,algorithm::Symbol,ws)
    if r.algorithm==algorithm && (r.rows,r.columns)==size(ws.problem.A) &&
       r.offset==ws.progress.iteration_offset && (!r.cleanup || r.cleanup_steps) &&
       r.base_section==(r.cleanup ? 8 : 3)
        r.iteration=ws.iterations
        return nothing
    end
    long_set_phase!(r,r.phase,algorithm,ws)
    r.cleanup && (r.cleanup_steps=true)
    r.base_section=r.cleanup ? 8 : 3
    long_select_section!(r)
    nothing
end
function long_cleanup!(r::LongRecorder,problem,prior_iterations)
    long_emit!(r,:cleanup_entry)
    r.cleanup=true;r.cleanup_steps=false;r.phase=:cleanup;r.algorithm=:none
    r.iteration=prior_iterations;r.offset=0
    r.rows,r.columns=size(problem.A);r.nonzeros=nnz(problem.A)
    r.base_section=7;long_select_section!(r)
    nothing
end
function long_phase!(r::LongRecorder,event::Symbol,ws)
    if event==:phase_cleanup
        r.cleanup=true
        long_set_phase!(r,:cleanup,:primal,ws)
        r.base_section=r.cleanup_steps ? 8 : 7
    elseif event==:phase_one || event==:phase_auxiliary
        long_set_phase!(r,r.cleanup ? :cleanup : event==:phase_one ? :phase_one : :auxiliary,
            event==:phase_one ? :primal : :dual,ws)
        r.base_section=r.cleanup ? (r.cleanup_steps ? 8 : 7) : 3
    elseif event==:phase_primal || event==:phase_dual
        # Method selection is not evidence that initialization/phase I ended.
        long_set_phase!(r,r.phase,event==:phase_primal ? :primal : :dual,ws)
    else
        long_set_phase!(r,r.cleanup ? :cleanup : event,r.algorithm,ws)
    end
    long_select_section!(r)
    nothing
end
@inline function (r::LongRecorder)(event::Symbol,ws)
    if event in (:pivot_completed,:flip_completed)
        r.accepted+=1;r.iteration=ws.iterations;r.offset=ws.progress.iteration_offset
        r.accepted%1024==0 && long_emit!(r,:periodic)
    elseif event==:pivot_rejected
        r.rejected+=1
    elseif event in (:phase_primal,:phase_dual,:phase_one,:phase_auxiliary,:phase_cleanup,:phase_lp_refinement,:phase_crash)
        long_phase!(r,event,ws)
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
    Core.eval(JS,:(const _lc_phase! = $(long_report_phase!)))
    Core.eval(JS,:(const _lc_algorithm! = $(long_algorithm!)))
    Core.eval(JS,:(const _lc_cleanup! = $(long_cleanup!)))
    for (index,section,expression) in entries
        body=expression.args[2];token=gensym(:region)
        cleanup=section==:cleanup_entry ? :(_lc_cleanup!(_lc_recorder,problem,prior_iterations)) : nothing
        expression.args[2]=quote
            @inbounds _lc_counts[$index]+=1
            try
                $cleanup
            catch exception
                throw(DiagnosticObserverFailure(exception))
            end
            local $token=_lc_enter!(_lc_recorder,$(QuoteNode(section)))
            try
                $body
            finally
                _lc_leave!(_lc_recorder,$token)
            end
        end
        Core.eval(JS,expression)
    end
    for (name,file,observation) in (
        (:_report_simplex_phase,"simplex.jl",:(_lc_phase!(_lc_recorder,phase,algorithm,workspace))),
        (:_primal_optimize!,"primal_simplex.jl",:(_lc_algorithm!(_lc_recorder,:primal,workspace))),
        (:_dual_optimize!,"dual_simplex.jl",:(_lc_algorithm!(_lc_recorder,:dual,workspace))),
    )
        expression=long_function(source_root,file,"function $(name)(")
        body=expression.args[2]
        expression.args[2]=quote
            try
                $observation
            catch exception
                throw(DiagnosticObserverFailure(exception))
            end
            $body
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
        # Generic history remains omitted. long_metadata.jl separately preserves
        # pricing work, committed recovery reasons and discarded metadata totals.
        @inline function record_event!(d::SimplexDiagnostics{F},reason::Symbol)::Nothing where {F<:_lc_owned_observer_type}
            reason in SIMPLEX_EVENT_REASONS || throw(ArgumentError("Unknown simplex diagnostic event: $reason"))
            nothing
        end
    end)
    nothing
end

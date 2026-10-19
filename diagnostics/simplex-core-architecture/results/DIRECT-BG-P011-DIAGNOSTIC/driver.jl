# OFFLINE preparation only. UNEXECUTED: no Julia parse/dispatch/cost acceptance.
# This diagnostic never invokes the frozen RED driver or its test entry point.
const LOAD_STATS = Base.gc_num()
const LOAD_START = time_ns()
Base.cumulative_compile_timing(true)
const LOAD_COMPILE = Base.cumulative_compile_time_ns()
using Test, LinearAlgebra, TOML
using JSimplex
const ROOT = normpath(joinpath(@__DIR__, "../../../.."))
const H = joinpath(ROOT, "diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS")
include(joinpath(H, "recorder.jl"))
include(joinpath(ROOT, "diagnostics/direct-bg-blocked-update/reproduce/panel.jl"))
include(joinpath(H, "panel-tests.jl")) # definitions only; run_task1_tests is NEVER called
const LOAD_DIFF = Base.GC_Diff(Base.gc_num(), LOAD_STATS)
const LOAD_SECONDS = (time_ns() - LOAD_START) / 1e9
const LOAD_COMPILE_DIFF = Base.cumulative_compile_time_ns() .- LOAD_COMPILE
Base.cumulative_compile_timing(false)

module P011Diagnostic
using ..TOML
import ..JSimplex, ..BGBlockedPanel, ..BGBlockedPanelTests
const K = BGBlockedPanel
const T = BGBlockedPanelTests
const Carrier = T.Carrier
const Decision = K.BGPanelDecision
require(ok, text) = ok || error(text)

# Reduced original-shaped scope, NOT the original compiled run_task1_tests caller.
# Keep the qualified macro expression and subsequent assignment to the captured f.
function original_bytes(input::Carrier, replacement::Carrier)
    f = input
    K._bgb_eligibility(f,1)
    bytes = @allocated K._bgb_eligibility(f,1)
    f = replacement
    return (bytes, f === replacement)
end
function original_events(input::Carrier, replacement::Carrier)
    f = input
    K._bgb_eligibility(f,1)
    events = @allocations K._bgb_eligibility(f,1)
    f = replacement
    return (events, f === replacement)
end
# Explicit function barrier, preserving the full result and all eligibility code.
# Base.allocated/allocations provide their own noinline call boundary on pinned Julia.
function concrete_call(f::Carrier)::Decision
    K._bgb_eligibility(f,1)
end
function concrete_bytes(input::Carrier, replacement::Carrier)
    concrete_call(input)
    bytes = Base.allocated(concrete_call, input)
    return (bytes, replacement === replacement)
end
function concrete_events(input::Carrier, replacement::Carrier)
    concrete_call(input)
    events = Base.allocations(concrete_call, input)
    return (events, replacement === replacement)
end
# A separately labelled escaped-result companion. Its cost is NOT the P011 cost.
# A typed Ref sink forces the full decision to remain observable after the call.
function consume_original!(sink::Base.RefValue{Decision}, f::Carrier)
    sink[] = K._bgb_eligibility(f,1)
    nothing
end
function consume_concrete!(sink::Base.RefValue{Decision}, f::Carrier)
    sink[] = concrete_call(f)
    nothing
end
function decision_ok(d::Decision)
    d.start == 1 && d.count == 0 && !d.accepted && d.reason === :dimensions &&
        d.finite && d.counters == ntuple(_ -> 0, 20)
end
function state(f::Carrier)
    order = f.upper[1].indices.order
    cache = f.row_cache
    # Every Carrier field and every row-cache field is covered. No prepared cache
    # is expected in this fixture; encountering one refuses the diagnostic.
    require(cache.prepared === nothing && f.sparse === nothing, "Unexpected cache")
    values = (T.snapshot(f), copy(order.order), copy(order.positions),
        copy(f.column_order), copy(f.positions), f.row_columns_ready,
        Tuple(deepcopy(getfield(cache, k)) for k in fieldnames(typeof(cache))))
    owners = Any[f, f.upper, f.column_order, f.positions, f.row_columns, cache,
        order.order, order.positions]
    append!(owners, f.row_columns)
    for col in f.upper
        push!(owners, col.values, col.indices.ids, col.indices.order.order,
            col.indices.order.positions)
    end
    for k in fieldnames(typeof(cache))
        x = getfield(cache,k)
        x isa AbstractArray && push!(owners,x)
    end
    (values=values, owners=owners)
end
function unchanged(before, after)
    isequal(before.values,after.values) && length(before.owners)==length(after.owners) &&
        all(a === b for (a,b) in zip(before.owners,after.owners))
end
function metrics(t)
    Dict("seconds"=>t.time, "bytes"=>t.bytes,
        "events"=>Base.gc_alloc_count(t.gcstats), "gc_seconds"=>t.gctime,
        "compile_seconds"=>t.compile_time, "recompile_seconds"=>t.recompile_time)
end
function save(output, name, value)
    p = joinpath(output,name)
    ispath(p) && error("Refusing existing output: " * p)
    open(p,"w") do io
        TOML.print(io,value; sorted=true)
        flush(io)
    end
end
function sample(bytesfun, eventsfun, consumer, input, replacement, sink)
    # Three distinct executions: never subtract outer counters from inner ones.
    b = @timed bytesfun(input,replacement)
    e = @timed eventsfun(input,replacement)
    c = @timed consumer(sink,input)
    Dict("inner_bytes"=>b.value[1], "inner_events"=>e.value[1],
        "assignment_ok"=>(b.value[2] && e.value[2]), "decision_ok"=>decision_ok(sink[]),
        "bytes_wrapper"=>metrics(b), "events_wrapper"=>metrics(e),
        "consumed_result"=>metrics(c))
end
function main(output, project, load_record)
    require(isdir(output) && isempty(readdir(output)), "Need reserved empty output directory")
    raw = Dict{String,Any}("schema"=>1, "complete"=>false, "fatal"=>"",
        "qualification"=>"diagnostic_only", "records"=>Any[])
    try
        require(realpath(pathof(JSimplex))==realpath(joinpath(project,"src/JSimplex.jl")), "Wrong staged package")
        require(Threads.nthreads()==1 && Main.LinearAlgebra.BLAS.get_num_threads()==1, "Thread configuration")
        raw["loaded"] = Dict(string(nameof(m))=>realpath(pathof(m)) for m in
            (JSimplex, Main.Test, Main.LinearAlgebra, TOML))
        save(output,"load.toml",load_record)
        setup = @timed begin
            input = T.carrier(zeros(32,32))
            replacement = T.carrier(T.denseband(64))
            sink = Ref(Decision(0,0,false,:uninitialized,false,ntuple(_->0,20)))
            (input,replacement,sink)
        end
        input,replacement,sink = setup.value
        save(output,"setup.toml",metrics(setup))
        checks = @timed (state(input),state(replacement))
        before = checks.value
        save(output,"snapshot-before.toml",metrics(checks))
        arms = (("original",original_bytes,original_events,consume_original!),
                ("concrete",concrete_bytes,concrete_events,consume_concrete!))
        # Fixed schedule: first calls, one warm pair, four alternating sample pairs.
        # First-call records are NOT cold-process comparisons: shared code warms once.
        schedule = [("first",0,1),("first",0,2),("warm",0,2),("warm",0,1)]
        for pair in 1:4
            for arm in (isodd(pair) ? (1,2) : (2,1))
                push!(schedule,("sample",pair,arm))
            end
        end
        for (index,(phase,pair,arm)) in enumerate(schedule)
            name,b,e,c = arms[arm]
            row = sample(b,e,c,input,replacement,sink)
            merge!(row,Dict("index"=>index,"phase"=>phase,"pair"=>pair,"arm"=>name))
            push!(raw["records"],row)
            save(output,"record-$index.toml",row) # before any result assertion
            require(row["assignment_ok"] && row["decision_ok"],"Wrong decision or assignment")
            require(row["inner_bytes"]>=0 && row["inner_events"]>=0,"Invalid allocation counters")
        end
        after_cost = @timed (state(input),state(replacement))
        save(output,"snapshot-after.toml",metrics(after_cost))
        raw["input_unchanged"] = unchanged(before[1],after_cost.value[1])
        raw["replacement_unchanged"] = unchanged(before[2],after_cost.value[2])
        require(raw["input_unchanged"] && raw["replacement_unchanged"],"Input mutation")
        raw["complete"] = true
    catch e
        raw["fatal"] = sprint(showerror,e,catch_backtrace())
    finally
        save(output,"raw.toml",raw)
    end
    raw["complete"] || exit(2)
end
end
length(ARGS)==2 || error("Expected reserved output directory and exact staged project")
P011Diagnostic.main(ARGS[1],ARGS[2],Dict(
    "seconds"=>LOAD_SECONDS, "bytes"=>LOAD_DIFF.allocd,
    "events"=>Base.gc_alloc_count(LOAD_DIFF), "gc_seconds"=>LOAD_DIFF.total_time/1e9,
    "compile_seconds"=>LOAD_COMPILE_DIFF[1]/1e9,
    "recompile_seconds"=>LOAD_COMPILE_DIFF[2]/1e9))

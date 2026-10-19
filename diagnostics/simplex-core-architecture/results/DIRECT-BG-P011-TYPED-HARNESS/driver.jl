# OFFLINE prepared. All includes happen at top level before main.
const LOAD_STATS=Base.gc_num()
const LOAD_START=time_ns()
Base.cumulative_compile_timing(true)
const LOAD_COMPILE=Base.cumulative_compile_time_ns()
using Test,LinearAlgebra,TOML,JSimplex,PrecompileTools
length(ARGS)==3 || error("Expected payload, stage, phase")
const OUTPUT,PROJECT,PHASE=ARGS
PHASE in ("p011-red300","p011-green300") || error("Unprepared phase")
const RED=PHASE=="p011-red300"
const RESULTS=dirname(@__DIR__)
const REPAIR=joinpath(RESULTS,"DIRECT-BG-P011-TYPED-REPAIR")
const TEST_SOURCE=RED ? joinpath(RESULTS,"DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS/panel-tests.jl") : joinpath(REPAIR,"panel-tests.jl")
include("recorder.jl")
const PANEL_LOAD=@timed include(joinpath(RESULTS,"DIRECT-BG-ZERO-COUNTS-CANDIDATE/panel.jl"))
const TESTS_LOAD=@timed begin
    include(TEST_SOURCE)
    # The original test body remains exact; helper definitions support a separate
    # diagnostic probe. GREEN already contains them, so never include them twice.
    if RED;Base.include(BGBlockedPanelTests,joinpath(REPAIR,"helpers.jl"));end
end
const LOAD_DIFF=Base.GC_Diff(Base.gc_num(),LOAD_STATS)
const LOAD_SECONDS=(time_ns()-LOAD_START)/1e9
const LOAD_COMPILE_DIFF=Base.cumulative_compile_time_ns().-LOAD_COMPILE
Base.cumulative_compile_timing(false)
module P011Driver
using ..Test,..TOML
import ..JSimplex,..BGBlockedPanelTests,..HarnessRecords
const B=BGBlockedPanelTests
require(ok,text)=ok || error(text)
metrics(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),
    "gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
function save(name,value)
    p=joinpath(Main.OUTPUT,name)
    ispath(p) && error("Existing output: "*p)
    open(p,"w") do io;TOML.print(io,value;sorted=true);flush(io);end
end
function decision(d)
    Dict{String,Any}("start"=>d.start,"count"=>d.count,"accepted"=>d.accepted,
        "reason"=>string(d.reason),"finite"=>d.finite,"counters"=>collect(d.counters))
end
function probe_record(p)
    Dict{String,Any}("bytes"=>p.bytes,"events"=>p.events,"consumed_bytes"=>p.consumed_bytes,
      "consumed_events"=>p.consumed_events,"warm"=>decision(p.warm),
      "bytes_decision"=>decision(p.bytes_decision),"events_decision"=>decision(p.events_decision),
      "values_unchanged"=>p.values_unchanged,"owners_unchanged"=>p.owners_unchanged)
end
function totals(t)
    a=[t["pass"],t["fail"],t["error"],t["broken"]]
    for child in t["children"];a .+= totals(child);end
    a
end
function tests()
    HarnessRecords.reset!();root=HarnessRecords.Capture("panel");complete=false;fatal="";row=Dict{String,Any}()
    try
        Test.@with_testset root begin;B.run_task1_tests();end
        complete=true
    catch e
        fatal=sprint(showerror,e,catch_backtrace())
    finally
        row=Dict("index"=>1,"name"=>"panel","complete"=>complete,"fatal"=>fatal,
            "tests"=>HarnessRecords.dictionary(root),"records"=>HarnessRecords.snapshot())
        save("unit-1.toml",row)
    end
    row
end
function main(load_record)
    require(isdir(Main.OUTPUT) && isempty(readdir(Main.OUTPUT)),"Need empty reserved payload")
    raw=Dict{String,Any}("schema"=>1,"phase"=>Main.PHASE,"complete"=>false,"fatal"=>"",
        "qualification"=>"p011_typed_structural","test_source"=>realpath(Main.TEST_SOURCE))
    valid=false
    try
        require(realpath(pathof(JSimplex))==realpath(joinpath(Main.PROJECT,"src/JSimplex.jl")),"Wrong stage")
        require(Threads.nthreads()==Main.LinearAlgebra.BLAS.get_num_threads()==1 && !Main.PrecompileTools.verbose[],"Threads/precompile verbose")
        raw["loaded"]=Dict(string(nameof(m))=>realpath(pathof(m)) for m in
            (JSimplex,Main.Test,Main.LinearAlgebra,TOML,Main.PrecompileTools))
        raw["threads"]=Threads.nthreads();raw["blas_threads"]=Main.LinearAlgebra.BLAS.get_num_threads()
        save("load.toml",load_record);save("panel-load.toml",metrics(Main.PANEL_LOAD));save("tests-load.toml",metrics(Main.TESTS_LOAD))
        setup=@timed B.carrier(zeros(32,32));save("probe-setup.toml",metrics(setup))
        probe=@timed B.p011_probe(setup.value)
        save("probe-cost.toml",metrics(probe));p=probe_record(probe.value);save("probe.toml",p);raw["probe"]=p
        require(all(p[k]==0 for k in ("bytes","events","consumed_bytes","consumed_events")) &&
            p["values_unchanged"] && p["owners_unchanged"] &&
            all(B.p011_expected(d) for d in (probe.value.warm,probe.value.bytes_decision,probe.value.events_decision)),"Typed probe failed")
        tc=@timed tests();save("tests-cost.toml",metrics(tc));raw["unit"]=tc.value
        t=totals(tc.value["tests"]);raw["totals"]=t
        failures=tc.value["records"]["failures"]
        expected=Main.RED ? 1 : 0
        valid=tc.value["complete"] && isempty(tc.value["fatal"]) && t[2]==expected && t[3]==t[4]==0 &&
            tc.value["records"]["failure_count"]==length(failures)==expected &&
            all(f["site"]=="P011" && f["kind"]=="fail" for f in failures)
        raw["complete"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace())
    finally
        save("raw.toml",raw)
    end
    # Exact test-site/tree totals and every payload are independently audited.
    exit(valid && isempty(raw["fatal"]) ? (Main.RED ? 1 : 0) : 2)
end
end
P011Driver.main(Dict("seconds"=>LOAD_SECONDS,"bytes"=>LOAD_DIFF.allocd,
    "events"=>Base.gc_alloc_count(LOAD_DIFF),"gc_seconds"=>LOAD_DIFF.total_time/1e9,
    "compile_seconds"=>LOAD_COMPILE_DIFF[1]/1e9,"recompile_seconds"=>LOAD_COMPILE_DIFF[2]/1e9))

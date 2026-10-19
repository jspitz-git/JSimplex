# OFFLINE prepared. All includes remain at top level before main.
const LOAD_STATS=Base.gc_num()
const LOAD_START=time_ns()
Base.cumulative_compile_timing(true)
const LOAD_COMPILE=Base.cumulative_compile_time_ns()
using Test, LinearAlgebra, SparseArrays, TOML, PrecompileTools
using JSimplex
length(ARGS)==3 || error("Exactly output/project/phase required")
const OUTPUT, PROJECT, PHASE=ARGS
PHASE in ("red300","green300") || error("Unprepared phase")
const RED=PHASE=="red300"
const C=normpath(joinpath(@__DIR__,"../../../direct-bg-blocked-update/reproduce"))
include("recorder.jl")
const PANEL_LOAD=@timed begin
    include("panel.jl")
    include("factor.jl")
    include("panel-fault.jl")
    include("factor-fault.jl")
end
const TESTS_LOAD=@timed begin
    include("panel-tests.jl")
    include("numerical-tests.jl")
    include("lifecycle-tests.jl")
end
const LOAD_DIFF=Base.GC_Diff(Base.gc_num(),LOAD_STATS)
const LOAD_SECONDS=(time_ns()-LOAD_START)/1e9
const LOAD_COMPILE_DIFF=Base.cumulative_compile_time_ns().-LOAD_COMPILE
Base.cumulative_compile_timing(false)
metrics(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),
    "gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
require(v,m)=v || error(m)
function save(name,value)
    p=joinpath(OUTPUT,name);ispath(p) && error("Existing output: "*p)
    open(p,"w") do io;TOML.print(io,value;sorted=true);flush(io);end
end
function totals(t)
    a=[t.passed,t.failed,t.errored,t.broken]
    for child in t.children;a .+= totals(child);end
    a
end
function unit!(body,index,name)
    println(stderr,"UNIT BEGIN ",index," ",name);flush(stderr)
    HarnessRecords.reset!();root=HarnessRecords.Capture(name);complete=false;fatal="";observations=Any[]
    try
        Test.@with_testset root begin
            result=body()
            if result isa AbstractVector
                observations=[Dict(string(k)=>v for (k,v) in pairs(row)) for row in result]
            end
        end
        complete=true
    catch e
        fatal=sprint(showerror,e,catch_backtrace());rethrow()
    finally
        save("unit-$index.toml",Dict("index"=>index,"name"=>name,"complete"=>complete,"fatal"=>fatal,
          "tests"=>HarnessRecords.dictionary(root),"records"=>HarnessRecords.snapshot(),"observations"=>observations))
    end
    println(stderr,"UNIT END ",index," ",name);flush(stderr)
    a=totals(root)
    expected=RED && name in ("dense96/native","dense96/markowitz","dense256/native","dense256/markowitz","dense96-long32/native","dense96-long32/markowitz") ? 1 : 0
    require(a[2]==expected && a[3]==a[4]==0 && HarnessRecords.failure_count[]==expected &&
        all(r["site"]=="N026" && r["kind"]=="fail" for r in HarnessRecords.failures),"Unexpected unit failure; saved prefix retained")
    a
end
function measured_unit!(body,index,name)
    t=@timed unit!(body,index,name)
    save("cost-$index.toml",metrics(t))
    t.value
end
function main()
    require(isdir(OUTPUT) && isempty(readdir(OUTPUT)),"Need empty reserved payload")
    raw=Dict{String,Any}("phase"=>PHASE,"complete"=>false,"fatal"=>"","units_completed"=>0)
    total=zeros(Int,4)
    try
        require(realpath(pathof(JSimplex))==realpath(joinpath(PROJECT,"src/JSimplex.jl")),"Wrong staged package")
        require(Threads.nthreads()==BLAS.get_num_threads()==1 && !PrecompileTools.verbose[],"Threads/precompile verbose")
        raw["loaded"]=Dict(string(nameof(m))=>realpath(pathof(m)) for m in (JSimplex,SparseArrays,LinearAlgebra,TOML,Test,PrecompileTools))
        raw["threads"]=Threads.nthreads();raw["blas_threads"]=BLAS.get_num_threads()
        save("load.toml",Dict("seconds"=>LOAD_SECONDS,"bytes"=>LOAD_DIFF.allocd,
          "events"=>Base.gc_alloc_count(LOAD_DIFF),"gc_seconds"=>LOAD_DIFF.total_time/1e9,
          "compile_seconds"=>LOAD_COMPILE_DIFF[1]/1e9,"recompile_seconds"=>LOAD_COMPILE_DIFF[2]/1e9))
        save("panel-load.toml",metrics(PANEL_LOAD));save("tests-load.toml",metrics(TESTS_LOAD))
        println(stderr,"BEGIN BG blocked U driver ",PHASE);flush(stderr)
        total .+= measured_unit!(BGBlockedPanelTests.run_task1_tests,1,"panel");raw["units_completed"]=1
        total .+= measured_unit!(BGBlockedLifecycleTests.run_lifecycle,2,"lifecycle");raw["units_completed"]=2
        fixtures=TOML.parsefile(joinpath(C,"fixtures.toml"))["fixtures"]
        for f in fixtures,(backend,policy) in BGBlockedNumericalTests.ARMS
            i=raw["units_completed"]+1;name=f["name"]*"/"*string(backend)
            total .+= measured_unit!(()->BGBlockedNumericalTests.run_stream(f,backend,policy;reference_route=RED),i,name)
            raw["units_completed"]=i
        end
        raw["complete"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace());println(stderr,"FATAL DRIVER: ",raw["fatal"]);flush(stderr)
    finally
        raw["totals"]=total
        save("raw.toml",raw) # before aggregate status and exit; prefix unit files survive.
    end
    valid=raw["complete"] && isempty(raw["fatal"]) && raw["units_completed"]==28 && total[2]==(RED ? 6 : 0) && total[3]==total[4]==0
    valid || (println(stderr,"GROUP/COUNT MISMATCH OR FATAL");flush(stderr))
    # External auditor also checks every site, formula, API count, named failure and observation.
    exit(valid ? (RED ? 1 : 0) : 2)
end
main()

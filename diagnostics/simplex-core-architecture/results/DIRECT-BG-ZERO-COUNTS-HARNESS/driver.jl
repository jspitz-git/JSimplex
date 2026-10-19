# Offline prepared driver; top-level includes prevent runtime world-age crossings.
const LOAD_STATS=Base.gc_num()
const LOAD_START=time_ns()
Base.cumulative_compile_timing(true)
const LOAD_COMPILE=Base.cumulative_compile_time_ns()
using Test,LinearAlgebra,TOML,JSimplex
include("/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS/recorder.jl") # ONE custom Test API owner
const REFERENCE_LOAD=@timed include(joinpath(@__DIR__,"reference-side.jl"))
const CANDIDATE_LOAD=@timed include(joinpath(@__DIR__,"candidate-side.jl"))
const LOAD_DIFF=Base.GC_Diff(Base.gc_num(),LOAD_STATS)
const LOAD_SECONDS=(time_ns()-LOAD_START)/1e9
const LOAD_COMPILE_DIFF=Base.cumulative_compile_time_ns().-LOAD_COMPILE
Base.cumulative_compile_timing(false)
module ZeroDriver
using ..Test,..TOML
import ..JSimplex,..BGZeroReference,..BGZeroCandidate,..HarnessRecords
const A=BGZeroReference
const B=BGZeroCandidate
require(ok,text)=ok || error(text)
metrics(t)=A.metrics(t)
function save(output,name,v)
    p=joinpath(output,name)
    ispath(p) && error("Existing output: "*p)
    open(p,"w") do io
        TOML.print(io,v;sorted=true);flush(io)
    end
end
function tests()
    HarnessRecords.reset!()
    t=@testset HarnessRecords.Capture "zero-count candidate" begin
        B.BGZeroCountsTests.run_zero_counts_tests()
    end
    Dict("tree"=>HarnessRecords.dictionary(t),"failure_count"=>HarnessRecords.failure_count[],
         "failures"=>copy(HarnessRecords.failures))
end
function tests_ok(t)
    tree=t["tree"]
    expected=(7,300,10,26,7)
    t["failure_count"]==0 && isempty(t["failures"]) &&
      all(tree[k]==0 for k in ("pass","fail","error","broken")) &&
      length(tree["children"])==5 && all(
        c["pass"]==p && all(c[k]==0 for k in ("fail","error","broken")) && isempty(c["children"])
        for (c,p) in zip(tree["children"],expected))
end
function main(output,project,load_record)
    require(isdir(output) && isempty(readdir(output)),"Need reserved empty output")
    raw=Dict{String,Any}("schema"=>1,"complete"=>false,"fatal"=>"",
      "qualification"=>"zero_counts_diagnostic","records"=>Any[])
    try
        require(realpath(pathof(JSimplex))==realpath(joinpath(project,"src/JSimplex.jl")),"Wrong stage")
        require(Threads.nthreads()==1 && Main.LinearAlgebra.BLAS.get_num_threads()==1,"Threads")
        raw["loaded"]=Dict(string(nameof(m))=>realpath(pathof(m)) for m in
          (JSimplex,Main.Test,Main.LinearAlgebra,TOML))
        save(output,"load.toml",load_record)
        save(output,"reference-load.toml",metrics(Main.REFERENCE_LOAD))
        save(output,"candidate-load.toml",metrics(Main.CANDIDATE_LOAD))
        setup=@timed (A.setup(),B.setup())
        a,b=setup.value;save(output,"setup.toml",metrics(setup))
        pre=@timed (A.state(a.input),A.state(a.replacement),B.state(b.input),B.state(b.replacement))
        save(output,"snapshot-before.toml",metrics(pre))
        schedule=[("first",0,1),("first",0,2),("warm",0,2),("warm",0,1)]
        for pair in 1:4, side in (isodd(pair) ? (1,2) : (2,1))
            push!(schedule,("sample",pair,side))
        end
        index=0
        for kind in (Val(:zeros),Val(:constructor),Val(:dimensions),Val(:eligibility),Val(:original))
            name=string(typeof(kind).parameters[1])
            for (phase,pair,side) in schedule
                index+=1
                row=side==1 ? A.sample(kind,a) : B.sample(kind,b)
                merge!(row,Dict("index"=>index,"case"=>name,"phase"=>phase,"pair"=>pair,
                  "arm"=>(side==1 ? "reference" : "candidate")))
                push!(raw["records"],row);save(output,"record-$index.toml",row)
                require(row["assignment_ok"] && row["decision_ok"],"Incorrect observed result")
            end
        end
        post=@timed (A.state(a.input),A.state(a.replacement),B.state(b.input),B.state(b.replacement))
        save(output,"snapshot-after.toml",metrics(post))
        raw["input_unchanged"]=A.unchanged(pre.value[1],post.value[1]) && B.unchanged(pre.value[3],post.value[3])
        raw["replacement_unchanged"]=A.unchanged(pre.value[2],post.value[2]) && B.unchanged(pre.value[4],post.value[4])
        require(raw["input_unchanged"] && raw["replacement_unchanged"],"Input mutation")
        tc=@timed tests()
        save(output,"tests-cost.toml",metrics(tc));save(output,"tests.toml",tc.value)
        raw["tests"]=tc.value
        require(tests_ok(tc.value),"Structural tests failed")
        raw["complete"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace())
    finally
        save(output,"raw.toml",raw)
    end
    raw["complete"] || exit(2)
end
end
length(ARGS)==2 || error("Expected payload and stage")
ZeroDriver.main(ARGS[1],ARGS[2],Dict("seconds"=>LOAD_SECONDS,"bytes"=>LOAD_DIFF.allocd,
  "events"=>Base.gc_alloc_count(LOAD_DIFF),"gc_seconds"=>LOAD_DIFF.total_time/1e9,
  "compile_seconds"=>LOAD_COMPILE_DIFF[1]/1e9,"recompile_seconds"=>LOAD_COMPILE_DIFF[2]/1e9))

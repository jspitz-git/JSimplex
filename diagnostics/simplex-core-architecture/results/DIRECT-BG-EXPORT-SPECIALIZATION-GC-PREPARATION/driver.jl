# UNEXECUTED GC preparation amendment; same lifecycle and gates, separate run admission required.
using Test, LinearAlgebra, SparseArrays, TOML, PrecompileTools
using JSimplex
const J=JSimplex
length(ARGS)==3 || error("Exactly output/project/phase required")
const OUTPUT, PROJECT, PHASE=ARGS
PHASE in ("redgc300","greengc300") || error("Invalid phase")
const MODE=startswith(PHASE,"red") ? "red" : "green"
require(v,s)=v || error(s)
include("recorder.jl")
if MODE=="red"
    include("red-kernel.jl")
else
    include("green-kernel.jl")
    include("/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/direct-bg-export-specialized/reproduce/workspace-tests.jl")
    include("/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/direct-bg-export-specialized/reproduce/import-tests.jl")
    include("/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/direct-bg-export-specialized/reproduce/lifecycle-tests.jl")
    include("/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/direct-bg-export-specialized/reproduce/boundary-tests.jl")
end
include("preparation.jl")
function exact_tree(root,expected)
    length(root.children)==length(expected["groups"]) || return false
    root.passed==root.failed==root.errored==root.broken==0 || return false
    isempty(root.failures) || return false
    for (t,e) in zip(root.children,expected["groups"])
        isempty(t.children) || return false
        (t.description,t.passed,t.failed,t.errored,t.broken)==
            (e["name"],e["pass"],e["fail"],e["error"],e["broken"]) || return false
        length(t.failures)==t.failed+t.errored || return false
    end
    true
end
median7(x)=length(x)==7 ? sort(x)[4] : error("Expected seven observed samples")
function allocation_tests()
    source=TOML.parsefile(joinpath(@__DIR__,"inputs.toml"))["fixtures"]
    selected=[s for s in source if s["name"] in ("sparse32","dense32","sparse96")]
    require([s["name"] for s in selected]==["sparse32","dense32","sparse96"],"Fixture selection/order")
    for (cell,input) in enumerate(selected)
        f=decode_fixture(input);outputs=[zeros(f.n) for _ in 1:24]
        refs_bytes=Int[];cands_bytes=Int[];refs_events=Int[];cands_events=Int[]
        for pair in 1:10
            sides=isodd(pair) ? (Val(:reference),Val(:candidate)) : (Val(:candidate),Val(:reference))
            paired=Dict{String,Any}()
            for (order,side) in enumerate(sides)
                row=window(J.BartelsGolubFactorization,Val(:native),side,f,input,pair,order,outputs)
                save_window("window-$cell-$(2*(pair-1)+order).toml",row)
                require(row["correct"],"Correctness/mode/input failure")
                require(!row["measured"] || (row["compile_seconds"]==0 && row["recompile_seconds"]==0),"Measured compilation")
                paired[row["side"]]=row
                if pair>3
                    push!(side===Val(:reference) ? refs_bytes : cands_bytes,row["bytes"])
                    push!(side===Val(:reference) ? refs_events : cands_events,row["events"])
                end
            end
            require(paired["reference"]["outputs"]==paired["candidate"]["outputs"] && paired["reference"]["modes"]==paired["candidate"]["modes"],"Paired output/mode mismatch")
            pair == 3 && prepare_gc!(cell,f.name)
        end
        @testset "allocation_nonincrease_$(f.name)" begin
            @test median7(cands_events)<=median7(refs_events) && median7(cands_bytes)<=median7(refs_bytes)
        end
    end
end
function main()
    raw=Dict{String,Any}("phase"=>PHASE,"complete"=>false,"fatal"=>"")
    root=RecordedTests.Capture("root")
    try
        require(realpath(pathof(J))==realpath(joinpath(PROJECT,"src/JSimplex.jl")),"Wrong package source")
        require(Threads.nthreads()==BLAS.get_num_threads()==1 && !PrecompileTools.verbose[],"Thread/precompile configuration")
        raw["loaded"]=Dict(string(nameof(m))=>realpath(pathof(m)) for m in
            (J,SparseArrays,LinearAlgebra,TOML,Test,PrecompileTools))
        raw["threads"]=Threads.nthreads();raw["blas_threads"]=BLAS.get_num_threads()
        println(stderr,"BEGIN BG specialization driver ",PHASE);flush(stderr)
        Test.@with_testset root begin
            if MODE=="green"
                BGSpecializedExportWorkspaceTests.run_workspace_tests()
                BGSpecializedExportImportTests.run_import_tests()
                BGSpecializedExportLifecycleTests.run_lifecycle_tests()
                BGSpecializedBoundaryTests.run_boundary_tests()
            end
            allocation_tests()
        end
        require(PREPARATION_CALLS[] == PREPARATION_COMPLETED[] == 3,"Preparation count")
        raw["complete"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace());println(stderr,"FATAL DRIVER: ",raw["fatal"]);flush(stderr)
    finally
        raw["preparation_calls"]=PREPARATION_CALLS[]
        raw["preparations_completed"]=PREPARATION_COMPLETED[]
        raw["tests"]=RecordedTests.dictionary(root)
        save_window("raw.toml",raw)
    end
    expected=TOML.parsefile(joinpath(@__DIR__,"expected-tests.toml"))[MODE]
    valid=raw["complete"] && isempty(raw["fatal"]) && exact_tree(root,expected)
    valid || (println(stderr,"GROUP/COUNT MISMATCH OR FATAL");flush(stderr))
    exit(valid ? (MODE=="red" ? 1 : 0) : 2)
end
main()

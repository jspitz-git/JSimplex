# UNEXECUTED; exactly one phase per separately admitted ordinary Julia process.
using Test, LinearAlgebra, SparseArrays, TOML, PrecompileTools
PrecompileTools.verbose[] && error("Unexpected precompile verbosity")
using JSimplex
include(joinpath(@__DIR__,"recorder.jl"))
const TEST_DIR=normpath(joinpath(@__DIR__,"../../../direct-lu-policy-adapters/reproduce"))
const GREEN_FUNCTIONS=(:test_exports,:test_export_rejections,:test_scale_selection,
    :test_normalization_and_scaling,:test_lifecycles,:test_fallback_transitions,
    :test_policy_transitions,:test_policy_rejections_and_forwarders,:test_generic_policy_forwarding)
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
    return true
end
function main()
    output,project,phase=ARGS
    phase in ("red300","green300","red600","green600") || error("Invalid phase")
    mode=startswith(phase,"red") ? "red" : "green"
    raw=Dict{String,Any}("phase"=>phase,"complete"=>false,"fatal"=>"")
    root=RecordedTests.Capture("root")
    try
        realpath(pathof(JSimplex))==realpath(joinpath(project,"src/JSimplex.jl")) || error("Wrong package source")
        Threads.nthreads()==BLAS.get_num_threads()==1 || error("Thread count")
        raw["loaded"]=Dict(string(nameof(m))=>realpath(pathof(m)) for m in
            (JSimplex,SparseArrays,LinearAlgebra,TOML,Test,PrecompileTools))
        raw["threads"]=Threads.nthreads();raw["blas_threads"]=BLAS.get_num_threads()
        println(stderr,"BEGIN adapter driver ",phase);flush(stderr)
        if mode=="red"
            include(joinpath(TEST_DIR,"red.jl"))
            Test.@with_testset root begin
                Base.invokelatest(run_direct_lu_policy_red)
            end
        else
            include(joinpath(TEST_DIR,"lifecycle-tests.jl"))
            include(joinpath(TEST_DIR,"policy-tests.jl"))
            Test.@with_testset root begin
                for name in GREEN_FUNCTIONS
                    println(stderr,"BEGIN ",name);flush(stderr)
                    Base.invokelatest(getfield(@__MODULE__,name))
                    println(stderr,"END ",name);flush(stderr)
                end
            end
        end
        raw["complete"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace());println(stderr,"FATAL DRIVER: ",raw["fatal"]);flush(stderr)
    finally
        raw["tests"]=RecordedTests.dictionary(root)
        p=joinpath(output,"raw.toml");ispath(p) && error("raw exists")
        open(p,"w") do io;TOML.print(io,raw);flush(io);end
    end
    # Preserve raw BEFORE aggregate validation. Expected RED failures exit1.
    expected=TOML.parsefile(joinpath(@__DIR__,"expected-tests.toml"))[mode]
    valid=raw["complete"] && isempty(raw["fatal"]) && exact_tree(root,expected)
    valid || (println(stderr,"GROUP/COUNT MISMATCH OR FATAL");flush(stderr))
    exit(valid ? (mode=="red" ? 1 : 0) : 2)
end
main()

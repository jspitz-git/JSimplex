# UNEXECUTED focused actual-master entry; no production instrumentation.
using Test, LinearAlgebra, SparseArrays, TOML, PrecompileTools
PrecompileTools.verbose[] && error("Unexpected precompile verbosity")
using JSimplex
include(joinpath(@__DIR__,"recorder.jl"))
const EXPECTED = ["options_and_copy_intent"=>4946,"backend_owned_policy"=>35,
    "private_spare_copy_and_failure"=>1568,"precision_and_factory_dispatch"=>245,
    "Native pivot policy public integration"=>48,"Native pivot policy private recovery"=>114]
passed(t)=t.passed+sum(passed(c) for c in t.children;init=0)
failed(t)=t.failed+t.errored+t.broken+sum(failed(c) for c in t.children;init=0)
function main()
    output,project=ARGS
    raw=Dict{String,Any}("complete"=>false,"fatal"=>"")
    root=RecordedTests.Capture("root")
    try
        realpath(pathof(JSimplex))==realpath(joinpath(project,"src/JSimplex.jl")) || error("Wrong package source")
        Threads.nthreads()==BLAS.get_num_threads()==1 || error("Thread count")
        raw["loaded"]=Dict("JSimplex"=>realpath(pathof(JSimplex)),"SparseArrays"=>realpath(pathof(SparseArrays)),"LinearAlgebra"=>realpath(pathof(LinearAlgebra)),"TOML"=>realpath(pathof(TOML)))
        raw["threads"]=Threads.nthreads();raw["blas_threads"]=BLAS.get_num_threads()
        Test.@with_testset root begin
            for name in ("native_pivot_policy_tests.jl","native_pivot_integration_tests.jl")
                println(stderr,"BEGIN ",name);flush(stderr)
                include(joinpath(project,"test",name))
                println(stderr,"END ",name);flush(stderr)
            end
        end
        [(t.description=>passed(t)) for t in root.children]==EXPECTED || error("Group/count mismatch")
        failed(root)==0 || error("Test failure")
        raw["complete"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace());println(stderr,raw["fatal"]);flush(stderr)
    finally
        raw["tests"]=RecordedTests.dictionary(root)
        p=joinpath(output,"raw.toml");ispath(p) && error("raw exists")
        open(p,"w") do io;TOML.print(io,raw);end
    end
    exit(raw["complete"] && isempty(raw["fatal"]) && passed(root)==6956 && failed(root)==0 ? 0 : 1)
end
main()

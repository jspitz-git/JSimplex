# UNEXECUTED ordinary installed-package loader. No full-module clone.
using Test, LinearAlgebra, SparseArrays, TOML, PrecompileTools
PrecompileTools.verbose[] && error("Unexpected precompile verbosity")
using JSimplex
include(joinpath(@__DIR__,"test-support.jl"))
module RecordedTests
using Test
mutable struct Capture <: Test.AbstractTestSet
    description::String
    passed::Int
    failed::Int
    errored::Int
    broken::Int
    failures::Vector{String}
    children::Vector{Capture}
end
Capture(s;kwargs...)=Capture(s,0,0,0,0,String[],Capture[])
Test.record(t::Capture,r::Test.Pass)=(t.passed+=1)
Test.record(t::Capture,r::Test.Fail)=(t.failed+=1;push!(t.failures,sprint(show,r)))
Test.record(t::Capture,r::Test.Error)=(t.errored+=1;push!(t.failures,sprint(show,r)))
Test.record(t::Capture,r::Test.Broken)=(t.broken+=1)
Test.record(t::Capture,r::Capture)=push!(t.children,r)
function Test.finish(t::Capture)
    Test.get_testset_depth()>0 && Test.record(Test.get_testset(),t)
    t
end
function dictionary(t)
    Dict("name"=>t.description,"pass"=>t.passed,"fail"=>t.failed,"error"=>t.errored,"broken"=>t.broken,"failures"=>t.failures,"children"=>dictionary.(t.children))
end
end
function main()
    output,phase,project=ARGS
    raw=Dict{String,Any}("phase"=>phase,"complete"=>false,"fatal"=>"","counts"=>NP.counts)
    root=RecordedTests.Capture("root");Test.push_testset(root)
    try
        NP.need(realpath(pathof(JSimplex))==realpath(joinpath(project,"src/JSimplex.jl")),"Wrong package source")
        NP.need(Threads.nthreads()==BLAS.get_num_threads()==1,"Thread count")
        raw["loaded"]=Dict("JSimplex"=>realpath(pathof(JSimplex)),"SparseArrays"=>realpath(pathof(SparseArrays)),"LinearAlgebra"=>realpath(pathof(LinearAlgebra)),"TOML"=>realpath(pathof(TOML)))
        raw["threads"]=Threads.nthreads();raw["blas_threads"]=BLAS.get_num_threads()
        if phase=="red"
            include(joinpath(@__DIR__,"red-contract.jl"))
        elseif phase=="green"
            include(joinpath(@__DIR__,"tests-observed.jl"))
            raw["main_counts"]=copy(NP.counts)
            include(joinpath(@__DIR__,"neighbors-observed.jl"))
        else
            error("Unknown phase")
        end
        raw["complete"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace());println(stderr,raw["fatal"])
    finally
        Test.pop_testset();raw["tests"]=RecordedTests.dictionary(root)
        raw["events"]=NP.events[1:NP.used[]]
        raw["equations"]=NP.equations[1:NP.equation_count[]]
        raw["observation_limit"]=length(NP.events)
        p=joinpath(output,"raw.toml");NP.need(!ispath(p),"raw exists")
        open(p,"w") do io;TOML.print(io,raw);end
    end
    # Exact result qualification lives in independent auditor; raw precedes exit.
    function failed(t)
        t.failed+t.errored+t.broken+sum(failed(c) for c in t.children;init=0)
    end
    exit(raw["complete"] && isempty(raw["fatal"]) && failed(root)==0 ? 0 : 1)
end
main()

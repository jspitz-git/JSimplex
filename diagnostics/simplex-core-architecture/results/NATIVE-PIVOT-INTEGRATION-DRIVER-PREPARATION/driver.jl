# UNEXECUTED. One ordinary installed-package load and one fixed integration suite.
using Test, LinearAlgebra, SparseArrays, TOML, PrecompileTools
PrecompileTools.verbose[] && error("Unexpected precompile verbosity")
include(joinpath(@__DIR__,"probe.jl"))
using JSimplex
include(joinpath(@__DIR__,"recorder.jl"))
const NP=NativePivotIntegrationProbe
function main()
    output,phase,project=ARGS
    raw=Dict{String,Any}("phase"=>phase,"complete"=>false,"fatal"=>"")
    root=RecordedTests.Capture("root")
    try
        NP.need(phase=="integration","wrong phase")
        NP.need(realpath(pathof(JSimplex))==realpath(joinpath(project,"src/JSimplex.jl")),"Wrong package source")
        NP.need(Threads.nthreads()==BLAS.get_num_threads()==1,"Thread count")
        raw["loaded"]=Dict("JSimplex"=>realpath(pathof(JSimplex)),"SparseArrays"=>realpath(pathof(SparseArrays)),"LinearAlgebra"=>realpath(pathof(LinearAlgebra)),"TOML"=>realpath(pathof(TOML)))
        raw["threads"]=Threads.nthreads();raw["blas_threads"]=BLAS.get_num_threads()
        Test.@with_testset root begin
            include(joinpath(@__DIR__,"observed-tests.jl"))
        end
        raw["complete"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace());println(stderr,raw["fatal"])
    finally
        raw["tests"]=RecordedTests.dictionary(root)
        raw["cases"]=NP.snapshot()
        raw["started"]=NP.started[];raw["active"]=NP.active[];raw["probe_failed"]=NP.failed[]
        raw["selected_scope"]="managed Float64 UMFPACK backend attempts; extracted-factor and raw auxiliary LU work excluded"
        p=joinpath(output,"raw.toml");ispath(p) && error("raw exists")
        open(p,"w") do io;TOML.print(io,raw);end
    end
    function failed(t)
        t.failed+t.errored+t.broken+sum(failed(c) for c in t.children;init=0)
    end
    exit(raw["complete"] && isempty(raw["fatal"]) && !NP.failed[] && NP.started[]==9 && NP.active[]==0 && failed(root)==0 ? 0 : 1)
end
main()

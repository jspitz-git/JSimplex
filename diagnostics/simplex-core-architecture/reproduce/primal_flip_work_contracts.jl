# Same work contract that failed on unchanged control; private candidate only.
using Test,JSimplex,LinearAlgebra,TOML
include("primal_flip_prototype.jl")
const FA=PrimalFlipPrototype
const JS=JSimplex
@assert Threads.nthreads()==BLAS.get_num_threads()==1
const OUTPUT=only(ARGS)
ispath(OUTPUT) && error("Do not overwrite an attempt")
const RECORD=Dict{String,Any}("mode"=>"private_candidate", "prototype_implemented"=>true,
    "source_hashes"=>FA.SOURCE_HASHES,"rewritten_hashes"=>FA.REWRITTEN_HASHES)
try
    @testset "Audited flip work contract" begin
        result=FA.run_flip_experiment!(Float64,:flip_chain)
        run,calls=result.run,result.calls
        @test run.status==JS.OPTIMAL
        @test run.primal==ones(4) && run.objective_value==-10.0
        @test result.feasible
        @test getproperty.(result.events,:event)==fill("flip_completed",4)
        @test result.basis_unchanged && result.prices_unchanged
        @test result.iterations==4 && result.updates==0
        RECORD["status"]=string(run.status)
        RECORD["kernel_calls"]=Dict(string(k)=>v for (k,v) in calls)
        RECORD["stats"]=Dict(string(k)=>v for (k,v) in pairs(result.stats))
        RECORD["iterations"]=result.iterations
        RECORD["primal"]=run.primal
        @test calls[:ftran]==5
        @test calls[:btran]==1
        @test result.enabled && !result.stats.dirty
        @test result.stats.applied==result.stats.audits==result.stats.skips==4
        @test result.stats.endpoint_refreshes==result.stats.direct_recomputations==1
        @test result.stats.candidate_copies==1 && result.stats.fallbacks==0
    end
finally
    open(io->TOML.print(io,RECORD),OUTPUT,"w")
end

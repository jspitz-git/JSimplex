# Deliberate owned fault between iterations; production helper methods unchanged.
using Test,JSimplex,LinearAlgebra,TOML
include("primal_flip_prototype.jl")
const FA=PrimalFlipPrototype
const JS=JSimplex
@assert Threads.nthreads()==BLAS.get_num_threads()==1
rows=Dict[]
try
@testset "Dirty early entry refresh" begin
    for fault in (:nonfinite,:infeasible),expired in (false,true)
        f=FA.PF.workspace(Float64,:flip_chain)
        c=FA.FlipAuditContext(f.ws);stop=FA.PF.deadline(f.ws,f.diagnostics)
        @test isnothing(FA._flip_iteration!(c,f.ws,stop,f.ws.options.dual_tolerance))
        @test c.dirty && c.skips==1 && f.ws.iterations==1
        f.ws.primal[end]=fault==:nonfinite ? NaN : -1.0
        final_stop=expired ? JS._guard_stop_callback(()->true) : stop
        terminal=FA._flip_optimize!(c,f.ws,final_stop,f.ws.options.dual_tolerance;perturb_degenerate=false)
        run=JS._internal_solution(f.ws,terminal)
        if expired
            @test run.status==JS.TIME_LIMIT && isnothing(run.primal)
            @test c.dirty && c.direct_recomputations==c.endpoint_refreshes==0
            @test f.ws.iterations==1
        else
            @test run.status==JS.OPTIMAL && run.primal==ones(4) && run.objective_value==-10
            @test JS._original_primal_feasible(f.problem,run.primal,f.ws.options.primal_tolerance)
            @test !c.dirty && c.direct_recomputations==c.endpoint_refreshes==2
            @test f.ws.iterations==4 && c.applied==4
        end
        push!(rows,Dict("fault"=>string(fault),"expired"=>expired,"status"=>string(run.status),
            "refreshes"=>c.endpoint_refreshes,"iterations"=>f.ws.iterations))
    end
end
finally
    open(io->TOML.print(io,Dict("cases"=>rows,"source_hashes"=>FA.SOURCE_HASHES)),only(ARGS),"w")
end

# Production-only continuations of the fresh FT and SS mismatch captures.
using Test,JSimplex,Serialization,LinearAlgebra
BLAS.set_num_threads(1)
@testset "Captured reliable-BTRAN price disagreement" begin
    for prefix in ARGS
        ws=deserialize(prefix*"-rejected.bin");data=deserialize(prefix*"-direction.bin")
        iterations=ws.iterations
        B=JSimplex.basis_matrix(ws);rhs=ws.costs[ws.basis.basic_indices]
        dual=similar(rhs);JSimplex.transpose_solve!(dual,ws.factorization,rhs)
        quality=JSimplex._compensated_solve_quality!(JSimplex.SolveQualityScratch(Float64,length(rhs)),
            B,dual,rhs,ws.progress.numerical_policy,true)
        @test quality.reliable && quality.absolute_error>0
        @test JSimplex._legacy_primal_point_certified(ws)
        terminal=JSimplex._primal_iteration!(ws,()->false,data.tolerance,true)
        @test !isnothing(terminal) && terminal.status==OPTIMAL
        @test ws.iterations==iterations
        @test JSimplex._legacy_primal_point_certified(ws)
        @test JSimplex._original_optimality_certified(ws,ws.primal[1:size(ws.problem.A,2)])
        println("AUXILIARY_OPTIMAL ",prefix," iteration=",ws.iterations)
    end
end

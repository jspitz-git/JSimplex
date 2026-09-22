module BasisRecoveryReplayTests
using Test, JSimplex
include("../simplex_replay.jl")

@testset "Replay overlays invalidate initialization checkpoints" begin
    mktempdir() do root
        p = LinearProblem(JSimplex.sparse([1.0;;]),[1.0])
        ws = JSimplex.initialize_workspace(p,SolverOptions(verbose=false,simplex_strategy=:adaptive))
        ws.costs[1] = 7.0
        path = joinpath(root,"working-costs.bin")
        JSimplexReplay.save_snapshot(path,ws;original_hash=repeat("c",64))
        restored,_ = JSimplexReplay.load_snapshot(path)
        @test length(restored.scratch.checkpoints) == 1
        @test all(c.costs == restored.costs for c in restored.scratch.checkpoints)
    end
end

@testset "Explicit replay recovery exchanges a singular basis" begin
    mktempdir() do root
        p = LinearProblem(JSimplex.sparse([1.0 1.0;1.0 1.0]),[0.0,0.0];
            column_lower=[1.0,0.0],row_lower=[1.0,2.0])
        ws = JSimplex.initialize_workspace(p,SolverOptions(verbose=false,pricing=:dantzig,simplex_strategy=:adaptive))
        ws.basis.basic_indices .= [1,2]
        ws.basis.states .= [JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER]
        ws.iterations,ws.refactorizations = 11,7
        path = joinpath(root,"singular-basis.bin")
        JSimplexReplay.save_snapshot(path,ws;original_hash=repeat("d",64))
        saved = read(path)
        @test_throws JSimplex.SingularException JSimplexReplay.load_snapshot(path)
        restored,metadata = JSimplexReplay.load_snapshot(path;repair_basis=true)
        @test metadata["basis_repaired"]
        @test restored.iterations == 11 && restored.refactorizations == 9
        @test restored.basis.basic_indices != [1,2]
        @test read(path) == saved
        result = JSimplex._solve_continuous_dual!(restored,()->false)
        @test result.status == OPTIMAL
        @test result.iterations == 11
        @test result.objective_value == 0.0
    end
end
end

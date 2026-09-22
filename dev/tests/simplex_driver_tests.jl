module SimplexDriverReplayTests
using Test, JSimplex
include("../simplex_replay.jl")

@testset "Replay dispatches a recovered primal snapshot to dual" begin
    mktempdir() do root
        p = LinearProblem(JSimplex.sparse([1.0;;]),[1.0];row_lower=[1.0])
        o = SolverOptions(verbose=false,algorithm=:primal,simplex_strategy=:adaptive)
        w = JSimplex.initialize_workspace(p,o)
        w.iterations = 7
        path = joinpath(root,"snapshot.bin")
        JSimplexReplay.save_snapshot(path,w;original_hash=repeat("e",64))
        restored,_ = JSimplexReplay.load_snapshot(path)
        run = JSimplexReplay.run_replay!(restored,()->false)
        @test run.status == OPTIMAL
        @test run.objective_value == 1.0
        @test run.iterations == 8
        @test JSimplex.event_count(restored.progress.diagnostics,:phase_dual) > 0
    end
end
@testset "Snapshots retain outer retry work offsets" begin
    mktempdir() do root
        p = LinearProblem(JSimplex.sparse([1.0;;]),[1.0];row_lower=[1.0])
        o = SolverOptions(verbose=false,simplex_strategy=:adaptive)
        w = JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;
            iteration_offset=11,refactorization_offset=5,
            numerical_policy=JSimplex.NumericalPolicy(Float64,o)))
        w.iterations = 7
        w.refactorizations = 3
        path = joinpath(root,"snapshot.bin")
        JSimplexReplay.save_snapshot(path,w;original_hash=repeat("f",64))
        restored,_ = JSimplexReplay.load_snapshot(path)
        @test restored.progress.iteration_offset == 11
        @test restored.progress.refactorization_offset == 5
        b = JSimplex.SimplexRunBudget(restored)
        @test b.iterations == 18
        @test b.refactorizations == 9
    end
end
end

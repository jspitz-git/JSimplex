using JSimplex.SparseArrays
using JSimplex.LinearAlgebra

@testset "Legacy degeneracy preserves pricing and costs while feasibility improves" begin
    for pricing in (:steepest_edge, :devex, :dantzig), streak in (255, 1023)
        problem = LinearProblem(sparse(Matrix{Float64}(I, 3, 3)), zeros(3);
            row_lower=ones(3))
        ws = JSimplex.initialize_workspace(problem,
            SolverOptions(simplex_strategy=:legacy, pricing=pricing, verbose=false))
        ws.zero_dual_step_streak = streak
        @test JSimplex.primal_infeasibility(ws) == 3.0
        @test isnothing(JSimplex.dual_iteration!(ws, () -> false))
        @test JSimplex.primal_infeasibility(ws) == 2.0
        @test JSimplex.dual_infeasibility(ws) == 0.0
        @test JSimplex._effective_pricing(ws, :dual) == pricing
        @test !ws.dual_pricing_fallback
        @test !ws.perturbed
        @test all(iszero, ws.costs)
    end
end

@testset "Legacy productive cycles respect the configured update ceiling" begin
    for update in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
        rows = 24
        problem = LinearProblem(sparse(Matrix{Float64}(I, rows, rows)),
            collect(1.0:rows); row_lower=ones(rows))
        ws = JSimplex.initialize_workspace(problem,
            SolverOptions(simplex_strategy=:legacy, basis_update=update,
                refactorization_interval=2, verbose=false))
        for _ in 1:rows
            @test isnothing(JSimplex.dual_iteration!(ws, () -> false))
            @test length(ws.factorization.updates) < 2
        end
        @test ws.refactorizations == 12
        @test ws.dual_refactorization_interval == 2
        @test JSimplex.primal_infeasibility(ws) == 0.0
        @test JSimplex.dual_infeasibility(ws) == 0.0
    end
end

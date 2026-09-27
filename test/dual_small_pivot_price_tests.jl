using JSimplex, Test, SparseArrays

@testset "Certified forward small-pivot prices drive the dual update" begin
    # Roundoff smaller than dual tolerance becomes significant after division
    # by a near-cutoff pivot (as in the Windows runtime.mps capture at 45538).
    coefficient = 1.2175185313102243e-7
    cost = 2.25893104810974e-10
    stored_cost = 2.266913543e-10
    for manager in (:pfi, :bartels_golub, :forrest_tomlin, :suhl_suhl), upper in (false, true)
        problem = LinearProblem(sparse([coefficient;;]), [upper ? -cost : cost];
            row_lower=[upper ? -Inf : 1.0], row_upper=[upper ? -1.0 : Inf],
            column_lower=[upper ? -Inf : 0.0], column_upper=[upper ? 0.0 : Inf])
        options = SolverOptions(algorithm=:dual, simplex_strategy=:legacy,
            basis_update=manager, verbose=false)
        ws = JSimplex.initialize_workspace(problem, options)
        ws.reduced_costs[1] = upper ? -stored_cost : stored_cost
        @test abs(ws.reduced_costs[1] - problem.objective[1]) < options.dual_tolerance
        @test isnothing(JSimplex.dual_iteration!(ws, () -> false))
        @test ws.basis.basic_indices == [1]
        @test ws.costs == [problem.objective[1], 0.0]
        expected = problem.objective[1] / coefficient
        @test isapprox(ws.reduced_costs[2], expected; atol=1e-12, rtol=1e-12)
        @test JSimplex.dual_infeasibility(ws) <= options.dual_tolerance
    end
end

@testset "Certified small-pivot price with a preceding bound flip" begin
    coefficient = 1.2175185313102243e-7
    cost = 2.25893104810974e-10
    for manager in (:pfi, :bartels_golub, :forrest_tomlin, :suhl_suhl), upper in (false, true)
        direction = upper ? -1.0 : 1.0
        problem = LinearProblem(sparse([coefficient 1.0]), direction .* [cost, 0.001];
            row_lower=[upper ? -Inf : 1.0], row_upper=[upper ? -1.0 : Inf],
            column_lower=upper ? [-Inf, -0.1] : [0.0, 0.0],
            column_upper=upper ? [0.0, 0.0] : [Inf, 0.1])
        ws = JSimplex.initialize_workspace(problem, SolverOptions(algorithm=:dual,
            simplex_strategy=:legacy, basis_update=manager, verbose=false))
        ws.basis.states[2] = upper ? JSimplex.AT_UPPER : JSimplex.AT_LOWER
        JSimplex.recompute!(ws)
        ws.reduced_costs[1] = direction * 2.266913543e-10
        @test isnothing(JSimplex.dual_iteration!(ws, () -> false))
        @test ws.basis.basic_indices == [1]
        @test ws.basis.states[2] == (upper ? JSimplex.AT_LOWER : JSimplex.AT_UPPER)
        @test ws.primal[2] == direction * 0.1
        @test ws.costs == [problem.objective; 0.0]
        dual = problem.objective[1] / coefficient
        @test ws.reduced_costs ≈ [0.0, problem.objective[2] - dual, dual] atol=1e-12
        @test JSimplex.dual_infeasibility(ws) <= ws.options.dual_tolerance
    end
end

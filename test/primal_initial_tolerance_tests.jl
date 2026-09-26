using JSimplex.SparseArrays

@testset "Legacy primal solves a feasible model with a tolerated initial row violation" begin
    # The zero-cost third column allows x2 to reach its upper bound.
    for sign in (1.0, -1.0)
        problem = LinearProblem(sparse(sign .* [-7e-8 -0.01 1.0]), [0.0, -1.0, 0.0];
            row_lower=[sign > 0 ? 0.0 : -Inf], row_upper=[sign > 0 ? Inf : 0.0],
            column_lower=[1.0, 0.0, 0.0], column_upper=[1.0, 1.0, 1.0])
        options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy,
            basis_update=:bartels_golub, presolve=false, scaling=:off, verbose=false)
        result = solve(problem; options)
        @test result.status == OPTIMAL
        if result.status == OPTIMAL
            @test result.objective_value ≈ -1.0
            @test result.primal[2] ≈ 1.0
            @test JSimplex._original_primal_feasible(problem, result.primal, options.primal_tolerance)
        end
    end
end

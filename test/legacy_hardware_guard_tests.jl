using JSimplex.SparseArrays

@testset "Legacy hardware guards leave other scalar workspaces untouched" begin
    for T in (BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(reshape(T[1], 1, 1)), T[-1];
            row_lower=T[0], row_upper=T[1], column_lower=T[0], column_upper=T[2])
        options = SolverOptions(T; algorithm=:primal, simplex_strategy=:legacy,
            presolve=false, scaling=:off, verbose=false)
        ws = JSimplex.initialize_workspace(problem, options)
        saved = copy(ws.primal)
        rho, rhs = copy(ws.scratch.rho), copy(ws.scratch.row_rhs)
        cache = ws.scratch.pivot_quality_cache
        destination = T[3]
        stop = () -> error("hardware-only helper called an excluded callback")
        @test !JSimplex._legacy_primal_row_validation_enabled(ws)
        @test !JSimplex._can_preserve_primal_row_value(ws, 2, JSimplex.AT_LOWER, ws.lower[2])
        @test isnothing(JSimplex._legacy_primal_point_candidate(ws, 1, 1, zero(T), T[1]))
        @test !JSimplex._restore_legacy_primal_point!(ws, T[1], stop)
        @test !JSimplex._legacy_primal_row_consistent(ws, options.primal_tolerance)
        @test !JSimplex._legacy_primal_pivot_row_ok!(ws, 1, 1, one(T), stop)
        for transposed in (false, true)
            @test !JSimplex._try_native_dual_correction!(ws, destination, 1, 1, stop; transposed)
        end
        @test destination == T[3]
        @test ws.primal == saved
        @test ws.scratch.rho == rho && ws.scratch.row_rhs == rhs
        @test ws.scratch.pivot_quality_cache === cache

        for algorithm in (:primal, :dual), strategy in (:legacy, :adaptive)
            run_options = SolverOptions(T; algorithm, simplex_strategy=strategy,
                presolve=false, scaling=:off, verbose=false)
            result = solve(problem; options=run_options)
            @test result.status == OPTIMAL
            @test result.primal == T[1]
            @test result.objective_value == -one(T)
            @test JSimplex._original_primal_feasible(problem, result.primal,
                run_options.primal_tolerance)
        end
    end
end

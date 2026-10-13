using Test, JSimplex, SparseArrays

@testset "Exact activity fallback distinguishes cancellation from an unrepresentable row" begin
    for T in (Float32, Float64)
        limit = floatmax(T)
        options = SolverOptions(T; verbose=false)
        for sign in (-one(T), one(T))
            overflow = LinearProblem(sparse(reshape(T[sign*limit], 1, 1)), T[0])
            ws = JSimplex.initialize_workspace(overflow, options)
            ws.primal[1] = T(2)
            @test !JSimplex._original_primal_feasible(overflow, T[2], options.primal_tolerance)
            run = JSimplex._internal_solution(ws, OPTIMAL, "candidate")
            @test run.status == NUMERICAL_ERROR
            @test isnothing(run.primal)
            @test isnothing(run.objective_value)

            # Exact activity is outside the finite range even though nearest
            # rounding of this final sum alone would return a finite endpoint.
            beyond = LinearProblem(sparse(reshape(T[sign*limit, sign], 1, 2)), T[0, 0])
            @test !JSimplex._original_primal_feasible(beyond, T[1, 1], options.primal_tolerance)
        end
        # Individual products overflow, but the stored binary model has the
        # exactly representable activity 3. Blanket rejection loses this case.
        cancelled = LinearProblem(sparse(reshape(T[limit, -limit, 1], 1, 3)), T[0, 0, 0];
            row_lower=T[3], row_upper=T[3])
        @test JSimplex._original_primal_feasible(cancelled, T[2, 2, 3], options.primal_tolerance)
    end
end

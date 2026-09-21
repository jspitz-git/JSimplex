using SparseArrays

@testset "Singleton pass avoids unused column-bound copies" begin
    problem = LinearProblem(sparse(ones(128, 128)), ones(128))
    JSimplex.reduce_singleton_rows(problem)
    @test (@allocated JSimplex.reduce_singleton_rows(problem)) <= 9_000
end

@testset "Singleton bounds are copied independently on first tightening" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for tighten_lower in (false, true)
            problem = LinearProblem(sparse(reshape(T[1, 1], 2, 1)), T[1];
                row_lower=tighten_lower ? T[2, 3] : [nothing, nothing],
                row_upper=tighten_lower ? [nothing, nothing] : T[8, 7],
                column_lower=T[0], column_upper=T[10])
            result = JSimplex.reduce_singleton_rows(problem)
            @test size(result.problem.A) == (0, 1)
            @test bound_value.(result.problem.column_lower) == (tighten_lower ? T[3] : T[0])
            @test bound_value.(result.problem.column_upper) == (tighten_lower ? T[10] : T[7])
            @test result.problem.column_lower !== problem.column_lower
            @test result.problem.column_upper !== problem.column_upper
            step = only(result.postsolve_stack)
            @test step.lower_sources == (tighten_lower ? [(2, JSimplex.AT_LOWER)] : [nothing])
            @test step.upper_sources == (tighten_lower ? [nothing] : [(2, JSimplex.AT_UPPER)])
            result.problem.column_lower[1] = Bound(T(-1))
            result.problem.column_upper[1] = Bound(T(20))
            @test bound_value.(problem.column_lower) == T[0]
            @test bound_value.(problem.column_upper) == T[10]
        end
    end
end

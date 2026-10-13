using SparseArrays

@testset "Basic presolve converts an eliminated value once per column" begin
    count = 256
    A = hcat(sparse(ones(count, 1)), sparse(1:count, 1:count, ones(count), count, count))
    for (value, budget) in ((0.5, 1_020_000), (0.0, 320_000))
        problem = LinearProblem(A, [2.0; ones(count)];
            row_lower=ones(count), row_upper=fill(3.0, count),
            column_lower=[value; zeros(count)], column_upper=[value; fill(2.0, count)])
        JSimplex._presolve_basic(problem)
        @test (@allocated JSimplex._presolve_basic(problem)) <= budget
    end
end

@testset "Cached values remain local to each eliminated column" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), explicit in (false, true)
        A = sparse(T[2 1 1; -1 2 1; 0 4 -1])
        problem = LinearProblem(A, T[4, -3, 2]; objective_constant=T(7),
            row_lower=T[1, 2, 3], row_upper=T[9, 10, 11],
            column_lower=[T(0.5), T(-2), nothing],
            column_upper=[T(0.5), T(-2), nothing])
        original = deepcopy(problem)
        selections = explicit ? [(T(0.5), JSimplex.AT_LOWER),
                                  (T(-2), JSimplex.AT_UPPER), nothing] : nothing
        result = JSimplex._presolve_basic(problem; selections)
        @test result.problem.A == reshape(T[1, 1, -1], 3, 1)
        @test result.problem.objective == T[2]
        @test result.problem.objective_constant == T(15)
        @test bound_value.(result.problem.row_lower) == T[2, 6.5, 11]
        @test bound_value.(result.problem.row_upper) == T[10, 14.5, 19]
        step = only(result.postsolve_stack)
        @test step.columns == [3]
        @test step.removed_states[2] == (explicit ? JSimplex.AT_UPPER : JSimplex.AT_LOWER)
        @test JSimplex.postsolve_primal(result, T[3]) == T[0.5, -2, 3]
        @test problem.A == original.A
        @test problem.objective == original.objective
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
    end
end

@testset "Eliminated BigFloat values retain input precision" begin
    problem = setprecision(BigFloat, 256) do
        value = one(BigFloat) + BigFloat(2)^(-200)
        LinearProblem(sparse(BigFloat[1 1]), BigFloat[0, 1];
            row_lower=[value], row_upper=[value],
            column_lower=[value, nothing], column_upper=[value, nothing])
    end
    original = deepcopy(problem)
    setprecision(BigFloat, 64) do
        result = JSimplex._presolve_basic(problem)
        @test only(result.postsolve_stack).columns == [2]
        @test iszero(bound_value(only(result.problem.row_lower)))
        @test iszero(bound_value(only(result.problem.row_upper)))
        restored = JSimplex.postsolve_primal(result, BigFloat[0])
        @test restored[1] == bound_value(original.column_lower[1])
        @test precision(restored[1]) == 256
        @test problem.column_lower == original.column_lower
        @test problem.row_lower == original.row_lower
    end
end

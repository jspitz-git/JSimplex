using SparseArrays

@testset "Negative unit parallel bounds avoid rational division" begin
    count = 128
    for (kind, limit) in ((:negative, 14_000), (:zero, 13_000), (:unit, 11_300),
                           (:positive, 16_900), (:nonunit, 16_900))
        pivot = kind == :unit ? 1.0 : kind == :positive ? 2.0 : kind == :nonunit ? -2.0 : -1.0
        endpoint = kind == :zero ? 0.0 : pivot
        problem = LinearProblem(sparse(repeat([pivot 2pivot -pivot], count, 1)), zeros(3);
            row_lower=fill(min(endpoint, 6pivot), count),
            row_upper=fill(max(endpoint, 6pivot), count), column_lower=fill(nothing, 3))
        JSimplex.reduce_parallel_rows(problem)
        measured = @timed JSimplex.reduce_parallel_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test only(JSimplex.reduce_parallel_rows(problem).postsolve_stack).rows == [1]
    end
end

@testset "Negative unit bounds preserve direction, zeros and unboundedness" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(ones(T, 8, 1)), zeros(T, 1);
            row_lower=[T(-6), T(2), T(-3), T(-0.0), T(-6), nothing, T(-2), nothing],
            row_upper=[T(-1), T(5), T(4), T(0), T(0), T(4), nothing, nothing])
        original = deepcopy(problem)
        expected = ((1, 6), (-5, -2), (-4, 3), (0, 0), (0, 6),
                    (-4, nothing), (nothing, 2), (nothing, nothing))
        for row in 1:8
            @test JSimplex._normalized_interval(problem, row, Rational{BigInt}(-1)) == expected[row]
        end
        @test isequal(bound_value(problem.row_lower[4]), bound_value(original.row_lower[4]))
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Negated parallel bounds preserve representative replacement and contradictions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[-1 -2; 1 2; -1 -2; -1 -3]), zeros(T, 2);
            row_lower=T[-6, 0, -4, -6], row_upper=T[0, 5, -1, 0],
            column_lower=fill(nothing, 2))
        original = deepcopy(problem)
        result = JSimplex.reduce_parallel_rows(problem)
        @test only(result.postsolve_stack).rows == [3, 4]
        @test result.problem.A == T[-1 -2; -1 -3]
        @test bound_value.(result.problem.row_lower) == T[-4, -6]
        @test bound_value.(result.problem.row_upper) == T[-1, 0]
        @test JSimplex.postsolve_primal(result, T[2, 0]) == T[2, 0]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(-8))
        problem.row_upper[3] = Bound(T(-7))
        @test JSimplex.reduce_parallel_rows(problem).status == INFEASIBLE
    end
end

@testset "Negative unit bounds retain stored BigFloat precision" begin
    lower = setprecision(BigFloat, 192) do
        -BigFloat(2) - BigFloat(2)^(-100)
    end
    upper = setprecision(BigFloat, 256) do
        -BigFloat(1) + BigFloat(2)^(-120)
    end
    problem = LinearProblem(sparse(ones(BigFloat, 1, 1)), zeros(BigFloat, 1))
    problem.row_lower[1] = Bound(lower)
    problem.row_upper[1] = Bound(upper)
    expected = (-Rational{BigInt}(upper), -Rational{BigInt}(lower))
    setprecision(BigFloat, 64) do
        @test JSimplex._normalized_interval(problem, 1, Rational{BigInt}(-1)) == expected
        @test (bound_value(problem.row_lower[1]), bound_value(problem.row_upper[1])) == (lower, upper)
        @test (precision(bound_value(problem.row_lower[1])), precision(bound_value(problem.row_upper[1]))) == (192, 256)
        @test precision(BigFloat) == 64
    end
end

using SparseArrays

@testset "Negative unit parallel pivots avoid rational division" begin
    count = 128
    for (kind, limit) in ((:negative, 14_100), (:unit, 10_900), (:positive, 15_500),
                           (:nonunit, 15_500), (:equal, 9_500))
        pivot = kind == :unit ? 1.0 : kind == :positive ? 2.0 : kind == :nonunit ? -2.0 : -1.0
        row = kind == :equal ? fill(pivot, 1, 3) : [pivot 2pivot -pivot]
        problem = LinearProblem(sparse(repeat(row, count, 1)), zeros(3);
            row_lower=fill(min(0.0, 6pivot), count), row_upper=fill(max(0.0, 6pivot), count),
            column_lower=fill(nothing, 3))
        JSimplex.reduce_parallel_rows(problem)
        measured = @timed JSimplex.reduce_parallel_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test only(JSimplex.reduce_parallel_rows(problem).postsolve_stack).rows == [1]
    end
end

@testset "Negative unit signatures preserve exact signs and fractions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), value in (2, -2, 1//2, -1//2)
        v = T(value)
        terms = [(5, T(-1)), (9, T(-1)), (12, v), (17, -v), (20, T(0)), (25, T(1))]
        original = deepcopy(terms)
        expected = Rational{BigInt}[1, 1, -value, value, 0, -1]
        @test JSimplex._parallel_signature(terms) == expected
        @test JSimplex._parallel_signature(Tuple(terms)) == expected
        @test JSimplex._parallel_signature([(7, T(-1))]) == Rational{BigInt}[1]
        @test terms == original
    end
end

@testset "Negative unit signatures preserve representatives and interval orientation" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[-1 -2 1; 1 2 -1; -1 -2 1; -1 -3 1]), zeros(T, 3);
            row_lower=T[-6, 0, -4, -6], row_upper=T[0, 5, -1, 0],
            column_lower=fill(nothing, 3))
        original = deepcopy(problem)
        result = JSimplex.reduce_parallel_rows(problem)
        @test only(result.postsolve_stack).rows == [3, 4]
        @test result.problem.A == T[-1 -2 1; -1 -3 1]
        @test JSimplex.postsolve_primal(result, T[2, 0, 0]) == T[2, 0, 0]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(-8))
        problem.row_upper[3] = Bound(T(-7))
        @test JSimplex.reduce_parallel_rows(problem).status == INFEASIBLE
        @test problem.A == original.A
    end
end

@testset "Negative unit signatures negate after exact BigFloat conversion" begin
    terms = setprecision(BigFloat, 256) do
        value = BigFloat(3) + BigFloat(2)^(-100)
        [(5, BigFloat(-1)), (9, value), (12, -value)]
    end
    original = deepcopy(terms)
    exact = (3big(2)^100 + 1) // big(2)^100
    setprecision(BigFloat, 64) do
        @test JSimplex._parallel_signature(terms) == Rational{BigInt}[1, -exact, exact]
        @test terms == original
        @test precision.(last.(terms)) == [256, 256, 256]
        @test precision(BigFloat) == 64
    end
end

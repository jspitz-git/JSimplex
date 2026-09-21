using SparseArrays

@testset "Parallel signatures construct their leading one directly" begin
    count = 128
    problem = LinearProblem(sparse(repeat([2.0 4.0 -2.0], count, 1)), zeros(3);
        row_lower=zeros(count), row_upper=fill(12.0, count), column_lower=fill(nothing, 3))
    JSimplex.reduce_parallel_rows(problem)
    measured = @timed JSimplex.reduce_parallel_rows(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 16_000
    @test only(JSimplex.reduce_parallel_rows(problem).postsolve_stack).rows == [1]
end

@testset "Signature leading one follows position rather than column index" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), pivot in (2, -2, 1//2, -1//2)
        terms = [(3, T(pivot)), (9, T(2pivot)), (20, T(-3pivot)), (25, T(pivot/4))]
        original = deepcopy(terms)
        @test JSimplex._parallel_signature(terms) == Rational{BigInt}[1, 2, -3, 1//4]
        @test JSimplex._parallel_signature(Tuple(terms)) == Rational{BigInt}[1, 2, -3, 1//4]
        @test JSimplex._parallel_signature([(7, T(pivot))]) == Rational{BigInt}[1]
        @test terms == original
    end
end

@testset "Signature construction preserves grouping and contradictions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[2 4; -2 -4; 3 6; 2 6]), zeros(T, 2);
            row_lower=T[0, -12, 0, 0], row_upper=T[12, 0, 18, 12], column_lower=[nothing, nothing])
        original = deepcopy(problem)
        result = JSimplex.reduce_parallel_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 4]
        @test result.problem.A == T[2 4; 2 6]
        @test JSimplex.postsolve_primal(result, T[1, 1]) == T[1, 1]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(21))
        problem.row_upper[3] = Bound(T(24))
        @test JSimplex.reduce_parallel_rows(problem).status == INFEASIBLE
        @test problem.A == original.A
    end
end

@testset "Signature head retains stored BigFloat precision" begin
    terms = setprecision(BigFloat, 256) do
        pivot = BigFloat(1) + BigFloat(2)^(-100)
        [(5, pivot), (8, 2pivot), (13, -3pivot)]
    end
    original = deepcopy(terms)
    setprecision(BigFloat, 64) do
        @test JSimplex._parallel_signature(terms) == Rational{BigInt}[1, 2, -3]
        @test terms == original
        @test precision(terms[1][2]) == 256
        @test precision(BigFloat) == 64
    end
end

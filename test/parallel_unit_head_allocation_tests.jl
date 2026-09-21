using SparseArrays

@testset "Unit parallel signatures reuse the converted pivot" begin
    count = 128
    problem = LinearProblem(sparse(repeat([1.0 2.0 -1.0], count, 1)), zeros(3);
        row_lower=zeros(count), row_upper=fill(6.0, count), column_lower=fill(nothing, 3))
    JSimplex.reduce_parallel_rows(problem)
    measured = @timed JSimplex.reduce_parallel_rows(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 11_500
    @test only(JSimplex.reduce_parallel_rows(problem).postsolve_stack).rows == [1]
end

@testset "Reused unit pivots preserve remaining coefficients and input values" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        terms = [(5, T(1)), (9, T(-3)), (20, T(0)), (31, T(1//4))]
        original = deepcopy(terms)
        @test JSimplex._parallel_signature(terms) == Rational{BigInt}[1, -3, 0, 1//4]
        @test JSimplex._parallel_signature(Tuple(terms)) == Rational{BigInt}[1, -3, 0, 1//4]
        @test JSimplex._parallel_signature([(7, T(1))]) == Rational{BigInt}[1]
        @test terms == original
    end
end

@testset "Unit signature reuse preserves mixed-sign representatives" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 2; -1 -2; 1 2; 1 3]), zeros(T, 2);
            row_lower=T[0, -5, 1, 0], row_upper=T[6, 0, 4, 6], column_lower=[nothing, nothing])
        original = deepcopy(problem)
        result = JSimplex.reduce_parallel_rows(problem)
        @test only(result.postsolve_stack).rows == [3, 4]
        @test result.problem.A == T[1 2; 1 3]
        @test JSimplex.postsolve_primal(result, T[2, 0]) == T[2, 0]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(7))
        problem.row_upper[3] = Bound(T(8))
        @test JSimplex.reduce_parallel_rows(problem).status == INFEASIBLE
        @test problem.A == original.A
    end
end

@testset "Unit pivot reuse preserves high-precision trailing coefficients" begin
    terms = setprecision(BigFloat, 256) do
        value = BigFloat(1) + BigFloat(2)^(-100)
        [(5, BigFloat(1)), (9, value), (12, -value)]
    end
    original = deepcopy(terms)
    exact = (big(2)^100 + 1) // big(2)^100
    setprecision(BigFloat, 64) do
        @test JSimplex._parallel_signature(terms) == Rational{BigInt}[1, exact, -exact]
        @test terms == original
        @test precision(terms[2][2]) == 256
        @test precision(BigFloat) == 64
    end
end

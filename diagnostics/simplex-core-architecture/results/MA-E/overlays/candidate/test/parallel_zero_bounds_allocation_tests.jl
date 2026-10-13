using SparseArrays

@testset "Parallel normalization avoids dividing zero bounds" begin
    count = 128
    problem = LinearProblem(sparse(repeat([2.0 4.0 -2.0], count, 1)), zeros(3);
        row_lower=zeros(count), row_upper=fill(12.0, count), column_lower=fill(nothing, 3))
    JSimplex.reduce_parallel_rows(problem)
    measured = @timed JSimplex.reduce_parallel_rows(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 17_600
    @test only(JSimplex.reduce_parallel_rows(problem).postsolve_stack).rows == [1]

    nonzero = LinearProblem(sparse(repeat([2.0 4.0 -2.0], count, 1)), zeros(3);
        row_lower=fill(2.0, count), row_upper=fill(12.0, count), column_lower=fill(nothing, 3))
    JSimplex.reduce_parallel_rows(nonzero)
    measured_nonzero = @timed JSimplex.reduce_parallel_rows(nonzero)
    @test Base.gc_alloc_count(measured_nonzero.gcstats) <= 19_000
end

@testset "Zero interval endpoints retain signs, direction and unboundedness" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(ones(T, 6, 1)), zeros(T, 1);
            row_lower=[T(0), T(-6), T(0), nothing, T(0), nothing],
            row_upper=[T(6), T(0), T(0), T(0), nothing, nothing])
        original = deepcopy(problem)
        for (pivot, expected) in (
            (2, ((0, 3), (-3, 0), (0, 0), (nothing, 0), (0, nothing), (nothing, nothing))),
            (-2, ((-3, 0), (0, 3), (0, 0), (0, nothing), (nothing, 0), (nothing, nothing))),
            (1//2, ((0, 12), (-12, 0), (0, 0), (nothing, 0), (0, nothing), (nothing, nothing))),
            (-1//2, ((-12, 0), (0, 12), (0, 0), (0, nothing), (nothing, 0), (nothing, nothing))))
            for row in 1:6
                @test JSimplex._normalized_interval(problem, row, Rational{BigInt}(pivot)) == expected[row]
            end
        end
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Zero normalized bounds preserve representative replacement and contradictions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[2 4; -2 -4; 4 8; 1 2]), zeros(T, 2);
            row_lower=T[0, -10, 0, 1], row_upper=T[12, 0, 16, 3], column_lower=[nothing, nothing])
        original = deepcopy(problem)
        result = JSimplex.reduce_parallel_rows(problem)
        @test only(result.postsolve_stack).rows == [4]
        @test result.problem.A == T[1 2]
        @test bound_value.(result.problem.row_lower) == T[1]
        @test bound_value.(result.problem.row_upper) == T[3]
        @test JSimplex.postsolve_primal(result, T[2, 0]) == T[2, 0]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[4] = Bound(T(7))
        problem.row_upper[4] = Bound(T(8))
        failure = JSimplex.reduce_parallel_rows(problem)
        @test failure.status == INFEASIBLE
        @test bound_value.(problem.row_lower) == T[0, -10, 0, 7]
        @test bound_value.(problem.row_upper) == T[12, 0, 16, 8]
    end
end

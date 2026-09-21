using SparseArrays

@testset "Negative unit dependency pivots avoid rational division" begin
    count = 128
    for (pivot, trailing, limit) in ((-1.0, 3.0, 5_600), (-1.0, -1.0, 5_100),
                                      (1.0, 3.0, 4_600), (-2.0, 3.0, 6_900))
        A = sparse([collect(1:count); collect(1:count)],
            [collect(1:count); collect(2:count+1)],
            [fill(pivot, count); fill(trailing, count)], count, count+1)
        problem = LinearProblem(A, zeros(count+1); row_upper=fill(3.0, count),
            column_lower=fill(nothing, count+1))
        JSimplex.reduce_dependent_rows(problem)
        measured = @timed JSimplex.reduce_dependent_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test JSimplex.reduce_dependent_rows(problem).problem === problem
    end
end

@testset "Negative unit normalization preserves combined dependency proofs" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), scale in (1, -1, 2, 1//2)
        s = T(scale)
        # Row two acquires a -1 pivot and an equal trailing coefficient after
        # elimination. Its proof then contains contributions from both rows.
        A = sparse(T[0 -1 2 0; 0 s -2s-1 -1; 0 s-1 1-2s -1])
        rhs = T[1, -s-2, -s-1]
        problem = LinearProblem(A, zeros(T, 4); row_lower=rhs, row_upper=rhs,
            column_lower=fill(nothing, 4))
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == A[1:2, :]
        @test bound_value.(result.problem.row_lower) == rhs[1:2]
        @test bound_value.(result.problem.row_upper) == rhs[1:2]
        @test JSimplex.postsolve_primal(result, T[0, 1, 1, 1]) == T[0, 1, 1, 1]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(-s))
        problem.row_upper[3] = Bound(T(-s))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
    end
end

@testset "Negative unit dependency proofs preserve inequality orientation" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[-1 2; 1 -2]), zeros(T, 2);
            row_lower=T[1, -3], row_upper=T[2, -1], column_lower=fill(nothing, 2))
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1]
        @test bound_value.(result.problem.row_lower) == T[1]
        @test bound_value.(result.problem.row_upper) == T[2]

        problem.row_lower[2] = Bound(T(0))
        problem.row_upper[2] = Bound(T(1))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
    end
end

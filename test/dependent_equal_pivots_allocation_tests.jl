using SparseArrays

@testset "Dependent normalization reuses one for equal pivot coefficients" begin
    count = 128
    for (pivot, trailing, limit) in ((2.0, 2.0, 6_200), (-2.0, -2.0, 6_200),
                                      (1.0, 1.0, 4_600), (2.0, 6.0, 6_900))
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

@testset "Equal pivot coefficients preserve dependency proofs" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), pivot in (2, -2, 1//2)
        s = T(pivot)
        # Both the original first row and the eliminated second row have
        # multiple coefficients equal to their respective nonunit pivots.
        A = sparse(T[0 s s 0; 0 s 4s 3s; 0 2s 5s 3s])
        rhs = T[2s, 8s, 10s]
        problem = LinearProblem(A, zeros(T, 4); row_lower=rhs, row_upper=rhs,
            column_lower=fill(nothing, 4))
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == T[0 s s 0; 0 s 4s 3s]
        @test bound_value.(result.problem.row_lower) == T[2s, 8s]
        @test bound_value.(result.problem.row_upper) == T[2s, 8s]
        @test JSimplex.postsolve_primal(result, T[0, 1, 1, 1]) == T[0, 1, 1, 1]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(10s + 1))
        problem.row_upper[3] = Bound(T(10s + 1))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
    end
end

@testset "Unequal and opposite coefficients retain their normalized ratios" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), pivot in (2, -2, 1//2)
        s = T(pivot)
        problem = LinearProblem(sparse(T[s -s 3s; 2s -2s 6s]), zeros(T, 3);
            row_lower=T[3s, 6s], row_upper=T[3s, 6s], column_lower=fill(nothing, 3))
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1]
        @test result.problem.A == reshape(T[s, -s, 3s], 1, 3)
        @test JSimplex.postsolve_primal(result, T[1, 1, 1]) == T[1, 1, 1]
    end
end

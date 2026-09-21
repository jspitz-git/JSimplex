using SparseArrays

@testset "Dependent normalization reuses the unit pivot value" begin
    count = 128
    for (pivot, limit) in ((2.0, 7_300), (-2.0, 7_300), (1.0, 4_600))
        A = sparse([collect(1:count); collect(1:count)],
            [collect(1:count); collect(2:count+1)], fill(pivot, 2count), count, count + 1)
        problem = LinearProblem(A, zeros(count + 1); row_upper=fill(3.0, count),
            column_lower=fill(nothing, count + 1))
        JSimplex.reduce_dependent_rows(problem)
        measured = @timed JSimplex.reduce_dependent_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test JSimplex.reduce_dependent_rows(problem).problem === problem
    end
end

@testset "Normalized dependency pivots preserve exact proofs" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), pivot in (2, -2, 1//2)
        s = T(pivot)
        # Eliminating the first column leaves a second nonunit pivot, 3s.
        # Column one is empty, so pivot identity must follow its dictionary key.
        A = sparse(T[0 s 2s 0; 0 s 5s 3s; 0 2s 7s 3s])
        rhs = T[3s, 9s, 12s]
        problem = LinearProblem(A, zeros(T, 4); row_lower=rhs, row_upper=rhs,
            column_lower=fill(nothing, 4))
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == T[0 s 2s 0; 0 s 5s 3s]
        @test bound_value.(result.problem.row_lower) == T[3s, 9s]
        @test bound_value.(result.problem.row_upper) == T[3s, 9s]
        @test JSimplex.postsolve_primal(result, T[0, 1, 1, 1]) == T[0, 1, 1, 1]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(12s + 1))
        problem.row_upper[3] = Bound(T(12s + 1))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
    end
end

@testset "Single-term dependency pivots retain bounds and postsolve" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), pivot in (2, -2, 1//2)
        s = T(pivot)
        problem = LinearProblem(sparse(reshape(T[0, s, 2s], 3, 1)), T[1];
            row_lower=T[0, s, 2s], row_upper=T[0, s, 2s], column_lower=[nothing])
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == reshape(T[0, s], 2, 1)
        @test JSimplex.postsolve_primal(result, T[1]) == T[1]
    end
end

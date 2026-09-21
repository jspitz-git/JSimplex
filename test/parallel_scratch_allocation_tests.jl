using SparseArrays

@testset "Parallel rows avoid unused interval and representative storage" begin
    count = 128
    unique = LinearProblem(sparse(1:count, 1:count, ones(count), count, count), zeros(count))
    JSimplex.reduce_parallel_rows(unique)
    @test (@allocated JSimplex.reduce_parallel_rows(unique)) <= 31_500
    @test JSimplex.reduce_parallel_rows(unique).problem === unique

    repeated = LinearProblem(sparse(repeat([1.0 2.0 -1.0], count, 1)), zeros(3);
        column_lower=fill(nothing, 3))
    JSimplex.reduce_parallel_rows(repeated)
    measured = @timed JSimplex.reduce_parallel_rows(repeated)
    @test Base.gc_alloc_count(measured.gcstats) <= 9_250
    @test only(JSimplex.reduce_parallel_rows(repeated).postsolve_stack).rows == [1]
end

@testset "Parallel caches initialize across multiple signatures and removed representatives" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 1 0; 1 2 0; 0 0 1; 1 2 0; 1 1 0; 2 4 0]),
            T[1, 2, 3]; row_lower=T[0, 0, 0, 2, 1, 6], row_upper=T[10, 20, 1, 8, 9, 12],
            row_names=["first", "second", "unique", "tighter", "other", "last"])
        original = deepcopy(problem)
        result = JSimplex.reduce_parallel_rows(problem)
        @test only(result.postsolve_stack).rows == [3, 5, 6]
        @test result.problem.A == T[0 0 1; 1 1 0; 2 4 0]
        @test bound_value.(result.problem.row_lower) == T[0, 1, 6]
        @test bound_value.(result.problem.row_upper) == T[1, 9, 12]
        @test result.problem.row_names == ["unique", "other", "last"]
        @test JSimplex.postsolve_primal(result, T[1, 1, 1]) == T[1, 1, 1]
        basis = JSimplex.Basis([4, 5, 6], [fill(JSimplex.AT_LOWER, 3); fill(JSimplex.BASIC, 3)])
        @test JSimplex.restore_basis(result, basis).basic_indices == collect(4:9)
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[6] = Bound(T(18))
        problem.row_upper[6] = Bound(T(20))
        failure = JSimplex.reduce_parallel_rows(problem)
        @test failure isa JSimplex.PresolveFailure
        @test failure.status == INFEASIBLE
        @test failure.message == "proportional rows 4 and 6 have disjoint bounds"
    end
end

@testset "Parallel interval storage is unnecessary without matching signatures" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 1; 1 2; 1 3]), zeros(T, 2))
        @test JSimplex.reduce_parallel_rows(problem).problem === problem
    end
    for (rows, columns) in ((0, 0), (0, 3), (3, 0), (3, 3))
        problem = LinearProblem(spzeros(rows, columns), zeros(columns))
        @test JSimplex.reduce_parallel_rows(problem).problem === problem
    end
end

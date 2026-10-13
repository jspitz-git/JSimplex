using SparseArrays

@testset "Dependent rows reuse their initial proof coefficient" begin
    count = 128
    problem = LinearProblem(sparse(repeat([1.0 2.0 -1.0], count, 1)), zeros(3);
        row_lower=zeros(count), row_upper=zeros(count), column_lower=fill(nothing, 3))
    JSimplex.reduce_dependent_rows(problem)
    measured = @timed JSimplex.reduce_dependent_rows(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 11_000
    @test only(JSimplex.reduce_dependent_rows(problem).postsolve_stack).rows == [1]
end

@testset "Shared proof seed survives nonunit pivot normalization" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), scale in (2, -2, 1//2)
        s = T(scale)
        problem = LinearProblem(sparse(T[s 2s 0; s 2s 1; 2s 4s 1]), zeros(T, 3);
            row_lower=T[3s, 3s + 1, 6s + 1], row_upper=T[3s, 3s + 1, 6s + 1],
            column_lower=fill(nothing, 3))
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == T[s 2s 0; s 2s 1]
        @test bound_value.(result.problem.row_lower) == T[3s, 3s + 1]
        @test bound_value.(result.problem.row_upper) == T[3s, 3s + 1]
        @test JSimplex.postsolve_primal(result, T[1, 1, 1]) == T[1, 1, 1]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
        # A fresh invocation must not inherit a normalized or eliminated seed.
        @test JSimplex.reduce_dependent_rows(problem).problem.A == result.problem.A

        problem.row_lower[3] = Bound(T(6s + 2))
        problem.row_upper[3] = Bound(T(6s + 2))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
    end
end

@testset "Empty rows do not require a proof seed" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), rows in (0, 5)
        problem = LinearProblem(spzeros(T, rows, 3), zeros(T, 3);
            row_lower=zeros(T, rows), row_upper=zeros(T, rows))
        @test JSimplex.reduce_dependent_rows(problem).problem === problem
    end
    # The first nonempty row may occur after several empty rows.
    problem = LinearProblem(sparse([0.0 0.0; 2.0 4.0; 0.0 0.0; 2.0 4.0]), zeros(2);
        row_lower=[0.0, 6.0, 0.0, 6.0], row_upper=[0.0, 6.0, 0.0, 6.0])
    @test only(JSimplex.reduce_dependent_rows(problem).postsolve_stack).rows == [1, 2, 3]
end

using SparseArrays

@testset "Basic presolve delays row-bound working copies" begin
    problem = LinearProblem(sparse(ones(128, 128)), ones(128))
    JSimplex._presolve_basic(problem)
    @test (@allocated JSimplex._presolve_basic(problem)) <= 5_000
end

@testset "Accepted eliminations update private row bounds cumulatively" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[2 1 0; 0 3 1; 0 0 2; 0 0 0]), T[5, 2, 3];
            objective_constant=T(7), row_lower=T[5, 4, -2, 0], row_upper=T[5, 7, 6, 0],
            column_lower=T[2, 1, 0], column_upper=[T(2), T(1), nothing])
        old_lower, old_upper = copy(problem.row_lower), copy(problem.row_upper)
        result = JSimplex._presolve_basic(problem)
        @test result.problem.A == reshape(T[1, 2], 2, 1)
        @test bound_value.(result.problem.row_lower) == T[1, -2]
        @test bound_value.(result.problem.row_upper) == T[4, 6]
        @test result.problem.objective == T[3]
        @test result.problem.objective_constant == T(19)
        @test only(result.postsolve_stack).rows == [2, 3]
        @test only(result.postsolve_stack).columns == [3]
        @test JSimplex.postsolve_primal(result, T[2]) == T[2, 1, 2]
        @test problem.row_lower == old_lower
        @test problem.row_upper == old_upper
        result.problem.row_lower[1] = Bound(T(-10))
        result.problem.row_upper[1] = Bound(T(20))
        @test problem.row_lower == old_lower
        @test problem.row_upper == old_upper

        unchanged = LinearProblem(sparse(T[1 1]), T[1, 2]; row_lower=T[2], row_upper=T[5])
        @test JSimplex._presolve_basic(unchanged).problem === unchanged
    end
end

@testset "Rejected eliminations never commit staged row shifts" begin
    for T in (Float32, Float64)
        # The first row shift is exact, but the second cannot be represented.
        rejected = LinearProblem(sparse(T[2 1; 0.1 1]), T[0, 1];
            row_lower=T[2, 1], row_upper=T[4, 2],
            column_lower=T[0.5, 0], column_upper=[T(0.5), nothing])
        result = JSimplex._presolve_basic(rejected)
        @test result.problem === rejected
        @test bound_value.(rejected.row_lower) == T[2, 1]
        @test bound_value.(rejected.row_upper) == T[4, 2]

        # A later rejection must preserve earlier accepted changes in the result.
        mixed = LinearProblem(sparse(T[1 0 1; 0 0.1 1]), T[0, 0, 1];
            row_lower=T[2, 1], row_upper=T[4, 2],
            column_lower=T[1, 0.1, 0], column_upper=[T(1), T(0.1), nothing])
        result = JSimplex._presolve_basic(mixed)
        @test only(result.postsolve_stack).columns == [2, 3]
        @test bound_value.(result.problem.row_lower) == T[1, 1]
        @test bound_value.(result.problem.row_upper) == T[3, 2]
        @test bound_value.(mixed.row_lower) == T[2, 1]
        @test bound_value.(mixed.row_upper) == T[4, 2]
    end
end

@testset "Unshifted reduced bounds remain independent" begin
    problem = LinearProblem(sparse([1.0 0.0; 2.0 0.0]), [1.0, 0.0];
        row_lower=[1.0, 2.0], row_upper=[3.0, 4.0])
    result = JSimplex._presolve_basic(problem)
    @test only(result.postsolve_stack).columns == [1]
    @test result.problem.row_lower == problem.row_lower
    @test result.problem.row_upper == problem.row_upper
    @test result.problem.row_lower !== problem.row_lower
    @test result.problem.row_upper !== problem.row_upper
    result.problem.row_lower[1] = Bound(-1.0)
    result.problem.row_upper[1] = Bound(5.0)
    @test bound_value.(problem.row_lower) == [1.0, 2.0]
    @test bound_value.(problem.row_upper) == [3.0, 4.0]

    infeasible = LinearProblem(spzeros(1, 1), [0.0]; row_lower=[1.0])
    failure = JSimplex._presolve_basic(infeasible)
    @test failure.status == INFEASIBLE
    @test (failure.rows, failure.columns, failure.nonzeros) == (0, 0, 0)
    @test bound_value(infeasible.row_lower[1]) == 1.0
end

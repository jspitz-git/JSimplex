using SparseArrays

@testset "Dependent rows skip unit-pivot normalization allocations" begin
    count = 128
    A = sparse([collect(1:count); collect(1:count)],
        [collect(1:count); collect(2:count+1)], ones(2count), count, count + 1)
    problem = LinearProblem(A, zeros(count + 1); row_upper=fill(3.0, count),
        column_lower=fill(nothing, count + 1))
    JSimplex.reduce_dependent_rows(problem)
    @test (@allocated JSimplex.reduce_dependent_rows(problem)) <= 350_000
    @test JSimplex.reduce_dependent_rows(problem).problem === problem
end

@testset "Dependent rows preserve proofs after unit and nonunit pivots" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), scale in (1, -1, 2, 1//2)
        s = T(scale)
        # The second row's pivot becomes one after eliminating the first column;
        # its proof combines two source rows. The third row is their sum.
        A = sparse(T[s 2s 0; s 2s 1; 2s 4s 1])
        rhs = T[3s, 3s + 1, 6s + 1]
        problem = LinearProblem(A, T[1, -1, 2]; row_lower=rhs, row_upper=rhs,
            column_lower=fill(nothing, 3))
        result = JSimplex.reduce_dependent_rows(problem)
        @test result.problem.A == A[1:2, :]
        @test result.problem.objective == T[1, -1, 2]
        @test result.problem.objective_constant == zero(T)
        @test bound_value.(result.problem.row_lower) == rhs[1:2]
        @test bound_value.(result.problem.row_upper) == rhs[1:2]
        @test only(result.postsolve_stack).rows == [1, 2]
        @test JSimplex.postsolve_primal(result, T[1, 1, 1]) == T[1, 1, 1]
        @test problem.A == A
        @test bound_value.(problem.row_lower) == rhs
        @test bound_value.(problem.row_upper) == rhs

        inconsistent_rhs = T[3s, 3s + 1, 6s + 2]
        inconsistent = LinearProblem(A, zeros(T, 3);
            row_lower=inconsistent_rhs, row_upper=inconsistent_rhs)
        failure = JSimplex.reduce_dependent_rows(inconsistent)
        @test failure isa JSimplex.PresolveFailure
        @test failure.status == INFEASIBLE
        @test inconsistent.A == A
        @test bound_value.(inconsistent.row_upper) == inconsistent_rhs
    end
end

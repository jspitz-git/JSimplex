using SparseArrays

@testset "Sparse aggregation reuses candidate scratch storage" begin
    count = 64
    A = vcat(hcat(sparse(1:count, 1:count, ones(count), count, count),
                  sparse(ones(count, 1))),
             sparse(reshape([ones(count); 2.0], 1, count + 1)))
    problem = LinearProblem(A, [ones(count); 2.0];
        row_lower=Union{Nothing,Float64}[ones(count); nothing],
        row_upper=[ones(count); 100.0], column_lower=fill(nothing, count + 1))
    JSimplex.aggregate_sparse_equalities(problem)
    @test (@allocated JSimplex.aggregate_sparse_equalities(problem)) <= 665_000
end

@testset "Rejected sparse candidates cannot leak staged changes" begin
    for T in (Float32, Float64, BigFloat), rejection in (:cost, :coefficient, :bound)
        failed_A = rejection == :cost ? T[3 3 1; 3 0 0] : T[3 1 1; 3 0 0; 1 0 0]
        failed_cost = T[rejection == :cost ? 1 : 3, 0, 0]
        rhs = T(rejection == :bound ? 1 : 3)
        rows = size(failed_A, 1)
        A = blockdiag(sparse(failed_A), sparse(T[1 1; 1 2]))
        lower = Union{Nothing,T}[rhs; fill(nothing, rows - 1); one(T); nothing]
        upper = T[rhs; fill(T(10), rows - 1); one(T); T(10)]
        problem = LinearProblem(A, [failed_cost; T[1, 2]];
            row_lower=lower, row_upper=upper, column_lower=fill(nothing, 5))
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test result.problem.A == blockdiag(sparse(failed_A), sparse(ones(T, 1, 1)))
        @test result.problem.objective == [failed_cost; one(T)]
        @test result.problem.objective_constant == one(T)
        @test result.problem.row_lower[1:rows] == problem.row_lower[1:rows]
        @test result.problem.row_upper[1:rows] == problem.row_upper[1:rows]
        @test bound_value(result.problem.row_upper[end]) == T(9)
        @test length(only(result.postsolve_stack).records) == 1
        @test only(result.postsolve_stack).map.columns == [1, 2, 3, 5]
        @test JSimplex.postsolve_primal(result, T[0, 0, 0, 3]) == T[0, 0, 0, -2, 3]
        @test problem.A == A
        @test problem.objective == [failed_cost; T[1, 2]]
        @test bound_value.(problem.row_upper) == upper
    end
end

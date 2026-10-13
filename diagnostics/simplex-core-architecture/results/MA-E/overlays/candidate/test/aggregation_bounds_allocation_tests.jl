using SparseArrays

@testset "Aggregation avoids unused row-bound copies" begin
    count = 128
    problem = LinearProblem(sparse(repeat(collect(1:count), inner=2), collect(1:2count),
        ones(2count), count, 2count), ones(2count); row_lower=zeros(count), row_upper=ones(count))
    for pass in (JSimplex.aggregate_singleton_equalities, JSimplex.aggregate_sparse_equalities)
        pass(problem)
        @test (@allocated pass(problem)) <= 17_000
        @test pass(problem).problem === problem
    end
end

@testset "Singleton aggregation owns bounds after multiple accepted rows" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 0 1; 0 1 1]), T[2, 3, 4];
            row_lower=T[4, 6], row_upper=T[4, 6], column_lower=T[1, 2, 0], column_upper=T[3, 5, 10])
        original = deepcopy(problem)
        result = JSimplex.aggregate_singleton_equalities(problem)
        @test result.problem.A == ones(T, 2, 1)
        @test result.problem.objective == T[-1]
        @test result.problem.objective_constant == T(26)
        @test bound_value.(result.problem.row_lower) == T[1, 1]
        @test bound_value.(result.problem.row_upper) == T[3, 4]
        @test length(only(result.postsolve_stack).records) == 2
        @test JSimplex.postsolve_primal(result, T[2]) == T[2, 4, 2]
        @test result.problem.row_lower !== problem.row_lower
        @test result.problem.row_upper !== problem.row_upper
        result.problem.row_lower[1] = Bound(T(-10))
        result.problem.row_upper[1] = Bound(T(10))
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
        @test problem.A == original.A
        @test problem.objective == original.objective
    end
end

@testset "Sparse aggregation accumulates shifts in private bounds" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), free_pivots in (false, true)
        problem = LinearProblem(sparse(T[1 0 1 0 0; 0 1 0 1 0; 2 3 0 0 1]), T[2, 3, 4, 5, 6];
            row_lower=[T(4), T(6), nothing], row_upper=T[4, 6, 30],
            column_lower=free_pivots ? fill(nothing, 5) : [T(0), T(0), nothing, nothing, nothing],
            column_upper=free_pivots ? fill(nothing, 5) : [T(1), T(1), nothing, nothing, nothing])
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        step = only(result.postsolve_stack)
        @test step.map.columns == [3, 4, 5]
        @test step.map.rows == (free_pivots ? [3] : [1, 2, 3])
        @test result.problem.A == (free_pivots ? reshape(T[-2, -3, 1], 1, 3) : T[1 0 0; 0 1 0; -2 -3 1])
        @test result.problem.objective == T[2, 2, 6]
        @test result.problem.objective_constant == T(26)
        @test bound_value.(result.problem.row_upper) == (free_pivots ? T[4] : T[4, 6, 4])
        @test !isfinite(result.problem.row_lower[end])
        if !free_pivots
            @test bound_value.(result.problem.row_lower[1:2]) == T[3, 5]
        end
        @test length(step.records) == 2
        @test JSimplex.postsolve_primal(result, T[3, 5, 1]) == T[1, 1, 3, 5, 1]
        @test result.problem.row_lower !== problem.row_lower
        @test result.problem.row_upper !== problem.row_upper
        result.problem.row_lower[1] = Bound(T(-10))
        result.problem.row_upper[1] = Bound(T(10))
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
        @test problem.A == original.A
        @test problem.objective == original.objective
    end
end

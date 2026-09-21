using SparseArrays

@testset "Propagation skips activity removal for absent row bounds" begin
    count = 128
    for kind in (:lower, :upper)
        problem = LinearProblem(sparse(ones(count, 2)), ones(2);
            row_lower=fill(kind == :lower ? 4.0 : nothing, count),
            row_upper=fill(kind == :upper ? 12.0 : nothing, count),
            column_lower=ones(2), column_upper=fill(10.0, 2))
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= 20_500
        @test JSimplex.propagate_row_bounds(problem).problem === problem
    end
end

@testset "One-sided rows tighten the correct bound for either coefficient sign" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2), kind in (:lower, :upper)
        problem = LinearProblem(sparse(fill(T(coefficient), 1, 2)), ones(T, 2);
            row_lower=[kind == :lower ? T(6coefficient) : nothing],
            row_upper=[kind == :upper ? T(6coefficient) : nothing],
            column_lower=T[0, 2], column_upper=T[10, 2])
        original = deepcopy(problem)
        changed = falses(2)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        lower_tightens = (kind == :lower) == (coefficient > 0)
        @test bound_value.(result.problem.column_lower) == (lower_tightens ? T[4, 2] : T[0, 2])
        @test bound_value.(result.problem.column_upper) == (lower_tightens ? T[10, 2] : T[4, 2])
        @test changed == [true, false]
        @test JSimplex.postsolve_primal(result, T[4, 2]) == T[4, 2]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "One-sided rows still check full activities for contradictions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), kind in (:lower, :upper)
        problem = LinearProblem(sparse(ones(T, 1, 2)), ones(T, 2);
            row_lower=[kind == :lower ? T(25) : nothing],
            row_upper=[kind == :upper ? T(1) : nothing],
            column_lower=T[1, 1], column_upper=T[10, 10])
        changed = falses(2)
        failure = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test failure.status == INFEASIBLE
        @test !any(changed)
        @test bound_value.(problem.column_lower) == T[1, 1]
        @test bound_value.(problem.column_upper) == T[10, 10]
    end
end

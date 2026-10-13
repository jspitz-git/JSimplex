using SparseArrays

@testset "Dependent intervals reuse terms when the sum is zero" begin
    count = 128
    for (scale, limit) in ((1.0, 17_500), (2.0, 24_000))
        multipliers = [1.0; fill(scale, count - 1)]
        problem = LinearProblem(sparse(multipliers * [1.0 2.0 -1.0]), zeros(3);
            row_lower=multipliers, row_upper=6multipliers, column_lower=fill(nothing, 3))
        JSimplex.reduce_dependent_rows(problem)
        measured = @timed JSimplex.reduce_dependent_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test only(JSimplex.reduce_dependent_rows(problem).postsolve_stack).rows == [1]
    end
end

@testset "Dependent interval sums preserve cancellation and unbounded endpoints" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(ones(T, 6, 1)), zeros(T, 1);
            row_lower=[T(2), T(-2), T(3), nothing, T(0), nothing],
            row_upper=[T(2), T(-2), T(5), T(0), nothing, nothing])
        original = deepcopy(problem)
        for (entries, expected) in (
            ((1 => -1,), (2, 2)),
            ((1 => -1, 2 => -1), (0, 0)),
            ((1 => -1, 2 => -1, 3 => -1), (3, 5)),
            ((1 => -1, 2 => -1, 3 => 1), (-5, -3)),
            ((1 => -2, 2 => -2, 3 => -2), (6, 10)),
            ((1 => -1, 2 => -1, 4 => -1), (nothing, 0)),
            ((1 => -1, 2 => -1, 5 => -1), (0, nothing)),
            ((1 => -1, 2 => -1, 4 => -1, 5 => -1), (nothing, nothing)),
            ((1 => -1, 4 => 0, 6 => 100), (2, 2)))
            combination = Dict{Int,Rational{BigInt}}(entries)
            saved = deepcopy(combination)
            @test JSimplex._implied_interval(problem, combination, 6) == expected
            @test combination == saved
        end
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Dependent row proofs preserve cancelling contributions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 0 0; 0 1 0; 0 0 1; 1 1 1]), zeros(T, 3);
            row_lower=T[2, -2, 3, 3], row_upper=T[2, -2, 5, 5],
            column_lower=fill(nothing, 3))
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2, 3]
        @test result.problem.A == T[1 0 0; 0 1 0; 0 0 1]
        @test bound_value.(result.problem.row_lower) == T[2, -2, 3]
        @test bound_value.(result.problem.row_upper) == T[2, -2, 5]
        @test JSimplex.postsolve_primal(result, T[2, -2, 4]) == T[2, -2, 4]
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[4] = Bound(T(6))
        problem.row_upper[4] = Bound(T(7))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
        @test problem.A == original.A
    end
end

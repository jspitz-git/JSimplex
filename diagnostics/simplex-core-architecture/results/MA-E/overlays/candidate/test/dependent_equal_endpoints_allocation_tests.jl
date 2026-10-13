using SparseArrays

@testset "Equal implied endpoints share an exact contribution" begin
    count = 128
    for (kind, limit) in ((:unit, 14_800), (:negative, 15_500), (:nonunit, 18_000),
                           (:unequal, 15_400), (:zero, 11_000))
        scale = kind == :negative ? -1.0 : kind == :nonunit ? 2.0 : 1.0
        multipliers = [1.0; fill(scale, count-1)]
        other = (kind == :unequal ? 6 : 3) .* multipliers
        problem = LinearProblem(sparse(multipliers * [1.0 2.0 -1.0]), zeros(3);
            row_lower=kind == :zero ? zeros(count) : min.(3multipliers, other),
            row_upper=kind == :zero ? zeros(count) : max.(3multipliers, other),
            column_lower=fill(nothing, 3))
        JSimplex.reduce_dependent_rows(problem)
        measured = @timed JSimplex.reduce_dependent_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test only(JSimplex.reduce_dependent_rows(problem).postsolve_stack).rows == [1]
    end
end

@testset "Equal endpoint reuse preserves partial and unbounded sums" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(ones(T, 7, 1)), zeros(T, 1);
            row_lower=[nothing, T(3), T(-2), T(-5), T(0), T(1), T(99)],
            row_upper=[T(5), T(3), T(-2), nothing, T(0), T(4), T(99)])
        original = deepcopy(problem)
        for (entries, expected) in (
            ((2 => -1,), (3, 3)),
            ((2 => 1,), (-3, -3)),
            ((2 => -2,), (6, 6)),
            ((2 => -1//2,), (3//2, 3//2)),
            ((2 => -1, 3 => -1), (1, 1)),
            ((1 => -1, 2 => -1), (nothing, 8)),
            ((1 => -1, 2 => 1), (nothing, 2)),
            ((4 => -1, 2 => -1), (-2, nothing)),
            ((1 => -1, 4 => -1, 2 => -1), (nothing, nothing)),
            ((5 => -1, 2 => -1), (3, 3)),
            ((6 => -1, 2 => -1), (4, 7)),
            ((6 => 1, 2 => -1), (-1, 2)),
            ((2 => -1, 7 => 123), (3, 3)))
            combination = Dict{Int,Rational{BigInt}}(entries)
            saved = deepcopy(combination)
            @test JSimplex._implied_interval(problem, combination, 7) == expected
            @test combination == saved
        end
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Shared equality contributions preserve dependent row certificates" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        rhs = T[3, -2, 1, -5, 2]
        problem = LinearProblem(sparse(T[1 0; 0 1; 1 1; -1 1; 2 2]), zeros(T, 2);
            row_lower=rhs, row_upper=rhs, column_lower=[nothing, nothing])
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == T[1 0; 0 1]
        @test bound_value.(result.problem.row_lower) == T[3, -2]
        @test bound_value.(result.problem.row_upper) == T[3, -2]
        @test JSimplex.postsolve_primal(result, T[3, -2]) == T[3, -2]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[4] = Bound(T(-4))
        problem.row_upper[4] = Bound(T(-4))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
    end
end

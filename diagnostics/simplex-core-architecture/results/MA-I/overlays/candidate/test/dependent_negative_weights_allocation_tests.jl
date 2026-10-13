using SparseArrays

@testset "Negative unit implied weights avoid rational multiplication" begin
    count = 128
    for (kind, limit) in ((:negative, 16_500), (:unit, 15_400),
                           (:zero, 11_400), (:nonunit, 19_100))
        scale = kind == :unit ? 1.0 : kind == :nonunit ? -2.0 : -1.0
        multipliers = [1.0; fill(scale, count-1)]
        problem = LinearProblem(sparse(multipliers * [1.0 2.0 -1.0]), zeros(3);
            row_lower=kind == :zero ? zeros(count) : min.(multipliers, 6multipliers),
            row_upper=kind == :zero ? zeros(count) : max.(multipliers, 6multipliers),
            column_lower=fill(nothing, 3))
        JSimplex.reduce_dependent_rows(problem)
        measured = @timed JSimplex.reduce_dependent_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test only(JSimplex.reduce_dependent_rows(problem).postsolve_stack).rows == [1]
    end
end

@testset "Negated implied endpoints preserve signed and unbounded intervals" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(ones(T, 6, 1)), zeros(T, 1);
            row_lower=[T(2), T(-3), nothing, T(-2), T(0), T(100)],
            row_upper=[T(6), T(-1), T(4), nothing, T(0), T(100)])
        original = deepcopy(problem)
        for (entries, expected) in (
            ((1 => 1,), (-6, -2)),
            ((2 => 1,), (1, 3)),
            ((1 => 1, 2 => 1), (-5, 1)),
            ((1 => 1, 2 => -1), (-9, -3)),
            ((1 => 1, 2 => 2), (-4, 4)),
            ((3 => 1,), (-4, nothing)),
            ((4 => 1,), (nothing, 2)),
            ((5 => 1,), (0, 0)),
            ((1 => 0, 2 => 1, 6 => 1), (1, 3)),
            ((1 => 1//2,), (-3, -1)),
            ((1 => -1,), (2, 6)))
            combination = Dict{Int,Rational{BigInt}}(entries)
            saved = deepcopy(combination)
            @test JSimplex._implied_interval(problem, combination, 6) == expected
            @test combination == saved
        end
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Negative implied contributions preserve reduction and contradictions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 0; 0 1; -1 -1; -1 1]), zeros(T, 2);
            row_lower=T[2, -3, -5, -9], row_upper=T[6, -1, 1, -3],
            column_lower=[nothing, nothing])
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == T[1 0; 0 1]
        @test bound_value.(result.problem.row_lower) == T[2, -3]
        @test bound_value.(result.problem.row_upper) == T[6, -1]
        @test JSimplex.postsolve_primal(result, T[3, -2]) == T[3, -2]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(2))
        problem.row_upper[3] = Bound(T(3))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
    end
end

using SparseArrays

@testset "Dependent intervals defer unused weight negation" begin
    count = 128
    for (kind, limit) in ((:zero, 11_400), (:unit, 15_800), (:nonunit, 22_650))
        multipliers = kind == :nonunit ? [1.0; fill(2.0, count - 1)] : ones(count)
        problem = LinearProblem(sparse(multipliers * [1.0 2.0 -1.0]), zeros(3);
            row_lower=kind == :zero ? zeros(count) : multipliers,
            row_upper=kind == :zero ? zeros(count) : 6multipliers,
            column_lower=fill(nothing, 3))
        JSimplex.reduce_dependent_rows(problem)
        measured = @timed JSimplex.reduce_dependent_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test only(JSimplex.reduce_dependent_rows(problem).postsolve_stack).rows == [1]
    end
end

@testset "Deferred weights preserve endpoint selection and unboundedness" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(ones(T, 6, 1)), zeros(T, 1);
            row_lower=[T(0), T(-2), nothing, T(0), nothing, nothing],
            row_upper=[T(6), T(0), T(6), nothing, nothing, nothing])
        original = deepcopy(problem)
        for (entries, expected) in (
            ((1 => -1,), (0, 6)),
            ((1 => 1,), (-6, 0)),
            ((2 => -1,), (-2, 0)),
            ((2 => 1,), (0, 2)),
            ((1 => -2,), (0, 12)),
            ((2 => -2,), (-4, 0)),
            ((3 => -1,), (nothing, 6)),
            ((3 => 1,), (-6, nothing)),
            ((4 => -1,), (0, nothing)),
            ((5 => -1, 1 => -2), (nothing, nothing)),
            ((5 => 0, 1 => -1, 6 => -1), (0, 6)))
            combination = Dict{Int,Rational{BigInt}}(entries)
            saved = deepcopy(combination)
            @test JSimplex._implied_interval(problem, combination, 6) == expected
            @test combination == saved
        end
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

using SparseArrays

@testset "Dependent intervals reuse unit-weight endpoints" begin
    count = 128
    problem = LinearProblem(sparse(repeat([1.0 2.0 -1.0], count, 1)), zeros(3);
        row_lower=ones(count), row_upper=fill(6.0, count), column_lower=fill(nothing, 3))
    JSimplex.reduce_dependent_rows(problem)
    measured = @timed JSimplex.reduce_dependent_rows(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 19_000
    @test only(JSimplex.reduce_dependent_rows(problem).postsolve_stack).rows == [1]
end

@testset "Unit implied contributions preserve exact intervals" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(ones(T, 5, 1)), zeros(T, 1);
            row_lower=[T(2), T(-3), nothing, T(0), nothing],
            row_upper=[T(6), T(-1), T(4), nothing, nothing])
        original = deepcopy(problem)
        for (entries, expected) in (
            ((1 => -1,), (2, 6)),
            ((1 => 1,), (-6, -2)),
            ((1 => -2,), (4, 12)),
            ((1 => 2,), (-12, -4)),
            ((1 => -1, 2 => -1), (-1, 5)),
            ((1 => -1, 2 => 1), (3, 9)),
            ((1 => -1, 3 => -1), (nothing, 10)),
            ((1 => -1, 3 => 1), (-2, nothing)),
            ((1 => -1, 4 => -1), (2, nothing)),
            ((1 => -1, 3 => 0, 5 => -1), (2, 6)))
            combination = Dict{Int,Rational{BigInt}}(entries)
            saved = deepcopy(combination)
            @test JSimplex._implied_interval(problem, combination, 5) == expected
            @test combination == saved
        end
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Unit implied contributions preserve row reduction and contradictions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 0; 0 1; 1 1; 1 -1]), zeros(T, 2);
            row_lower=T[2, -3, -1, 3], row_upper=T[6, -1, 5, 9],
            column_lower=[nothing, nothing])
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == T[1 0; 0 1]
        @test bound_value.(result.problem.row_lower) == T[2, -3]
        @test bound_value.(result.problem.row_upper) == T[6, -1]
        @test JSimplex.postsolve_primal(result, T[3, -2]) == T[3, -2]
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(6))
        problem.row_upper[3] = Bound(T(7))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
        @test problem.A == original.A
    end
end

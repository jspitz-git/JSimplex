using SparseArrays

@testset "Dependent intervals skip zero source bounds" begin
    count = 128
    for (low, high) in ((0.0, 6.0), (-6.0, 0.0))
        problem = LinearProblem(sparse(repeat([1.0 2.0 -1.0], count, 1)), zeros(3);
            row_lower=fill(low, count), row_upper=fill(high, count), column_lower=fill(nothing, 3))
        JSimplex.reduce_dependent_rows(problem)
        measured = @timed JSimplex.reduce_dependent_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= 18_000
        @test only(JSimplex.reduce_dependent_rows(problem).postsolve_stack).rows == [1]
    end
end

@testset "Zero source bounds remain distinct from unbounded endpoints" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(ones(T, 5, 1)), zeros(T, 1);
            row_lower=[T(0), nothing, T(0), T(2), nothing],
            row_upper=[T(0), T(0), nothing, T(6), nothing])
        original = deepcopy(problem)
        for (entries, expected) in (
            ((1 => -2, 4 => -1), (2, 6)),
            ((1 => 2, 4 => 1), (-6, -2)),
            ((1 => -2, 2 => -1), (nothing, 0)),
            ((1 => -2, 2 => 1), (0, nothing)),
            ((1 => 2, 3 => -1), (0, nothing)),
            ((2 => -1, 3 => -1), (nothing, nothing)),
            ((2 => 0, 4 => -1), (2, 6)),
            ((1 => -2, 4 => -1, 5 => 100), (2, 6)))
            combination = Dict{Int,Rational{BigInt}}(entries)
            saved = deepcopy(combination)
            @test JSimplex._implied_interval(problem, combination, 5) == expected
            @test combination == saved
        end
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Zero bounds preserve dependent row proofs and contradictions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 0; 0 1; 1 1; 1 -1]), zeros(T, 2);
            row_lower=T[0, 0, 0, -3], row_upper=T[2, 3, 5, 2], column_lower=[nothing, nothing])
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == T[1 0; 0 1]
        @test bound_value.(result.problem.row_lower) == T[0, 0]
        @test bound_value.(result.problem.row_upper) == T[2, 3]
        @test JSimplex.postsolve_primal(result, T[1, 1]) == T[1, 1]
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(6))
        problem.row_upper[3] = Bound(T(7))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
        @test problem.A == original.A
    end
end

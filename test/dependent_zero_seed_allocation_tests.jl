using SparseArrays

@testset "Dependent intervals share their initial exact zero" begin
    count = 128
    problem = LinearProblem(sparse(repeat([1.0 2.0 -1.0], count, 1)), zeros(3);
        row_lower=zeros(count), row_upper=zeros(count), column_lower=fill(nothing, 3))
    JSimplex.reduce_dependent_rows(problem)
    measured = @timed JSimplex.reduce_dependent_rows(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 11_900
    @test only(JSimplex.reduce_dependent_rows(problem).postsolve_stack).rows == [1]
end

@testset "Shared initial zero preserves independent interval endpoints" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(ones(T, 5, 1)), zeros(T, 1);
            row_lower=[T(2), T(0), nothing, T(0), nothing],
            row_upper=[T(6), T(0), T(0), nothing, nothing])
        original = deepcopy(problem)
        for (entries, expected) in (
            ((), (0, 0)),
            ((5 => 1,), (0, 0)),
            ((1 => 0,), (0, 0)),
            ((2 => -1,), (0, 0)),
            ((1 => -1,), (2, 6)),
            ((1 => 1,), (-6, -2)),
            ((3 => -1,), (nothing, 0)),
            ((4 => -1,), (0, nothing)),
            ((3 => -1, 4 => -1), (nothing, nothing)))
            combination = Dict{Int,Rational{BigInt}}(entries)
            saved = deepcopy(combination)
            interval = JSimplex._implied_interval(problem, combination, 5)
            @test interval == expected
            @test combination == saved
            # Later calls must not overwrite either endpoint returned earlier.
            JSimplex._implied_interval(problem, Dict{Int,Rational{BigInt}}(1 => -2), 5)
            @test interval == expected
        end
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

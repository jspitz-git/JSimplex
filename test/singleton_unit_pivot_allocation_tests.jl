using SparseArrays

@testset "Singleton unit pivots avoid exact division allocations" begin
    count = 128
    problem = LinearProblem(sparse(1:count, 1:count, ones(count), count, count), ones(count);
        row_lower=fill(2.0, count), row_upper=fill(6.0, count), column_lower=fill(nothing, count))
    JSimplex.reduce_singleton_rows(problem)
    measured = @timed JSimplex.reduce_singleton_rows(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 11_000
    result = JSimplex.reduce_singleton_rows(problem)
    @test size(result.problem.A) == (0, count)
    @test bound_value.(result.problem.column_lower) == fill(2.0, count)
    @test bound_value.(result.problem.column_upper) == fill(6.0, count)
end

@testset "Singleton bound normalization preserves other pivots and input values" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for pivot in (big(1)//1, -big(1)//1, big(2)//1, big(1)//2), value in (0, 6, -6)
            bound = Bound(T(value))
            saved = deepcopy(bound)
            result = JSimplex._singleton_bound(T, bound, pivot)
            @test bound_value(result) == T(value / pivot)
            @test bound == saved
        end
        unbounded = JSimplex._unbounded_bound(T)
        @test JSimplex._singleton_bound(T, unbounded, big(1)//1) === unbounded
    end
    for T in (Float32, Float64, BigFloat)
        @test isnothing(JSimplex._singleton_bound(T, Bound(T(1)), big(3)//1))
    end
end

@testset "Unit singleton pivots retain signed-zero normalization" begin
    for T in (Float32, Float64, BigFloat)
        bound = Bound(-zero(T))
        result = JSimplex._singleton_bound(T, bound, big(1)//1)
        @test iszero(bound_value(result))
        @test !signbit(bound_value(result))
        @test signbit(bound_value(bound))
    end
end

@testset "Unit singleton pivots still reject inexact low-precision BigFloat bounds" begin
    problem = setprecision(BigFloat, 256) do
        value = BigFloat(1) + BigFloat(2)^(-100)
        LinearProblem(sparse(ones(BigFloat, 1, 1)), ones(BigFloat, 1);
            row_lower=[value], row_upper=[value], column_lower=[nothing])
    end
    saved = deepcopy(problem.row_lower[1])
    setprecision(BigFloat, 64) do
        @test isnothing(JSimplex._singleton_bound(BigFloat, problem.row_lower[1], big(1)//1))
        @test JSimplex.reduce_singleton_rows(problem).problem === problem
        @test problem.row_lower[1] == saved
        @test precision(bound_value(problem.row_lower[1])) == 256
        @test precision(BigFloat) == 64
    end
end

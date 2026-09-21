using SparseArrays

@testset "Relaxation avoids temporary bounds for unchanged domains" begin
    for domain in (CONTINUOUS, INTEGER)
        problem = LinearProblem(spzeros(0, 4096), zeros(4096);
            column_lower=ones(4096), variable_domains=fill(domain, 4096))
        JSimplex.relax_integrality(problem)
        @test (@allocated JSimplex.relax_integrality(problem)) <= 220_000
    end
end

@testset "Unchanged relaxation bounds remain independently owned" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for domains in ([CONTINUOUS, CONTINUOUS], [INTEGER, INTEGER], [CONTINUOUS, INTEGER])
            problem = LinearProblem(sparse(T[2 -1]), T[3, 4];
                column_lower=[T(-2), nothing], column_upper=[nothing, T(7)],
                variable_domains=domains)
            relaxed = @inferred JSimplex.relax_integrality(problem)
            @test relaxed.column_lower == problem.column_lower
            @test relaxed.column_upper == problem.column_upper
            @test relaxed.column_lower !== problem.column_lower
            @test relaxed.column_upper !== problem.column_upper
            @test relaxed.variable_domains == [CONTINUOUS, CONTINUOUS]
            @test relaxed.variable_domains !== problem.variable_domains
            relaxed.column_lower[1] = Bound(T(5))
            relaxed.column_upper[2] = Bound(T(9))
            @test bound_value(problem.column_lower[1]) == T(-2)
            @test bound_value(problem.column_upper[2]) == T(7)
            @test problem.variable_domains == domains
        end
    end
end

@testset "Relaxation copies bounds before the first special domain" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        domains = [CONTINUOUS, INTEGER, SEMI_CONTINUOUS, CONTINUOUS, SEMI_INTEGER, BINARY]
        problem = LinearProblem(spzeros(T, 0, 6), zeros(T, 6);
            column_lower=[T(-2), T(-3), T(2), nothing, T(3), T(0)],
            column_upper=[T(9), T(8), T(7), nothing, T(10), T(1)], variable_domains=domains)
        old_lower, old_upper = copy(problem.column_lower), copy(problem.column_upper)
        relaxed = @inferred JSimplex.relax_integrality(problem)
        @test relaxed.column_lower == Bound{T}[Bound(T(-2)), Bound(T(-3)), Bound(T(0)),
                                               Bound{T}(nothing), Bound(T(0)), Bound(T(0))]
        @test relaxed.column_upper == old_upper
        @test relaxed.variable_domains == fill(CONTINUOUS, 6)
        @test problem.column_lower == old_lower
        @test problem.column_upper == old_upper
        @test problem.variable_domains == domains
        relaxed.column_lower[3] = Bound(T(5))
        relaxed.column_upper[5] = Bound(T(20))
        @test problem.column_lower == old_lower
        @test problem.column_upper == old_upper

        free = LinearProblem(spzeros(T, 0, 1), zeros(T, 1);
            column_lower=[nothing], variable_domains=[SEMI_CONTINUOUS])
        free_relaxed = JSimplex.relax_integrality(free)
        @test !isfinite(only(free_relaxed.column_lower))
        @test !isfinite(only(free_relaxed.column_upper))
        @test free_relaxed.column_lower !== free.column_lower
        @test free_relaxed.column_upper !== free.column_upper
    end
end

@testset "Relaxation preserves precision and empty model ownership" begin
    problem = setprecision(BigFloat, 256) do
        value = BigFloat(1) / 3
        LinearProblem(spzeros(BigFloat, 0, 1), [value];
            column_lower=[value], column_upper=[BigFloat(7) / 3], variable_domains=[INTEGER])
    end
    relaxed = setprecision(BigFloat, 64) do
        JSimplex.relax_integrality(problem)
    end
    @test bound_value(relaxed.column_lower[1]) === bound_value(problem.column_lower[1])
    @test bound_value(relaxed.column_upper[1]) === bound_value(problem.column_upper[1])
    @test precision(bound_value(relaxed.column_lower[1])) == 256

    empty = LinearProblem(spzeros(0, 0), Float64[])
    result = JSimplex.relax_integrality(empty)
    @test size(result.A) == (0, 0)
    @test result !== empty
    @test result.column_lower !== empty.column_lower
    @test result.column_upper !== empty.column_upper
end

using SparseArrays

@testset "Propagation avoids subtracting zero from candidate numerators" begin
    count = 128
    problem = LinearProblem(sparse(1:count, 1:count, ones(count), count, count), ones(count);
        row_lower=fill(2.0, count), row_upper=fill(6.0, count), column_upper=fill(10.0, count))
    JSimplex.propagate_row_bounds(problem)
    measured = @timed JSimplex.propagate_row_bounds(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 18_000
    result = JSimplex.propagate_row_bounds(problem)
    @test bound_value.(result.problem.column_lower) == fill(2.0, count)
    @test bound_value.(result.problem.column_upper) == fill(6.0, count)
end

@testset "Zero other activity from cancellation preserves coefficient direction" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (1, -1, 2, -2, 1//2, -1//2)
        endpoints = sort(T[2coefficient, 6coefficient])
        problem = LinearProblem(sparse(reshape(T[coefficient, 2, -2], 1, 3)), ones(T, 3);
            row_lower=[endpoints[1]], row_upper=[endpoints[2]],
            column_lower=T[0, 1, 1], column_upper=T[10, 1, 1])
        original = deepcopy(problem)
        changed = falses(3)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test bound_value.(result.problem.column_lower) == T[2, 1, 1]
        @test bound_value.(result.problem.column_upper) == T[6, 1, 1]
        @test changed == [true, false, false]
        @test JSimplex.postsolve_primal(result, T[4, 1, 1]) == T[4, 1, 1]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Zero subtraction retains exact conversion and normalized zero" begin
    for T in (Float32, Float64, BigFloat), coefficient in (1, -1, 2, -2)
        low, high = coefficient > 0 ? (-zero(T), T(6coefficient)) : (T(6coefficient), -zero(T))
        problem = LinearProblem(sparse(reshape(T[coefficient], 1, 1)), ones(T, 1);
            row_lower=[low], row_upper=[high], column_lower=[nothing], column_upper=T[10])
        result = JSimplex.propagate_row_bounds(problem)
        @test iszero(bound_value(result.problem.column_lower[1]))
        @test !signbit(bound_value(result.problem.column_lower[1]))
        @test bound_value.(result.problem.column_upper) == T[6]
        @test !isfinite(problem.column_lower[1])
    end
    problem = setprecision(BigFloat, 256) do
        value = BigFloat(1) + BigFloat(2)^(-100)
        LinearProblem(sparse(ones(BigFloat, 1, 1)), ones(BigFloat, 1);
            row_lower=[value], row_upper=BigFloat[6], column_upper=BigFloat[10])
    end
    original = deepcopy(problem)
    setprecision(BigFloat, 64) do
        result = JSimplex.propagate_row_bounds(problem)
        @test bound_value.(result.problem.column_lower) == BigFloat[0]
        @test bound_value.(result.problem.column_upper) == BigFloat[6]
        @test problem.row_lower == original.row_lower
        @test problem.column_upper == original.column_upper
        @test precision(bound_value(problem.row_lower[1])) == 256
        @test precision(BigFloat) == 64
    end
end

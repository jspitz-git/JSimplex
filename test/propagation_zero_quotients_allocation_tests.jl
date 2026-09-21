using SparseArrays

@testset "Propagation reuses zero candidate numerators" begin
    count = 128
    for (kind, limit) in ((:positive, 9_800), (:negative, 9_700), (:negative_unit, 9_400),
                           (:unit, 9_400), (:nonzero, 13_200))
        coefficient = kind == :unit ? 1.0 : kind == :negative_unit ? -1.0 : kind == :negative ? -2.0 : 2.0
        endpoint = kind == :nonzero ? 6.0 : 0.0
        problem = LinearProblem(sparse(1:count, 1:count, fill(coefficient, count), count, count), ones(count);
            row_lower=fill(endpoint, count), row_upper=fill(endpoint, count),
            column_lower=fill(nothing, count), column_upper=fill(nothing, count))
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = JSimplex.propagate_row_bounds(problem)
        @test bound_value.(result.problem.column_lower) == fill(endpoint / coefficient, count)
        @test bound_value.(result.problem.column_upper) == fill(endpoint / coefficient, count)
    end
end

@testset "Cancellation to zero preserves signed candidate normalization" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2, 1//2, -1)
        problem = LinearProblem(sparse(reshape(T[coefficient, 2, -1], 1, 3)), ones(T, 3);
            row_lower=T[3], row_upper=T[3], column_lower=[nothing, T(2), T(1)],
            column_upper=[nothing, T(2), T(1)])
        original = deepcopy(problem)
        changed = falses(3)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test bound_value.(result.problem.column_lower) == T[0, 2, 1]
        @test bound_value.(result.problem.column_upper) == T[0, 2, 1]
        @test changed == [true, false, false]
        @test JSimplex.postsolve_primal(result, T[0, 2, 1]) == T[0, 2, 1]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Zero quotient shortcuts preserve zero signs and unbounded activity" begin
    for T in (Float32, Float64, BigFloat), coefficient in (2, -2, -1)
        problem = LinearProblem(sparse(reshape(T[coefficient], 1, 1)), T[1];
            row_lower=[-zero(T)], row_upper=[-zero(T)], column_lower=[nothing])
        result = JSimplex.propagate_row_bounds(problem)
        @test isequal(bound_value(result.problem.column_lower[1]), zero(T))
        @test isequal(bound_value(result.problem.column_upper[1]), zero(T))
        @test signbit(bound_value(problem.row_lower[1]))
        @test !isfinite(problem.column_lower[1])
    end
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        free = LinearProblem(sparse(reshape(T[2, -2], 1, 2)), ones(T, 2);
            row_lower=T[0], row_upper=T[0], column_lower=[nothing, nothing])
        changed = falses(2)
        @test JSimplex._propagate_row_bounds(free, trues(1), changed).problem === free
        @test !any(changed)
    end
end

@testset "Tiny exact differences remain nonzero below ambient BigFloat precision" begin
    problem = setprecision(BigFloat, 256) do
        endpoint = BigFloat(1) + BigFloat(2)^(-100)
        LinearProblem(sparse(reshape(BigFloat[2, 1], 1, 2)), ones(BigFloat, 2);
            row_lower=[endpoint], row_upper=[endpoint], column_lower=[nothing, BigFloat(1)],
            column_upper=[nothing, BigFloat(1)])
    end
    original = deepcopy(problem)
    setprecision(BigFloat, 64) do
        changed = falses(2)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test bound_value.(result.problem.column_lower) == BigFloat[BigFloat(2)^(-101), 1]
        @test bound_value.(result.problem.column_upper) == BigFloat[BigFloat(2)^(-101), 1]
        @test changed == [true, false]
        @test problem.row_lower == original.row_lower
        @test precision(bound_value(problem.row_lower[1])) == 256
    end
end

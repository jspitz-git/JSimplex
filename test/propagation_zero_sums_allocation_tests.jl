using SparseArrays

@testset "Propagation reuses a term when the running sum is zero" begin
    count = 128
    problem = LinearProblem(sparse(ones(count, 2)), ones(2);
        row_lower=zeros(count), row_upper=fill(20.0, count),
        column_lower=ones(2), column_upper=fill(10.0, 2))
    JSimplex.propagate_row_bounds(problem)
    measured = @timed JSimplex.propagate_row_bounds(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 11_200
    result = JSimplex.propagate_row_bounds(problem)
    @test size(result.problem.A) == (0, 2)
    @test JSimplex.postsolve_primal(result, [1.0, 10.0]) == [1.0, 10.0]
end

@testset "Activity sums retain cancellation and leading zero terms" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for (values, rhs) in (([2, -2, 3, 0], 3), ([0, 2, -2, 3], 3), ([0, -2, -3, 0], -5))
            problem = LinearProblem(sparse(ones(T, 1, 4)), ones(T, 4);
                row_lower=T[rhs], row_upper=T[rhs], column_lower=T.(values), column_upper=T.(values))
            original = deepcopy(problem)
            result = JSimplex.propagate_row_bounds(problem)
            @test size(result.problem.A) == (0, 4)
            @test bound_value.(result.problem.column_lower) == T.(values)
            @test bound_value.(result.problem.column_upper) == T.(values)
            @test problem.column_lower == original.column_lower
            @test problem.column_upper == original.column_upper
        end
    end
end

@testset "A cancelled sum can restart before tightening another column" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(ones(T, 1, 4)), ones(T, 4);
            row_lower=T[5], row_upper=T[7], column_lower=T[2, -2, 3, 0], column_upper=T[2, -2, 3, 10])
        original = deepcopy(problem)
        changed = falses(4)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test bound_value.(result.problem.column_lower) == T[2, -2, 3, 2]
        @test bound_value.(result.problem.column_upper) == T[2, -2, 3, 4]
        @test changed == [false, false, false, true]
        @test JSimplex.postsolve_primal(result, T[2, -2, 3, 3]) == T[2, -2, 3, 3]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
    end
end

@testset "Nonzero finite sums retain unbounded activity counts" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(ones(T, 1, 3)), ones(T, 3);
            row_lower=T[7], row_upper=T[9], column_lower=[nothing, T(2), T(3)],
            column_upper=[nothing, T(2), T(3)])
        changed = falses(3)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test bound_value.(result.problem.column_lower) == T[2, 2, 3]
        @test bound_value.(result.problem.column_upper) == T[4, 2, 3]
        @test changed == [true, false, false]
        @test !isfinite(problem.column_lower[1])
        @test !isfinite(problem.column_upper[1])
    end
end

using SparseArrays

@testset "Propagation avoids dividing candidate bounds by one" begin
    count = 128
    problem = LinearProblem(sparse(1:count, 1:count, ones(count), count, count), ones(count);
        row_lower=fill(2.0, count), row_upper=fill(6.0, count), column_upper=fill(10.0, count))
    JSimplex.propagate_row_bounds(problem)
    measured = @timed JSimplex.propagate_row_bounds(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 22_000
    result = JSimplex.propagate_row_bounds(problem)
    @test bound_value.(result.problem.column_lower) == fill(2.0, count)
    @test bound_value.(result.problem.column_upper) == fill(6.0, count)
end

@testset "Candidate normalization preserves unit, negative and nonunit coefficients" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), pivot in (1, -1, 2, 1//2)
        endpoints = sort(T[2pivot, 6pivot])
        problem = LinearProblem(sparse(reshape(T[pivot], 1, 1)), T[1];
            row_lower=[endpoints[1]], row_upper=[endpoints[2]], column_upper=T[10])
        original = deepcopy(problem)
        changed = falses(1)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test bound_value.(result.problem.column_lower) == T[2]
        @test bound_value.(result.problem.column_upper) == T[6]
        @test changed == [true]
        @test JSimplex.postsolve_primal(result, T[4]) == T[4]
        basis = JSimplex.Basis([2], [JSimplex.AT_LOWER, JSimplex.BASIC])
        restored = JSimplex.restore_basis(result, basis)
        @test restored.basic_indices == basis.basic_indices
        @test restored.states == basis.states
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Propagation candidate conversion retains exactness and zero signs" begin
    for T in (Float32, Float64, BigFloat)
        inexact = LinearProblem(sparse(reshape(T[3], 1, 1)), T[1]; row_lower=T[1], column_upper=T[1])
        @test JSimplex.propagate_row_bounds(inexact).problem === inexact
        signed_zero = LinearProblem(sparse(ones(T, 1, 1)), T[1]; row_lower=[-zero(T)],
            column_lower=[nothing], column_upper=T[1])
        result = JSimplex.propagate_row_bounds(signed_zero)
        @test iszero(bound_value(result.problem.column_lower[1]))
        @test !signbit(bound_value(result.problem.column_lower[1]))
        @test signbit(bound_value(signed_zero.row_lower[1]))
    end
    problem = setprecision(BigFloat, 256) do
        value = BigFloat(1) + BigFloat(2)^(-100)
        LinearProblem(sparse(ones(BigFloat, 1, 1)), ones(BigFloat, 1);
            row_lower=[value], column_upper=BigFloat[10])
    end
    original = deepcopy(problem)
    setprecision(BigFloat, 64) do
        changed = falses(1)
        @test JSimplex._propagate_row_bounds(problem, trues(1), changed).problem === problem
        @test !any(changed)
        @test problem.row_lower == original.row_lower
        @test precision(bound_value(problem.row_lower[1])) == 256
        @test precision(BigFloat) == 64
    end
end

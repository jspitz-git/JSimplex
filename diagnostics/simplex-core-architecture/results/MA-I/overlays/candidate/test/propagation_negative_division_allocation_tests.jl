using SparseArrays

@testset "Propagation negates candidates for negative unit coefficients" begin
    count = 128
    for (kind, limit) in ((:negative, 33_000), (:upper_only, 21_500), (:unit, 29_100),
                           (:positive, 38_900), (:nonunit, 38_600))
        coefficient = kind == :unit ? 1.0 : kind == :positive ? 2.0 : kind == :nonunit ? -2.0 : -1.0
        lower = kind == :upper_only ? nothing : min(4coefficient, 18coefficient)
        problem = LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
            row_lower=fill(lower, count), row_upper=fill(max(4coefficient, 18coefficient), count),
            column_lower=fill(1.0, 2), column_upper=fill(10.0, 2))
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test JSimplex.propagate_row_bounds(problem).problem === problem
    end
end

@testset "Negative unit candidates tighten both bounds with exact orientation" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), (low, high) in ((-4, -1), (2, 6))
        problem = LinearProblem(sparse(reshape(T[-1], 1, 1)), T[1];
            row_lower=T[-high], row_upper=T[-low], column_lower=[nothing])
        original = deepcopy(problem)
        changed = falses(1)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test bound_value.(result.problem.column_lower) == T[low]
        @test bound_value.(result.problem.column_upper) == T[high]
        @test changed == [true]
        @test JSimplex.postsolve_primal(result, T[low]) == T[low]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Candidate normalization checks each negative coefficient separately" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}),
        (coefficients, expected) in (((-1, -2), (9, 9//2)),
                                    ((-2, -1), (9//2, 9)), ((-1, -1), (9, 9)))
        problem = LinearProblem(sparse(reshape(T[coefficients...], 1, 2)), ones(T, 2);
            row_lower=T[-9], row_upper=T[-3], column_upper=fill(T(10), 2))
        original = deepcopy(problem)
        changed = falses(2)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test bound_value.(result.problem.column_lower) == T[0, 0]
        @test bound_value.(result.problem.column_upper) == T[expected...]
        @test changed == trues(2)
        @test result.problem.A == original.A
        @test problem.column_upper == original.column_upper
    end
end

@testset "Negated candidates preserve representability, zero signs and contradictions" begin
    for T in (Float32, Float64, BigFloat)
        inexact = LinearProblem(sparse(reshape(T[-3], 1, 1)), T[1]; row_upper=T[-1], column_upper=T[1])
        @test JSimplex.propagate_row_bounds(inexact).problem === inexact
        signed_zero = LinearProblem(sparse(reshape(T[-1], 1, 1)), T[1]; row_upper=[-zero(T)],
            column_lower=[nothing], column_upper=T[1])
        result = JSimplex.propagate_row_bounds(signed_zero)
        @test iszero(bound_value(result.problem.column_lower[1]))
        @test !signbit(bound_value(result.problem.column_lower[1]))
        @test signbit(bound_value(signed_zero.row_upper[1]))
    end
    problem = setprecision(BigFloat, 256) do
        value = BigFloat(1) + BigFloat(2)^(-100)
        LinearProblem(sparse(reshape(BigFloat[-1], 1, 1)), ones(BigFloat, 1);
            row_upper=[-value], column_upper=BigFloat[10])
    end
    original = deepcopy(problem)
    setprecision(BigFloat, 64) do
        changed = falses(1)
        @test JSimplex._propagate_row_bounds(problem, trues(1), changed).problem === problem
        @test !any(changed)
        @test problem.row_upper == original.row_upper
        @test precision(bound_value(problem.row_upper[1])) == 256
        @test precision(BigFloat) == 64
    end
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        inconsistent = LinearProblem(sparse(reshape(T[-1], 1, 1)), T[1];
            row_upper=T[-2], column_upper=T[1])
        @test JSimplex.propagate_row_bounds(inconsistent).status == INFEASIBLE
        @test bound_value.(inconsistent.column_upper) == T[1]
    end
end

using SparseArrays

@testset "Propagation reuses its zero for finite zero row bounds" begin
    function zero_row_bounds_probe(kind; count=128)
        coefficient = kind == :equality ? -2.0 : 2.0
        low = kind in (:upper_only, :unbounded) ? nothing : kind == :nonzero ? 2.0 : 0.0
        high = kind in (:lower_only, :unbounded) ? nothing : kind == :nonzero ? 6.0 : 0.0
        return LinearProblem(sparse(1:count, 1:count, fill(coefficient, count), count, count), ones(count);
            row_lower=fill(low, count), row_upper=fill(high, count),
            column_lower=fill(nothing, count), column_upper=fill(nothing, count))
    end
    for (kind, limit) in ((:lower_only, 5_500), (:upper_only, 5_500), (:equality, 7_300),
                           (:nonzero, 13_200), (:unbounded, 2_700))
        problem = zero_row_bounds_probe(kind)
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = JSimplex.propagate_row_bounds(problem)
        low = kind in (:upper_only, :unbounded) ? nothing : kind == :nonzero ? 1.0 : 0.0
        high = kind in (:lower_only, :unbounded) ? nothing : kind == :nonzero ? 3.0 : 0.0
        @test result.problem.column_lower == fill(Bound{Float64}(low), 128)
        @test result.problem.column_upper == fill(Bound{Float64}(high), 128)
        @test size(result.problem.A, 1) == (kind == :unbounded ? 0 : 128)
    end
end

@testset "Finite zero row bounds preserve signs and unbounded sides" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2, 1//2, -1//2), kind in (:lower_only, :upper_only, :equality)
        has_lower, has_upper = kind != :upper_only, kind != :lower_only
        problem = LinearProblem(sparse(reshape(T[coefficient], 1, 1)), ones(T, 1);
            row_lower=[has_lower ? -zero(T) : nothing], row_upper=[has_upper ? zero(T) : nothing],
            column_lower=[nothing], column_upper=[nothing])
        original = deepcopy(problem)
        changed = falses(1)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        low = (coefficient > 0 ? has_lower : has_upper) ? zero(T) : nothing
        high = (coefficient > 0 ? has_upper : has_lower) ? zero(T) : nothing
        @test result.problem.column_lower == [Bound{T}(low)]
        @test result.problem.column_upper == [Bound{T}(high)]
        @test changed == [true]
        @test isequal(problem.row_lower, original.row_lower)
        @test isequal(problem.row_upper, original.row_upper)
    end
end

@testset "Shared row zero remains valid as later rows tighten" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[2 0; 1 2]), ones(T, 2);
            row_lower=T[0, 4], row_upper=T[0, 8],
            column_lower=[nothing, nothing], column_upper=[nothing, nothing])
        original = deepcopy(problem)
        for active in (trues(2), BitVector([true, false]))
            changed = falses(2)
            result = JSimplex._propagate_row_bounds(problem, active, changed)
            @test bound_value.(result.problem.column_lower) == T[0, 2]
            @test bound_value.(result.problem.column_upper) == T[0, 4]
            @test changed == trues(2)
            @test JSimplex.postsolve_primal(result, T[0, 3]) == T[0, 3]
            @test problem.column_lower == original.column_lower
            @test problem.column_upper == original.column_upper
        end
    end
end

@testset "Tiny stored BigFloat row bounds remain nonzero" begin
    for coefficient in (2, -2), ambient in (32, 64)
        tiny = setprecision(BigFloat, 256) do
            BigFloat(2)^(-200)
        end
        problem = LinearProblem(sparse(reshape(BigFloat[coefficient], 1, 1)), ones(BigFloat, 1);
            column_lower=[nothing], column_upper=[nothing])
        problem.row_lower[1], problem.row_upper[1] = Bound(-tiny), Bound(tiny)
        setprecision(BigFloat, ambient) do
            result = JSimplex.propagate_row_bounds(problem)
            @test bound_value(result.problem.column_lower[1]) == -tiny / 2
            @test bound_value(result.problem.column_upper[1]) == tiny / 2
            @test !iszero(bound_value(result.problem.column_lower[1]))
            @test !iszero(bound_value(result.problem.column_upper[1]))
            @test precision(bound_value(problem.row_upper[1])) == 256
        end
    end
end

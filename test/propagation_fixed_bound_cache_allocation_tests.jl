using SparseArrays

@testset "Propagation seeds fixed upper-bound caches from lower bounds" begin
    function fixed_bound_cache_probe(kind; count=128)
        coefficient = kind == :negative ? -2.0 : 2.0
        low = kind == :negative ? -2.0 : kind == :zero ? 0.0 : kind in (:unequal, :unbounded) ? 1.0 : 2.0
        high = kind == :unequal ? 10.0 : kind == :unbounded ? nothing : low
        row_lower = isnothing(high) ? coefficient*low : min(coefficient*low, coefficient*high)
        row_upper = isnothing(high) ? nothing : max(coefficient*low, coefficient*high)
        return LinearProblem(sparse(1:count, 1:count, fill(coefficient, count), count, count), ones(count);
            row_lower=fill(row_lower, count), row_upper=fill(row_upper, count),
            column_lower=fill(low, count), column_upper=fill(high, count))
    end
    for (kind, limit) in ((:positive, 8_000), (:negative, 8_000), (:zero, 5_800),
                           (:unequal, 11_850), (:unbounded, 7_300))
        problem = fixed_bound_cache_probe(kind)
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = JSimplex.propagate_row_bounds(problem)
        @test size(result.problem.A) == (0, 128)
        @test result.problem.column_upper == problem.column_upper
    end
end

@testset "Shared fixed-bound caches preserve tightening and sources" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2), fixed in (-2, 0, 2)
        problem = LinearProblem(sparse(reshape(T[coefficient, 1], 1, 2)), ones(T, 2);
            row_lower=T[coefficient*fixed + 3], row_upper=T[coefficient*fixed + 7],
            column_lower=T[fixed, 0], column_upper=T[fixed, 10])
        original = deepcopy(problem)
        changed = falses(2)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test bound_value.(result.problem.column_lower) == T[fixed, 3]
        @test bound_value.(result.problem.column_upper) == T[fixed, 7]
        @test changed == [false, true]
        @test JSimplex.postsolve_primal(result, T[fixed, 5]) == T[fixed, 5]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
    end
end

@testset "Initially unbounded caches follow accepted fixing" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), (low, high) in ((0, 10), (nothing, 10), (0, nothing), (nothing, nothing))
        problem = LinearProblem(sparse(T[1 0; 2 1]), ones(T, 2);
            row_lower=T[2, 7], row_upper=T[2, 11],
            column_lower=[isnothing(low) ? nothing : T(low), T(0)],
            column_upper=[isnothing(high) ? nothing : T(high), T(10)])
        original = deepcopy(problem)
        for active in (trues(2), BitVector([true, false]))
            changed = falses(2)
            result = JSimplex._propagate_row_bounds(problem, active, changed)
            @test bound_value.(result.problem.column_lower) == T[2, 3]
            @test bound_value.(result.problem.column_upper) == T[2, 7]
            @test changed == trues(2)
            @test problem.column_lower == original.column_lower
            @test problem.column_upper == original.column_upper
        end
    end
end

@testset "An unbounded upper endpoint does not share a finite zero" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(reshape(T[2, 1], 1, 2)), ones(T, 2);
            row_upper=T[6], column_lower=zeros(T, 2), column_upper=[nothing, T(0)])
        changed = falses(2)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test bound_value.(result.problem.column_upper) == T[3, 0]
        @test changed == [true, false]
        @test !isfinite(problem.column_upper[1])
    end
end

@testset "Cache seeding distinguishes nearly equal stored bounds" begin
    for equal in (true, false), ambient in (32, 64)
        low = setprecision(BigFloat, 192) do
            BigFloat(2) + BigFloat(2)^(-100)
        end
        high, lower_activity = setprecision(BigFloat, 256) do
            value = BigFloat(low) + (equal ? BigFloat(0) : BigFloat(2)^(-180))
            (value, 2low)
        end
        problem = LinearProblem(sparse(reshape(BigFloat[2, 1], 1, 2)), ones(BigFloat, 2))
        problem.column_lower[1], problem.column_upper[1] = Bound(low), Bound(high)
        problem.column_lower[2], problem.column_upper[2] = Bound(BigFloat(0)), Bound(BigFloat(0))
        # An equality at the lower activity is implied only for a fixed column.
        problem.row_lower[1] = Bound(lower_activity)
        problem.row_upper[1] = Bound(lower_activity)
        setprecision(BigFloat, ambient) do
            @test BigFloat(low) == BigFloat(high)
            result = JSimplex.propagate_row_bounds(problem)
            @test size(result.problem.A, 1) == (equal ? 0 : 1)
            @test bound_value(problem.column_lower[1]) == low
            @test bound_value(problem.column_upper[1]) == high
            @test precision(bound_value(problem.column_lower[1])) == 192
            @test precision(bound_value(problem.column_upper[1])) == 256
        end
    end
end

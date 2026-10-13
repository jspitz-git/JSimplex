using SparseArrays

@testset "Zero activity totals use negation without losing unbounded terms" begin
    for term in (big(7)//3, -big(7)//3)
        total = zero(term)
        JSimplex._other_activity(total, 0, term)
        @test (@allocated JSimplex._other_activity(total, 0, term)) <= 176
    end
    for (total, unbounded, term, expected) in (
        (0, 0, 7//3, -7//3), (0, 0, -7//3, 7//3),
        (0, 1, 7//3, nothing), (0, 2, -7//3, nothing),
        (0, 1, nothing, 0), (0, 2, nothing, nothing),
        (0, 0, 0, 0), (0, 1, 0, nothing),
        (7//3, 0, 7//3, 0), (7//3, 0, -7//3, 14//3),
        (1//3, 0, 7//3, -2))
        value = Rational{BigInt}(total)
        contribution = isnothing(term) ? nothing : Rational{BigInt}(term)
        saved = deepcopy((value, contribution))
        for seed in (nothing, zero(value))
            @test JSimplex._other_activity(value, unbounded, contribution, seed) == expected
            @test (value, contribution) == saved
        end
    end
end

@testset "Zero minimum and maximum totals tighten the correct column sides" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2, 1, -1, 1//2, -1//2), side in (:minimum, :maximum)
        minimum_side = side == :minimum
        endpoint = T(coefficient * (minimum_side ? 1//2 : -1//2))
        upper_row = (coefficient > 0) == minimum_side
        lower = minimum_side ? T[2, 1] : T[1, 2]
        upper = minimum_side ? T[3, 2] : T[2, 3]
        problem = LinearProblem(sparse(reshape(T[coefficient, -coefficient], 1, 2)), ones(T, 2);
            row_lower=[upper_row ? nothing : endpoint], row_upper=[upper_row ? endpoint : nothing],
            column_lower=lower, column_upper=upper)
        saved = deepcopy(problem)
        changed = falses(2)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test bound_value.(result.problem.column_lower) == (minimum_side ? T[2, 3//2] : T[3//2, 2])
        @test bound_value.(result.problem.column_upper) == (minimum_side ? T[5//2, 2] : T[2, 5//2])
        @test changed == [true, true]
        @test JSimplex.postsolve_primal(result, T[2, 2]) == T[2, 2]
        @test problem.column_lower == saved.column_lower
        @test problem.column_upper == saved.column_upper
        @test problem.row_lower == saved.row_lower
        @test problem.row_upper == saved.row_upper
    end
end

@testset "Tightenings from zero totals activate a later row" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), side in (:minimum, :maximum)
        minimum_side = side == :minimum
        problem = LinearProblem(sparse(T[2 -2 0; 1 0 1]), ones(T, 3);
            row_lower=[minimum_side ? nothing : T(-1), T(5)],
            row_upper=[minimum_side ? T(1) : nothing, T(5)],
            column_lower=[minimum_side ? T(2) : T(1), minimum_side ? T(1) : T(2), nothing],
            column_upper=[minimum_side ? T(3) : T(2), minimum_side ? T(2) : T(3), nothing])
        for active in (trues(2), BitVector([true, false]))
            changed = falses(3)
            result = JSimplex._propagate_row_bounds(problem, active, changed)
            @test bound_value.(result.problem.column_lower) == (minimum_side ? T[2, 3//2, 5//2] : T[3//2, 2, 3])
            @test bound_value.(result.problem.column_upper) == (minimum_side ? T[5//2, 2, 3] : T[2, 5//2, 7//2])
            @test changed == [true, true, true]
            @test JSimplex.postsolve_primal(result, T[2, 2, 3]) == T[2, 2, 3]
        end
    end
end

@testset "Tiny exact activity totals remain nonzero at lower working precision" begin
    for side in (:minimum, :maximum), direction in (-1, 1), ambient in (32, 64)
        stored = setprecision(BigFloat, 256) do
            BigFloat(2) + direction * BigFloat(2)^(-200)
        end
        minimum_side = side == :minimum
        problem = LinearProblem(sparse(BigFloat[2 -2]), ones(BigFloat, 2);
            row_lower=[minimum_side ? nothing : BigFloat(-1)],
            row_upper=[minimum_side ? BigFloat(1) : nothing],
            column_lower=minimum_side ? BigFloat[2, 1] : BigFloat[1, 2],
            column_upper=minimum_side ? BigFloat[3, 2] : BigFloat[2, 3])
        column = minimum_side ? 1 : 2
        problem.column_lower[column] = Bound(stored)
        saved = deepcopy(problem.column_lower)
        setprecision(BigFloat, ambient) do
            changed = falses(2)
            result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
            # The opposite column's candidate is 1.5 ± 2^-200 and must be
            # rejected as unrepresentable, while the upper bound 2.5 is exact.
            @test result.problem.column_lower == saved
            @test bound_value.(result.problem.column_upper) == (minimum_side ? BigFloat[2.5, 2] : BigFloat[2, 2.5])
            @test changed == (minimum_side ? [true, false] : [false, true])
            @test problem.column_lower == saved
            @test precision(bound_value(problem.column_lower[column])) == 256
        end
    end
end

@testset "Propagation avoids subtraction from zero activity totals" begin
function propagation_zero_total_negation_probe(kind; count=128)
    coefficient = kind == :unit ? 1.0 : 2.0
    lower_side = kind == :maximum
    first_low, first_high = lower_side ? (1.0,2.0) : (2.0,3.0)
    second_low, second_high = lower_side ? (2.0,3.0) : (1.0,2.0)
    kind == :nonzero && ((first_low, first_high) = (3.0,4.0))
    A = sparse(vcat(collect(1:count),collect(1:count)),
        vcat(collect(1:count),collect(count+1:2count)),
        vcat(fill(coefficient,count),fill(-coefficient,count)),count,2count)
    endpoint = (lower_side ? -0.5 : kind == :nonzero ? 1.5 : 0.5)*coefficient
    return LinearProblem(A,ones(2count);
        row_lower=fill(lower_side ? endpoint : nothing,count),
        row_upper=fill(lower_side ? nothing : endpoint,count),
        column_lower=vcat(fill(kind == :unbounded ? nothing : first_low,count),fill(second_low,count)),
        column_upper=vcat(fill(first_high,count),fill(second_high,count)))
end

    for (kind, limit) in ((:minimum, 35_000), (:maximum, 34_900), (:unit, 30_000),
                          (:nonzero, 36_550), (:unbounded, 23_100))
        problem = propagation_zero_total_negation_probe(kind)
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = JSimplex.propagate_row_bounds(problem)
        expected_lower = kind == :maximum ? vcat(fill(1.5,128),fill(2.0,128)) :
            kind == :nonzero ? vcat(fill(3.0,128),fill(1.5,128)) :
            kind == :unbounded ? vcat(fill(nothing,128),fill(1.0,128)) :
            vcat(fill(2.0,128),fill(1.5,128))
        expected_upper = kind == :maximum ? vcat(fill(2.0,128),fill(2.5,128)) :
            kind == :nonzero ? vcat(fill(3.5,128),fill(2.0,128)) :
            vcat(fill(2.5,128),fill(2.0,128))
        @test result.problem.column_lower == Bound{Float64}.(expected_lower)
        @test bound_value.(result.problem.column_upper) == expected_upper
    end
end

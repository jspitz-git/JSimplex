using SparseArrays

@testset "Propagation avoids general subtraction for cancelled other activity" begin
    count = 128
    for (kind, limit) in ((:positive, 20_700), (:negative, 20_600), (:unit, 15_900),
                           (:free, 10_900), (:unequal, 38_900))
        coefficient = kind == :negative ? -2.0 : kind in (:unit, :free) ? 1.0 : 2.0
        problem = if kind == :unequal
            LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
                row_lower=fill(4coefficient, count), row_upper=fill(18coefficient, count),
                column_lower=fill(1.0, 2), column_upper=fill(10.0, 2))
        else
            LinearProblem(sparse(1:count, 1:count, fill(coefficient, count), count, count), ones(count);
                row_lower=fill(min(2coefficient, 6coefficient), count),
                row_upper=fill(max(2coefficient, 6coefficient), count),
                column_lower=fill(kind == :free ? nothing : 1.0, count),
                column_upper=fill(kind == :free ? nothing : 10.0, count))
        end
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = JSimplex.propagate_row_bounds(problem)
        @test bound_value.(result.problem.column_lower) == fill(kind == :unequal ? 1.0 : 2.0, size(problem.A, 2))
        @test bound_value.(result.problem.column_upper) == fill(kind == :unequal ? 10.0 : 6.0, size(problem.A, 2))
    end
end

@testset "Exact activity cancellation respects unbounded terms" begin
    value = big(7)//3
    term = deepcopy(value)
    JSimplex._other_activity(value, 0, term)
    @test (@allocated JSimplex._other_activity(value, 0, term)) <= 176
    for (total, term, unbounded, expected) in (
        (7//3, 7//3, 0, 0), (-7//3, -7//3, 0, 0),
        (7//3, 7//3, 1, nothing), (7//3, 7//3, 2, nothing),
        (0, 0, 0, 0), (0, 0, 1, nothing),
        (7//3, nothing, 1, 7//3), (7//3, 2//3, 0, 5//3),
        (7//3, -7//3, 0, 14//3))
        exact_total = Rational{BigInt}(total)
        exact_term = isnothing(term) ? nothing : Rational{BigInt}(term)
        saved_total, saved_term = deepcopy(exact_total), deepcopy(exact_term)
        @test JSimplex._other_activity(exact_total, unbounded, exact_term) == expected
        @test exact_total == saved_total
        @test exact_term == saved_term
    end
end

@testset "Cancelled nonzero activity preserves candidate bounds and source values" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2, 1//2, -1//2)
        endpoints = sort(T[2coefficient, 6coefficient])
        # The two fixed columns cancel: the finite activity total equals the
        # first column's term even though this row has three nonzero entries.
        problem = LinearProblem(sparse(reshape(T[coefficient, 2, -2], 1, 3)), ones(T, 3);
            row_lower=[endpoints[1]], row_upper=[endpoints[2]],
            column_lower=T[1, 1, 1], column_upper=T[10, 1, 1])
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

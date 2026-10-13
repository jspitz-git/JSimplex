using SparseArrays

@testset "Propagation reuses its shared zero for cancelled other activity" begin
    count = 128
    for (kind, limit) in ((:positive, 19_700), (:negative, 19_600), (:unit, 14_800),
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

@testset "Shared activity zero preserves finite and unbounded arithmetic" begin
    Q = Rational{BigInt}
    activity_zero = zero(Q)
    saved_zero = deepcopy(activity_zero)
    for (total, term, unbounded, expected) in (
        (7//3, 7//3, 0, 0), (-7//3, -7//3, 0, 0),
        (7//3, 7//3, 1, nothing), (7//3, 7//3, 2, nothing),
        (0, 0, 0, 0), (0, 0, 1, nothing),
        (7//3, nothing, 1, 7//3), (7//3, nothing, 2, nothing),
        (7//3, 0, 0, 7//3), (7//3, 2//3, 0, 5//3),
        (7//3, -7//3, 0, 14//3))
        exact_total = Q(total)
        exact_term = isnothing(term) ? nothing : Q(term)
        original_total, original_term = deepcopy(exact_total), deepcopy(exact_term)
        result = JSimplex._other_activity(exact_total, unbounded, exact_term, activity_zero)
        @test result == expected
        @test result == JSimplex._other_activity(exact_total, unbounded, exact_term)
        if !isnothing(result)
            @test result + Q(2//3) == Q(expected) + Q(2//3)
        end
        @test activity_zero == saved_zero
        @test exact_total == original_total
        @test exact_term == original_term
    end
end

@testset "Shared activity zero survives later rows and incremental propagation" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2, 1//2, -1//2)
        endpoints = sort(T[2coefficient, 6coefficient])
        # Fixed terms cancel in the first row; its tightening activates row two.
        problem = LinearProblem(sparse(T[coefficient 2 -2 0; 1 0 0 -1]), ones(T, 4);
            row_lower=T[endpoints[1], 0], row_upper=T[endpoints[2], 0],
            column_lower=T[1, 1, 1, 0], column_upper=T[10, 1, 1, 10])
        original = deepcopy(problem)
        for active in (trues(2), BitVector([true, false]))
            changed = falses(4)
            result = JSimplex._propagate_row_bounds(problem, active, changed)
            @test bound_value.(result.problem.column_lower) == T[2, 1, 1, 2]
            @test bound_value.(result.problem.column_upper) == T[6, 1, 1, 6]
            @test changed == [true, false, false, true]
            @test JSimplex.postsolve_primal(result, T[4, 1, 1, 4]) == T[4, 1, 1, 4]
            @test problem.column_lower == original.column_lower
            @test problem.column_upper == original.column_upper
            @test problem.row_lower == original.row_lower
            @test problem.row_upper == original.row_upper
        end
    end
end

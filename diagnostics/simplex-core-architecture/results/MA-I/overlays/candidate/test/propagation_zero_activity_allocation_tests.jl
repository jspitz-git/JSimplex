using SparseArrays

@testset "Propagation avoids zero-activity arithmetic allocations" begin
    total, term = big(7)//3, big(0)//1
    JSimplex._other_activity(total, 0, term)
    @test (@allocated JSimplex._other_activity(total, 0, term)) <= 128

    count = 128
    problem = LinearProblem(sparse(1:count, 1:count, ones(count), count, count), ones(count);
        row_lower=fill(2.0, count), row_upper=fill(6.0, count), column_upper=fill(10.0, count))
    JSimplex.propagate_row_bounds(problem)
    measured = @timed JSimplex.propagate_row_bounds(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 20_500
end

@testset "Other activity distinguishes zero, cancellation and unbounded terms" begin
    for (total, unbounded, term, expected) in (
        (7//3, 0, 0//1, 7//3), (7//3, 1, 0//1, nothing),
        (7//3, 1, nothing, 7//3), (7//3, 2, nothing, nothing),
        (7//3, 0, 2//3, 5//3), (7//3, 0, -2//3, 3//1),
        (-7//3, 0, 0//1, -7//3), (0//1, 0, 0//1, 0//1),
        (7//3, 0, 7//3, 0//1))
        exact_total = Rational{BigInt}(total)
        exact_term = isnothing(term) ? nothing : Rational{BigInt}(term)
        saved_total, saved_term = deepcopy(exact_total), deepcopy(exact_term)
        @test JSimplex._other_activity(exact_total, unbounded, exact_term) == expected
        @test exact_total == saved_total
        @test exact_term == saved_term
    end
end

@testset "Zero activities preserve negative columns and cancellation" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for coefficient in (1, -1)
            endpoints = coefficient == 1 ? T[-6, -2] : T[2, 6]
            problem = LinearProblem(sparse(reshape(T[coefficient], 1, 1)), T[1];
                row_lower=[endpoints[1]], row_upper=[endpoints[2]],
                column_lower=T[-10], column_upper=T[0])
            original = deepcopy(problem)
            result = JSimplex.propagate_row_bounds(problem)
            @test bound_value.(result.problem.column_lower) == T[-6]
            @test bound_value.(result.problem.column_upper) == T[-2]
            @test JSimplex.postsolve_primal(result, T[-3]) == T[-3]
            @test problem.column_lower == original.column_lower
            @test problem.column_upper == original.column_upper
        end
        cancellation = LinearProblem(sparse(ones(T, 1, 2)), ones(T, 2);
            row_lower=T[0], row_upper=T[0], column_lower=T[1, -1], column_upper=T[1, -1])
        result = JSimplex.propagate_row_bounds(cancellation)
        @test size(result.problem.A) == (0, 2)
        @test bound_value.(result.problem.column_lower) == T[1, -1]
        @test bound_value.(result.problem.column_upper) == T[1, -1]
    end
end

@testset "Zero finite terms coexist with unbounded activities" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        free = LinearProblem(sparse(ones(T, 1, 2)), ones(T, 2);
            row_lower=T[2], row_upper=T[6], column_lower=[nothing, nothing])
        @test JSimplex.propagate_row_bounds(free).problem === free
        partial = LinearProblem(sparse(ones(T, 1, 2)), ones(T, 2);
            row_lower=T[2], row_upper=T[6], column_lower=[nothing, T(0)],
            column_upper=[nothing, T(0)])
        changed = falses(2)
        result = JSimplex._propagate_row_bounds(partial, trues(1), changed)
        @test bound_value.(result.problem.column_lower) == T[2, 0]
        @test bound_value.(result.problem.column_upper) == T[6, 0]
        @test changed == [true, false]
        @test !isfinite(partial.column_lower[1])
        @test !isfinite(partial.column_upper[1])
    end
end

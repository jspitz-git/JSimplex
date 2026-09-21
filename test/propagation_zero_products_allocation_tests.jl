using SparseArrays

@testset "Propagation avoids multiplying exact zero bounds" begin
    count = 128
    for (low, high, row_low, row_high) in ((0.0, 10.0, 4.0, 12.0), (-10.0, 0.0, -12.0, -4.0))
        problem = LinearProblem(sparse(1:count, 1:count, fill(2.0, count), count, count), ones(count);
            row_lower=fill(row_low, count), row_upper=fill(row_high, count),
            column_lower=fill(low, count), column_upper=fill(high, count))
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= 23_500
    end
end

@testset "Zero products preserve bound direction and nonzero terms" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2, 1//2, -1//2)
        for (low, high, want_low, want_high) in ((0, 10, 2, 6), (-10, 0, -6, -2))
            endpoints = sort(T[coefficient * want_low, coefficient * want_high])
            problem = LinearProblem(sparse(reshape(T[coefficient], 1, 1)), T[1];
                row_lower=[endpoints[1]], row_upper=[endpoints[2]],
                column_lower=T[low], column_upper=T[high])
            original = deepcopy(problem)
            changed = falses(1)
            result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
            @test bound_value.(result.problem.column_lower) == T[want_low]
            @test bound_value.(result.problem.column_upper) == T[want_high]
            @test changed == [true]
            @test JSimplex.postsolve_primal(result, T[want_low]) == T[want_low]
            @test problem.column_lower == original.column_lower
            @test problem.column_upper == original.column_upper
        end
    end
end

@testset "Zero products do not replace unbounded contributions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2)
        free = LinearProblem(sparse(reshape(T[coefficient, -coefficient], 1, 2)), ones(T, 2);
            row_lower=T[4], row_upper=T[12], column_lower=[nothing, nothing])
        @test JSimplex.propagate_row_bounds(free).problem === free

        partial = LinearProblem(sparse(reshape(T[coefficient, -coefficient], 1, 2)), ones(T, 2);
            row_lower=T[4], row_upper=T[12], column_lower=[nothing, T(0)],
            column_upper=[nothing, T(0)])
        original = deepcopy(partial)
        changed = falses(2)
        result = JSimplex._propagate_row_bounds(partial, trues(1), changed)
        @test bound_value.(result.problem.column_lower) == (coefficient > 0 ? T[2, 0] : T[-6, 0])
        @test bound_value.(result.problem.column_upper) == (coefficient > 0 ? T[6, 0] : T[-2, 0])
        @test changed == [true, false]
        @test partial.column_lower == original.column_lower
        @test partial.column_upper == original.column_upper
    end
end

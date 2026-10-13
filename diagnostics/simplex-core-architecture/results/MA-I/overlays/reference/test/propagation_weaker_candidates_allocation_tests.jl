using SparseArrays

@testset "Propagation skips conversion of weaker candidate bounds" begin
    function weaker_candidates_probe(kind; count=128)
        coefficient = kind == :negative ? -2.0 : kind == :unit ? 1.0 : 2.0
        if kind == :tightening
            return LinearProblem(sparse(1:count, 1:count, fill(coefficient, count), count, count), ones(count);
                row_lower=fill(4.0, count), row_upper=fill(12.0, count),
                column_lower=fill(1.0, count), column_upper=fill(10.0, count))
        elseif kind == :equal
            return LinearProblem(sparse(ones(count, 2)), ones(2);
                row_lower=fill(10.0, count), row_upper=fill(10.0, count),
                column_lower=zeros(2), column_upper=fill(10.0, 2))
        end
        return LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
            row_lower=fill(min(4coefficient, 18coefficient), count),
            row_upper=fill(max(4coefficient, 18coefficient), count),
            column_lower=fill(1.0, 2), column_upper=fill(10.0, 2))
    end
    for (kind, limit) in ((:positive, 37_000), (:negative, 36_800), (:unit, 27_000),
                           (:equal, 24_000), (:tightening, 19_700))
        problem = weaker_candidates_probe(kind)
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = JSimplex.propagate_row_bounds(problem)
        if kind == :tightening
            @test bound_value.(result.problem.column_lower) == fill(2.0, 128)
            @test bound_value.(result.problem.column_upper) == fill(6.0, 128)
        else
            @test result.problem === problem
            @test isempty(result.postsolve_stack)
        end
    end
end

@testset "Weaker candidates preserve bounds and flags" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (1, -1, 2, -2, 1//2, -1//2)
        endpoints = sort(T[4coefficient, 18coefficient])
        problem = LinearProblem(sparse(fill(T(coefficient), 1, 2)), ones(T, 2);
            row_lower=[endpoints[1]], row_upper=[endpoints[2]],
            column_lower=T[1, 1], column_upper=T[10, 10])
        original = deepcopy(problem)
        changed = BitVector([true, false])
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test result.problem === problem
        @test changed == [true, false]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
        @test JSimplex.postsolve_primal(result, T[4, 6]) == T[4, 6]
    end
end

@testset "Weaker candidates use bounds tightened by earlier rows" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 0; 1 1]), ones(T, 2);
            row_lower=T[2, 4], row_upper=T[6, 15],
            column_lower=T[1, 1], column_upper=T[10, 10])
        for active in (trues(2), BitVector([true, false]))
            changed = falses(2)
            result = JSimplex._propagate_row_bounds(problem, active, changed)
            @test bound_value.(result.problem.column_lower) == T[2, 1]
            @test bound_value.(result.problem.column_upper) == T[6, 10]
            @test changed == [true, false]
            @test bound_value.(problem.column_lower) == T[1, 1]
            @test bound_value.(problem.column_upper) == T[10, 10]
        end
    end
end

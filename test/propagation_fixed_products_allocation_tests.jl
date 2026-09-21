using SparseArrays

@testset "Propagation reuses fixed-column activity products" begin
    function fixed_products_probe(kind; count=128)
        coefficient = kind == :negative ? -2.0 : kind == :negative_unit ? -1.0 : kind == :unit ? 1.0 : 2.0
        low, high = kind == :unequal ? (1.0, 10.0) : (2.0, 2.0)
        return LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
            row_lower=fill(min(2low*coefficient, 2high*coefficient), count),
            row_upper=fill(max(2low*coefficient, 2high*coefficient), count),
            column_lower=fill(low, 2), column_upper=fill(high, 2))
    end
    for (kind, limit) in ((:positive, 12_000), (:negative, 12_000), (:negative_unit, 9_500),
                           (:unit, 8_600), (:unequal, 15_300))
        problem = fixed_products_probe(kind)
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = JSimplex.propagate_row_bounds(problem)
        @test size(result.problem.A) == (0, 2)
        @test result.problem.column_lower == problem.column_lower
    end
end

@testset "Fixed activity products preserve tightening and inputs" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2, 1//2, -1//2), fixed in (2, -2)
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
        @test problem.A == original.A
    end
end

@testset "Fixed products use bounds accepted from earlier rows" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2)
        problem = LinearProblem(sparse(T[1 0; coefficient 1]), ones(T, 2);
            row_lower=T[2, 2coefficient + 3], row_upper=T[2, 2coefficient + 7],
            column_lower=zeros(T, 2), column_upper=T[10, 10])
        for active in (trues(2), BitVector([true, false]))
            changed = falses(2)
            result = JSimplex._propagate_row_bounds(problem, active, changed)
            @test bound_value.(result.problem.column_lower) == T[2, 3]
            @test bound_value.(result.problem.column_upper) == T[2, 7]
            @test changed == trues(2)
            @test bound_value.(problem.column_lower) == T[0, 0]
            @test bound_value.(problem.column_upper) == T[10, 10]
        end
    end
end

@testset "Nearly equal cached bounds remain a nonfixed interval" begin
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

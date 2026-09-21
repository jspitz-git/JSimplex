using SparseArrays

@testset "Propagation reuses zero for cancelled candidate differences" begin
    function cancelled_candidates_probe(kind; count=128)
        coefficient = kind == :negative ? -2.0 : kind == :unit ? 1.0 : 2.0
        fixed = kind == :zero_other ? 0.0 : 1.0
        endpoint = kind == :unequal ? 5.0 : kind == :zero_other ? 4.0 : 3.0
        A = sparse(vcat(collect(1:count), collect(1:count)),
            vcat(collect(1:count), fill(count+1, count)),
            vcat(fill(coefficient, count), fill(3.0, count)), count, count+1)
        return LinearProblem(A, ones(count+1);
            row_lower=fill(endpoint, count), row_upper=fill(endpoint, count),
            column_lower=vcat(fill(nothing, count), fixed),
            column_upper=vcat(fill(nothing, count), fixed))
    end
    for (kind, limit) in ((:positive, 13_200), (:negative, 13_100), (:unit, 13_200),
                           (:unequal, 17_850), (:zero_other, 14_250))
        problem = cancelled_candidates_probe(kind)
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = JSimplex.propagate_row_bounds(problem)
        expected = vcat(fill(kind == :unequal ? 1.0 : kind == :zero_other ? 2.0 : 0.0, 128), kind == :zero_other ? 0.0 : 1.0)
        @test bound_value.(result.problem.column_lower) == expected
        @test bound_value.(result.problem.column_upper) == expected
    end
end

@testset "Exact candidate cancellation respects signs and missing row bounds" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2, 1//2, -1), kind in (:both, :lower, :upper)
        has_lower, has_upper = kind != :upper, kind != :lower
        problem = LinearProblem(sparse(reshape(T[coefficient, 3], 1, 2)), ones(T, 2);
            row_lower=[has_lower ? T(3) : nothing], row_upper=[has_upper ? T(3) : nothing],
            column_lower=[nothing, T(1)], column_upper=[nothing, T(1)])
        original = deepcopy(problem)
        changed = falses(2)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        low = (coefficient > 0 ? has_lower : has_upper) ? zero(T) : nothing
        high = (coefficient > 0 ? has_upper : has_lower) ? zero(T) : nothing
        @test result.problem.column_lower == [Bound{T}(low), Bound(T(1))]
        @test result.problem.column_upper == [Bound{T}(high), Bound(T(1))]
        @test changed == [true, false]
        @test JSimplex.postsolve_primal(result, T[0, 1]) == T[0, 1]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
    end
end

@testset "Cancelled candidates propagate through later rows" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2)
        problem = LinearProblem(sparse(T[coefficient 0 3; 1 1 0]), ones(T, 3);
            row_lower=T[3, 5], row_upper=T[3, 5],
            column_lower=[nothing, nothing, T(1)], column_upper=[nothing, nothing, T(1)])
        for active in (trues(2), BitVector([true, false]))
            changed = falses(3)
            result = JSimplex._propagate_row_bounds(problem, active, changed)
            @test bound_value.(result.problem.column_lower) == T[0, 5, 1]
            @test bound_value.(result.problem.column_upper) == T[0, 5, 1]
            @test changed == [true, true, false]
            @test JSimplex.postsolve_primal(result, T[0, 5, 1]) == T[0, 5, 1]
        end
    end
end

@testset "Nearly cancelled candidates retain their tiny exact residual" begin
    for coefficient in (2, -2), direction in (1, -1), ambient in (32, 64)
        endpoint, residual = setprecision(BigFloat, 256) do
            delta = direction * BigFloat(2)^(-100)
            (BigFloat(3) + delta, delta / coefficient)
        end
        problem = LinearProblem(sparse(reshape(BigFloat[coefficient, 3], 1, 2)), ones(BigFloat, 2);
            column_lower=[nothing, BigFloat(1)], column_upper=[nothing, BigFloat(1)])
        problem.row_lower[1], problem.row_upper[1] = Bound(endpoint), Bound(endpoint)
        setprecision(BigFloat, ambient) do
            @test BigFloat(endpoint) == BigFloat(3)
            result = JSimplex.propagate_row_bounds(problem)
            @test bound_value(result.problem.column_lower[1]) == residual
            @test bound_value(result.problem.column_upper[1]) == residual
            @test !iszero(bound_value(result.problem.column_lower[1]))
            @test precision(bound_value(problem.row_lower[1])) == 256
        end
    end
end

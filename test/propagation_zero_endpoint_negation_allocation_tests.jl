using SparseArrays

@testset "Propagation negates activity for zero row endpoints" begin
    function zero_endpoint_negation_probe(kind; count=128)
        coefficient = kind == :negative ? -2.0 : kind == :unit ? 1.0 : 2.0
        fixed = kind == :zero_other ? 0.0 : 1.0
        endpoint = kind == :unequal ? 5.0 : kind == :zero_other ? 4.0 : 0.0
        A = sparse(vcat(collect(1:count), collect(1:count)),
            vcat(collect(1:count), fill(count+1, count)),
            vcat(fill(coefficient, count), fill(3.0, count)), count, count+1)
        return LinearProblem(A, ones(count+1);
            row_lower=fill(endpoint, count), row_upper=fill(endpoint, count),
            column_lower=vcat(fill(nothing, count), fixed),
            column_upper=vcat(fill(nothing, count), fixed))
    end
    for (kind, limit) in ((:positive, 15_200), (:negative, 15_100), (:unit, 13_000),
                           (:unequal, 17_850), (:zero_other, 14_250))
        problem = zero_endpoint_negation_probe(kind)
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = JSimplex.propagate_row_bounds(problem)
        coefficient = kind == :negative ? -2.0 : kind == :unit ? 1.0 : 2.0
        expected = vcat(fill(kind == :unequal ? 1.0 : kind == :zero_other ? 2.0 : -3/coefficient, 128), kind == :zero_other ? 0.0 : 1.0)
        @test bound_value.(result.problem.column_lower) == expected
        @test bound_value.(result.problem.column_upper) == expected
    end
end

@testset "Zero endpoint negation preserves both activity signs and missing bounds" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2), fixed in (1, -1), kind in (:both, :lower, :upper)
        has_lower, has_upper = kind != :upper, kind != :lower
        problem = LinearProblem(sparse(reshape(T[coefficient, 3], 1, 2)), ones(T, 2);
            row_lower=[has_lower ? -zero(T) : nothing], row_upper=[has_upper ? zero(T) : nothing],
            column_lower=[nothing, T(fixed)], column_upper=[nothing, T(fixed)])
        original = deepcopy(problem)
        changed = falses(2)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        value = T(-3fixed / coefficient)
        low = (coefficient > 0 ? has_lower : has_upper) ? value : nothing
        high = (coefficient > 0 ? has_upper : has_lower) ? value : nothing
        @test result.problem.column_lower == [Bound{T}(low), Bound(T(fixed))]
        @test result.problem.column_upper == [Bound{T}(high), Bound(T(fixed))]
        @test changed == [true, false]
        @test JSimplex.postsolve_primal(result, T[value, fixed]) == T[value, fixed]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
    end
end

@testset "Negated activity candidates activate later nonzero rows" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (2, -2)
        problem = LinearProblem(sparse(T[coefficient 0 3; 1 1 0]), ones(T, 3);
            row_lower=T[0, 5], row_upper=T[0, 5],
            column_lower=[nothing, nothing, T(1)], column_upper=[nothing, nothing, T(1)])
        expected = T[-3/coefficient, 5+3/coefficient, 1]
        for active in (trues(2), BitVector([true, false]))
            changed = falses(3)
            result = JSimplex._propagate_row_bounds(problem, active, changed)
            @test bound_value.(result.problem.column_lower) == expected
            @test bound_value.(result.problem.column_upper) == expected
            @test changed == [true, true, false]
            @test JSimplex.postsolve_primal(result, expected) == expected
        end
    end
end

@testset "Tiny nonzero row endpoints do not become zero during subtraction" begin
    for coefficient in (2, -2), direction in (1, -1), ambient in (32, 64)
        endpoint = setprecision(BigFloat, 256) do
            direction * BigFloat(2)^(-200)
        end
        problem = LinearProblem(sparse(reshape(BigFloat[coefficient, 3], 1, 2)), ones(BigFloat, 2);
            column_lower=[nothing, BigFloat(1)], column_upper=[nothing, BigFloat(1)])
        problem.row_lower[1], problem.row_upper[1] = Bound(endpoint), Bound(endpoint)
        setprecision(BigFloat, ambient) do
            changed = falses(2)
            result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
            # The exact candidate differs slightly from -3/coefficient and is
            # unrepresentable at this precision; replacing the endpoint by zero
            # would incorrectly accept the nearby representable bound.
            @test result.problem === problem
            @test !any(changed)
            @test !isfinite(result.problem.column_lower[1])
            @test !isfinite(result.problem.column_upper[1])
            @test precision(bound_value(problem.row_lower[1])) == 256
        end
    end
end

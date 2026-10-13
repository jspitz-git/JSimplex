using SparseArrays

@testset "Propagation converts equal row bounds once" begin
    function equal_row_bounds_probe(kind; count=128)
        coefficient = kind == :negative ? -2.0 : kind == :unit ? 1.0 : 2.0
        if kind in (:unequal, :upper_only)
            return LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
                row_lower=fill(kind == :upper_only ? nothing : 4coefficient, count),
                row_upper=fill(18coefficient, count),
                column_lower=fill(1.0, 2), column_upper=fill(10.0, 2))
        end
        return LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
            row_lower=fill(10coefficient, count), row_upper=fill(10coefficient, count),
            column_lower=zeros(2), column_upper=fill(10.0, 2))
    end
    for (kind, limit) in ((:positive, 19_900), (:negative, 19_650), (:unit, 15_000),
                           (:unequal, 31_200), (:upper_only, 22_200))
        problem = equal_row_bounds_probe(kind)
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = JSimplex.propagate_row_bounds(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
    end
end

@testset "Equal row bounds preserve source values and propagation" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (1, -1, 2, -2, 1//2, -1//2)
        problem = LinearProblem(sparse(T[coefficient 0; 1 1]), ones(T, 2);
            row_lower=T[3coefficient, 7], row_upper=T[3coefficient, 7],
            column_lower=zeros(T, 2), column_upper=T[10, 10])
        original = deepcopy(problem)
        changed = falses(2)
        active = BitVector([true, false])
        result = JSimplex._propagate_row_bounds(problem, active, changed)
        @test bound_value.(result.problem.column_lower) == T[3, 4]
        @test bound_value.(result.problem.column_upper) == T[3, 4]
        @test changed == trues(2)
        @test active == [true, false]
        @test JSimplex.postsolve_primal(result, T[3, 4]) == T[3, 4]
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
    end
end

@testset "Finite zero row bounds remain distinct from unbounded bounds" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), kind in (:equal, :lower_only, :upper_only, :free)
        lower = kind in (:upper_only, :free) ? nothing : -zero(T)
        upper = kind in (:lower_only, :free) ? nothing : zero(T)
        problem = LinearProblem(sparse(ones(T, 1, 2)), ones(T, 2);
            row_lower=[lower], row_upper=[upper], column_upper=T[10, 10])
        result = JSimplex.propagate_row_bounds(problem)
        if kind in (:equal, :upper_only)
            @test bound_value.(result.problem.column_upper) == zeros(T, 2)
        else
            @test size(result.problem.A, 1) == 0
        end
        @test bound_value.(problem.column_upper) == T[10, 10]
        @test isfinite(problem.row_lower[1]) == !isnothing(lower)
        @test isfinite(problem.row_upper[1]) == !isnothing(upper)
    end
end

@testset "Row-bound comparison respects stored BigFloat precision" begin
    for equal in (true, false), ambient in (32, 64, 128)
        low, high = setprecision(BigFloat, 256) do
            value = BigFloat(3) + BigFloat(2)^(-200)
            (value, value + (equal ? BigFloat(0) : BigFloat(2)^(-230)))
        end
        problem = LinearProblem(sparse(ones(BigFloat, 1, 2)), ones(BigFloat, 2);
            row_lower=[BigFloat(3)], row_upper=[BigFloat(3)], column_upper=BigFloat[10, 10])
        # Insert stored values directly; construction would normalize precision.
        problem.row_lower[1] = Bound(low)
        problem.row_upper[1] = Bound(high)
        original = deepcopy(problem)
        setprecision(BigFloat, ambient) do
            changed = falses(2)
            result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
            @test result.problem === problem
            @test !any(changed)
            @test problem.row_lower == original.row_lower
            @test problem.row_upper == original.row_upper
            @test precision(bound_value(problem.row_lower[1])) == 256
            @test precision(bound_value(problem.row_upper[1])) == 256
        end
    end
end

@testset "Near-equal stored row bounds retain the feasible endpoint" begin
    for equal in (true, false), ambient in (32, 64)
        low = setprecision(BigFloat, 192) do
            BigFloat(3) + BigFloat(2)^(-100)
        end
        high = setprecision(BigFloat, 256) do
            BigFloat(low) + (equal ? BigFloat(0) : BigFloat(2)^(-180))
        end
        problem = LinearProblem(sparse(ones(BigFloat, 1, 1)), ones(BigFloat, 1))
        problem.row_lower[1], problem.row_upper[1] = Bound(low), Bound(high)
        problem.column_lower[1], problem.column_upper[1] = Bound(high), Bound(high)
        setprecision(BigFloat, ambient) do
            @test BigFloat(low) == BigFloat(high)
            result = JSimplex.propagate_row_bounds(problem)
            # Mistaking unequal stored endpoints for equal ones would report
            # infeasibility instead of removing this satisfied row.
            @test result isa JSimplex.PresolveResult
            if result isa JSimplex.PresolveResult
                @test size(result.problem.A, 1) == 0
                @test bound_value(result.problem.column_lower[1]) == high
            end
            @test precision(bound_value(problem.row_lower[1])) == 192
            @test precision(bound_value(problem.row_upper[1])) == 256
        end
    end
end

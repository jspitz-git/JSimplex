using SparseArrays

@testset "Dependent elimination skips multiplication by unit source terms" begin
    count = 128
    for (scale, limit) in ((2.0, 20_500), (-2.0, 20_500), (1.0, 15_400))
        multipliers = [1.0; fill(scale, count - 1)]
        problem = LinearProblem(sparse(multipliers * [1.0 2.0 -1.0]), zeros(3);
            row_lower=min.(multipliers, 6multipliers), row_upper=max.(multipliers, 6multipliers),
            column_lower=fill(nothing, 3))
        JSimplex.reduce_dependent_rows(problem)
        measured = @timed JSimplex.reduce_dependent_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test only(JSimplex.reduce_dependent_rows(problem).postsolve_stack).rows == [1]
    end
end

@testset "Unit source terms preserve exact subtraction and cancellation" begin
    Q = Rational{BigInt}
    for (scale, expected) in (
        (2, Dict(2 => 5, 3 => -4, 5 => 7, 6 => -2)),
        (-2, Dict(2 => 1, 3 => 4, 5 => 7, 6 => 2)),
        (1, Dict(2 => 4, 3 => -2, 5 => 7, 6 => -1)),
        (-1, Dict(2 => 2, 3 => 2, 5 => 7, 6 => 1)),
        (-3, Dict(3 => 6, 5 => 7, 6 => 3)),
        (1//2, Dict(2 => 7//2, 3 => -1, 5 => 7, 6 => -1//2)),
        (0, Dict(2 => 3, 5 => 7)))
        source = Dict{Int,Q}(1 => 1, 2 => -1, 3 => 2, 4 => 0, 6 => 1)
        target = Dict{Int,Q}(1 => scale, 2 => 3, 3 => 0, 5 => 7)
        factor = Q(scale)
        original_source, original_factor = deepcopy(source), deepcopy(factor)
        JSimplex._subtract_scaled!(target, source, factor)
        @test target == expected
        @test source == original_source
        @test factor == original_factor
    end
end

@testset "Unit source terms preserve dependency proofs and contradictions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), scale in (2, -2, 1//2)
        s = T(scale)
        A = sparse(T[1 2 0; s 2s 1; 2s 4s 1])
        rhs = T[3, 3s + 1, 6s + 1]
        problem = LinearProblem(A, zeros(T, 3); row_lower=rhs, row_upper=rhs,
            column_lower=fill(nothing, 3))
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == T[1 2 0; s 2s 1]
        @test bound_value.(result.problem.row_lower) == T[3, 3s + 1]
        @test bound_value.(result.problem.row_upper) == T[3, 3s + 1]
        @test JSimplex.postsolve_primal(result, T[1, 1, 1]) == T[1, 1, 1]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(6s + 2))
        problem.row_upper[3] = Bound(T(6s + 2))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
    end
end

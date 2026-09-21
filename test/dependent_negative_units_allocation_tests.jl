using SparseArrays

@testset "Dependent elimination skips general negative-unit multiplication" begin
    count = 128
    for (scale, limit) in ((2.0, 19_400), (-1.0, 18_800), (1.0, 15_400))
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

@testset "Negative unit products preserve exact subtraction" begin
    Q = Rational{BigInt}
    for (scale, expected) in (
        (-1, Dict(2 => 5, 3 => 2, 5 => 7, 6 => -1)),
        (-2, Dict(1 => 1, 2 => 7, 3 => 4, 5 => 7, 6 => -2)),
        (2, Dict(1 => -3, 2 => -1, 3 => -4, 5 => 7, 6 => 2)),
        (1, Dict(1 => -2, 2 => 1, 3 => -2, 5 => 7, 6 => 1)),
        (-1//2, Dict(1 => -1//2, 2 => 4, 3 => 1, 5 => 7, 6 => -1//2)),
        (0, Dict(1 => -1, 2 => 3, 5 => 7)))
        source = Dict{Int,Q}(1 => 1, 2 => 2, 3 => 2, 4 => 0, 6 => -1)
        target = Dict{Int,Q}(1 => -1, 2 => 3, 3 => 0, 5 => 7)
        factor = Q(scale)
        original_source, original_factor = deepcopy(source), deepcopy(factor)
        JSimplex._subtract_scaled!(target, source, factor)
        @test target == expected
        @test source == original_source
        @test factor == original_factor
    end
    source = Dict{Int,Q}(1 => -1, 2 => -1)
    target = Dict{Int,Q}(1 => 1, 2 => -1)
    JSimplex._subtract_scaled!(target, source, Q(-1))
    @test target == Dict(2 => -2)
    @test source == Dict(1 => -1, 2 => -1)
end

@testset "Negative unit elimination preserves dependency proofs" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), scale in (-1, 2, -1//2)
        s = T(scale)
        A = sparse(T[1 -1 0; s -s 1; 2s -2s 1])
        rhs = T[-1, -s + 1, -2s + 1]
        problem = LinearProblem(A, zeros(T, 3); row_lower=rhs, row_upper=rhs,
            column_lower=fill(nothing, 3))
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == T[1 -1 0; s -s 1]
        @test bound_value.(result.problem.row_lower) == T[-1, -s + 1]
        @test bound_value.(result.problem.row_upper) == T[-1, -s + 1]
        @test JSimplex.postsolve_primal(result, T[1, 2, 1]) == T[1, 2, 1]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(-2s + 2))
        problem.row_upper[3] = Bound(T(-2s + 2))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
    end
end

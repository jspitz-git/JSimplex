using SparseArrays

@testset "Dependent elimination reuses a negated scale for unit terms" begin
    count = 128
    for (scale, value, limit) in ((2.0, 1.0, 2_900), (2.0, 2.0, 4_300), (-1.0, 1.0, 1_700))
        A = sparse([ones(Int, count+1); 2; 2], [collect(1:count+1); 1; count+2],
            [1.0; fill(value, count); scale; 1.0], 2, count+2)
        problem = LinearProblem(A, zeros(count+2); row_upper=fill(3.0, 2),
            column_lower=fill(nothing, count+2))
        JSimplex.reduce_dependent_rows(problem)
        measured = @timed JSimplex.reduce_dependent_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test JSimplex.reduce_dependent_rows(problem).problem === problem
    end
end

@testset "Cached negative scale preserves missing and existing entries" begin
    Q = Rational{BigInt}
    for (scale, expected) in (
        (2, Dict(1 => -2, 2 => -2, 3 => 1, 4 => 2, 6 => -4)),
        (-2, Dict(1 => 2, 2 => 2, 3 => 5, 4 => -2, 6 => 4)),
        (1//2, Dict(1 => -1//2, 2 => -1//2, 3 => 5//2, 4 => 1//2, 6 => -1)),
        (0, Dict(3 => 3)),
        (-1, Dict(1 => 1, 2 => 1, 3 => 4, 4 => -1, 6 => 2)))
        source = Dict{Int,Q}(1 => 1, 2 => 1, 3 => 1, 4 => -1, 5 => 0, 6 => 2)
        target = Dict{Int,Q}(3 => 3)
        factor = Q(scale)
        original_source, original_factor = deepcopy(source), deepcopy(factor)
        JSimplex._subtract_scaled!(target, source, factor)
        @test target == expected
        @test source == original_source
        @test factor == original_factor
        @test !haskey(target, 5)
        # A later call must not overwrite the cached values returned earlier.
        JSimplex._subtract_scaled!(Dict{Int,Q}(), source, Q(7))
        @test target == expected
    end
    target = Dict{Int,Q}(1 => 2)
    JSimplex._subtract_scaled!(target, Dict{Int,Q}(1 => 1, 2 => 1, 3 => 1), Q(2))
    @test target == Dict(2 => -2, 3 => -2)
end

@testset "Cached negative scale preserves dependency proofs" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), scale in (2, -2, 1//2)
        s = T(scale)
        A = sparse(T[1 1 1 0; s 0 0 1; 1+s 1 1 1])
        rhs = T[3, s+1, s+4]
        problem = LinearProblem(A, zeros(T, 4); row_lower=rhs, row_upper=rhs,
            column_lower=fill(nothing, 4))
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == T[1 1 1 0; s 0 0 1]
        @test bound_value.(result.problem.row_lower) == T[3, s+1]
        @test bound_value.(result.problem.row_upper) == T[3, s+1]
        @test JSimplex.postsolve_primal(result, T[1, 1, 1, 1]) == T[1, 1, 1, 1]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(s+5))
        problem.row_upper[3] = Bound(T(s+5))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
    end
end

using SparseArrays

@testset "Dependent elimination reuses missing negative-unit contributions" begin
    count = 128
    for (scale, value, limit) in ((-1.0, 2.0, 6_450), (2.0, -1.0, 6_450), (2.0, 2.0, 7_150))
        A = kron(spdiagm(0 => ones(count ÷ 2)), sparse([1.0 value 0.0; scale 0.0 1.0]))
        problem = LinearProblem(A, zeros(size(A, 2)); row_upper=fill(3.0, count),
            column_lower=fill(nothing, size(A, 2)))
        JSimplex.reduce_dependent_rows(problem)
        measured = @timed JSimplex.reduce_dependent_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test JSimplex.reduce_dependent_rows(problem).problem === problem
    end
end

@testset "Missing negative-unit products preserve exact values" begin
    Q = Rational{BigInt}
    for (scale, expected) in (
        (-1, Dict(1 => -1, 3 => 1, 4 => 2, 5 => 1//2)),
        (2, Dict(1 => 2, 3 => -2, 4 => -4, 5 => -1)),
        (0, Dict{Int,Int}()),
        (1//2, Dict(1 => 1//2, 3 => -1//2, 4 => -1, 5 => -1//4)))
        source = Dict{Int,Q}(1 => -1, 2 => 0, 3 => 1, 4 => 2, 5 => 1//2)
        target = Dict{Int,Q}()
        factor = Q(scale)
        original_source, original_factor = deepcopy(source), deepcopy(factor)
        JSimplex._subtract_scaled!(target, source, factor)
        @test target == expected
        @test source == original_source
        @test factor == original_factor
        @test !haskey(target, 2)
    end
    # Existing entries must retain subtraction and exact cancellation.
    target = Dict{Int,Q}(1 => -1, 2 => 0, 3 => 2)
    source = Dict{Int,Q}(1 => 1, 2 => 0, 3 => -1, 4 => -1)
    JSimplex._subtract_scaled!(target, source, Q(-1))
    @test target == Dict(3 => 1, 4 => -1)
    @test source == Dict(1 => 1, 2 => 0, 3 => -1, 4 => -1)
end

@testset "Missing entries preserve elimination proofs and contradictions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), (s0, v0) in ((-1, 2), (2, -1), (1//2, -1))
        s, v = T(s0), T(v0)
        A = sparse(T[1 v 0; s 0 1; 1+s v 1])
        rhs = T[1+v, s+1, 2+s+v]
        problem = LinearProblem(A, zeros(T, 3); row_lower=rhs, row_upper=rhs,
            column_lower=fill(nothing, 3))
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2]
        @test result.problem.A == T[1 v 0; s 0 1]
        @test bound_value.(result.problem.row_lower) == T[1+v, s+1]
        @test bound_value.(result.problem.row_upper) == T[1+v, s+1]
        @test JSimplex.postsolve_primal(result, T[1, 1, 1]) == T[1, 1, 1]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(3+s+v))
        problem.row_upper[3] = Bound(T(3+s+v))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
    end
end

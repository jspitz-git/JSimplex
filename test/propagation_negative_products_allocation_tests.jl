using SparseArrays

@testset "Propagation negates exact bounds for negative unit products" begin
    count = 128
    for (kind, limit) in ((:negative, 13_000), (:zero, 9_900), (:unit, 10_150),
                           (:positive, 15_300), (:nonunit, 15_300))
        coefficient = kind == :unit ? 1.0 : kind == :positive ? 2.0 : kind == :nonunit ? -2.0 : -1.0
        low = kind == :zero ? 0.0 : 1.0
        problem = LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
            row_lower=fill(min(2low*coefficient, 20coefficient), count),
            row_upper=fill(max(2low*coefficient, 20coefficient), count),
            column_lower=fill(low, 2), column_upper=fill(10.0, 2))
        JSimplex.propagate_row_bounds(problem)
        measured = @timed JSimplex.propagate_row_bounds(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test size(JSimplex.propagate_row_bounds(problem).problem.A) == (0, 2)
    end
end

@testset "Negated activity terms remain valid as incremental caches change" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), scale in (1, 2)
        problem = LinearProblem(sparse(T[-1 -1 0; 0 -1 -1; -scale 0 scale]), ones(T, 3);
            row_lower=[T(-6), nothing, nothing], row_upper=[nothing, T(-8), T(2scale)],
            column_upper=fill(T(10), 3))
        original = deepcopy(problem)
        active, changed = BitVector([true, false, false]), falses(3)
        result = JSimplex._propagate_row_bounds(problem, active, changed)
        @test bound_value.(result.problem.column_lower) == T[0, 0, 2]
        @test bound_value.(result.problem.column_upper) == T[6, 6, 8]
        @test changed == trues(3)
        @test active == [true, false, false]
        @test result.problem.A == problem.A
        @test JSimplex.postsolve_primal(result, T[2, 6, 2]) == T[2, 6, 2]
        basis = JSimplex.Basis([4, 5, 6], [JSimplex.AT_LOWER, JSimplex.AT_UPPER,
            JSimplex.AT_LOWER, JSimplex.BASIC, JSimplex.BASIC, JSimplex.BASIC])
        restored = JSimplex.restore_basis(result, basis)
        @test restored.basic_indices == basis.basic_indices
        @test restored.states == basis.states
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
        @test problem.A == original.A
    end
end

@testset "Negative unit propagation preserves free activity and contradictions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        free = LinearProblem(sparse(-ones(T, 1, 2)), ones(T, 2);
            row_lower=T[-1], row_upper=T[0], column_lower=[nothing, nothing])
        @test JSimplex.propagate_row_bounds(free).problem === free
        partial = LinearProblem(sparse(-ones(T, 1, 2)), ones(T, 2);
            row_lower=T[-5], row_upper=T[-3], column_lower=[nothing, T(1)],
            column_upper=[nothing, T(2)])
        result = JSimplex.propagate_row_bounds(partial)
        @test bound_value.(result.problem.column_lower) == T[1, 1]
        @test bound_value.(result.problem.column_upper) == T[4, 2]
        @test !isfinite(partial.column_lower[1])
        @test !isfinite(partial.column_upper[1])

        inconsistent = LinearProblem(sparse(-ones(T, 1, 2)), ones(T, 2);
            row_lower=T[1], column_lower=fill(T(1), 2), column_upper=fill(T(2), 2))
        @test JSimplex.propagate_row_bounds(inconsistent).status == INFEASIBLE
        @test bound_value.(inconsistent.column_lower) == T[1, 1]
    end
end

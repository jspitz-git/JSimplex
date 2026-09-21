using SparseArrays

@testset "Propagation avoids multiplying exact bounds by one" begin
    count = 128
    problem = LinearProblem(sparse(ones(count, 2)), ones(2);
        row_lower=zeros(count), row_upper=fill(20.0, count), column_upper=fill(10.0, 2))
    JSimplex.propagate_row_bounds(problem)
    measured = @timed JSimplex.propagate_row_bounds(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 16_000
    @test size(JSimplex.propagate_row_bounds(problem).problem.A) == (0, 2)
end

@testset "Unit activity terms retain original values as incremental caches change" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), scale in (1, 2)
        problem = LinearProblem(sparse(T[1 1 0; 0 1 1; -scale 0 scale]), ones(T, 3);
            row_lower=[nothing, T(8), nothing], row_upper=[T(6), nothing, T(2scale)],
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

@testset "Unit propagation keeps unbounded activity terms distinct from zero" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        free = LinearProblem(sparse(ones(T, 1, 2)), ones(T, 2);
            row_lower=T[0], row_upper=T[1], column_lower=[nothing, nothing])
        @test JSimplex.propagate_row_bounds(free).problem === free
        partial = LinearProblem(sparse(ones(T, 1, 2)), ones(T, 2);
            row_lower=T[3], row_upper=T[5], column_lower=[nothing, T(1)],
            column_upper=[nothing, T(2)])
        result = JSimplex.propagate_row_bounds(partial)
        @test bound_value.(result.problem.column_lower) == T[1, 1]
        @test bound_value.(result.problem.column_upper) == T[4, 2]
        @test !isfinite(partial.column_lower[1])
        @test !isfinite(partial.column_upper[1])
    end
end

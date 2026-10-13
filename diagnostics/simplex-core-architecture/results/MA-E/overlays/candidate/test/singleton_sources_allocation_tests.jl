using SparseArrays

@testset "Singleton identity passes avoid unused source maps" begin
    count = 128
    for kind in (:wide, :rejected)
        A = kind == :wide ? sparse(ones(count, count)) :
            sparse([1], [1], [3.0], 1, count)
        problem = LinearProblem(A, ones(count); row_lower=ones(size(A, 1)),
            row_upper=ones(size(A, 1)), column_lower=fill(nothing, count))
        JSimplex.reduce_singleton_rows(problem)
        if kind == :wide
            @test (@allocated JSimplex.reduce_singleton_rows(problem)) <= 4_000
        else
            # Exact-arithmetic byte totals vary with context; source-map
            # allocation counts remain stable after warmup.
            measured = @timed JSimplex.reduce_singleton_rows(problem)
            @test Base.gc_alloc_count(measured.gcstats) <= 155
        end
        @test JSimplex.reduce_singleton_rows(problem).problem === problem
    end
end

@testset "Singleton source maps preserve repeated tightening and basis restoration" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(reshape(T[0, 1, -1], 3, 1)), T[1];
            row_lower=T[0, 2, -7], row_upper=T[0, 8, -3],
            column_lower=T[0], column_upper=T[10])
        original = deepcopy(problem)
        result = JSimplex.reduce_singleton_rows(problem)
        step = only(result.postsolve_stack)
        @test size(result.problem.A) == (1, 1)
        @test bound_value.(result.problem.column_lower) == T[3]
        @test bound_value.(result.problem.column_upper) == T[7]
        @test step.lower_sources == [(3, JSimplex.AT_UPPER)]
        @test step.upper_sources == [(3, JSimplex.AT_LOWER)]
        @test JSimplex.postsolve_primal(result, T[3]) == T[3]
        for (state, slack_state) in ((JSimplex.AT_LOWER, JSimplex.AT_UPPER),
                                     (JSimplex.AT_UPPER, JSimplex.AT_LOWER))
            basis = JSimplex.Basis([2], [state, JSimplex.BASIC])
            restored = JSimplex.restore_basis(result, basis)
            @test restored.basic_indices == [2, 3, 1]
            @test restored.states == [JSimplex.BASIC, JSimplex.BASIC,
                                      JSimplex.BASIC, slack_state]
        end
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Removed singletons retain empty source maps when no bounds tighten" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(reshape(T[1], 1, 1)), T[1];
            row_lower=T[0], row_upper=T[10], column_lower=T[2], column_upper=T[8])
        result = JSimplex.reduce_singleton_rows(problem)
        step = only(result.postsolve_stack)
        @test size(result.problem.A) == (0, 1)
        @test step.lower_sources == [nothing]
        @test step.upper_sources == [nothing]
        @test step.lower_sources !== step.upper_sources
        restored = JSimplex.restore_basis(result, JSimplex.Basis(Int[], [JSimplex.AT_LOWER]))
        @test restored.basic_indices == [2]
        @test restored.states == [JSimplex.AT_LOWER, JSimplex.BASIC]
    end
end

@testset "Rejected first singleton does not shift accepted source rows" begin
    for T in (Float32, Float64, BigFloat)
        problem = LinearProblem(sparse(T[3 0; 0 1]), zeros(T, 2);
            row_lower=T[1, 2], row_upper=T[1, 4])
        result = JSimplex.reduce_singleton_rows(problem)
        step = only(result.postsolve_stack)
        @test step.map.rows == [1]
        @test step.lower_sources == [nothing, (2, JSimplex.AT_LOWER)]
        @test step.upper_sources == [nothing, (2, JSimplex.AT_UPPER)]
    end
end

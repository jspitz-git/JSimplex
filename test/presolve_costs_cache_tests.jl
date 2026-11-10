using SparseArrays

@testset "Singleton equality can require exact objective costs" begin
    for T in (Float32, Float64)
        problem = LinearProblem(sparse(T[1 1; 0 1]), T[1, -eps(T) / T(2)];
            row_lower=T[0, -3], row_upper=T[0, 3],
            column_lower=[nothing, -one(T)], column_upper=[nothing, one(T)])
        @test JSimplex.aggregate_singleton_equalities(problem;
            rounded_costs=false).problem === problem
        reduced = JSimplex.aggregate_singleton_equalities(problem)
        @test reduced.problem.objective == T[-1]
        @test iszero(reduced.problem.objective_constant)
        @test JSimplex.postsolve_primal(reduced, T[1]) == T[-1, 1]
    end
end

@testset "Presolve rounds only eligible objective coefficients" begin
    for T in (Float32, Float64, Float16)
        tiny = eps(T) / T(2)
        for (pass, matrix, extra_lower, extra_upper) in (
            (JSimplex.aggregate_sparse_equalities, sparse(T[1 1; 1 0]), T[-3], T[3]),
            (JSimplex.substitute_free_doubleton, sparse(T[1 1]), T[], T[]),
        )
            problem = LinearProblem(matrix, T[1, -tiny];
                row_lower=vcat(zero(T), extra_lower), row_upper=vcat(zero(T), extra_upper),
                column_lower=[nothing, -one(T)], column_upper=[nothing, one(T)])
            @test pass(problem).problem === problem
            result = pass(problem; rounded_costs=true)
            if T === Float16
                @test result.problem === problem
            else
                @test result.problem.objective == T[-1]
                @test iszero(result.problem.objective_constant)
                @test size(result.problem.A) == (length(extra_lower), 1)
                @test JSimplex.postsolve_primal(result, T[1]) == T[-1, 1]
            end

            # A representable coefficient change still cannot round the constant.
            problem = LinearProblem(matrix, T[1, 0]; objective_constant=tiny,
                row_lower=vcat(one(T), extra_lower), row_upper=vcat(one(T), extra_upper),
                column_lower=[nothing, -one(T)], column_upper=[nothing, one(T)])
            @test pass(problem; rounded_costs=true).problem === problem
        end
    end
end

@testset "Presolve cost rounding respects subnormal mode" begin
    old_mode = get_zero_subnormals()
    try
        set_zero_subnormals(true)
        if get_zero_subnormals()
            for T in (Float32, Float64)
                problem = LinearProblem(sparse(T[1 1]), T[1, -eps(T) / T(2)];
                    row_lower=T[0], row_upper=T[0],
                    column_lower=[nothing, -one(T)], column_upper=[nothing, one(T)])
                @test JSimplex.substitute_free_doubleton(problem;
                    rounded_costs=true).problem === problem
            end
        end
    finally
        set_zero_subnormals(old_mode)
    end
end

@testset "Dependent-row no-change cache owns its exact key" begin
    for T in (Float32, Float64)
        cache = JSimplex._DependentRowsCache{T}()
        matrix = sparse(T[1 1; 1 1])
        problem = LinearProblem(matrix, T[0, 0];
            row_lower=T[-1, 0], row_upper=T[1, 0])
        @test JSimplex._cached_dependent_rows!(cache, problem).problem === problem
        snapshot = cache.snapshot
        @test snapshot !== nothing
        other = LinearProblem(matrix, T[1, -1];
            row_lower=T[-1, 0], row_upper=T[1, 0])
        @test JSimplex._cached_dependent_rows!(cache, other).problem === other
        @test cache.snapshot === snapshot

        problem.row_lower[1] = JSimplex.Bound(T(1))
        failure = JSimplex._cached_dependent_rows!(cache, problem)
        @test failure isa JSimplex.PresolveFailure
        @test cache.snapshot === nothing

        @test JSimplex._cached_dependent_rows!(cache, other).problem === other
        snapshot = cache.snapshot
        other.A.nzval[1] = T(2)
        @test JSimplex._cached_dependent_rows!(cache, other).problem === other
        @test cache.snapshot !== snapshot
        @test snapshot.A.nzval[1] == one(T)
        other.A.nzval[1] = one(T)
        # With matching rows and bounds, the second row is redundant.
        other.row_lower[2] = JSimplex.Bound(T(-1))
        other.row_upper[2] = JSimplex.Bound(T(1))
        @test size(JSimplex._cached_dependent_rows!(cache, other).problem.A, 1) == 1
        @test cache.snapshot === nothing

        @test JSimplex._cached_dependent_rows!(cache, problem) isa JSimplex.PresolveFailure
        @test JSimplex._cached_dependent_rows!(cache,
            LinearProblem(sparse(T[1 0; 0 1]), zeros(T, 2))) isa JSimplex.PresolveResult
        @test cache.snapshot !== nothing
        wide = LinearProblem(spzeros(T, 1, 10_001), zeros(T, 10_001))
        @test JSimplex._cached_dependent_rows!(cache, wide).problem === wide
        @test cache.snapshot === nothing
    end

    problem = LinearProblem(sparse(Float16[1 0; 0 1]), Float16[0, 0])
    cache = JSimplex._DependentRowsCache{Float16}()
    @test JSimplex._cached_dependent_rows!(cache, problem).problem === problem
    @test cache.snapshot === nothing
end

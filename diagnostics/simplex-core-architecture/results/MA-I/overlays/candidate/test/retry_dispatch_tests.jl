using Logging
using SparseArrays

@testset "Retry options retain concrete basis strategies and option values" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}),
        basis_update in (:pfi, :forrest_tomlin, :bartels_golub, :suhl_suhl),
        basis_refactorization in (:native, :markowitz)
        options = SolverOptions(T; primal_tolerance=T(1 // 100),
            dual_tolerance=T(1 // 200), zero_tolerance=T(1 // 1000),
            iteration_limit=19, time_limit=2.5, refactorization_interval=7,
            verbose=false, log_level=Logging.Warn, algorithm=:primal,
            pricing=:devex, basis_update, basis_refactorization, scaling=:off,
            presolve=false)
        remaining = @inferred JSimplex._remaining_options(options; iterations=6)
        @test typeof(remaining) === typeof(options)
        @test remaining.iteration_limit == 13
        for field in fieldnames(typeof(options))
            field === :iteration_limit && continue
            @test getfield(remaining, field) == getfield(options, field)
        end
        @test JSimplex._remaining_options(options; iterations=19).iteration_limit == 0
        @test JSimplex._remaining_options(options; iterations=20).iteration_limit == 0
    end

    options = setprecision(BigFloat, 256) do
        SolverOptions(BigFloat; primal_tolerance=BigFloat(1) / 7,
            dual_tolerance=BigFloat(1) / 11, zero_tolerance=BigFloat(1) / 13,
            verbose=false)
    end
    setprecision(BigFloat, 64) do
        remaining = @inferred JSimplex._remaining_options(options; iterations=1)
        for field in (:primal_tolerance, :dual_tolerance, :zero_tolerance)
            @test getfield(remaining, field) == getfield(options, field)
            @test precision(getfield(remaining, field)) == 256
        end
    end
end

@testset "Original LP retries preserve budgets and accumulated statistics" begin
    for T in (Float64, Rational{BigInt}), algorithm in (:dual, :primal)
        # This problem needs one pivot from the initial slack basis.
        problem = LinearProblem(sparse(T[1;;]), T[1]; row_lower=T[1])
        previous = JSimplex.DualRunResult{T}(
            NUMERICAL_ERROR, nothing, nothing, 7, 3, "reduced basis failed")
        context = JSimplex.SolveContext(time_ns(), Inf)
        options = SolverOptions(T; algorithm, iteration_limit=9,
            refactorization_interval=1, verbose=false, scaling=:off)
        retry = @inferred JSimplex._retry_original(problem, options, context, previous)
        @test retry.status == OPTIMAL
        @test retry.primal == T[1]
        @test retry.objective_value == one(T)
        @test retry.iterations == 8
        @test retry.refactorizations > previous.refactorizations
        @test retry.basis isa JSimplex.Basis

        # Dual simplex can set the upper bound during initialization; primal
        # simplex takes one bound-flip step. This also checks sense conversion.
        maximization = LinearProblem(sparse(T[1;;]), T[1];
            objective_sense=MAX_SENSE, row_upper=T[2], column_upper=T[1])
        max_retry = JSimplex._retry_original(maximization, options, context, previous)
        @test max_retry.status == OPTIMAL
        @test max_retry.primal == T[1]
        @test max_retry.objective_value == -one(T)
        @test max_retry.iterations == (algorithm == :dual ? 7 : 8)

        exhausted = SolverOptions(T; algorithm, iteration_limit=7, verbose=false)
        limited = JSimplex._retry_original(problem, exhausted, context, previous)
        @test limited.status == ITERATION_LIMIT
        @test limited.iterations == 7
        @test limited.refactorizations >= previous.refactorizations
        @test isnothing(limited.primal)

        expired_context = JSimplex.SolveContext(time_ns(), 0.0)
        expired = JSimplex._retry_original(problem, options, expired_context, previous)
        @test expired.status == TIME_LIMIT
        @test expired.iterations == 7
        @test expired.refactorizations == 3
        @test isnothing(expired.primal)
    end
end

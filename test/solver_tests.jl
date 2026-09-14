using JSimplex.SparseArrays
using JSimplex.Logging
using JSimplex.LinearAlgebra

@testset "Public solve returns owned structural values and original objective" begin
    problem = LinearProblem(sparse([1.0 1.0]), [1.0, 2.0];
        row_lower=[1.0], objective_constant=7.0, name="public-api",
        row_names=["demand"], column_names=["x", "y"])
    before = deepcopy(problem)
    result = solve(problem)
    @test result isa Solution
    @test result.status == OPTIMAL
    @test result.primal ≈ [1.0, 0.0]
    @test result.objective_value ≈ 8.0
    @test result.statistics.iterations == 1
    @test result.statistics.refactorizations == 0
    @test result.statistics.elapsed_seconds >= 0.0
    @test !isempty(result.message)
    result.primal[1] = 99.0
    @test solve(problem).primal ≈ [1.0, 0.0]
    for field in fieldnames(LinearProblem)
        @test getfield(problem, field) == getfield(before, field)
    end

    maximum_problem = LinearProblem(sparse([1.0 1.0]), [2.0, 1.0];
        row_upper=[3.0], objective_sense=MAX_SENSE, objective_constant=7.0)
    before = deepcopy(maximum_problem)
    for _ in 1:2
        result = solve(maximum_problem)
        @test result.status == OPTIMAL
        @test result.primal ≈ [3.0, 0.0]
        @test result.objective_value ≈ 13.0
        for field in fieldnames(LinearProblem)
            @test getfield(maximum_problem, field) == getfield(before, field)
        end
    end
end

@testset "Discrete domains require explicit owned LP relaxation" begin
    # The semi-domain optima lie below their active lower bounds; certification
    # must use the relaxed hull, and binary bounds must remain clipped to [0, 1].
    problem = LinearProblem(sparse(Matrix{Float64}(I, 4, 4)), [-1.0, 1.0, 1.0, 1.0];
        row_lower=[-Inf, 0.5, 0.5, 0.5],
        column_lower=[0.0, 0.0, 3.0, 2.0],
        column_upper=[Inf, 8.0, 9.0, 7.0],
        variable_domains=[BINARY, INTEGER, SEMI_CONTINUOUS, SEMI_INTEGER])
    before = deepcopy(problem)
    rejected = solve(problem)
    @test rejected.status == MIP_NOT_SUPPORTED
    @test isnothing(rejected.primal)
    @test isnothing(rejected.objective_value)
    @test rejected.statistics.iterations == 0
    @test rejected.statistics.refactorizations == 0
    relaxed = solve(problem; relax_integrality=true)
    @test relaxed.status == OPTIMAL
    @test relaxed.primal ≈ [1.0, 0.5, 0.5, 0.5]
    @test relaxed.objective_value ≈ 0.5
    for field in fieldnames(LinearProblem)
        @test getfield(problem, field) == getfield(before, field)
    end
    @test solve(problem).status == MIP_NOT_SUPPORTED
end

@testset "Validation and algorithm selection precede numerical work" begin
    valid = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    for field in (:objective, :row_lower, :column_upper)
        invalid = deepcopy(valid)
        getfield(invalid, field)[1] = NaN
        result = solve(invalid)
        @test result.status == INVALID_MODEL
        @test result.message == JSimplex._validation_error(invalid)
        @test isnothing(result.primal)
        @test isnothing(result.objective_value)
        @test result.statistics.iterations == 0
        @test result.statistics.refactorizations == 0
    end
    invalid_dimensions = deepcopy(valid)
    empty!(invalid_dimensions.objective)
    @test solve(invalid_dimensions).status == INVALID_MODEL
    for algorithm in (:primal, :auto, :unknown)
        result = solve(invalid_dimensions; options=SolverOptions(algorithm=algorithm))
        @test result.status == ALGORITHM_NOT_SUPPORTED
        @test isnothing(result.primal)
        @test isnothing(result.objective_value)
        @test result.statistics.iterations == 0
    end
end

@testset "Time limits take precedence and iteration limits count completed pivots" begin
    problem = LinearProblem(sparse([1.0 0.0; -1.0 1.0]), [1.0, 1.0];
        row_lower=[1.0, 1.0])
    invalid = deepcopy(problem)
    empty!(invalid.objective)
    discrete = LinearProblem(spzeros(0, 1), [1.0]; variable_domains=[INTEGER])
    for input in (problem, invalid, discrete), algorithm in (:dual, :primal, :auto)
        result = solve(input; options=SolverOptions(time_limit=0.0,
            iteration_limit=0, algorithm=algorithm))
        @test result.status == TIME_LIMIT
        @test isnothing(result.primal)
        @test isnothing(result.objective_value)
        @test result.statistics.iterations == 0
        @test result.statistics.refactorizations == 0
        @test result.statistics.elapsed_seconds >= 0.0
    end
    # The smallest positive Float64 deadline has elapsed by the first clock check.
    @test solve(problem; options=SolverOptions(time_limit=nextfloat(0.0))).status == TIME_LIMIT
    for limit in 0:2
        result = solve(problem; options=SolverOptions(iteration_limit=limit,
            refactorization_interval=1))
        @test result.status == (limit < 2 ? ITERATION_LIMIT : OPTIMAL)
        @test result.statistics.iterations == limit
        @test result.statistics.refactorizations == limit
        @test isnothing(result.primal) == (limit < 2)
        @test isnothing(result.objective_value) == (limit < 2)
    end
    # An already optimal model needs no pivots, even with a zero pivot budget.
    @test solve(LinearProblem(spzeros(0, 1), [1.0]);
        options=SolverOptions(iteration_limit=0)).status == OPTIMAL
end

@testset "Nonoptimal results preserve absence of primal and objective" begin
    for (problem, options, expected) in (
        (LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[2.0], column_upper=[1.0]),
         SolverOptions(), INFEASIBLE),
        (LinearProblem(spzeros(0, 1), [1.0]; objective_sense=MAX_SENSE),
         SolverOptions(), UNBOUNDED),
        (LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0]),
         SolverOptions(zero_tolerance=2.0), NUMERICAL_ERROR),
        (LinearProblem(spzeros(0, 1), [1.0e308]; column_lower=[2.0]),
         SolverOptions(), NUMERICAL_ERROR),
    )
        result = solve(problem; options=options)
        @test result.status == expected
        @test isnothing(result.primal)
        @test isnothing(result.objective_value)
        @test result.statistics.elapsed_seconds >= 0.0
        @test !isempty(result.message)
    end
end

@testset "Logging follows the requested level and reports refactorizations" begin
    problem = LinearProblem(sparse([1.0 0.0; -1.0 1.0]), [1.0, 1.0];
        row_lower=[1.0, 1.0])
    @test_logs min_level=Logging.Info solve(problem)
    @test_logs (:info, "Starting solve") (:info, "Refactorizing basis") (:info, "Refactorizing basis") (:info, "Solve terminated") begin
        solve(problem; options=SolverOptions(log_level=Logging.Info, refactorization_interval=1))
    end
    @test_logs (:debug, "Starting solve") (:debug, "Solve terminated") min_level=Logging.Debug solve(problem)
    @test_logs (:info, "Starting solve") (:info, "Solve terminated") solve(problem;
        options=SolverOptions(log_level=Logging.Info, time_limit=0.0))
end

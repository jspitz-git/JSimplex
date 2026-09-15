using JSimplex.SparseArrays
using JSimplex.Logging
using JSimplex.LinearAlgebra

@testset "Binary relaxation clips caller-mutated bounds" begin
    for (cost, bounds, hull, expected, objective) in (
        (-1.0, (0.0, 10.0), (0.0, 1.0), 1.0, -1.0),
        (1.0, (-10.0, 1.0), (0.0, 1.0), 0.0, 0.0),
        (-1.0, (-10.0, 10.0), (0.0, 1.0), 1.0, -1.0),
        (1.0, (0.25, 0.75), (0.25, 0.75), 0.25, 0.25),
    )
        problem = LinearProblem(spzeros(0, 1), [cost]; variable_domains=[BINARY])
        problem.column_lower[1], problem.column_upper[1] = Bound.(bounds)
        before = deepcopy(problem)
        relaxed = JSimplex.relax_integrality(problem)
        @test bound_value.(relaxed.column_lower) == [hull[1]]
        @test bound_value.(relaxed.column_upper) == [hull[2]]
        result = solve(problem; relax_integrality=true)
        @test result.status == OPTIMAL
        @test result.primal == [expected]
        @test result.objective_value == objective
        @test solve(problem).status == MIP_NOT_SUPPORTED
        for field in fieldnames(typeof(problem))
            @test getfield(problem, field) == getfield(before, field)
        end
    end
    for (lower, upper) in ((2.0, 3.0), (-3.0, -2.0)), relax in (false, true)
        problem = LinearProblem(spzeros(0, 1), [-1.0]; variable_domains=[BINARY])
        problem.column_lower[1] = Bound(lower)
        problem.column_upper[1] = Bound(upper)
        result = solve(problem; relax_integrality=relax)
        @test result.status == INVALID_MODEL
        @test result.message == JSimplex._validation_error(problem)
        @test isnothing(result.primal)
        @test isnothing(result.objective_value)
        @test result.statistics.iterations == 0
        @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.column_lower) ==
                  map(value -> isfinite(value) ? value : nothing, [lower])
        @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.column_upper) ==
                  map(value -> isfinite(value) ? value : nothing, [upper])
    end
end

struct ThrowingSolverLogger <: AbstractLogger
    message::String
    exception::Exception
end
Logging.min_enabled_level(::ThrowingSolverLogger) = Logging.Debug
Logging.shouldlog(::ThrowingSolverLogger, args...) = true
Logging.catch_exceptions(::ThrowingSolverLogger) = false
function Logging.handle_message(logger::ThrowingSolverLogger, level, message, args...; kwargs...)
    message == logger.message && throw(logger.exception)
    return nothing
end

@testset "Caller logger exceptions retain identity through numerical catches" begin
    main = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    phase = LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[3.0])
    for exception in (SingularException(7), ZeroPivotException(7))
        for message in ("Starting solve", "Refactorizing basis", "Solve terminated")
            for (problem, interval) in ((main, 1), (phase, 1), (phase, 20))
                caught = try
                    with_logger(ThrowingSolverLogger(message, exception)) do
                        solve(problem; options=SolverOptions(refactorization_interval=interval))
                    end
                catch error
                    error
                end
                @test caught === exception
            end
        end
        for (problem, interval) in ((main, 1), (phase, 1), (phase, 20))
            workspace = JSimplex.initialize_workspace(problem,
                SolverOptions(refactorization_interval=interval))
            caught = try
                with_logger(ThrowingSolverLogger("Refactorizing basis", exception)) do
                    problem === main ? JSimplex.dual_iteration!(workspace, () -> false) :
                        JSimplex.make_dual_feasible!(workspace, () -> false)
                end
            catch error
                error
            end
            @test caught === exception
        end
        # Leaving a failing logger scope must not affect subsequent solves.
        @test solve(main).status == OPTIMAL
        failed = solve(main; options=SolverOptions(zero_tolerance=2.0))
        @test failed.status == NUMERICAL_ERROR
        @test isnothing(failed.primal)
    end
end

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
    for field in fieldnames(typeof(problem))
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
        for field in fieldnames(typeof(problem))
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
    for field in fieldnames(typeof(problem))
        @test getfield(problem, field) == getfield(before, field)
    end
    @test solve(problem).status == MIP_NOT_SUPPORTED
end

@testset "Validation and algorithm selection precede numerical work" begin
    valid = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    for field in (:objective,)
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
    for field in (:row_lower, :column_upper)
        @test_throws ArgumentError LinearProblem(sparse([1.0;;]), [1.0];
            NamedTuple{(field,)}(([NaN],))...)
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

using JSimplex.SparseArrays
using JSimplex.Logging
using JSimplex.LinearAlgebra

function typed_bounded_problem(::Type{T}) where {T}
    A = sparse(T[1 1; 1 0; 0 1])
    return LinearProblem(A, T[-3, -2]; objective_constant=T(1 // 3),
        row_lower=fill(nothing, 3), row_upper=T[4, 2, 3],
        column_lower=T[0, 0], column_upper=fill(nothing, 2))
end

function test_public_solve_type(::Type{T}) where {T}
    problem = @inferred typed_bounded_problem(T)
    result = @inferred solve(problem)
    @test result isa Solution{T}
    @test result.status == OPTIMAL
    @test result.primal isa Vector{T}
    @test result.objective_value isa T
    @test result.statistics.elapsed_seconds isa Float64
    if T <: Rational
        @test result.primal == T[2, 2]
        @test result.objective_value == T(-29 // 3)
    else
        @test result.primal ≈ T[2, 2]
        @test result.objective_value ≈ T(-29 // 3)
    end
end

@testset "Floating solves use reversible scaling by default" begin
    problem = LinearProblem(sparse([8.0 2.0; 16.0 0.5]), [4.0, 1.0];
        row_lower=[8.0, 16.0])
    original = deepcopy(problem)
    for algorithm in (:dual, :primal), mode in (:auto, :on, :off)
        result = solve(problem;
            options=SolverOptions(; algorithm, scaling=mode, verbose=false))
        @test result.status == OPTIMAL
        @test result.primal ≈ [1.0, 0.0]
        @test result.objective_value ≈ 4.0
    end
    @test problem.A == original.A
    @test problem.objective == original.objective
    @test problem.row_lower == original.row_lower

    tiny = LinearProblem(sparse(reshape([2.0^-30], 1, 1)), [1.0];
        row_lower=[2.0^-30])
    @test solve(tiny; options=SolverOptions(scaling=:on, verbose=false)).primal == [1.0]
    @test solve(tiny; options=SolverOptions(scaling=:off, verbose=false)).primal == [1.0]
end

@testset "Selectable basis updates solve pivoting LPs" begin
    for (mode, Factorization) in ((:forrest_tomlin, JSimplex.ForrestTomlinFactorization),
                                  (:bartels_golub, JSimplex.BartelsGolubFactorization),
                                  (:suhl_suhl, JSimplex.SuhlSuhlFactorization))
        for T in (Float32, Float64, BigFloat, Rational{BigInt})
            options = SolverOptions(T; basis_update=mode, refactorization_interval=3,
                                    verbose=false)
            problem = typed_bounded_problem(T)
            workspace = @inferred JSimplex.initialize_workspace(problem, options)
            @test workspace.factorization isa Factorization
            @test all(isconcretetype, fieldtypes(typeof(workspace)))
            result = solve(problem; options)
            @test result.status == OPTIMAL
            @test result.primal ≈ T[2, 2]
            @test result.objective_value ≈ T(-29 // 3)
        end
    end
end

function test_typed_statuses(::Type{T}) where {T}
    infeasible = LinearProblem(sparse(reshape(T[1], 1, 1)), T[1];
                               row_lower=T[2], column_upper=T[1])
    unbounded = LinearProblem(spzeros(T, 0, 1), T[1]; objective_sense=MAX_SENSE)
    pivoting = LinearProblem(sparse(T[1 1; -1 1]), T[1, 2];
                             row_lower=T[3, 1], column_lower=T[0, 1])
    discrete = LinearProblem(spzeros(T, 0, 1), T[-1];
                             column_upper=T[1], variable_domains=[INTEGER])
    numerical = LinearProblem(sparse(T[1 1]), T[1, 1]; row_lower=T[1])
    invalid = deepcopy(pivoting)
    empty!(invalid.objective)

    for (problem, options, expected) in (
        (infeasible, nothing, INFEASIBLE),
        (unbounded, nothing, UNBOUNDED),
        (pivoting, SolverOptions(T; iteration_limit=0), ITERATION_LIMIT),
        (pivoting, SolverOptions(T; time_limit=0.0), TIME_LIMIT),
        (discrete, nothing, MIP_NOT_SUPPORTED),
        (pivoting, SolverOptions(T; algorithm=:auto), ALGORITHM_NOT_SUPPORTED),
        (invalid, nothing, INVALID_MODEL),
        (numerical, SolverOptions(T; zero_tolerance=T(2)), NUMERICAL_ERROR),
    )
        @testset "$expected" begin
            result = @inferred solve(problem; options)
            @test result isa Solution{T}
            @test result.status == expected
            @test isnothing(result.primal)
            @test isnothing(result.objective_value)
            @test result.statistics.elapsed_seconds isa Float64
        end
    end

    refactorized = @inferred solve(
        pivoting; options=SolverOptions(T; refactorization_interval=1),
    )
    @test refactorized isa Solution{T}
    @test refactorized.status == OPTIMAL
    @test refactorized.primal == T[1, 2]
    @test refactorized.statistics.iterations == 2
    @test refactorized.statistics.refactorizations == 2

    maximum = LinearProblem(spzeros(T, 0, 1), T[2];
        objective_constant=T(1), objective_sense=MAX_SENSE,
        column_lower=T[0], column_upper=T[3])
    @test (@inferred solve(maximum)).objective_value == T(7)
    @test (@inferred solve(discrete; relax_integrality=true)).status == OPTIMAL
end

@testset "Solver allocation regression" begin
    problem = read_mps(joinpath(@__DIR__, "fixtures", "solver", "afiro.mps"))
    options = SolverOptions(verbose=false)

    solve(problem; options)
    allocated = @allocated solve(problem; options)

    # Exact dependency, bound, and sparse equality passes build rational rows.
    @test allocated <= 2_600_000
end

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
    is_progress = logger.message == "Simplex progress" &&
                  message isa AbstractString && startswith(message, "iter=")
    (message == logger.message || is_progress) && throw(logger.exception)
    return nothing
end

@testset "Caller logger exceptions retain identity through numerical catches" begin
    main = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    phase = LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[3.0])
    for exception in (SingularException(7), ZeroPivotException(7))
        for message in (
            "Starting solve",
            "Refactorizing basis",
            "Simplex progress",
            "Solve terminated",
        )
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
        pivot_required = LinearProblem(sparse([1.0 1.0]), [1.0, 1.0]; row_lower=[1.0])
        failed = solve(pivot_required; options=SolverOptions(zero_tolerance=2.0))
        @test failed.status == NUMERICAL_ERROR
        @test isnothing(failed.primal)
    end
end

@testset "Primal phase I preserves caller logger exceptions" begin
    problem = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    exception = SingularException(7)
    caught = try
        with_logger(ThrowingSolverLogger("Refactorizing basis", exception)) do
            solve(problem; options=SolverOptions(algorithm=:primal))
        end
        nothing
    catch error
        error
    end
    @test caught === exception
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
    for algorithm in (:auto, :unknown)
        result = solve(invalid_dimensions; options=SolverOptions(algorithm=algorithm))
        @test result.status == ALGORITHM_NOT_SUPPORTED
        @test isnothing(result.primal)
        @test isnothing(result.objective_value)
        @test result.statistics.iterations == 0
    end
end

@testset "Time limits take precedence and iteration limits count completed pivots" begin
    problem = LinearProblem(sparse([1.0 1.0; 1.0 -1.0]), [2.0, 1.0];
        row_lower=[3.0, 1.0], column_lower=[1.0, 0.0])
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
        (LinearProblem(sparse([1.0 1.0]), [1.0, 1.0]; row_lower=[1.0]),
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
    problem = LinearProblem(sparse([1.0 1.0; 1.0 -1.0]), [2.0, 1.0];
        row_lower=[3.0, 1.0], column_lower=[1.0, 0.0])
    @test_logs (:info, "Loaded problem: rows=2 columns=2 nnz=4") (:info, "Starting presolve") (:info, "After presolve: rows=2 columns=2 nnz=4") (:info, r"^Solve finished:") min_level=Logging.Info solve(problem)
    @test_logs (:info, "Starting solve") (:info, "Loaded problem: rows=2 columns=2 nnz=4") (:info, "Starting presolve") (:info, "After presolve: rows=2 columns=2 nnz=4") (:info, "Refactorizing basis") (:info, r"^iter=") (:info, "Refactorizing basis") (:info, r"^iter=") (:info, "Solve terminated") (:info, r"^Solve finished:") begin
        solve(problem; options=SolverOptions(log_level=Logging.Info, refactorization_interval=1))
    end
    @test_logs (:debug, "Starting solve") (:info, "Loaded problem: rows=2 columns=2 nnz=4") (:info, "Starting presolve") (:info, "After presolve: rows=2 columns=2 nnz=4") (:debug, "Solve terminated") (:info, r"^Solve finished:") min_level=Logging.Debug solve(problem)
    @test_logs (:info, "Starting solve") (:info, "Loaded problem: rows=2 columns=2 nnz=4") (:info, "Solve terminated") (:info, r"^Solve finished:") solve(problem;
        options=SolverOptions(log_level=Logging.Info, time_limit=0.0))
end

@testset "Solve reports its final status at Info level" begin
    cases = (
        (LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0]), OPTIMAL),
        (LinearProblem(spzeros(1, 1), [0.0]; row_lower=[1.0]), INFEASIBLE),
        (LinearProblem(spzeros(0, 1), [-1.0]), UNBOUNDED),
    )
    for (problem, expected) in cases
        logger = Test.TestLogger(min_level=Logging.Info)
        result = with_logger(logger) do
            solve(problem)
        end
        endings = [record.message for record in logger.logs
                   if record.message isa AbstractString &&
                      startswith(record.message, "Solve finished:")]
        @test result.status == expected
        @test length(endings) == 1
        @test occursin("status=$expected", only(endings))
        @test occursin("iterations=", only(endings))
        @test occursin("time=", only(endings))
        @test occursin("objective=", only(endings)) == (expected == OPTIMAL)
    end

    logger = Test.TestLogger(min_level=Logging.Info)
    with_logger(logger) do
        solve(first(cases)[1]; options=SolverOptions(verbose=false))
    end
    @test all(record -> !startswith(string(record.message), "Solve finished:"), logger.logs)
end

@testset "Phase-I refactorization reports the original MAX objective" begin
    problem = LinearProblem(
        sparse([1.0;;]), [1.0];
        objective_constant=4.0,
        objective_sense=MAX_SENSE,
        row_upper=[3.0],
    )
    records = Any[]
    result = JSimplex.Logging.with_logger(RecordingSimplexLogger(records)) do
        solve(problem; options=SolverOptions(refactorization_interval=1))
    end
    progress = filter(
        record -> record.message isa AbstractString && startswith(record.message, "iter="),
        records,
    )
    objectives = map(progress) do record
        matched = match(r" obj=([^ ]+) ", record.message)
        parse(Float64, only(something(matched).captures))
    end

    @test result.status == OPTIMAL
    @test !isempty(progress)
    @test all(>=(4.0), objectives)
    @test 7.0 in objectives
end

@testset "Parametric public solve" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        @testset "$T" begin
            test_public_solve_type(T)
        end
    end
    exact = typed_bounded_problem(Rational{BigInt})
    @test (@inferred solve(exact; options=SolverOptions())).status == OPTIMAL

    exact_path = joinpath(@__DIR__, "fixtures", "parser", "exact-rational.mps")
    exact_mps_result = @inferred solve(read_mps(exact_path; value_type=Rational{BigInt}))
    @test exact_mps_result.status == OPTIMAL
    @test exact_mps_result.primal == Rational{BigInt}[2]
    @test exact_mps_result.objective_value == 11 // big(4)
end

@testset "Parametric solve statuses and resource limits" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        @testset "$T" begin
            test_typed_statuses(T)
        end
    end
end

@testset "Phase-I roundoff cannot prove infeasibility" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[3 -1]), T[-4, 2];
            row_upper=T[2], column_lower=[T(-1), nothing],
            column_upper=[nothing, T(2)])
        for interval in (nothing, 1, 2, 3, 20)
            @testset "$T, interval=$interval" begin
                result = if isnothing(interval)
                    @inferred solve(problem)
                else
                    @inferred solve(problem; options=SolverOptions(T; refactorization_interval=interval))
                end
                @test result isa Solution{T}
                @test result.status == OPTIMAL
                @test result.primal == T[-1, -5]
                @test result.objective_value == T(-6)
                @test result.statistics.iterations == 2
            end
        end
    end

    problem = LinearProblem(sparse(Float32[3 -1]), Float32[-4, 2];
        row_upper=Float32[2], column_lower=[-1f0, nothing], column_upper=[nothing, 2f0])
    limited = @inferred solve(problem; options=SolverOptions(Float32; iteration_limit=1))
    @test limited.status == ITERATION_LIMIT
    @test limited.statistics.iterations == 1
    @test limited.statistics.refactorizations == 1

    for exception in (SingularException(7), ZeroPivotException(7))
        captured = try
            with_logger(ThrowingSolverLogger("Refactorizing basis", exception)) do
                solve(problem)
            end
        catch error
            error
        end
        @test captured === exception
    end
end

@testset "Floating status certificates reject unresolved roundoff" begin
    for T in (Float32, Rational{BigInt})
        for (problem, objective, primal) in (
            (LinearProblem(sparse(T[8 9; -8 -8]), T[3, -3];
                row_upper=T[-2, 0], column_lower=T[-1, -2], column_upper=T[4, 5]),
             T(12), T[2, -2]),
            (LinearProblem(sparse(T[-7 3; -8 -6]), T[4, 3];
                row_lower=[nothing, T(-6)], row_upper=[nothing, T(-4)],
                column_lower=[nothing, nothing]), T(2), nothing),
        )
            @testset "$T, objective=$objective" begin
                result = @inferred solve(problem)
                @test result isa Solution{T}
                @test result.status in (OPTIMAL, NUMERICAL_ERROR)
                if T <: Rational
                    @test result.status == OPTIMAL
                end
                if result.status == OPTIMAL
                    @test T <: Rational ? result.objective_value == objective : result.objective_value ≈ objective
                    isnothing(primal) || @test T <: Rational ? result.primal == primal : result.primal ≈ primal
                else
                    @test isnothing(result.primal)
                    @test isnothing(result.objective_value)
                end
            end
        end
    end
end

@testset "A nearly singular bounded model has no recession ray" begin
    scale = ldexp(1f0, -20)
    coefficients = Float32[scale scale; scale nextfloat(scale)]
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T.(coefficients)), T[0, -1];
            row_lower=T[-1, -1], row_upper=T[1, 1], column_lower=[nothing, nothing])
        result = @inferred solve(problem)
        @test result isa Solution{T}
        # The two rows bound an invertible transformation of the free columns.
        @test result.status in (OPTIMAL, NUMERICAL_ERROR)
        T <: Rational && @test result.status == OPTIMAL
        if result.status == OPTIMAL
            @test result.objective_value == -T(big(2)^44)
        else
            @test isnothing(result.primal)
            @test isnothing(result.objective_value)
        end
    end
end

@testset "Rounded dependent rows cannot certify a feasible primal origin" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), ray in (false, true)
        coefficients = ray ? T[1 3 0; 3 9 0] : T[1 3; 3 9]
        costs = ray ? T[0, 0, -1] : T[0, 0]
        lower = ray ? [nothing, T(-16777220), zero(T)] : [nothing, T(-16777220)]
        upper = ray ? [nothing, T(-16777220), nothing] : [nothing, T(-16777220)]
        problem = LinearProblem(sparse(coefficients), costs;
            row_lower=T[0, -4], row_upper=T[0, -4], column_lower=lower, column_upper=upper)
        for interval in (1, 20)
            result = @inferred solve(problem; options=SolverOptions(T; refactorization_interval=interval))
            @test result isa Solution{T}
            @test result.status in (INFEASIBLE, NUMERICAL_ERROR)
            T <: Rational && @test result.status == INFEASIBLE
            @test isnothing(result.primal)
            @test isnothing(result.objective_value)
        end
    end
end

@testset "Original objective cancellation cannot certify a false optimum" begin
    for (T, exponent) in ((Float32, 27), (Float64, 54), (BigFloat, 54), (Rational{BigInt}, 54))
        magnitude = T(big(2)^exponent)
        for sense in (MIN_SENSE, MAX_SENSE), interval in (1, 20)
            sign = sense == MIN_SENSE ? one(T) : -one(T)
            problem = LinearProblem(sparse(T[1 0 0 1; 0 1 0 1; 0 0 1 1]),
                sign .* T[magnitude, 1, magnitude, 2magnitude];
                row_lower=ones(T, 3), row_upper=ones(T, 3),
                objective_sense=sense, objective_constant=-sign * 2magnitude)
            result = @inferred solve(problem; options=SolverOptions(T; refactorization_interval=interval))
            @test result isa Solution{T}
            @test result.status in (OPTIMAL, NUMERICAL_ERROR)
            T in (BigFloat, Rational{BigInt}) && @test result.status == OPTIMAL
            if result.status == OPTIMAL
                # The identity-basis point has exact stored objective +/-1;
                # the unique optimum instead uses the fourth column.
                @test result.primal == T[0, 0, 0, 1]
                exact_objective = dot(Rational{BigInt}.(problem.objective),
                                      Rational{BigInt}.(result.primal)) +
                                  Rational{BigInt}(problem.objective_constant)
                @test exact_objective == 0
                @test result.objective_value == zero(T)
            else
                @test isnothing(result.primal)
                @test isnothing(result.objective_value)
            end
        end
    end
end

using Test, JSimplex
using JSimplex.SparseArrays, JSimplex.Logging, JSimplex.LinearAlgebra

function phase_log_solve(problem, algorithm; strategy=:legacy, phase_one=false,
                         verbose=true, iteration_offset=0)
    options = SolverOptions(; algorithm, simplex_strategy=strategy, verbose,
                            presolve=false, scaling=:off)
    policy = JSimplex.NumericalPolicy(Float64; simplex_strategy=strategy, phase_one)
    progress = JSimplex.SimplexProgressContext(problem; numerical_policy=policy,
                                               iteration_offset)
    logger = Test.TestLogger(min_level=Logging.Info)
    result = with_logger(logger) do
        runner = algorithm == :primal ? JSimplex._solve_continuous_primal :
                                       JSimplex._solve_continuous_dual
        runner(problem, options; progress)
    end
    phases = filter(record -> startswith(string(record.message), "Starting simplex phase "), logger.logs)
    return result, phases
end

@testset "Simplex phase announcements" begin
    for algorithm in (:primal, :dual), strategy in (:legacy, :adaptive), phase_one in (false, true)
        problem = algorithm == :primal ?
            LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0]) :
            LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[3.0])
        result, phases = phase_log_solve(problem, algorithm; strategy, phase_one,
                                        iteration_offset=7)
        @test result.status == OPTIMAL
        @test [r.message for r in phases] == ["Starting simplex phase I", "Starting simplex phase II"]
        if length(phases) == 2
            @test all(r -> r.level == Logging.Info && r.kwargs[:algorithm] == algorithm, phases)
            @test phases[1].kwargs[:iter] == 7
            @test 7 < phases[2].kwargs[:iter] <= 7 + result.iterations
            @test 0 <= phases[1].kwargs[:time] <= phases[2].kwargs[:time]
        end
        result, phases = phase_log_solve(problem, algorithm; strategy, phase_one, verbose=false)
        @test result.status == OPTIMAL
        @test isempty(phases)

        feasible = LinearProblem(sparse([1.0;;]), [1.0]; row_upper=[3.0])
        result, phases = phase_log_solve(feasible, algorithm; strategy, phase_one)
        @test result.status == OPTIMAL
        @test [r.message for r in phases] == ["Starting simplex phase II"]
    end

    for phase_one in (false, true)
        infeasible = LinearProblem(spzeros(1, 1), [1.0]; row_lower=[1.0])
        result, phases = phase_log_solve(infeasible, :primal; phase_one)
        @test result.status == INFEASIBLE
        @test [r.message for r in phases] == ["Starting simplex phase I"]
        unbounded = LinearProblem(sparse([1.0;;]), [-1.0]; row_lower=[0.0])
        result, phases = phase_log_solve(unbounded, :dual; phase_one)
        @test result.status == UNBOUNDED
        @test [r.message for r in phases] == ["Starting simplex phase I"]
    end
end

struct PhaseThrowingLogger <: Logging.AbstractLogger
    message::String
    exception::Exception
end
Logging.min_enabled_level(::PhaseThrowingLogger) = Logging.Info
Logging.shouldlog(::PhaseThrowingLogger, args...) = true
Logging.catch_exceptions(::PhaseThrowingLogger) = false
function Logging.handle_message(logger::PhaseThrowingLogger, level, message, args...; kwargs...)
    message == logger.message && throw(logger.exception)
    return nothing
end

@testset "Phase logger exceptions retain caller provenance" begin
    for algorithm in (:primal, :dual), phase_one in (false, true), phase in ("I", "II")
        problem = algorithm == :primal ?
            LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0]) :
            LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[3.0])
        options = SolverOptions(; algorithm, presolve=false, scaling=:off)
        policy = JSimplex.NumericalPolicy(Float64; phase_one)
        progress = JSimplex.SimplexProgressContext(problem; numerical_policy=policy)
        exception = SingularException(23)
        caught = try
            with_logger(PhaseThrowingLogger("Starting simplex phase $phase", exception)) do
                runner = algorithm == :primal ? JSimplex._solve_continuous_primal :
                                               JSimplex._solve_continuous_dual
                runner(problem, options; progress)
            end
            nothing
        catch error
            error
        end
        @test caught === exception
    end
end

using LinearAlgebra, Logging, SparseArrays

struct HandoffBoundaryLogger{E} <: AbstractLogger
    reached::Base.RefValue{Bool}
    fail::Bool
    exception::E
end
Logging.min_enabled_level(::HandoffBoundaryLogger) = Logging.Debug
Logging.shouldlog(::HandoffBoundaryLogger, args...) = true
Logging.catch_exceptions(::HandoffBoundaryLogger) = false
function Logging.handle_message(logger::HandoffBoundaryLogger, level, message, args...; kwargs...)
    if message == "Refactorizing basis"
        logger.reached[] = true
        logger.fail && throw(logger.exception)
    end
end

@testset "Interrupted auxiliary handoff preserves the live basis and factor" begin
    for phase_one in (false, true), interruption in (:logger, :callback, :deadline)
        p = LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[1.0])
        o = SolverOptions(; verbose=false, pricing=:dantzig, simplex_strategy=:adaptive,
                          presolve=false, scaling=:off)
        policy = JSimplex.NumericalPolicy(Float64; simplex_strategy=:adaptive, phase_one)
        w = JSimplex.initialize_workspace(p, o; progress=JSimplex.SimplexProgressContext(p;
            numerical_policy=policy))
        JSimplex._reject_recovery_pair!(w, 1, 1, policy)
        original_basis = copy(w.basis.basic_indices)
        original_values = copy(w.primal)
        original_factor = w.factorization
        initial_refactors = w.refactorizations
        reached = Ref(false)
        failure = SingularException(23)
        stop = () -> reached[] ? (interruption == :callback ? throw(failure) :
                                 interruption == :deadline) : false
        result = try
            with_logger(HandoffBoundaryLogger(reached, interruption == :logger, failure)) do
                JSimplex.make_dual_feasible!(w, stop)
            end
        catch exception
            exception
        end
        @test reached[]
        if interruption == :deadline
            @test result isa JSimplex.DualTermination && result.status == TIME_LIMIT
        else
            @test result === failure
        end
        @test w.basis.basic_indices == original_basis
        @test w.primal == original_values
        @test w.factorization === original_factor
        @test JSimplex.basis_matrix(w) * JSimplex.forward_solve!(zeros(1), w.factorization, [1.0]) ≈ [1.0]
        @test transpose(JSimplex.basis_matrix(w)) * JSimplex.transpose_solve!(zeros(1), w.factorization, [1.0]) ≈ [1.0]
        @test w.iterations == 1
        @test w.refactorizations >= initial_refactors
        # A retained workspace can resume with consistent original bounds.
        @test JSimplex.make_dual_feasible!(w, () -> false) === nothing
        @test w.primal ≈ [1.0, 1.0]
        @test isempty(w.scratch.recovery_rejections)
        @test JSimplex.basis_matrix(w) * JSimplex.forward_solve!(zeros(1), w.factorization, [1.0]) ≈ [1.0]
    end
end

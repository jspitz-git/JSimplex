using Test, JSimplex, SparseArrays

@testset "Crash respects fixed, upper-only and free variables with rows" begin
    p = LinearProblem(spdiagm(0=>ones(3)),[0.0,-1.0,1.0];
        column_lower=[2.0,-Inf,-Inf],column_upper=[2.0,3.0,Inf],
        row_lower=[2.0,3.0,1.0],row_upper=[2.0,3.0,1.0])
    for algorithm in (:primal,:dual)
        options = SolverOptions(;verbose=false,algorithm)
        policy = JSimplex.NumericalPolicy(Float64;crash=true)
        basis = JSimplex.crash_basis(p,options,policy,()->false)
        ws = JSimplex.initialize_from_basis(p,basis,options;policy)
        @test ws.primal[1:3] == [2.0,3.0,1.0]
        @test basis.states[1:3] == [JSimplex.AT_LOWER,JSimplex.AT_UPPER,JSimplex.BASIC]
        @test iszero(JSimplex.primal_infeasibility(ws))
    end
end

@testset "Crash rejects objective-aware states with worse primal violation" begin
    p = LinearProblem(sparse([1.0 1.0]),[-1.0,-1.0];column_upper=ones(2),row_upper=[0.0])
    d = JSimplex.SimplexDiagnostics()
    policy = JSimplex.NumericalPolicy(Float64;crash=true)
    progress = JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy)
    initial = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);progress)
    ws,expired = JSimplex._crash_workspace(initial,()->false)
    @test ws === initial
    @test !expired
    @test ws.primal == zeros(3)
    @test JSimplex.event_count(d,:crash_fallback) == 1
    @test ws.iterations == 0
end

@testset "Crash interruption after final factorization uses no fresh budget" begin
    p = LinearProblem(spdiagm(0=>[2.0,3.0]),ones(2);row_lower=[2.0,3.0])
    done = Ref(false)
    d = JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin
        reason == :refactor_other && (done[]=true)
    end)
    policy = JSimplex.NumericalPolicy(Float64;crash=true)
    progress = JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy)
    initial = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);progress)
    ws,expired = JSimplex._crash_workspace(initial,()->done[])
    @test expired
    @test ws === initial
    @test ws.iterations == 2
    @test ws.refactorizations >= 2
    @test ws.basis.basic_indices == [3,4]
    @test JSimplex.event_count(d,:crash_accepted) == 0
end

@testset "Crash handles the empty model" begin
    p = LinearProblem(spzeros(0,0),Float64[])
    options = SolverOptions(verbose=false)
    policy = JSimplex.NumericalPolicy(Float64;crash=true)
    b = JSimplex.crash_basis(p,options,policy,()->false)
    @test isempty(b.basic_indices) && isempty(b.states)
    ws = JSimplex.initialize_from_basis(p,b,options;policy)
    @test isempty(ws.primal)
    @test JSimplex._recomputed_basis_reliable(ws)
end

module CrashLoggerTests
using Test, JSimplex, Logging, LinearAlgebra
struct FailingLogger <: AbstractLogger
    failure::SingularException
end
Logging.min_enabled_level(::FailingLogger) = Debug
Logging.shouldlog(::FailingLogger,args...) = true
Logging.catch_exceptions(::FailingLogger) = false
function Logging.handle_message(logger::FailingLogger,level,message,args...;kwargs...)
    message == "Refactorizing basis" && throw(logger.failure)
end
@testset "Crash refactorization logger failures propagate unchanged" begin
    p = LinearProblem(JSimplex.sparse(reshape([2.0],1,1)),[1.0];row_lower=[2.0])
    policy = JSimplex.NumericalPolicy(Float64;crash=true)
    for algorithm in (:primal,:dual)
        failure = SingularException(42)
        progress = JSimplex.SimplexProgressContext(p;numerical_policy=policy)
        options = SolverOptions(;verbose=false,algorithm)
        try
            with_logger(FailingLogger(failure)) do
                algorithm == :primal ? JSimplex._solve_continuous_primal(p,options;progress) :
                    JSimplex._solve_continuous_dual(p,options;progress)
            end
            @test false
        catch exception
            @test exception === failure
        end
    end
end
end

@testset "Crash refuses a relatively tiny pivot even for a feasible structural basis" begin
    delta = 1e-14
    p = LinearProblem(sparse([1.0 1.0;1.0 1.0+delta]),ones(2);
        row_lower=[2.0,2.0+delta],row_upper=[2.0,2.0+delta])
    options = SolverOptions(;verbose=false,algorithm=:dual,primal_tolerance=1e-16)
    policy = JSimplex.NumericalPolicy(Float64;crash=true)
    d = JSimplex.SimplexDiagnostics()
    progress = JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy)
    initial = JSimplex.initialize_workspace(p,options;progress)
    ws,expired = JSimplex._crash_workspace(initial,()->false)
    @test !expired
    @test JSimplex.event_count(d,:crash_pivot) == 1
    @test !(1 in ws.basis.basic_indices && 2 in ws.basis.basic_indices)
    @test JSimplex._recomputed_basis_reliable(ws)
end

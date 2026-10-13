using SparseArrays, LinearAlgebra, Logging

@testset "Postsolve keeps a feasible basis on the target face" begin
    # z can move along an objective-neutral face. Its restored row slack is
    # nonbasic at the original lower bound, so reconstruction returns z=0,
    # while the supplied feasible target has z=5. Discarding this basis loses
    # the useful x/y exchange even though the original LP is already optimal.
    p=LinearProblem(sparse([1.0 1.0 0.0; 0.0 0.0 1.0]),[-1.0,0.0,0.0];
        row_lower=[nothing,0.0],row_upper=[10.0,10.0],
        column_lower=[0.0,4.0,0.0],column_upper=[nothing,8.0,nothing])
    basis=JSimplex.Basis([2,3],JSimplex.VariableState[
        JSimplex.AT_LOWER,JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_UPPER,JSimplex.AT_LOWER])
    options=SolverOptions(basis_update=:bartels_golub,verbose=false,scaling=:off)
    ws=JSimplex.initialize_workspace(p,options)
    ws.basis=JSimplex.Basis(basis.basic_indices,basis.states)
    JSimplex.recompute!(ws;refactorize=true)
    target=[6.0,4.0,5.0]
    @test JSimplex.primal_infeasibility(ws)>0
    @test JSimplex._project_postsolve_basis!(ws,target,()->false)==1
    @test ws.primal[1:3]==[6.0,4.0,0.0]
    @test JSimplex._original_primal_feasible(p,ws.primal[1:3],options.primal_tolerance)
    result=JSimplex.cleanup_original(p,basis,
        SolverOptions(basis_update=:bartels_golub,iteration_limit=0,verbose=false),
        JSimplex.SolveContext(time_ns(),Inf),0,0;target_primal=target)
    @test result.status==OPTIMAL
    @test result.objective_value == -6.0
    @test result.iterations == 0
end

@testset "Feasible postsolve cleanup uses original-cost primal optimization" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        p=LinearProblem(sparse(T[1 1 0; 0 0 1]),T[-1,0,-1];
            row_lower=[nothing,T(0)],row_upper=T[10,10],
            column_lower=T[0,4,0],column_upper=[nothing,T(8),nothing])
        basis=JSimplex.Basis([2,3],JSimplex.VariableState[
            JSimplex.AT_LOWER,JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_UPPER,JSimplex.AT_LOWER])
        target=T[6,4,5]
        observed=Ref{Any}(nothing)
        observer=(reason,ws)->begin
            if reason==:phase_primal
                @test ws.options.algorithm==:primal
                @test JSimplex.primal_infeasibility(ws)<=ws.options.primal_tolerance
                observed[]=ws
            end
        end
        diagnostics=JSimplex.SimplexDiagnostics(;observer)
        options=SolverOptions(T;algorithm=:dual,verbose=false,iteration_limit=8)
        result=JSimplex.cleanup_original(p,basis,options,
            JSimplex.SolveContext(time_ns(),Inf,diagnostics),7,0;target_primal=target)
        @test result.status==OPTIMAL
        @test result.objective_value==T(-16)
        @test result.primal==T[6,4,10]
        @test result.iterations==8
        @test diagnostics.counts[:phase_primal]==1
        @test diagnostics.counts[:phase_dual]==0
        @test !isnothing(observed[])
        if !isnothing(observed[])
            @test observed[].options===options
        end
        limited=JSimplex.cleanup_original(p,basis,options,
            JSimplex.SolveContext(time_ns(),Inf),8,0;target_primal=target)
        @test limited.status==ITERATION_LIMIT
        @test limited.iterations==8
        expired=JSimplex.cleanup_original(p,basis,options,
            JSimplex.SolveContext(time_ns(),0.0),7,0;target_primal=target)
        @test expired.status==TIME_LIMIT
        @test expired.iterations==7
    end
end

@testset "Primal cleanup restores options on cancellation and observer errors" begin
    p=LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[1.0])
    options=SolverOptions(algorithm=:dual,verbose=false)
    ws=JSimplex.initialize_workspace(p,options)
    result=JSimplex._cleanup_primal_feasible!(ws,()->true)
    @test result.status==TIME_LIMIT
    @test result.iterations==0
    @test ws.options===options
    diagnostics=JSimplex.SimplexDiagnostics(;observer=(reason,state)->
        reason==:phase_primal ? error("stop during cleanup phase transition") : nothing)
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;diagnostics))
    @test_throws JSimplex.DiagnosticObserverFailure JSimplex._cleanup_primal_feasible!(ws,()->false)
    @test ws.options===options
end

@testset "Projection depends on numerical implementation, not strategy" begin
    p=LinearProblem(sparse([1.0 1.0 0.0; 0.0 0.0 1.0]),[-1.0,0.0,0.0];
        row_lower=[nothing,0.0],row_upper=[10.0,10.0],
        column_lower=[0.0,4.0,0.0],column_upper=[nothing,8.0,nothing])
    for profile in (:native,:checked), strategy in (:legacy,:adaptive)
    options=SolverOptions(simplex_strategy=strategy,verbose=false)
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=JSimplex.NumericalPolicy(Float64;numerical_profile=profile)))
    ws.basis=JSimplex.Basis([2,3],JSimplex.VariableState[
        JSimplex.AT_LOWER,JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_UPPER,JSimplex.AT_LOWER])
    JSimplex.recompute!(ws;refactorize=true)
    @test isnothing(JSimplex._project_postsolve_basis!(ws,[6.0,4.0,5.0],()->false)) == (profile == :checked)
    end
end

struct CleanupThrowingLogger <: AbstractLogger
    exception::Exception
end
Logging.min_enabled_level(::CleanupThrowingLogger) = Logging.Info
Logging.shouldlog(::CleanupThrowingLogger, args...) = true
Logging.catch_exceptions(::CleanupThrowingLogger) = false
function Logging.handle_message(logger::CleanupThrowingLogger, level, message, args...; kwargs...)
    message == "Starting primal postsolve cleanup from feasible basis" && throw(logger.exception)
    return nothing
end

@testset "Postsolve propagates numerical exceptions from caller logging" begin
    p=LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[1.0])
    options=SolverOptions(algorithm=:dual,verbose=true)
    basis=JSimplex.initialize_workspace(p,options).basis
    for exception in (SingularException(7),ZeroPivotException(7))
        caught=try
            with_logger(CleanupThrowingLogger(exception)) do
                JSimplex.cleanup_original(p,basis,options,JSimplex.SolveContext(time_ns(),Inf),0,0;
                    target_primal=[0.0])
            end
        catch error
            error
        end
        @test caught === exception
    end
end

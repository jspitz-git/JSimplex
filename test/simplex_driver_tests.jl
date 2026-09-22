using SparseArrays

@testset "Feasibility recovery decision table" begin
    @test JSimplex.feasibility_mode(true,true) == :certify
    @test JSimplex.feasibility_mode(true,false) == :primal
    @test JSimplex.feasibility_mode(false,true) == :dual
    @test JSimplex.feasibility_mode(false,false) == :phase_one
end

@testset "Original-cost cleanup recovers a newly inaccurate factor" begin
    injected = Ref(false)
    d = JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
        if event == :restore_perturbations && !injected[]
            injected[] = true
            ws.factorization.base = JSimplex._factorize_basis(-JSimplex.basis_matrix(ws))
        end
    end)
    p = LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0],row_upper=[2.0])
    o = SolverOptions(verbose=false,simplex_strategy=:adaptive)
    w = JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;
        diagnostics=d,numerical_policy=JSimplex.NumericalPolicy(Float64,o)))
    w.costs[1] = -1.0
    w.perturbed = true
    JSimplex.recompute!(w)
    result = JSimplex._solve_continuous_dual!(w,()->false)
    @test injected[]
    @test result.status == OPTIMAL
    @test result.primal ≈ [1.0]
end

@testset "Completed auxiliary work survives a callback exception" begin
    completed = Ref(0)
    d = JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
        event == :pivot_completed && (completed[] = ws.iterations)
    end)
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_lower=[1.0],row_upper=[2.0])
    o = SolverOptions(verbose=false,simplex_strategy=:adaptive)
    w = JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;
        diagnostics=d,numerical_policy=JSimplex.NumericalPolicy(Float64,o)))
    b = JSimplex.SimplexRunBudget(w)
    failure = JSimplex.SingularException(29)
    caught = try
        JSimplex.run_from_basis!(w,b,w.progress.numerical_policy,
            () -> completed[] > 0 ? throw(failure) : false)
    catch e
        e
    end
    @test completed[] > 0
    @test caught === failure
    @test w.iterations == b.iterations == completed[]
end

@testset "Shared driver solves all feasibility combinations" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), primal_ok in (false,true), dual_ok in (false,true)
        p = LinearProblem(sparse(T[1;;]),T[dual_ok ? 1 : -1];
            row_lower=T[primal_ok ? -1 : 1],row_upper=T[2])
        options = SolverOptions(T;verbose=false,simplex_strategy=:adaptive)
        w = JSimplex.initialize_workspace(p,options)
        w.iterations = 7
        before = w.refactorizations
        budget = JSimplex.SimplexRunBudget(w)
        run = @inferred JSimplex.run_from_basis!(w,budget,w.progress.numerical_policy,()->false)
        @test run.status == OPTIMAL
        @test run.primal ≈ T[dual_ok ? (primal_ok ? 0 : 1) : 2]
        @test run.iterations >= 7
        @test budget.iterations == run.iterations
        @test budget.refactorizations == run.refactorizations >= before
    end
end

@testset "Driver honors zero remaining iterations and an expired clock" begin
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[2.0])
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false,simplex_strategy=:adaptive,iteration_limit=0))
    b = JSimplex.SimplexRunBudget(w)
    @test JSimplex.run_from_basis!(w,b,w.progress.numerical_policy,()->false).status == ITERATION_LIMIT
    @test w.iterations == b.iterations == 0
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false,simplex_strategy=:adaptive,time_limit=0.0))
    b = JSimplex.SimplexRunBudget(w)
    @test JSimplex.run_from_basis!(w,b,w.progress.numerical_policy,()->false).status == TIME_LIMIT
    @test w.iterations == 0
end

@testset "Driver policy override and callback provenance" begin
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_lower=[1.0],row_upper=[2.0])
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false))
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,max_recovery_rounds=1)
    run = JSimplex.run_from_basis!(w,JSimplex.SimplexRunBudget(w),policy,()->false)
    @test run.status == OPTIMAL
    @test w.progress.numerical_policy === policy
    failure = JSimplex.SingularException(17)
    caught = try
        JSimplex.run_from_basis!(w,JSimplex.SimplexRunBudget(w),policy,()->throw(failure))
    catch e
        e
    end
    @test caught === failure
end

@testset "Driver keeps outer retry offsets and stricter phase I prices" begin
    p = LinearProblem(sparse([1.0;;]),[-1e-9];row_upper=[2.0])
    options = SolverOptions(verbose=false,simplex_strategy=:adaptive,iteration_limit=1,dual_tolerance=1e-7)
    progress = JSimplex.SimplexProgressContext(p;iteration_offset=11,
        numerical_policy=JSimplex.NumericalPolicy(Float64,options))
    w = JSimplex.initialize_workspace(p,options;progress)
    budget = JSimplex.SimplexRunBudget(w)
    @test budget.iteration_limit == 12
    run = JSimplex.run_from_basis!(w,budget,w.progress.numerical_policy,()->false;
        reduced_cost_tolerance=0.0)
    @test run.status == OPTIMAL
    @test run.iterations == 1
    @test budget.iterations == 12
    @test w.primal[1] == 2.0
end

@testset "A repaired basis is dispatched by its new feasibility" begin
    p = LinearProblem(sparse([1.0 1.0;1.0 1.0]),[1.0,2.0];
        row_lower=[1.0,1.0])
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false,simplex_strategy=:adaptive))
    w.basis = JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
    w.iterations = 13
    run = JSimplex.run_from_basis!(w,JSimplex.SimplexRunBudget(w),w.progress.numerical_policy,()->false)
    @test run.status == OPTIMAL
    @test run.objective_value ≈ 1.0
    @test run.iterations >= 13
    @test JSimplex.primal_infeasibility(w) <= w.options.primal_tolerance
    @test JSimplex.dual_infeasibility(w) <= w.options.dual_tolerance
end

@testset "Auxiliary phases respect cancellation and preserve user errors" begin
    for throwing in (false,true)
        entered = Ref(false)
        d = JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
            event == :phase_auxiliary && (entered[] = true)
        end)
        p = LinearProblem(sparse([1.0;;]),[-1.0];row_lower=[1.0],row_upper=[2.0])
        o = SolverOptions(verbose=false,simplex_strategy=:adaptive)
        w = JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;
            diagnostics=d,numerical_policy=JSimplex.NumericalPolicy(Float64,o)))
        b = JSimplex.SimplexRunBudget(w)
        failure = JSimplex.ZeroPivotException(9)
        stop = () -> entered[] ? (throwing ? throw(failure) : true) : false
        result = try
            JSimplex.run_from_basis!(w,b,w.progress.numerical_policy,stop)
        catch e
            e
        end
        @test entered[]
        @test throwing ? result === failure : result.status == TIME_LIMIT
        @test b.iterations == w.iterations == 0
        @test b.refactorizations == w.refactorizations
    end
end
@testset "A shared budget cannot be replenished by a fresh workspace" begin
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[2.0])
    o = SolverOptions(verbose=false,simplex_strategy=:adaptive,iteration_limit=2)
    w = JSimplex.initialize_workspace(p,o)
    budget = JSimplex.SimplexRunBudget(w)
    @test JSimplex.run_from_basis!(w,budget,w.progress.numerical_policy,()->false).status == OPTIMAL
    @test budget.iterations == 1
    q = LinearProblem(sparse([1.0 0.0;0.0 1.0]),[-1.0,-1.0];row_upper=[2.0,2.0])
    fresh = JSimplex.initialize_workspace(q,o)
    result = JSimplex.run_from_basis!(fresh,budget,fresh.progress.numerical_policy,()->false)
    @test result.status == ITERATION_LIMIT
    @test result.iterations == budget.iterations == 2
end

@testset "Ablating feasibility recovery disables method handoff" begin
    p = LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0])
    o = SolverOptions(verbose=false,algorithm=:primal,simplex_strategy=:adaptive)
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,feasibility_recovery=false)
    w = JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    result = JSimplex.run_from_basis!(w,JSimplex.SimplexRunBudget(w),policy,()->false)
    @test result.status == NUMERICAL_ERROR
    @test w.iterations == 0
end

@testset "Outer retries retain cumulative refactorization counts" begin
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[2.0])
    o = SolverOptions(verbose=false,simplex_strategy=:adaptive)
    progress = JSimplex.SimplexProgressContext(p;iteration_offset=11,refactorization_offset=7,
        numerical_policy=JSimplex.NumericalPolicy(Float64,o))
    w = JSimplex.initialize_workspace(p,o;progress)
    b = JSimplex.SimplexRunBudget(w)
    run = JSimplex.run_from_basis!(w,b,w.progress.numerical_policy,()->false)
    @test run.status == OPTIMAL
    @test b.iterations == 11+run.iterations
    @test b.refactorizations == 7+run.refactorizations
    @test w.progress.refactorization_offset == 7
end

@testset "Adaptive public solves certify the original model after phase I and postsolve" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), algorithm in (:primal,:dual), presolve in (false,true)
        p = LinearProblem(sparse(T[1 1]),T[2,1];row_lower=T[1],objective_constant=T(7))
        result = @inferred solve(p;options=SolverOptions(T;algorithm,presolve,
            simplex_strategy=:adaptive,verbose=false))
        @test result.status == OPTIMAL
        @test result.primal ≈ T[0,1]
        @test result.objective_value ≈ T(8)
    end
end
@testset "No-progress feasibility recovery remains bounded" begin
    for rounds in (0,1,100)
        p = LinearProblem(sparse([0.1;;]),[-1.0];row_upper=[1.0])
        o = SolverOptions(verbose=false,algorithm=:primal,zero_tolerance=0.5)
        policy = JSimplex.NumericalPolicy(Float64;feasibility_recovery=true,max_recovery_rounds=rounds)
        d = JSimplex.SimplexDiagnostics()
        w = JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;
            diagnostics=d,numerical_policy=policy))
        checks = Ref(0)
        run = JSimplex.run_from_basis!(w,JSimplex.SimplexRunBudget(w),policy,()->begin
            checks[] += 1
            checks[] > 100
        end)
        @test run.status == NUMERICAL_ERROR
        @test w.iterations == 0
        @test JSimplex.event_count(d,:phase_primal) <= 3
        @test JSimplex.event_count(d,:feasibility_recovery) > 0
        @test checks[] <= 100
    end
end
@testset "Final driver verification classifies internal solve failure" begin
    damaged = Ref(false)
    d = JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
        if event == :pivot_completed && !damaged[]
            damaged[] = true
            ws.factorization.base = JSimplex._factorize_basis(-2JSimplex.basis_matrix(ws))
        end
    end)
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[2.0])
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,max_recovery_rounds=0)
    o = SolverOptions(verbose=false,simplex_strategy=:adaptive)
    w = JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;
        diagnostics=d,numerical_policy=policy))
    b = JSimplex.SimplexRunBudget(w)
    result = JSimplex.run_from_basis!(w,b,policy,()->false)
    @test damaged[]
    @test result.status == NUMERICAL_ERROR
    @test result.iterations == b.iterations == 1
end

@testset "Driver restores working costs before original-model certification" begin
    p = LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0],row_upper=[2.0])
    o = SolverOptions(verbose=false,simplex_strategy=:adaptive)
    w = JSimplex.initialize_workspace(p,o)
    w.costs[1] = -1.0
    w.perturbed = true
    JSimplex.recompute!(w)
    b = JSimplex.SimplexRunBudget(w)
    result = JSimplex.run_from_basis!(w,b,w.progress.numerical_policy,()->false)
    @test result.status == OPTIMAL
    @test result.primal ≈ [1.0]
    @test w.costs == [1.0,0.0]
    @test !w.perturbed
    @test result.iterations == b.iterations
end

using Logging
struct DriverThrowLogger{E} <: AbstractLogger
    failure::E
    calls::Base.RefValue{Int}
end
Logging.min_enabled_level(::DriverThrowLogger) = Logging.Debug
Logging.shouldlog(::DriverThrowLogger,args...) = true
Logging.catch_exceptions(::DriverThrowLogger) = false
function Logging.handle_message(logger::DriverThrowLogger,level,message,args...;kwargs...)
    if message == "Refactorizing basis" && get(kwargs,:iterations,0) > 0
        logger.calls[] += 1
        throw(logger.failure)
    end
end
@testset "Budget wrappers preserve logger provenance through public catches" begin
    for algorithm in (:primal,:dual), enabled in (false,true), failure in (JSimplex.SingularException(41),JSimplex.ZeroPivotException(42))
        p = algorithm == :primal ? LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[2.0]) :
            LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0])
        o = SolverOptions(;verbose=false,algorithm,presolve=false,scaling=:off,
            refactorization_interval=1,simplex_strategy=:adaptive)
        policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,feasibility_recovery=enabled)
        logger = DriverThrowLogger(failure,Ref(0))
        caught = try
            with_logger(logger) do
                JSimplex._solve_diagnosed(p,nothing;options=o,numerical_policy=policy)
            end
        catch e
            e
        end
        @test logger.calls[] > 0
        @test caught === failure
    end
end

@testset "Replacement workspaces pass the shared deadline to inner solves" begin
    for algorithm in (:primal,:dual)
        p = algorithm == :primal ? LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[2.0]) :
            LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0])
        o = SolverOptions(;algorithm,verbose=false,simplex_strategy=:adaptive)
        original = JSimplex.initialize_workspace(p,o)
        budget = JSimplex.SimplexRunBudget(original)
        budget.time_limit_seconds = 120.0
        clocks = Tuple{UInt64,Float64}[]
        diagnostics = JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
            if event in (:phase_primal,:phase_dual)
                clock = JSimplex._basis_solve_stop(ws,nothing)
                push!(clocks,(clock.start_ns,clock.limit_seconds))
            end
        end)
        fresh = JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;
            diagnostics,numerical_policy=JSimplex.NumericalPolicy(Float64,o)))
        result = JSimplex.run_from_basis!(fresh,budget,fresh.progress.numerical_policy,()->false)
        @test result.status == OPTIMAL
        @test !isempty(clocks)
        @test all(clock->clock[1]==budget.start_ns,clocks)
        @test all(clock->clock[2]==budget.time_limit_seconds,clocks)
        @test fresh.options === o
    end
end

@testset "Working-cost unboundedness is not an original-model proof" begin
    for T in (Float64,Rational{BigInt}), empty_rows in (false,true), entry in (:driver,:dual)
        p = empty_rows ? LinearProblem(spzeros(T,0,1),T[1]) :
            LinearProblem(sparse(T[1;;]),T[1];row_lower=T[0])
        o = SolverOptions(T;verbose=false,simplex_strategy=:adaptive)
        w = JSimplex.initialize_workspace(p,o)
        w.costs[1] = -one(T)
        w.perturbed = true
        JSimplex.recompute!(w)
        result = entry == :driver ?
            JSimplex.run_from_basis!(w,JSimplex.SimplexRunBudget(w),w.progress.numerical_policy,()->false) :
            JSimplex._solve_continuous_dual!(w,()->false)
        @test result.status == OPTIMAL
        @test result.primal == T[0]
        @test result.objective_value == zero(T)
    end
end

@testset "Working-bound proofs cannot certify the original model" begin
    for entry in (:driver,:dual), proof in (:unbounded,:infeasible)
        p = proof == :unbounded ? LinearProblem(sparse([1.0;;]),[-1.0];column_upper=[1.0]) :
            LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0],column_upper=[2.0])
        w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false,simplex_strategy=:adaptive))
        w.upper[1] = proof == :unbounded ? Bound{Float64}(nothing) : Bound(0.0)
        JSimplex.recompute!(w)
        result = entry == :driver ?
            JSimplex.run_from_basis!(w,JSimplex.SimplexRunBudget(w),w.progress.numerical_policy,()->false) :
            JSimplex._solve_continuous_dual!(w,()->false)
        @test result.status == NUMERICAL_ERROR
        @test result.primal === nothing
    end
end

using SparseArrays

function stalling_workspace(;constant=0.0,window=4,enabled=true)
    p = LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0],objective_constant=constant)
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,
        adaptive_stalling=enabled,stagnation_window=window,refactor_timing=false)
    diagnostics = JSimplex.SimplexDiagnostics()
    return JSimplex.initialize_workspace(p,SolverOptions(verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
end

@testset "Only distinct completed steps advance workspace stagnation" begin
    ws = stalling_workspace()
    for i in 1:8
        ws.iterations += 1
        JSimplex._observe_stagnation!(ws,:dual,1e-30,1e-30)
        JSimplex._observe_stagnation!(ws,:dual,1e-30,1e-30)
        @test ws.scratch.stagnation.monitor.observations == i
    end
    @test ws.scratch.stagnation.monitor.state == :stalled
    @test ws.dual_pricing_fallback
    @test JSimplex.event_count(ws.progress.diagnostics,:stagnation_watch) == 1
    @test JSimplex.event_count(ws.progress.diagnostics,:stagnation_stalled) == 1
    @test JSimplex.event_count(ws.progress.diagnostics,:stagnation_fallback) == 1
    disabled = stalling_workspace(enabled=false)
    disabled.iterations = 8
    JSimplex._observe_stagnation!(disabled,:dual,0.0,0.0)
    @test isnothing(disabled.scratch.stagnation)
end

@testset "Restoring the same basis preserves the watched window" begin
    ws = stalling_workspace()
    saved = JSimplex.checkpoint_basis(ws)
    for i in 1:8
        ws.iterations += 1
        JSimplex._observe_stagnation!(ws,:dual,0.0,0.0)
        history = ws.scratch.stagnation
        @test JSimplex.restore_checkpoint!(ws,saved,()->false)
        @test ws.scratch.stagnation === history
        @test history.monitor.observations == i
    end
    @test ws.scratch.stagnation.monitor.state == :stalled
end

@testset "A working cost, bound, scaling, or algorithm change resets history" begin
    for change in (:cost,:bound,:scale,:algorithm)
        ws = stalling_workspace()
        for _ in 1:4
            ws.iterations += 1
            JSimplex._observe_stagnation!(ws,:dual,0.0,0.0)
        end
        @test ws.scratch.stagnation.monitor.state == :watch
        change == :cost && (ws.costs[1] += 1.0)
        change == :bound && (ws.upper[1] = JSimplex.Bound(10.0))
        change == :scale && (ws.progress.scaling.row_factors[1] *= 2.0)
        ws.iterations += 1
        JSimplex._observe_stagnation!(ws,change == :algorithm ? :primal : :dual,0.0,0.0)
        @test ws.scratch.stagnation.monitor.state == :progress
        @test ws.scratch.stagnation.monitor.window_count == 1
    end
end

@testset "Working observations ignore the additive objective constant" begin
    plain, shifted = stalling_workspace(), stalling_workspace(constant=1e20)
    for i in 1:12
        for ws in (plain,shifted)
            ws.iterations += 1
            JSimplex._observe_stagnation!(ws,:dual,1e-30,1e-30)
        end
        a,b = plain.scratch.stagnation.monitor,shifted.scratch.stagnation.monitor
        @test a.state == b.state
        @test a.end_objective == b.end_objective
        @test a.objective_improvement == b.objective_improvement
    end
end

@testset "Both simplex loops record productive completed steps" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}), algorithm in (:primal,:dual), update in (:pfi,:forrest_tomlin)
        n = 24
        p = algorithm == :primal ?
            LinearProblem(spdiagm(0=>ones(T,n)),-ones(T,n);row_upper=ones(T,n)) :
            LinearProblem(spdiagm(0=>ones(T,n)),ones(T,n);row_lower=ones(T,n))
        policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
            stagnation_window=4,refactor_timing=false)
        ws = JSimplex.initialize_workspace(p,SolverOptions(T;algorithm,basis_update=update,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        result = algorithm == :primal ? JSimplex._primal_optimize!(ws,()->false) :
            JSimplex._dual_optimize!(ws,()->false)
        @test result.status == OPTIMAL
        @test ws.iterations == n
        @test ws.scratch.stagnation.monitor.observations == n
        @test ws.scratch.stagnation.monitor.state == :progress
        @test !ws.dual_pricing_fallback
        @test ws.primal[1:n] == ones(T,n)
    end
end

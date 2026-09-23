using SparseArrays

@testset "Every working cost participates in the stagnation context" begin
    n = 40000
    problem = LinearProblem(spzeros(1,n),Float64.(1:n))
    ws = JSimplex.initialize_workspace(problem,SolverOptions(verbose=false))
    original = JSimplex._stagnation_context(ws,:dual)
    for j in (1,2,8192,20000,30000)
        ws.costs[j] += 0.5
        @test JSimplex._stagnation_context(ws,:dual) != original
        ws.costs[j] -= 0.5
    end
end

@testset "A degenerate primal pivot records its actual dual step" for incremental in (false,true)
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[0.0])
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,
        refactor_timing=false,stagnation_window=4,incremental_primal_pivots=incremental)
    ws = JSimplex.initialize_workspace(p,SolverOptions(algorithm=:primal,verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    result = JSimplex._primal_optimize!(ws,()->false)
    @test result.status == OPTIMAL
    @test ws.iterations == 1
    @test ws.scratch.last_primal_step == 0.0
    @test ws.scratch.last_dual_step == 1.0
    @test ws.scratch.stagnation.monitor.insignificant_steps == 0
end

@testset "Cache resets and rejected trials preserve live stagnation history" begin
    ws = stalling_workspace()
    for i in 1:8
        ws.iterations += 1
        JSimplex._observe_stagnation!(ws,:dual,0.0,0.0)
        history = ws.scratch.stagnation
        JSimplex.reset_devex!(ws)
        @test_throws JSimplex._PivotRejection JSimplex._transactional_simplex_step!(ws,()->false) do candidate,stop
            candidate.iterations += 1
            throw(JSimplex._PivotRejection(1,1,:refresh))
        end
        @test ws.scratch.stagnation === history
        @test history.monitor.observations == i
    end
    @test ws.scratch.stagnation.monitor.state == :stalled
end

@testset "Stagnation observations retain stored BigFloat precision" begin
    ws = setprecision(192) do
        p = LinearProblem(sparse(BigFloat[1;;]),BigFloat[1];row_lower=BigFloat[1])
        policy = JSimplex.NumericalPolicy(BigFloat;simplex_strategy=:adaptive,
            refactor_timing=false,stagnation_window=4)
        JSimplex.initialize_workspace(p,SolverOptions(BigFloat;verbose=false);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    end
    setprecision(64) do
        for i in 1:8
            ws.iterations += 1
            JSimplex._observe_stagnation!(ws,:dual,0,0)
        end
        @test precision(BigFloat) == 64
        @test precision(ws.scratch.stagnation.monitor.end_objective) == 192
        @test precision(ws.scratch.stagnation.cost_scale) == 192
        @test ws.scratch.stagnation.monitor.state == :stalled
    end
end

@testset "Diagnostic price steps do not overflow finite solver data" begin
    @test JSimplex._stagnation_price_step(typemax(Int64)//1,1//typemax(Int64)) ==
        big(typemax(Int64))^2//1
    m = JSimplex.StagnationMonitor{Float64}(2)
    for _ in 1:4
        JSimplex.observe_progress!(m;objective=1.0,primal_violation=1.0,
            dual_violation=0.0,primal_step=0.0,
            dual_step=floatmax(Float64)/floatmin(Float64))
    end
    @test m.state == :stalled
    @test m.insignificant_steps == 0
    @test_throws ArgumentError JSimplex.observe_progress!(m;objective=1.0,
        primal_violation=0.0,dual_violation=0.0,primal_step=NaN,dual_step=0.0)
end

using SparseArrays

function marginal_price_workspace(T=Float64; update=:pfi, strategy=:legacy,
                                  violation=1.0002033976466948, upper=false)
    sign=upper ? one(T) : -one(T)
    problem=LinearProblem(sparse(T[1 0]),T[1,sign];row_lower=T[1],column_upper=T[Inf,1])
    options=SolverOptions(T;algorithm=:dual,basis_update=update,simplex_strategy=strategy,
        verbose=false,presolve=false)
    ws=JSimplex.initialize_workspace(problem,options)
    ws.basis.states[2]=upper ? JSimplex.AT_UPPER : JSimplex.AT_LOWER
    ws.costs[2]=sign*T(violation)*options.dual_tolerance
    ws.perturbed=true
    JSimplex.recompute!(ws;refactorize=true)
    return ws
end

@testset "Legacy dual retains a basis after marginal working-price drift" begin
    for T in (Float32,Float64), update in (:pfi,:bartels_golub,:forrest_tomlin,:suhl_suhl), upper in (false,true)
        ws=marginal_price_workspace(T;update,upper)
        options=ws.options
        @test JSimplex.primal_infeasibility(ws)>options.primal_tolerance
        @test options.dual_tolerance<JSimplex.dual_infeasibility(ws)<2options.dual_tolerance
        terminal=JSimplex._dual_optimize!(ws,()->false)
        @test terminal.status==OPTIMAL
        if terminal.status==OPTIMAL
            @test ws.iterations==1
            @test JSimplex.dual_infeasibility(ws)<=options.dual_tolerance
            @test ws.options.dual_tolerance==options.dual_tolerance
            @test !JSimplex._original_optimality_certified(ws,ws.primal[1:2])
            # Restoring the real costs must still optimize the improving y edge.
            JSimplex._restore_original_costs!(ws)
            JSimplex.recompute!(ws;refactorize=true)
            terminal=JSimplex._primal_optimize!(ws,()->false;perturb_degenerate=false)
            run=JSimplex._internal_solution(ws,terminal)
            @test run.status==OPTIMAL
            @test run.primal==T[1,upper ? 0 : 1]
            @test run.objective_value==T(upper ? 1 : 0)
        end
    end
end

@testset "Marginal price repair cannot hide larger errors or ignore cancellation" begin
    for violation in (4.0,1e6)
        ws=marginal_price_workspace(;violation)
        costs=copy(ws.costs)
        terminal=JSimplex._dual_optimize!(ws,()->false)
        @test terminal.status==NUMERICAL_ERROR
        @test ws.costs==costs
        @test ws.iterations==0
    end
    ws=marginal_price_workspace()
    costs=copy(ws.costs)
    terminal=JSimplex._dual_optimize!(ws,()->true)
    @test terminal.status==TIME_LIMIT
    @test ws.costs==costs
    @test ws.iterations==0
    terminal=JSimplex._dual_optimize!(ws,()->false;perturb_degenerate=false)
    @test terminal.status==NUMERICAL_ERROR
    @test ws.costs==costs
end

@testset "Working-cost repair preserves an original unbounded direction" begin
    ws=marginal_price_workspace()
    ws.problem.column_lower[2]=JSimplex._unbounded_bound(Float64)
    ws.problem.column_upper[2]=JSimplex._unbounded_bound(Float64)
    ws.lower[2]=JSimplex._unbounded_bound(Float64);ws.upper[2]=JSimplex._unbounded_bound(Float64)
    ws.basis.states[2]=JSimplex.FREE_NONBASIC
    JSimplex.recompute!(ws;refactorize=true)
    terminal=JSimplex._dual_optimize!(ws,()->false)
    @test terminal.status==OPTIMAL
    if terminal.status==OPTIMAL
        @test !JSimplex._original_optimality_certified(ws,ws.primal[1:2])
        JSimplex._restore_original_costs!(ws)
        JSimplex.recompute!(ws;refactorize=true)
        terminal=JSimplex._primal_optimize!(ws,()->false;perturb_degenerate=false)
        @test terminal.status==UNBOUNDED
    end
end

@testset "Native price repair is independent of inactive perturbation policies" begin
    for setting in (:adaptive_dual_perturbation,:adaptive_primal_perturbation)
        ws=marginal_price_workspace()
        policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:legacy,
            Dict(setting=>true)...)
        progress=JSimplex.SimplexProgressContext(ws.problem;numerical_policy=policy)
        mixed=JSimplex.initialize_workspace(ws.problem,ws.options;progress)
        mixed.costs .= ws.costs;mixed.perturbed=true
        JSimplex.recompute!(mixed;refactorize=true)
        costs,prices=copy(mixed.costs),copy(mixed.reduced_costs)
        @test JSimplex._shift_marginal_dual_prices!(mixed,()->false)
        @test mixed.costs!=costs
        @test mixed.reduced_costs!=prices
        @test JSimplex.dual_infeasibility(mixed)==0
    end
end

@testset "Cancellation inside native price repair cannot start higher precision" begin
    source=marginal_price_workspace()
    diagnostics=JSimplex.SimplexDiagnostics()
    ws=JSimplex.initialize_workspace(source.problem,source.options;
        progress=JSimplex.SimplexProgressContext(source.problem;diagnostics))
    ws.costs .= source.costs;ws.perturbed=true
    JSimplex.recompute!(ws;refactorize=true)
    calls=Ref(0)
    stop=()->(calls[]+=1;calls[]>=2)
    costs,prices=copy(ws.costs),copy(ws.reduced_costs)
    @test !JSimplex._dual_prices_feasible_or_refined!(ws,stop;allow_cost_shifts=true)
    @test JSimplex.event_count(diagnostics,:correction_attempt)==0
    @test ws.costs==costs
    @test ws.reduced_costs==prices
end

@testset "Native price repair is atomic and excludes original-cost phases" begin
    ws=marginal_price_workspace()
    costs,prices=copy(ws.costs),copy(ws.reduced_costs)
    ws.perturbed=false
    @test !JSimplex._shift_marginal_dual_prices!(ws,()->false)
    @test ws.costs==costs && ws.reduced_costs==prices
    ws.perturbed=true
    ws.costs[2]=1e16 # The requested small adjustment is not representable here.
    costs=copy(ws.costs)
    @test !JSimplex._shift_marginal_dual_prices!(ws,()->false)
    @test ws.costs==costs && ws.reduced_costs==prices
    ws=marginal_price_workspace(;strategy=:adaptive)
    @test JSimplex._shift_marginal_dual_prices!(ws,()->false)
    ws=marginal_price_workspace()
    journal=JSimplex.PerturbationJournal(ws)
    journal.active=true;ws.scratch.perturbations=journal;ws.costs=journal.active_costs
    costs,prices=copy(ws.costs),copy(ws.reduced_costs)
    @test !JSimplex._shift_marginal_dual_prices!(ws,()->false)
    @test ws.costs==costs && ws.reduced_costs==prices
end

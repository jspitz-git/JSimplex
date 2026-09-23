@testset "Wide coupled LP retains its independent original optimum" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}), update in (:pfi,:forrest_tomlin)
        costs = fill(-one(T),129)
        costs[end] = -T(2)
        problem = LinearProblem(sparse(ones(T,1,129)),costs;row_upper=T[1],column_upper=ones(T,129))
        options = SolverOptions(T;algorithm=:primal,pricing=:auto,basis_update=update,
            presolve=false,simplex_strategy=:adaptive,verbose=false)
        policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
            partial_pricing=true,refactor_timing=false)
        diagnostics = JSimplex.SimplexDiagnostics()
        result = JSimplex._solve_diagnosed(problem,diagnostics;options,numerical_policy=policy)
        @test result.status == OPTIMAL
        @test result.objective_value == -T(2)
        @test result.primal[129] == one(T)
        @test iszero(sum(result.primal[1:128]))
        @test JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
        @test JSimplex.event_count(diagnostics,:pricing_full_scan) > 0
    end
end

@testset "Cancelled pivot and recovery preserve live candidate state" begin
    cancelled,enabled = Ref(false),Ref(true)
    ws,policy,diagnostics = partial_pricing_workspace(Float64;
        observer=(reason,trial)->begin
            reason in (:pivot_proposed,:restore_checkpoint) && enabled[] && (cancelled[]=true)
        end)
    ws.costs[1] = -1.0
    JSimplex.recompute!(ws)
    pool = JSimplex._pricing_pool!(ws,:primal)
    @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 1
    indices,cursor,passes = copy(pool.indices),pool.scan_position,pool.passes
    result = JSimplex._primal_iteration!(ws,()->cancelled[],ws.options.dual_tolerance)
    @test result.status == TIME_LIMIT
    @test ws.iterations == 0
    @test pool.indices == indices && pool.scan_position == cursor && pool.passes == passes
    cancelled[] = false
    checkpoint = JSimplex.checkpoint_basis(ws)
    generation = pool.basis_generation
    @test !JSimplex.restore_checkpoint!(ws,checkpoint,()->cancelled[])
    @test pool.indices == indices && pool.scan_position == cursor && pool.passes == passes
    @test pool.basis_generation == generation
    cancelled[] = enabled[] = false
    @test JSimplex.restore_checkpoint!(ws,checkpoint,()->cancelled[])
    @test pool.basis_generation > generation
    @test !pool.valid && isempty(pool.indices)
    @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 1
    @test pool.full_scan
end

@testset "Actual perturbation and restoration invalidate pool cost generations" begin
    ws,policy,_ = partial_pricing_workspace(Float64)
    pool = JSimplex._pricing_pool!(ws,:primal)
    @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 0
    generation = pool.cost_generation
    monitor = JSimplex.StagnationMonitor{Float64}(2;tolerance=policy.solve_tolerance)
    for _ in 1:4
        JSimplex.observe_progress!(monitor;objective=1.0,primal_violation=1.0,
            dual_violation=0.0,primal_step=0.0,dual_step=0.0)
    end
    journal = JSimplex.PerturbationJournal(ws)
    @test JSimplex.perturb_dual_costs!(ws,monitor,journal,policy) == 129
    @test pool.cost_generation > generation
    @test !pool.valid
    generation = pool.cost_generation
    JSimplex.restore_perturbations!(ws,journal)
    @test pool.cost_generation > generation
    @test !pool.valid
    JSimplex.recompute!(ws)
    @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 0
    @test pool.full_scan
end

@testset "Partial pricing shares the completed-step limit" begin
    costs = fill(-1.0,129);costs[end] = -2.0
    problem = LinearProblem(sparse(ones(1,129)),costs;row_upper=[1.0],column_upper=ones(129))
    options = SolverOptions(algorithm=:primal,pricing=:dantzig,presolve=false,
        simplex_strategy=:adaptive,iteration_limit=1,verbose=false)
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,
        partial_pricing=true,refactor_timing=false)
    result = JSimplex._solve_diagnosed(problem,nothing;options,numerical_policy=policy)
    @test result.status == ITERATION_LIMIT
    @test result.statistics.iterations == 1
end

@testset "Partial dual pricing retains extreme eligible scores and recovers weights" begin
    for (T,value,tolerance) in ((Float32,1e-6,1e-7),(Float64,1e-200,1e-220))
        A = sparse([1],[1],T[1],129,1)
        lower = fill(-one(T),129);lower[1] = T(value)
        problem = LinearProblem(A,T[1];row_lower=lower)
        options = SolverOptions(T;algorithm=:dual,pricing=:auto,verbose=false,
            simplex_strategy=:adaptive,primal_tolerance=T(tolerance))
        policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
            partial_pricing=true,refactor_timing=false)
        diagnostics = JSimplex.SimplexDiagnostics()
        ws = JSimplex.initialize_workspace(problem,options;
            progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy,diagnostics))
        @test JSimplex._prepare_auto_pricing!(ws,:dual)
        ws.pricing_weights .= floatmax(T)
        @test JSimplex.dual_edge_selection(ws) == 1
        @test !ws.scratch.pricing_pool.full_scan
        @test isnothing(JSimplex.dual_iteration!(ws,()->false))
        @test ws.iterations == 1
        @test ws.primal[1] == T(value)
        @test JSimplex.event_count(diagnostics,:pricing_weight_rejected) == 1
        @test JSimplex.event_count(diagnostics,:pricing_full_scan) > 0
    end
end

@testset "Generated wide pricing calibration has the intended MPS model" begin
    model = read_mps(joinpath(@__DIR__,"fixtures/solver/generated/wide-bound129.mps"))
    @test size(model.A) == (1,129)
    @test nnz(model.A) == 0
    @test model.objective == fill(-1.0,129)
    @test all(b -> isfinite(b) && JSimplex.bound_value(b) == 1.0,model.column_upper)
end

using SparseArrays

function watched_perturbation_workspace()
    ws,policy = perturbation_workspace()
    for _ in 1:4
        ws.iterations += 1
        JSimplex._observe_stagnation!(ws,:dual,0.0,0.0)
    end
    @test ws.scratch.stagnation.monitor.state == :stalled
    return ws,policy
end

@testset "The dual driver consumes completed stagnation windows" begin
    ws,policy = watched_perturbation_workspace()
    @test JSimplex._maybe_perturb_dual_costs!(ws,()->false) == 2
    @test ws.scratch.perturbations.active
    @test JSimplex._maybe_perturb_dual_costs!(ws,()->false) == 0
    @test ws.scratch.perturbations.level == 1
end

@testset "Auxiliary bounds never inherit adaptive cost shifts" begin
    ws,policy = watched_perturbation_workspace()
    @test JSimplex._maybe_perturb_dual_costs!(ws,()->false) == 2
    journal = ws.scratch.perturbations
    auxiliary = JSimplex._auxiliary_workspace(ws)
    @test isequal(auxiliary.costs,journal.original_costs)
    @test !auxiliary.scratch.dual_perturbation_allowed
    @test isnothing(auxiliary.scratch.perturbations)
    @test journal.active && ws.costs !== auxiliary.costs
    other = JSimplex.PerturbationJournal(auxiliary)
    @test JSimplex.perturb_dual_costs!(auxiliary,
        stalled_perturbation_monitor(Float64,policy),other,policy) == 0
end

@testset "Basis recovery cools perturbation without erasing stagnation history" begin
    ws,policy = watched_perturbation_workspace()
    @test JSimplex._maybe_perturb_dual_costs!(ws,()->false) == 2
    journal = ws.scratch.perturbations
    checkpoint = JSimplex.checkpoint_basis(ws)
    history = ws.scratch.stagnation
    @test JSimplex.restore_checkpoint!(ws,checkpoint,()->false)
    @test ws.scratch.perturbations === journal
    @test ws.costs === journal.active_costs
    @test ws.scratch.stagnation === history
    @test journal.cooldown_until >= ws.iterations+2policy.stagnation_window
end

@testset "Original objective restoration retires the adaptive journal" begin
    ws,policy = watched_perturbation_workspace()
    @test JSimplex._maybe_perturb_dual_costs!(ws,()->false) == 2
    journal = ws.scratch.perturbations
    JSimplex._restore_original_costs!(ws)
    @test !journal.active
    @test isnothing(ws.scratch.perturbations)
    @test isequal(ws.costs[1:4],ws.problem.objective)
end

function perturbation_chain_workspace(::Type{T}=Float64;enabled=true,update=:pfi,iteration_limit=100) where T
    A = T[0 0 1 -1; 0 1 -1 0; 1 -1 0 0; -1 0 0 1]
    p = LinearProblem(sparse(A),zeros(T,4);row_lower=T[1,1,1,-3])
    policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
        adaptive_dual_perturbation=enabled,stagnation_window=1,refactor_timing=false)
    diagnostics = JSimplex.SimplexDiagnostics()
    ws = JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:dual,
        basis_update=update,verbose=false,iteration_limit,time_limit=30.0);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
    return ws,policy
end

@testset "Actual stalled dual steps perturb and certify the original LP" begin
    for T in (Float32,Float64,BigFloat), update in (:pfi,:forrest_tomlin)
        ws,policy = perturbation_chain_workspace(T;update)
        original = copy(ws.costs)
        result = JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
        @test result.status == OPTIMAL
        @test ws.iterations == 3
        @test JSimplex.event_count(ws.progress.diagnostics,:perturbation) == 1
        @test JSimplex.event_count(ws.progress.diagnostics,:phase_cleanup) == 1
        @test JSimplex.event_count(ws.progress.diagnostics,:restore_perturbations) >= 1
        @test isequal(ws.costs,original)
        @test !ws.perturbed && isnothing(ws.scratch.perturbations)
        @test ws.primal[1:4] == [3.0,2,1,0]
        @test JSimplex.primal_infeasibility(ws) == 0
        @test JSimplex.dual_infeasibility(ws) == 0
        disabled,other = perturbation_chain_workspace(T;enabled=false,update=update)
        plain = JSimplex.run_from_basis!(disabled,JSimplex.SimplexRunBudget(disabled),other,()->false)
        @test plain.status == OPTIMAL
        @test disabled.primal[1:4] == ws.primal[1:4]
        @test JSimplex.event_count(disabled.progress.diagnostics,:perturbation) == 0
    end
end

@testset "An infeasibility result also retires active adaptive costs" begin
    p = LinearProblem(sparse([1.0;;]),[0.0];row_upper=[-1.0])
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,refactor_timing=false)
    ws = JSimplex.initialize_workspace(p,SolverOptions(algorithm=:dual,verbose=false,iteration_limit=10);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=JSimplex.SimplexDiagnostics()))
    original = copy(ws.costs)
    @test JSimplex.perturb_dual_costs!(ws,stalled_perturbation_monitor(Float64,policy),
        JSimplex.PerturbationJournal(ws),policy) == 1
    result = JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    @test result.status == INFEASIBLE
    @test JSimplex.event_count(ws.progress.diagnostics,:perturbation) == 1
    @test isequal(ws.costs,original)
    @test !ws.perturbed && isnothing(ws.scratch.perturbations)
end

@testset "Original-cost cleanup shares the completed-step and time budgets" begin
    ws,policy = perturbation_chain_workspace(iteration_limit=2)
    budget = JSimplex.SimplexRunBudget(ws)
    result = JSimplex.run_from_basis!(ws,budget,policy,()->false)
    @test result.status == ITERATION_LIMIT
    @test ws.iterations == budget.iterations == 2
    @test JSimplex.event_count(ws.progress.diagnostics,:perturbation) == 1
    @test JSimplex.event_count(ws.progress.diagnostics,:phase_cleanup) == 0
    ws,policy = perturbation_chain_workspace()
    budget = JSimplex.SimplexRunBudget(ws)
    # Cancellation immediately after restoration cannot certify a stale price.
    stop = () -> JSimplex.event_count(ws.progress.diagnostics,:phase_cleanup) > 0
    result = JSimplex.run_from_basis!(ws,budget,policy,stop)
    @test result.status == TIME_LIMIT
    @test ws.iterations == budget.iterations == 3
    @test !ws.perturbed && isnothing(ws.scratch.perturbations)
    @test all(iszero,ws.costs)
end

@testset "Automatic perturbation needs monitoring and original-cost recovery" begin
    for disabled in (:adaptive_dual_perturbation,:adaptive_stalling,:feasibility_recovery)
        ws,_ = watched_perturbation_workspace()
        policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,
            NamedTuple{(disabled,)}((false,))...)
        JSimplex._install_driver_policy!(ws,policy)
        @test !JSimplex._adaptive_dual_perturbation_enabled(policy)
        @test JSimplex._maybe_perturb_dual_costs!(ws,()->false) == 0
        @test isnothing(ws.scratch.perturbations)
    end
    ws,policy = perturbation_chain_workspace(Rational{BigInt})
    result = JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    @test result.status == OPTIMAL
    @test ws.primal[1:4] == [3,2,1,0]
    @test JSimplex.event_count(ws.progress.diagnostics,:perturbation) == 0
    @test isnothing(ws.scratch.perturbations)
end

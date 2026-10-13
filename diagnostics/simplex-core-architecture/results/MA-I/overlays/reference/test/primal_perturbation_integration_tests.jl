using SparseArrays

function primal_perturbation_chain(::Type{T}=Float64;enabled=true,update=:pfi,iteration_limit=100,dimension=3,window=1) where T
    objective=zeros(T,dimension); objective[1]=-one(T)
    upper=zeros(T,dimension); upper[end]=one(T)
    p=LinearProblem(spdiagm(0=>ones(T,dimension),1=>-ones(T,dimension-1)),objective;row_upper=upper)
    policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
        adaptive_pricing=false,adaptive_primal_perturbation=enabled,stagnation_window=window,refactor_timing=false)
    ws=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,
        basis_update=update,iteration_limit,time_limit=30.0,verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,
            diagnostics=JSimplex.SimplexDiagnostics()))
    return ws,policy
end

@testset "Actual stalled primal steps perturb and certify original bounds" begin
    for T in (Float32,Float64,BigFloat), update in (:pfi,:forrest_tomlin)
        ws,policy=primal_perturbation_chain(T;update)
        original=(copy(ws.lower),copy(ws.upper))
        budget=JSimplex.SimplexRunBudget(ws)
        run=JSimplex.run_from_basis!(ws,budget,policy,()->false)
        @test run.status==OPTIMAL
        @test ws.iterations==budget.iterations==3
        @test JSimplex.event_count(ws.progress.diagnostics,:perturbation)==1
        @test JSimplex.event_count(ws.progress.diagnostics,:phase_cleanup)==1
        @test JSimplex.event_count(ws.progress.diagnostics,:restore_perturbations)>=1
        @test isequal(original,(ws.lower,ws.upper))
        @test isnothing(ws.scratch.perturbations) && !ws.perturbed
        @test ws.primal[1:3]==ones(T,3)
        @test JSimplex._original_primal_feasible(ws,ws.primal[1:3])
        @test JSimplex.primal_infeasibility(ws)==JSimplex.dual_infeasibility(ws)==0
        plain,other=primal_perturbation_chain(T;enabled=false,update)
        result=JSimplex.run_from_basis!(plain,JSimplex.SimplexRunBudget(plain),other,()->false)
        @test result.status==OPTIMAL && result.objective_value==run.objective_value
        @test JSimplex.event_count(plain.progress.diagnostics,:perturbation)==0
    end
end

function shifted_primal_workspace(;unbounded=false)
    A=unbounded ? [1.0 0.0] : [1.0;;]
    p=LinearProblem(sparse(A),unbounded ? [0.0,-1.0] : [1.0];
        row_lower=[nothing],row_upper=[nothing])
    policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,refactor_timing=false)
    ws=JSimplex.initialize_workspace(p,SolverOptions(algorithm=:primal,
        iteration_limit=20,time_limit=30.0,verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,
            diagnostics=JSimplex.SimplexDiagnostics()))
    states=unbounded ? [JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.FREE_NONBASIC] :
        [JSimplex.BASIC,JSimplex.FREE_NONBASIC]
    ws.basis=JSimplex.Basis([1],states)
    JSimplex.recompute!(ws;refactorize=true)
    journal=JSimplex.PerturbationJournal(ws)
    @test JSimplex.perturb_primal_bounds!(ws,primal_stalled_monitor(Float64,policy),journal,policy)==1
    return ws,policy
end

@testset "A shifted optimum must be recomputed against original bounds" begin
    ws,policy=shifted_primal_workspace()
    terminal=JSimplex._primal_optimize!(ws,()->false)
    @test terminal.status==OPTIMAL
    @test ws.primal[1] < -ws.options.primal_tolerance
    @test !JSimplex._original_primal_feasible(ws,ws.primal[1:1])
    budget=JSimplex.SimplexRunBudget(ws)
    run=JSimplex.run_from_basis!(ws,budget,policy,()->false)
    @test run.status==OPTIMAL && run.objective_value==0
    @test run.primal==[0.0]
    @test JSimplex._original_bounds_active(ws)
    @test !ws.perturbed && isnothing(ws.scratch.perturbations)
    @test ws.iterations==budget.iterations
end

@testset "Expanded bounds are restored before an unboundedness proof" begin
    ws,policy=shifted_primal_workspace(unbounded=true)
    run=JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    @test run.status==UNBOUNDED
    @test JSimplex._original_bounds_active(ws)
    @test !ws.perturbed && isnothing(ws.scratch.perturbations)
    @test JSimplex.event_count(ws.progress.diagnostics,:phase_cleanup)==1
end

@testset "Primal bound cleanup honors cancellation and auxiliary isolation" begin
    ws,policy=shifted_primal_workspace()
    auxiliary=JSimplex._auxiliary_workspace(ws)
    @test !auxiliary.scratch.primal_perturbation_allowed
    @test isnothing(auxiliary.scratch.perturbations)
    @test !auxiliary.perturbed
    budget=JSimplex.SimplexRunBudget(ws)
    stop=()->JSimplex.event_count(ws.progress.diagnostics,:phase_cleanup)>0
    run=JSimplex.run_from_basis!(ws,budget,policy,stop)
    @test run.status==TIME_LIMIT
    @test JSimplex._original_bounds_active(ws)
    @test !ws.perturbed && isnothing(ws.scratch.perturbations)
    @test ws.iterations==budget.iterations
end

@testset "Primal perturbation shares the completed-step budget and exact branch" begin
    ws,policy=primal_perturbation_chain(iteration_limit=2)
    budget=JSimplex.SimplexRunBudget(ws)
    run=JSimplex.run_from_basis!(ws,budget,policy,()->false)
    @test run.status==ITERATION_LIMIT
    @test ws.iterations==budget.iterations==2
    @test JSimplex.event_count(ws.progress.diagnostics,:perturbation)==1
    @test JSimplex.event_count(ws.progress.diagnostics,:phase_cleanup)==0
    @test ws.scratch.perturbations.bounds.active
    ws,policy=primal_perturbation_chain(Rational{BigInt})
    run=JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    @test run.status==OPTIMAL && run.primal==[1,1,1]
    @test JSimplex.event_count(ws.progress.diagnostics,:perturbation)==0
    @test isnothing(ws.scratch.perturbations)
end

@testset "Primal perturbation requires monitoring" begin
    for disabled in (:adaptive_primal_perturbation,:adaptive_stalling)
        ws,_=primal_perturbation_chain()
        for _ in 1:2
            ws.iterations+=1
            JSimplex._observe_stagnation!(ws,:primal,0.0,0.0)
        end
        @test ws.scratch.stagnation.monitor.state==:stalled
        policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,
            NamedTuple{(disabled,)}((false,))...)
        JSimplex._install_driver_policy!(ws,policy)
        @test !JSimplex._adaptive_primal_perturbation_enabled(policy)
        @test JSimplex._maybe_perturb_primal_bounds!(ws,()->false)==0
        @test isnothing(ws.scratch.perturbations)
    end
end

@testset "Phase I excludes bound perturbation and phase II restores eligibility" begin
    p=LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0])
    phase_one=Bool[]
    phase_two=Bool[]
    d=JSimplex.SimplexDiagnostics(observer=(event,ws)->begin
        event==:phase_one && push!(phase_one,ws.scratch.primal_perturbation_allowed)
        if event==:phase_primal && ws.problem.objective==[1.0,0.0]
            push!(phase_two,ws.scratch.primal_perturbation_allowed)
        end
    end)
    policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,stagnation_window=1)
    result=JSimplex._solve_diagnosed(p,d;options=SolverOptions(algorithm=:primal,
        verbose=false,presolve=false,scaling=:off,iteration_limit=20),numerical_policy=policy)
    @test result.status==OPTIMAL && result.primal==[1.0]
    @test !isempty(phase_one) && all(!,phase_one)
    @test !isempty(phase_two) && all(phase_two)
end

@testset "Public primal results preserve the original LP through postsolve" begin
    for presolve in (false,true)
        ws,policy=primal_perturbation_chain()
        p=ws.problem
        original=(copy(p.A),copy(p.objective),copy(p.column_lower),copy(p.column_upper),
            copy(p.row_lower),copy(p.row_upper))
        d=JSimplex.SimplexDiagnostics()
        result=JSimplex._solve_diagnosed(p,d;options=SolverOptions(algorithm=:primal,
            verbose=false,presolve=presolve,scaling=:off,iteration_limit=100),numerical_policy=policy)
        @test result.status==OPTIMAL
        @test result.primal==ones(3) && result.objective_value==-1
        @test isequal(original,(p.A,p.objective,p.column_lower,p.column_upper,p.row_lower,p.row_upper))
        @test JSimplex._original_primal_feasible(p,result.primal,1e-7)
        if !presolve
            @test JSimplex.event_count(d,:perturbation)==1
            @test JSimplex.event_count(d,:phase_cleanup)==1
        end
    end
end

@testset "The default stagnation window triggers on a longer primal chain" begin
    ws,policy=primal_perturbation_chain(dimension=130,window=64,iteration_limit=200)
    budget=JSimplex.SimplexRunBudget(ws)
    run=JSimplex.run_from_basis!(ws,budget,policy,()->false)
    @test run.status==OPTIMAL && run.objective_value==-1
    @test run.primal==ones(130)
    @test JSimplex._original_primal_feasible(ws,run.primal)
    @test JSimplex.event_count(ws.progress.diagnostics,:perturbation)==1
    @test JSimplex.event_count(ws.progress.diagnostics,:phase_cleanup)==1
    @test JSimplex._original_bounds_active(ws)
    @test ws.iterations==budget.iterations==130
end

@testset "Native cleanup retires an owned bound journal after heuristics are disabled" begin
    ws, _ = shifted_primal_workspace()
    @test JSimplex._primal_optimize!(ws, ()->false).status == OPTIMAL
    policy = JSimplex.NumericalPolicy(Float64)
    JSimplex._install_driver_policy!(ws, policy)
    @test JSimplex._original_objective_driver_required(ws)
    run = JSimplex.run_from_basis!(ws, JSimplex.SimplexRunBudget(ws), policy, ()->false)
    @test run.status == OPTIMAL && run.primal == [0.0]
    @test JSimplex._original_bounds_active(ws)
    @test isnothing(ws.scratch.perturbations)
    @test !ws.progress.numerical_policy.feasibility_recovery
end

# Exercise native cleanup's first public entry with an owned bound journal.
# These are caller interruptions, not experiments in actual deadline expiry.
function native_bound_entry_interruption(mode)
    ws, _ = shifted_primal_workspace()
    d = ws.progress.diagnostics
    # Real setup has already run; disabled setup counters are not zero setup work.
    d.kernel_timing = true
    @test JSimplex._primal_optimize!(ws, ()->false).status == OPTIMAL
    @test all(d.kernel_calls[k] == get((ftran=2, btran=3, pricing=2), k, 0)
              for k in keys(d.kernel_calls))
    @test all(reinterpret(UInt64, x) == 0xbeae32f0ee144531 for x in ws.primal)
    @test ws.basis.basic_indices == [2]
    @test ws.basis.states == [JSimplex.AT_LOWER, JSimplex.BASIC]
    policy = JSimplex.NumericalPolicy(Float64)
    JSimplex._install_driver_policy!(ws, policy)
    budget = JSimplex.SimplexRunBudget(ws)
    journal = ws.scratch.perturbations
    @test journal.workspace_id == objectid(ws) && journal.bounds.active
    @test ws.lower === journal.bounds.active_lower && ws.upper === journal.bounds.active_upper
    # One owned snapshot of this tiny fixture; never a per-solve snapshot.
    p = ws.problem
    before = (point=copy(ws.primal), costs=copy(ws.costs), prices=copy(ws.reduced_costs),
        rho=copy(ws.scratch.rho), lower=copy(ws.lower), upper=copy(ws.upper),
        basis=copy(ws.basis.basic_indices), states=copy(ws.basis.states),
        original_lower=copy(journal.bounds.original_lower), original_upper=copy(journal.bounds.original_upper),
        original_costs=copy(journal.original_costs), active_costs=copy(journal.active_costs),
        journal_flags=(journal.workspace_id, journal.active, journal.original_perturbed, journal.bounds.level),
        storage=(objectid(ws.lower), objectid(ws.upper)), perturbed=ws.perturbed,
        options=ws.options, policy=ws.progress.numerical_policy, start_ns=ws.progress.start_ns,
        offsets=(ws.progress.iteration_offset, ws.progress.refactorization_offset),
        work=(ws.iterations, ws.refactorizations),
        row_scaling=copy(ws.progress.scaling.row_factors), column_scaling=copy(ws.progress.scaling.column_factors),
        matrix=copy(p.A), objective=copy(p.objective), row_lower=copy(p.row_lower), row_upper=copy(p.row_upper),
        column_lower=copy(p.column_lower), column_upper=copy(p.column_upper), domains=copy(p.variable_domains),
        model_scalars=(p.objective_constant, p.objective_sense, p.name),
        kernel_calls=copy(d.kernel_calls), event_counts=copy(d.counts), next_event=d.next_event)
    callback_calls = Ref(0)
    sentinel = JSimplex.LinearAlgebra.SingularException(29)
    stop = () -> begin
        callback_calls[] += 1
        mode == :throw && throw(sentinel)
        true
    end
    run = nothing
    caught = nothing
    try
        run = JSimplex.run_from_basis!(ws, budget, policy, stop)
    catch exception
        caught = exception
    end
    @test callback_calls[] == 1
    # Existing pre-guard cost/bound scans are not counted as numerical kernels.
    @test d.kernel_calls == before.kernel_calls
    @test (ws.iterations, ws.refactorizations) == before.work
    @test ws.scratch.perturbations === journal
    @test journal.workspace_id == objectid(ws) && journal.bounds.active
    @test ws.lower === journal.bounds.active_lower && ws.upper === journal.bounds.active_upper
    @test (objectid(ws.lower), objectid(ws.upper)) == before.storage
    @test (journal.workspace_id, journal.active, journal.original_perturbed, journal.bounds.level) == before.journal_flags
    @test isequal((ws.primal, ws.costs, ws.reduced_costs, ws.scratch.rho, ws.lower, ws.upper,
                   ws.basis.basic_indices, ws.basis.states),
                  (before.point, before.costs, before.prices, before.rho, before.lower, before.upper,
                   before.basis, before.states))
    @test isequal((journal.bounds.original_lower, journal.bounds.original_upper,
                   journal.original_costs, journal.active_costs),
                  (before.original_lower, before.original_upper, before.original_costs, before.active_costs))
    @test ws.perturbed == before.perturbed
    @test ws.options == before.options && ws.progress.numerical_policy == before.policy
    @test ws.progress.start_ns == budget.start_ns == before.start_ns
    @test (ws.progress.iteration_offset, ws.progress.refactorization_offset) == before.offsets
    @test (budget.iterations, budget.refactorizations) == before.work
    @test budget.iteration_limit == before.options.iteration_limit == 20
    @test budget.time_limit_seconds == before.options.time_limit == 30.0
    @test isequal((ws.progress.scaling.row_factors, ws.progress.scaling.column_factors),
                  (before.row_scaling, before.column_scaling))
    @test ws.problem === p
    @test isequal((p.A, p.objective, p.row_lower, p.row_upper, p.column_lower, p.column_upper, p.variable_domains),
                  (before.matrix, before.objective, before.row_lower, before.row_upper,
                   before.column_lower, before.column_upper, before.domains))
    @test (p.objective_constant, p.objective_sense, p.name) == before.model_scalars
    @test isnothing(d.observer)
    if mode == :stop
        @test isnothing(caught) && !isnothing(run)
        @test run.status == TIME_LIMIT && run.message == "time limit reached during feasibility recovery"
        @test isnothing(run.primal) && isnothing(run.objective_value) && isnothing(run.basis)
    else
        @test caught === sentinel && isnothing(run)
    end
    @test d.next_event == before.next_event + (mode == :stop ? 1 : 0)
    @test all(d.counts[k] - before.event_counts[k] == (mode == :stop && k == :checkpoint ? 1 : 0)
              for k in keys(d.counts))
end

@testset "Native owned-bound entry interruptions preserve working state" begin
    for mode in (:stop, :throw)
        @testset "$mode" begin
            native_bound_entry_interruption(mode)
        end
    end
end

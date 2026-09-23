using SparseArrays

function perturbation_workspace(::Type{T}=Float64) where T
    p = LinearProblem(sparse(ones(T,1,4)),[-zero(T),zero(T),zero(T),zero(T)];
        row_lower=T[1],column_lower=[zero(T),nothing,zero(T),nothing],
        column_upper=[nothing,zero(T),zero(T),nothing])
    policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
        stagnation_window=2,refactor_timing=false)
    ws = JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    return ws,policy
end

function stalled_perturbation_monitor(::Type{T},policy) where T
    m = JSimplex.StagnationMonitor{T}(2;tolerance=policy.solve_tolerance)
    for _ in 1:4
        JSimplex.observe_progress!(m;objective=one(T),primal_violation=one(T),
            dual_violation=zero(T),primal_step=zero(T),dual_step=zero(T))
    end
    return m
end

@testset "Dual perturbations own their costs and restore exact original bits" begin
    for T in (Float32,Float64,BigFloat)
        ws,policy = perturbation_workspace(T)
        model = copy(ws.problem.objective)
        original = copy(ws.costs)
        m = stalled_perturbation_monitor(T,policy)
        journal = JSimplex.PerturbationJournal(ws)
        @test journal.original_costs !== ws.costs
        @test journal.original_costs !== ws.problem.objective
        @test journal.active_costs !== ws.problem.objective
        @test JSimplex.perturb_dual_costs!(ws,m,journal,policy) == 2
        @test ws.costs === journal.active_costs
        @test ws.costs[1] > original[1]
        @test ws.costs[2] < original[2]
        @test isequal(ws.costs[3:end],original[3:end]) # Fixed, free, and basic.
        @test JSimplex.dual_infeasibility(ws) <= ws.options.dual_tolerance
        @test isequal(ws.problem.objective,model)
        @test isequal(journal.original_costs,original)
        @test ws.perturbed && journal.active
        @test JSimplex.restore_perturbations!(ws,journal) === nothing
        @test isequal(ws.costs,original)
        @test isequal(ws.problem.objective,model)
        @test !ws.perturbed && !journal.active
        JSimplex.recompute!(ws)
        @test JSimplex.dual_infeasibility(ws) == zero(T)
    end
end

@testset "Exact arithmetic never receives dual cost perturbations" begin
    for T in (Rational{Int64},Rational{BigInt})
        ws,policy = perturbation_workspace(T)
        original = copy(ws.costs)
        m = stalled_perturbation_monitor(T,policy)
        journal = JSimplex.PerturbationJournal(ws)
        @test JSimplex.perturb_dual_costs!(ws,m,journal,policy) == 0
        @test isequal(ws.costs,original)
        @test !ws.perturbed && !journal.active
    end
end

function advance_perturbation_window!(m,ws)
    for _ in 1:m.window
        ws.iterations += 1
        JSimplex.observe_progress!(m;objective=1,primal_violation=1,
            dual_violation=0,primal_step=0,dual_step=0)
    end
end

@testset "Perturbation levels are bounded and observations are not replayed" begin
    ws,policy = perturbation_workspace()
    m = stalled_perturbation_monitor(Float64,policy)
    journal = JSimplex.PerturbationJournal(ws)
    previous = 0.0
    for level in 1:3
        @test JSimplex.perturb_dual_costs!(ws,m,journal,policy) == 2
        @test journal.level == level
        @test previous < ws.costs[1] <= 512ws.options.dual_tolerance
        previous = ws.costs[1]
        saved = copy(ws.costs)
        @test JSimplex.perturb_dual_costs!(ws,m,journal,policy) == 0
        @test isequal(ws.costs,saved)
        advance_perturbation_window!(m,ws)
    end
    @test JSimplex.perturb_dual_costs!(ws,m,journal,policy) == 0
    @test journal.level == 3
end

@testset "Restoration imposes a cooldown without discarding the journal" begin
    ws,policy = perturbation_workspace()
    m = stalled_perturbation_monitor(Float64,policy)
    journal = JSimplex.PerturbationJournal(ws)
    @test JSimplex.perturb_dual_costs!(ws,m,journal,policy) == 2
    JSimplex.restore_perturbations!(ws,journal)
    JSimplex.recompute!(ws)
    advance_perturbation_window!(m,ws)
    @test JSimplex.perturb_dual_costs!(ws,m,journal,policy) == 0
    advance_perturbation_window!(m,ws)
    @test JSimplex.perturb_dual_costs!(ws,m,journal,policy) == 2
    @test journal.level == 2
end

@testset "Perturbation publication is guarded and journals have one owner" begin
    for cancel_at in (1,2)
        ws,policy = perturbation_workspace()
        m = stalled_perturbation_monitor(Float64,policy)
        journal = JSimplex.PerturbationJournal(ws)
        costs,prices = copy(ws.costs),copy(ws.reduced_costs)
        calls = Ref(0)
        stop = () -> (calls[] += 1; calls[] >= cancel_at)
        @test JSimplex.perturb_dual_costs!(ws,m,journal,policy;stop_requested=stop) == -1
        @test isequal(ws.costs,costs) && isequal(ws.reduced_costs,prices)
        @test journal.level == 0 && !journal.active && !ws.perturbed
        other,_ = perturbation_workspace()
        @test_throws ArgumentError JSimplex.perturb_dual_costs!(other,m,journal,policy)
        @test_throws ArgumentError JSimplex.restore_perturbations!(other,journal)
    end
end

@testset "Margins respect representability at huge and subnormal scales" begin
    p = LinearProblem(sparse([1.0 1.0]),[1e20,1e20];row_lower=[1.0],column_upper=[0.0,nothing])
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,refactor_timing=false)
    ws = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    ws.basis = JSimplex.Basis([1],JSimplex.VariableState[JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
    JSimplex.recompute!(ws;refactorize=true)
    @test JSimplex.dual_infeasibility(ws) == 0.0
    @test JSimplex.primal_infeasibility(ws) == 1.0
    @test ws.reduced_costs[2] == 0.0
    saved = copy(ws.costs)
    journal = JSimplex.PerturbationJournal(ws)
    @test JSimplex.perturb_dual_costs!(ws,stalled_perturbation_monitor(Float64,policy),journal,policy) == 0
    @test isequal(ws.costs,saved)
    ws,policy = perturbation_workspace()
    tiny = nextfloat(0.0)
    ws.options = SolverOptions(dual_tolerance=tiny,verbose=false)
    journal = JSimplex.PerturbationJournal(ws)
    @test JSimplex.perturb_dual_costs!(ws,stalled_perturbation_monitor(Float64,policy),journal,policy) == 2
    @test 0 < ws.costs[1] < floatmin(Float64)
    @test -floatmin(Float64) < ws.costs[2] < 0
    JSimplex.restore_perturbations!(ws,journal)
    @test isequal(ws.costs,journal.original_costs)
end

@testset "A new working-cost monitor can advance the next perturbation level" begin
    ws,policy = perturbation_workspace()
    journal = JSimplex.PerturbationJournal(ws)
    first = stalled_perturbation_monitor(Float64,policy)
    @test JSimplex.perturb_dual_costs!(ws,first,journal,policy) == 2
    # F11 creates a fresh monitor after a working-cost change; its observation
    # count starts over, while the journal's bounded level must survive.
    second = stalled_perturbation_monitor(Float64,policy)
    ws.iterations += 4
    @test JSimplex.perturb_dual_costs!(ws,second,journal,policy) == 2
    @test journal.level == 2
end

@testset "Dual perturbations preserve the workspace's BigFloat precision" begin
    setprecision(BigFloat,384) do
        ws,policy = perturbation_workspace(BigFloat)
        monitor = stalled_perturbation_monitor(BigFloat,policy)
        journal = JSimplex.PerturbationJournal(ws)
        original = copy(ws.costs)
        setprecision(BigFloat,96) do
            @test JSimplex.perturb_dual_costs!(ws,monitor,journal,policy) == 2
            @test precision(BigFloat) == 96
            @test precision(ws.costs[1]) == 384
            @test precision(ws.reduced_costs[1]) == 384
            JSimplex.restore_perturbations!(ws,journal)
            @test isequal(ws.costs,original)
        end
    end
end

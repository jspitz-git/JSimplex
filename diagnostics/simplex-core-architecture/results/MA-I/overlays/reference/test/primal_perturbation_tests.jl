using SparseArrays

function primal_perturbation_workspace(::Type{T}=Float64) where T
    # Structural variables form an identity basis at a lower, upper, fixed,
    # and free bound respectively. Row activities stay nonbasic at zero.
    p = LinearProblem(spdiagm(0=>ones(T,4)),zeros(T,4);
        row_lower=zeros(T,4),row_upper=zeros(T,4),
        column_lower=[-zero(T),nothing,zero(T),nothing],
        column_upper=[nothing,zero(T),zero(T),nothing])
    policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
        stagnation_window=2,refactor_timing=false)
    ws = JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    ws.basis = JSimplex.Basis(collect(1:4),vcat(fill(JSimplex.BASIC,4),fill(JSimplex.AT_LOWER,4)))
    JSimplex.recompute!(ws;refactorize=true)
    return ws,policy
end

function primal_stalled_monitor(::Type{T},policy) where T
    m=JSimplex.StagnationMonitor{T}(2;tolerance=policy.solve_tolerance)
    for _ in 1:4
        JSimplex.observe_progress!(m;objective=one(T),primal_violation=zero(T),
            dual_violation=one(T),primal_step=zero(T),dual_step=zero(T))
    end
    return m
end

@testset "Primal bounds expand outward and restore exact owned values" begin
    for T in (Float32,Float64,BigFloat)
        ws,policy=primal_perturbation_workspace(T)
        lower,upper=copy(ws.lower),copy(ws.upper)
        model=(copy(ws.problem.column_lower),copy(ws.problem.column_upper),
            copy(ws.problem.row_lower),copy(ws.problem.row_upper))
        primal=copy(ws.primal)
        journal=JSimplex.PerturbationJournal(ws)
        @test JSimplex.perturb_primal_bounds!(ws,primal_stalled_monitor(T,policy),journal,policy)==2
        @test ws.lower[1].value < lower[1].value
        @test ws.upper[2].value > upper[2].value
        @test isequal(ws.lower[2:end],lower[2:end])
        @test isequal(ws.upper[[1;3:8]],upper[[1;3:8]])
        @test all(b.bounded==a.bounded for (a,b) in zip(lower,ws.lower))
        @test all(b.bounded==a.bounded for (a,b) in zip(upper,ws.upper))
        @test ws.primal==primal
        @test JSimplex.primal_infeasibility(ws)==0
        @test ws.lower === journal.bounds.active_lower
        @test ws.upper === journal.bounds.active_upper
        @test journal.bounds.original_lower !== ws.lower
        @test journal.bounds.original_upper !== ws.upper
        @test journal.bounds.active && JSimplex._has_active_perturbations(journal)
        @test JSimplex.restore_perturbations!(ws,journal)===nothing
        @test isequal(ws.lower,lower) && isequal(ws.upper,upper)
        @test !JSimplex._has_active_perturbations(journal) && !ws.perturbed
        @test isequal(model,(ws.problem.column_lower,ws.problem.column_upper,
            ws.problem.row_lower,ws.problem.row_upper))
    end
end

@testset "Exact primal bounds never shift" begin
    for T in (Rational{Int64},Rational{BigInt})
        ws,policy=primal_perturbation_workspace(T)
        lower,upper=copy(ws.lower),copy(ws.upper)
        journal=JSimplex.PerturbationJournal(ws)
        @test JSimplex.perturb_primal_bounds!(ws,primal_stalled_monitor(T,policy),journal,policy)==0
        @test isequal(ws.lower,lower) && isequal(ws.upper,upper)
        @test isnothing(journal.bounds)
    end
end

@testset "Primal publication is cancellable without a partial journal" begin
    for cancel_at in (1,2)
        ws,policy=primal_perturbation_workspace()
        lower,upper=copy(ws.lower),copy(ws.upper)
        journal=JSimplex.PerturbationJournal(ws)
        calls=Ref(0)
        stop=()->(calls[]+=1;calls[]>=cancel_at)
        @test JSimplex.perturb_primal_bounds!(ws,primal_stalled_monitor(Float64,policy),
            journal,policy;stop_requested=stop)==-1
        @test isequal(ws.lower,lower) && isequal(ws.upper,upper)
        @test isnothing(journal.bounds) && !ws.perturbed
    end
end

@testset "Recovery cooldown also protects the first bound perturbation" begin
    ws,policy=primal_perturbation_workspace()
    journal=JSimplex.PerturbationJournal(ws)
    ws.scratch.perturbations=journal
    JSimplex._perturbation_recovered!(ws)
    monitor=primal_stalled_monitor(Float64,policy)
    @test JSimplex.perturb_primal_bounds!(ws,monitor,journal,policy)==0
    @test isnothing(journal.bounds)
    ws.iterations+=2policy.stagnation_window
    @test JSimplex.perturb_primal_bounds!(ws,monitor,journal,policy)==2
    @test journal.bounds.level==1 && journal.level==0
end

@testset "Huge primal bounds reject unrepresentable shifts with bounded attempts" begin
    p=LinearProblem(sparse([1.0;;]),[0.0];row_lower=[1e20],row_upper=[1e20],column_lower=[1e20])
    policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,stagnation_window=2)
    ws=JSimplex.initialize_workspace(p,SolverOptions(algorithm=:primal,verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    ws.basis=JSimplex.Basis([1],JSimplex.VariableState[JSimplex.BASIC,JSimplex.AT_LOWER])
    JSimplex.recompute!(ws;refactorize=true)
    journal=JSimplex.PerturbationJournal(ws)
    original=copy(ws.lower)
    @test JSimplex.primal_infeasibility(ws)==0
    for attempt in 1:4
        monitor=primal_stalled_monitor(Float64,policy)
        @test JSimplex.perturb_primal_bounds!(ws,monitor,journal,policy)==0
        @test journal.bounds.level==min(attempt,3)
        @test !journal.bounds.active && !ws.perturbed
        @test isequal(ws.lower,original)
    end
end

@testset "Primal perturbations preserve subnormal margins and stored precision" begin
    ws,policy=primal_perturbation_workspace()
    ws.options=SolverOptions(algorithm=:primal,verbose=false,primal_tolerance=nextfloat(0.0))
    journal=JSimplex.PerturbationJournal(ws)
    @test JSimplex.perturb_primal_bounds!(ws,primal_stalled_monitor(Float64,policy),journal,policy)==2
    @test -floatmin(Float64)<ws.lower[1].value<0
    @test 0<ws.upper[2].value<floatmin(Float64)
    setprecision(BigFloat,384) do
        ws,policy=primal_perturbation_workspace(BigFloat)
        original=copy(ws.lower)
        journal=JSimplex.PerturbationJournal(ws)
        monitor=primal_stalled_monitor(BigFloat,policy)
        setprecision(BigFloat,96) do
            @test JSimplex.perturb_primal_bounds!(ws,monitor,journal,policy)==2
            @test precision(ws.lower[1].value)==384
            @test precision(BigFloat)==96
            JSimplex.restore_perturbations!(ws,journal)
            @test isequal(ws.lower,original)
        end
    end
end

@testset "One journal restores independent cost and bound actions" begin
    p=LinearProblem(sparse([1.0;;]),[0.0];row_lower=[0.0])
    policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,stagnation_window=2)
    ws=JSimplex.initialize_workspace(p,SolverOptions(algorithm=:primal,verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    ws.basis=JSimplex.Basis([1],JSimplex.VariableState[JSimplex.BASIC,JSimplex.AT_LOWER])
    JSimplex.recompute!(ws;refactorize=true)
    original=(copy(ws.costs),copy(ws.lower),copy(ws.upper))
    journal=JSimplex.PerturbationJournal(ws)
    monitor=primal_stalled_monitor(Float64,policy)
    @test JSimplex.perturb_dual_costs!(ws,monitor,journal,policy)==1
    @test JSimplex.perturb_primal_bounds!(ws,monitor,journal,policy)==1
    @test journal.level==journal.bounds.level==1
    @test journal.active && journal.bounds.active
    JSimplex.restore_perturbations!(ws,journal)
    @test isequal(original,(ws.costs,ws.lower,ws.upper))
    @test !JSimplex._has_active_perturbations(journal) && !ws.perturbed
end

@testset "Basis recovery preserves active bound ownership and cooldown" begin
    ws,policy=primal_perturbation_workspace()
    journal=JSimplex.PerturbationJournal(ws)
    @test JSimplex.perturb_primal_bounds!(ws,primal_stalled_monitor(Float64,policy),journal,policy)==2
    lower,upper=copy(ws.lower),copy(ws.upper)
    checkpoint=JSimplex.checkpoint_basis(ws)
    @test JSimplex.restore_checkpoint!(ws,checkpoint,()->false)
    @test ws.scratch.perturbations===journal && journal.bounds.active
    @test ws.lower===journal.bounds.active_lower && ws.upper===journal.bounds.active_upper
    @test isequal((ws.lower,ws.upper),(lower,upper))
    @test journal.bounds.cooldown_until>=ws.iterations+2policy.stagnation_window
    @test journal.bounds.level==1 && journal.level==0
end

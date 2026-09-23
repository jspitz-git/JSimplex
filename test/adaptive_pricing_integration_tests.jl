@testset "Pricing consumes stagnation and rebuilds its reference" begin
    ws,d = automatic_pricing_workspace(Float64)
    JSimplex._prepare_auto_pricing!(ws,:primal)
    monitor = JSimplex.StagnationMonitor{Float64}(2)
    ws.scratch.stagnation = JSimplex.WorkspaceStagnation(monitor,UInt(0),0,1.0,1.0)
    pricing_observations!(monitor,4)
    JSimplex._observe_auto_pricing!(ws,:primal)
    @test ws.scratch.pricing.active == :dantzig
    pricing_observations!(monitor,4)
    fill!(ws.pricing_weights,17.0)
    JSimplex._observe_auto_pricing!(ws,:primal)
    @test ws.scratch.pricing.active == :devex
    @test all(isone,ws.pricing_weights)
    @test JSimplex.event_count(d,:pricing_dantzig) == 1
    @test JSimplex.event_count(d,:pricing_devex) == 1
    resets = ws.scratch.pricing.resets
    fill!(ws.pricing_weights,13.0)
    JSimplex.recompute!(ws;refactorize=true)
    @test all(isone,ws.pricing_weights)
    @test ws.scratch.pricing.resets == resets+1
    state = ws.scratch.pricing
    cooldown = state.cooldown_until
    checkpoint = JSimplex.checkpoint_basis(ws)
    @test JSimplex.restore_checkpoint!(ws,checkpoint,()->false)
    @test ws.scratch.pricing === state
    @test state.active == :devex && state.cooldown_until == cooldown
    @test state.last_monitor === monitor
    JSimplex._restore_original_costs!(ws)
    @test isnothing(ws.scratch.pricing)
    @test JSimplex._prepare_auto_pricing!(ws,:dual)
    @test ws.scratch.pricing.algorithm == :dual
    @test ws.scratch.pricing.active == :steepest_edge
end

@testset "Corrupted selected weights recover inside the actual pivot path" begin
    for T in (Float64,Rational{BigInt}),algorithm in (:primal,:dual)
        A=sparse(T[1 2;1 1])
        problem=algorithm==:primal ? LinearProblem(A,T[-3,-4];row_upper=T[4,3]) :
                                    LinearProblem(A,T[3,4];row_lower=T[4,3])
        options=SolverOptions(T;algorithm,pricing=:auto,simplex_strategy=:adaptive,
            verbose=false,iteration_limit=20)
        policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,refactor_timing=false)
        d=JSimplex.SimplexDiagnostics()
        ws=JSimplex.initialize_workspace(problem,options;
            progress=JSimplex.SimplexProgressContext(problem;diagnostics=d,numerical_policy=policy))
        JSimplex._prepare_auto_pricing!(ws,algorithm)
        algorithm==:primal && JSimplex._primal_entering(ws,options.dual_tolerance)
        for j in eachindex(ws.basis.states)
            if (ws.basis.states[j]==JSimplex.BASIC) == (algorithm==:dual)
                ws.pricing_weights[j] *= 8
            end
        end
        run=JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
        @test run.status==OPTIMAL
        @test run.primal==T[2,1]
        @test run.objective_value==(algorithm==:primal ? T(-10) : T(10))
        @test JSimplex._original_primal_feasible(ws,run.primal)
        @test JSimplex.event_count(d,:pricing_weight_rejected)==1
        @test JSimplex.event_count(d,:pricing_devex)==1
        @test ws.scratch.pricing.active==:devex
    end
end

@testset "Explicit pricing does not allocate automatic histories" begin
    for pricing in (:steepest_edge,:devex,:dantzig)
        ws,d=automatic_pricing_workspace(Float64;pricing)
        original=copy(ws.pricing_weights)
        monitor=JSimplex.StagnationMonitor{Float64}(2)
        pricing_observations!(monitor,4)
        ws.scratch.stagnation=JSimplex.WorkspaceStagnation(monitor,UInt(0),0,1.0,1.0)
        @test JSimplex._prepare_auto_pricing!(ws,:primal)
        JSimplex._observe_auto_pricing!(ws,:primal)
        @test isnothing(ws.scratch.pricing)
        @test ws.pricing_weights==original
        @test JSimplex._effective_pricing(ws,:primal)==pricing
    end
end

@testset "Cancelled checkpoint recovery does not publish pricing resets" begin
    cancelled,enabled=Ref(false),Ref(true)
    ws,d=automatic_pricing_workspace(Float64;observer=(reason,trial)->begin
        reason==:restore_checkpoint && enabled[] && (cancelled[]=true)
    end)
    JSimplex._prepare_auto_pricing!(ws,:primal)
    checkpoint=JSimplex.checkpoint_basis(ws)
    state=ws.scratch.pricing
    resets=state.resets
    count=JSimplex.event_count(d,:pricing_reset)
    weights=copy(ws.pricing_weights)
    @test !JSimplex.restore_checkpoint!(ws,checkpoint,()->cancelled[])
    @test ws.scratch.pricing === state
    @test state.resets==resets
    @test ws.pricing_weights==weights
    @test JSimplex.event_count(d,:pricing_reset)==count
    cancelled[]=false
    enabled[]=false
    @test JSimplex.restore_checkpoint!(ws,checkpoint,()->cancelled[])
    @test state.resets==resets+1
    @test JSimplex.event_count(d,:pricing_reset)==count+1
end

@testset "Exact weight validation does not overflow a fixed-width proof" begin
    T=Rational{Int64}
    direct,_=automatic_pricing_workspace(T;algorithm=:dual)
    JSimplex._prepare_auto_pricing!(direct,:dual)
    @test !JSimplex._validate_dual_edge!(direct,3,T[Int64(1)<<40,0])
    problem=LinearProblem(sparse(T[1//(Int64(1)<<40);;]),T[0];row_lower=T[-1],row_upper=T[-1])
    options=SolverOptions(T;algorithm=:dual,pricing=:auto,simplex_strategy=:adaptive,
        verbose=false,iteration_limit=10)
    policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,refactor_timing=false)
    d=JSimplex.SimplexDiagnostics()
    ws=JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;diagnostics=d,numerical_policy=policy))
    ws.basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER])
    JSimplex.recompute!(ws;refactorize=true)
    result=JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    @test result.status==INFEASIBLE
    @test ws.iterations==0
    @test JSimplex.event_count(d,:pricing_weight_rejected)==1
    @test JSimplex.event_count(d,:pricing_devex)==1
end

@testset "Automatic dual scores keep extreme eligible rows" begin
    for (T,violation,tolerance,large) in ((Float32,1e-6,1e-7,1e20),(Float64,1e-200,1e-220,1e200))
        problem=LinearProblem(sparse(T[1;;]),T[1];row_lower=T[violation])
        options=SolverOptions(T;algorithm=:dual,pricing=:auto,simplex_strategy=:adaptive,
            primal_tolerance=T(tolerance),verbose=false,iteration_limit=10)
        policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,refactor_timing=false)
        d=JSimplex.SimplexDiagnostics()
        ws=JSimplex.initialize_workspace(problem,options;
            progress=JSimplex.SimplexProgressContext(problem;diagnostics=d,numerical_policy=policy))
        JSimplex._prepare_auto_pricing!(ws,:dual)
        fill!(ws.pricing_weights,floatmax(T))
        result=JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
        @test result.status==OPTIMAL
        @test result.primal==T[violation]
        @test JSimplex.event_count(d,:pricing_weight_rejected)==1
        @test ws.iterations==1

        wide=LinearProblem(sparse(T[1 0;0 1]),T[1,1];row_lower=T[large,2large])
        workspace=JSimplex.initialize_workspace(wide,SolverOptions(T;pricing=:auto,verbose=false))
        @test JSimplex.dual_edge_selection(workspace)==2
    end
end

@testset "Refactorization retains basis-invariant steepest-edge caches" begin
    p=LinearProblem(sparse([1.0 2.0 0.0;2.0 1.0 1.0]),[-5.0,-4.0,1.0];row_upper=[4.0,5.0])
    options=SolverOptions(algorithm=:primal,pricing=:auto,simplex_strategy=:adaptive,verbose=false)
    policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,refactor_timing=false)
    d=JSimplex.SimplexDiagnostics(kernel_timing=true)
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy))
    @test isnothing(JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance))
    entering,_=JSimplex._primal_entering(ws,options.dual_tolerance)
    @test entering>0 && ws.scratch.steepest_valid[entering]
    weights=copy(ws.pricing_weights)
    valid=copy(ws.scratch.steepest_valid)
    JSimplex.recompute!(ws;refactorize=true)
    @test ws.pricing_weights==weights
    @test ws.scratch.steepest_valid==valid
    calls=copy(d.kernel_calls)
    @test first(JSimplex._primal_entering(ws,options.dual_tolerance))==entering
    @test d.kernel_calls==calls
    direction=zeros(2)
    JSimplex.forward_solve!(direction,ws.factorization,Vector(p.A[:,entering]))
    ws.pricing_weights[entering]*=8
    @test !JSimplex._validate_primal_edge!(ws,entering,direction)
    @test ws.scratch.pricing.active==:devex
end

@testset "Automatic pricing reaches an independently known vertex" begin
    # Intersection of x+2y=4 and x+y=3: (x,y)=(2,1), min -3x-4y=-10.
    # Dual multipliers (-1,-2) are also exact in every tested scalar type.
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}),
        algorithm in (:primal,:dual), strategy in (:legacy,:adaptive)
        problem = LinearProblem(sparse(T[1 2;1 1]),T[-3,-4];row_upper=T[4,3])
        options = SolverOptions(T;algorithm,pricing=:auto,simplex_strategy=strategy,
            presolve=false,scaling=:off,verbose=false,iteration_limit=30)
        seen = Ref(false)
        d = JSimplex.SimplexDiagnostics(observer=(reason,ws)->begin
            if reason == :pivot_completed
                seen[] |= !isnothing(ws.scratch.pricing)
            end
        end)
        result = JSimplex._solve_diagnosed(problem,d;options)
        @test result.status == OPTIMAL
        @test seen[]
        if result.status == OPTIMAL
            @test result.objective_value ≈ T(-10)
            @test result.primal ≈ T[2,1]
            @test JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
        end
        algorithm == :primal && @test JSimplex.event_count(d,:pricing_weight_rejected) == 0
    end
end

function auto_pricing_chain(::Type{T}=Float64;update=:pfi,limit=30,observer=nothing) where T
    n=10
    A=spdiagm(0=>ones(T,n),1=>fill(-one(T),n-1))
    p=LinearProblem(A,vcat(-one(T),zeros(T,n-1));row_upper=vcat(zeros(T,n-1),one(T)))
    options=SolverOptions(T;algorithm=:primal,pricing=:auto,simplex_strategy=:adaptive,
        basis_update=update,iteration_limit=limit,verbose=false)
    policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,stagnation_window=2,
        adaptive_dual_perturbation=false,adaptive_primal_perturbation=false,refactor_timing=false)
    d=JSimplex.SimplexDiagnostics(;observer)
    progress=JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy)
    return JSimplex.initialize_workspace(p,options;progress),policy,d
end

@testset "A stalled primal path uses and leaves temporary Dantzig" begin
    for T in (Float64,Rational{BigInt}),update in (:pfi,:forrest_tomlin)
        ws,policy,d=auto_pricing_chain(T;update)
        budget=JSimplex.SimplexRunBudget(ws)
        result=JSimplex.run_from_basis!(ws,budget,policy,()->false)
        @test result.status==OPTIMAL
        @test result.objective_value == -one(T)
        @test result.primal == ones(T,10)
        @test JSimplex._original_primal_feasible(ws,result.primal)
        @test ws.iterations==budget.iterations==10
        @test JSimplex.event_count(d,:pricing_dantzig)==1
        @test JSimplex.event_count(d,:pricing_devex)==1
        @test ws.scratch.pricing.active==:devex
        @test ws.scratch.pricing.pricing_passes>0
    end
end

@testset "Automatic pricing shares step and stop budgets" begin
    ws,policy,d=auto_pricing_chain(limit=6)
    budget=JSimplex.SimplexRunBudget(ws)
    result=JSimplex.run_from_basis!(ws,budget,policy,()->false)
    @test result.status==ITERATION_LIMIT
    @test ws.iterations==budget.iterations==6
    @test ws.scratch.pricing.active==:dantzig
    cancelled=Ref(false)
    ws,policy,d=auto_pricing_chain(observer=(reason,ws)->begin
        reason==:pricing_dantzig && (cancelled[]=true)
    end)
    result=JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),policy,()->cancelled[])
    @test result.status==TIME_LIMIT
    @test ws.iterations==4
    fresh,_=automatic_pricing_workspace(Float64)
    @test !JSimplex._prepare_auto_pricing!(fresh,:primal;stop=()->true)
    @test isnothing(fresh.scratch.pricing)
end

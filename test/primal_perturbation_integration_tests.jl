using SparseArrays

function primal_perturbation_chain(::Type{T}=Float64;enabled=true,update=:pfi,iteration_limit=100,dimension=3,window=1) where T
    objective=zeros(T,dimension); objective[1]=-one(T)
    upper=zeros(T,dimension); upper[end]=one(T)
    p=LinearProblem(spdiagm(0=>ones(T,dimension),1=>-ones(T,dimension-1)),objective;row_upper=upper)
    policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
        adaptive_primal_perturbation=enabled,stagnation_window=window,refactor_timing=false)
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

@testset "Primal perturbation requires monitoring and original-model recovery" begin
    for disabled in (:adaptive_primal_perturbation,:adaptive_stalling,:feasibility_recovery)
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

using Test,JSimplex,SparseArrays,LinearAlgebra,SHA
BLAS.set_num_threads(1)
include(joinpath(@__DIR__,"pricing_isolation.jl"))
const INTERACTION_ISOLATION_SHA256=isolate_pricing_trials!()

function phase_chain(::Type{T},n=12) where T
    A=vcat(spdiagm(0=>ones(T,n),1=>-ones(T,n-1)),sparse([1],[1],[one(T)],1,n))
    return LinearProblem(A,vcat(-one(T),zeros(T,n-1));
        row_lower=vcat(fill(Bound{T}(nothing),n),Bound(one(T))),
        row_upper=vcat(fill(Bound(zero(T)),n-1),Bound(one(T)),Bound{T}(nothing)))
end

@testset "Phase-I perturbation and bounded pricing compose with original cleanup" begin
    for T in (Float64,Rational{BigInt}), mode in (:none,:perturb,:pricing,:both)
        p=phase_chain(T)
        events=NamedTuple[]
        observer=(event,ws)->begin
            if event in (:phase_one,:phase_primal,:phase_cleanup,:pricing_dantzig,
                :pricing_progress_return,:pricing_trial_expired,:perturbation,
                :restore_perturbations,:pricing_phase_reset)
                s=ws.scratch.pricing
                push!(events,(;event,iteration=ws.iterations,
                    pricing=isnothing(s) ? :steepest_edge : s.active,
                    temporary=!isnothing(s) && s.temporary,
                    original_bounds=JSimplex._original_bounds_active(ws),
                    active=JSimplex._has_active_perturbations(ws.scratch.perturbations)))
            end
        end
        perturb=mode in (:perturb,:both)
        pricing=mode in (:pricing,:both)
        policy=JSimplex.NumericalPolicy(T;phase_one=true,adaptive_stalling=true,stagnation_window=1,
            adaptive_primal_perturbation=perturb,adaptive_pricing=pricing,refactor_timing=false)
        @test all(s->getfield(policy,s)==(s in (:phase_one,:adaptive_stalling) ||
            (perturb && s==:adaptive_primal_perturbation) || (pricing && s==:adaptive_pricing)),JSimplex.NUMERICAL_SWITCHES)
        d=JSimplex.SimplexDiagnostics(;observer)
        options=SolverOptions(T;algorithm=:primal,pricing=:steepest_edge,presolve=false,scaling=:off,
            time_limit=30.0,iteration_limit=1000,verbose=false)
        result=JSimplex._solve_diagnosed(p,d;options,numerical_policy=policy)
        @test result.status==OPTIMAL
        @test result.objective_value ≈ -one(T)
        @test JSimplex._original_primal_feasible(p,result.primal,options.primal_tolerance)
        @test count(x->x.event==:phase_one,events)==1
        phases=filter(x->x.event==:phase_primal,events)
        @test !isempty(phases)
        @test all(x->x.original_bounds && !x.active && !x.temporary,phases)
        shifts=filter(x->x.event==:perturbation,events)
        @test isempty(shifts)==(!perturb || T <: Rational)
        @test any(x->x.event==:pricing_dantzig,events)==pricing
        if !isempty(shifts)
            @test any(x->x.event==:restore_perturbations,events)
            @test any(x->x.event==:phase_cleanup,events)
            @test all(x->x.active && !x.original_bounds,shifts)
        end
    end
end

@testset "Dual cost perturbation and pricing retire before original certification" begin
    for mode in (:none,:perturb,:pricing,:both), n in (4,12)
        # The short cycle finishes within a pricing trial; the long one stays
        # stalled long enough to exercise expiry, perturbation and cleanup.
        A=zeros(n,n)
        for row in 1:n-1
            j=n-row
            A[row,j]=1.0; A[row,j+1]=-1.0
        end
        A[n,1]=-1.0; A[n,n]=1.0
        p=LinearProblem(sparse(A),zeros(n);row_lower=vcat(ones(n-1),1.0-n))
        perturb=mode in (:perturb,:both); pricing=mode in (:pricing,:both)
        policy=JSimplex.NumericalPolicy(Float64;phase_one=true,adaptive_stalling=true,stagnation_window=1,
            adaptive_dual_perturbation=perturb,adaptive_pricing=pricing,refactor_timing=false)
        d=JSimplex.SimplexDiagnostics()
        ws=JSimplex.initialize_workspace(p,SolverOptions(algorithm=:dual,pricing=:steepest_edge,verbose=false,time_limit=30.0);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
        result=JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
        @test result.status==OPTIMAL
        @test result.objective_value==0.0
        @test JSimplex._original_primal_feasible(p,result.primal,ws.options.primal_tolerance)
        @test JSimplex._original_costs_active(ws) && JSimplex._original_bounds_active(ws)
        @test !JSimplex._has_active_perturbations(ws.scratch.perturbations)
        shifted = JSimplex.event_count(d,:perturbation)>0
        @test shifted == (perturb && (!pricing || n==12))
        if shifted && pricing
            @test !isnothing(ws.scratch.pricing) && !ws.scratch.pricing.temporary
            @test JSimplex._effective_pricing(ws,:dual)==:steepest_edge
        end
    end
end

@testset "Combined Phase-I interventions remain private on cancellation" begin
    for stop_event in (:perturbation,:restore_perturbations)
        p=phase_chain(Float64)
        cancelled=Ref(false)
        private_phase=Ref{Any}(nothing)
        observer=(event,ws)->begin
            event==:phase_one && (private_phase[]=ws)
            event==stop_event && (cancelled[]=true)
        end
        policy=JSimplex.NumericalPolicy(Float64;phase_one=true,adaptive_stalling=true,
            adaptive_primal_perturbation=true,adaptive_pricing=true,stagnation_window=1,
            refactor_timing=false)
        d=JSimplex.SimplexDiagnostics(;observer)
        options=SolverOptions(algorithm=:primal,pricing=:steepest_edge,verbose=false,time_limit=30.0)
        ws=JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
        original=(copy(ws.basis.basic_indices),copy(ws.basis.states),copy(ws.lower),copy(ws.upper))
        budget=JSimplex.SimplexRunBudget(ws)
        result=JSimplex.run_phase_one!(ws,budget,policy,()->cancelled[])
        @test cancelled[]
        @test result.status==TIME_LIMIT
        @test isnothing(result.primal) && isnothing(result.objective_value)
        @test original==(ws.basis.basic_indices,ws.basis.states,ws.lower,ws.upper)
        @test !JSimplex._has_active_perturbations(ws.scratch.perturbations)
        @test JSimplex.event_count(d,:phase_primal)==0
        phase=private_phase[]
        @test !isnothing(phase)
        @test 0<phase.iterations==ws.iterations==budget.iterations
        if stop_event==:perturbation
            @test JSimplex._has_active_bound_perturbations(phase.scratch.perturbations)
            @test !phase.scratch.pricing.temporary
            @test phase.scratch.pricing.last_transition==:trial_limit
        else
            @test JSimplex._original_bounds_active(phase)
            @test !JSimplex._has_active_perturbations(phase.scratch.perturbations)
            @test !phase.scratch.pricing.temporary
        end
    end
end

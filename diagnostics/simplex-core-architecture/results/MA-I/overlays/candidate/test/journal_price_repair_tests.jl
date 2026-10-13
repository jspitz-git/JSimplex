using Test, JSimplex, SparseArrays

# Exercise a real perturbation journal, then a freshly recomputed marginal
# working price. The correction must retain ownership and original-cost cleanup.
function journal_price_fixture(T;upper=false)
    p=LinearProblem(sparse(T[1 0]),zeros(T,2);row_lower=T[1],column_upper=T[Inf,1])
    policy=JSimplex.NumericalPolicy(T;adaptive_stalling=true,adaptive_dual_perturbation=true)
    diagnostics=JSimplex.SimplexDiagnostics()
    ws=JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false,algorithm=:dual);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
    ws.basis.states[2]=upper ? JSimplex.AT_UPPER : JSimplex.AT_LOWER
    journal=JSimplex.PerturbationJournal(ws)
    monitor=JSimplex.StagnationMonitor{T}(2;tolerance=policy.solve_tolerance)
    for _ in 1:4
        JSimplex.observe_progress!(monitor;objective=one(T),primal_violation=one(T),
            dual_violation=zero(T),primal_step=zero(T),dual_step=zero(T))
    end
    @assert JSimplex.perturb_dual_costs!(ws,monitor,journal,policy)>0
    ws.costs[2]=(upper ? one(T) : -one(T))*nextfloat(ws.options.dual_tolerance)
    JSimplex.recompute!(ws;refactorize=true)
    ws,journal,diagnostics
end

@testset "Marginal working-price repair composes with active cost perturbations" begin
    for T in (Float32,Float64), upper in (false,true)
        ws,journal,diagnostics=journal_price_fixture(T;upper)
        original=copy(journal.original_costs);model=copy(ws.problem.objective)
        before=copy(ws.costs);level=journal.level
        @test JSimplex.dual_infeasibility(ws)>ws.options.dual_tolerance
        @test JSimplex._dual_prices_feasible_or_refined!(ws,()->false;allow_cost_shifts=true)
        @test JSimplex.dual_infeasibility(ws)<=ws.options.dual_tolerance
        @test JSimplex.event_count(diagnostics,:correction_attempt)==0
        @test ws.costs===journal.active_costs && journal.active
        @test maximum(abs,ws.costs-before)<=4ws.options.dual_tolerance
        @test journal.level==level
        @test isequal(journal.original_costs,original)
        JSimplex.recompute!(ws;refactorize=true)
        @test JSimplex.dual_infeasibility(ws)<=ws.options.dual_tolerance
        JSimplex.restore_perturbations!(ws,journal)
        @test isequal(ws.costs,original) && isequal(ws.problem.objective,model)
        @test !journal.active && !ws.perturbed
    end
end

@testset "Journal price repair respects ownership, displacement and cancellation" begin
    for reason in (:detached,:foreign,:cap,:large,:cancel,:cleanup)
        ws,journal,_=journal_price_fixture(Float64)
        reason==:detached && (ws.costs=copy(ws.costs))
        reason==:foreign && (journal.workspace_id=zero(UInt))
        reason==:cap && (journal.original_costs[2]=-512ws.options.dual_tolerance)
        reason==:large && (ws.reduced_costs[2]=-3ws.options.dual_tolerance)
        reason==:cleanup && (ws.perturbed=false)
        before=deepcopy((ws.costs,ws.reduced_costs,journal.original_costs,journal.active_costs))
        accepted=reason==:cleanup ? JSimplex._dual_prices_feasible_or_refined!(ws,()->false;allow_cost_shifts=false) :
            JSimplex._shift_marginal_dual_prices!(ws,()->reason==:cancel)
        @test !accepted
        @test isequal(before,(ws.costs,ws.reduced_costs,journal.original_costs,journal.active_costs))
    end
end

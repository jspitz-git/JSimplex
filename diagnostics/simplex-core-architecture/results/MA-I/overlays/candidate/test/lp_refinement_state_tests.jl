using Test,JSimplex,SparseArrays,LinearAlgebra

@testset "LP recovery retains shared work, deadlines, and callback provenance" begin
    ws,policy=lp_recovery_fixture()
    budget=JSimplex.SimplexRunBudget(ws)
    budget.time_limit_seconds=0
    before=budget.refactorizations
    run=JSimplex.refine_lp!(ws,budget,policy,()->false)
    @test run.status==TIME_LIMIT && budget.refactorizations==before
    for failure in (ErrorException("LP callback"),SingularException(7),ArgumentError("LP callback"))
        ws,policy=lp_recovery_fixture()
        budget=JSimplex.SimplexRunBudget(ws)
        caught=try
            JSimplex.refine_lp!(ws,budget,policy,()->budget.refactorizations>1 ? throw(failure) : false)
        catch exception
            exception
        end
        @test caught===failure
        @test budget.refactorizations==2
    end
    failure=SingularException(9)
    diagnostics=JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin
        reason==:lp_correction_certification && throw(failure)
    end)
    ws,policy=lp_recovery_fixture(;diagnostics)
    caught=try
        JSimplex.refine_lp!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    catch exception
        exception
    end
    @test caught isa JSimplex.DiagnosticObserverFailure
    @test caught.cause===failure

    ws,policy=lp_recovery_fixture()
    p=ws.progress
    ws.progress=typeof(p)(p.start_ns,p.objective,p.objective_constant,p.scaling,7,11,p.diagnostics,p.numerical_policy)
    ws.iterations=2;ws.refactorizations=3
    budget=JSimplex.SimplexRunBudget(ws)
    budget.iteration_limit=9
    run=JSimplex.refine_lp!(ws,budget,policy,()->false)
    @test run.status==OPTIMAL
    @test run.iterations==ws.iterations==2 && budget.iterations==9
    @test run.refactorizations==ws.refactorizations==5 && budget.refactorizations==16
end

@testset "A rejected correction falls back with the remaining budget" begin
    diagnostics=JSimplex.SimplexDiagnostics()
    ws,policy=lp_recovery_fixture(;diagnostics,boost=true)
    # Already exact: the correction cannot reduce any error, so the LP driver
    # must stop and escalate once rather than repeat its full round allowance.
    ws.factorization=JSimplex._basis_factorization(sparse([1.0;;]),ws.options)
    budget=JSimplex.SimplexRunBudget(ws)
    budget.iterations=budget.iteration_limit=9
    budget.refactorizations=12
    run=JSimplex.refine_lp!(ws,budget,policy,()->false)
    @test run.status==OPTIMAL && run.primal==[1.0]
    @test diagnostics.counts[:lp_refinement]==1
    @test diagnostics.counts[:precision_boost]==1
    @test run.iterations==budget.iterations==9
    @test run.refactorizations==budget.refactorizations==14
end

@testset "LP recovery restores owned working perturbations" begin
    ws,policy=lp_recovery_fixture()
    journal=JSimplex.PerturbationJournal(ws)
    journal.bounds=JSimplex.BoundPerturbationState(ws)
    journal.active_costs[1]=1.25;journal.active=true
    journal.bounds.active_lower[2]=Bound(0.75);journal.bounds.active=true
    ws.costs=journal.active_costs;ws.lower=journal.bounds.active_lower;ws.upper=journal.bounds.active_upper
    ws.scratch.perturbations=journal;ws.perturbed=true
    run=JSimplex.refine_lp!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    @test run.status==OPTIMAL && run.primal==[1.0]
    @test ws.costs==[1.0,0.0] && !ws.perturbed
    @test !journal.active && !journal.bounds.active
    @test ws.lower==vcat(ws.problem.column_lower,ws.problem.row_lower)
end

@testset "Enabling LP recovery leaves rational arithmetic exact" begin
    for T in (Rational{Int64},Rational{BigInt}),algorithm in (:primal,:dual)
        p=LinearProblem(sparse(T[1;;]),T[1];row_lower=T[1])
        diagnostics=JSimplex.SimplexDiagnostics()
        policy=JSimplex.NumericalPolicy(T;lp_refinement=true,precision_boosting=true)
        options=SolverOptions(T;algorithm,verbose=false,presolve=false,scaling=:off)
        solution=JSimplex._solve_diagnosed(p,diagnostics;options,numerical_policy=policy)
        @test solution isa Solution{T}
        @test solution.status==OPTIMAL && solution.primal==T[1]
        @test diagnostics.counts[:lp_refinement]==diagnostics.counts[:precision_boost]==0
    end
end

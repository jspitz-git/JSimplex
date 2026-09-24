using Test, JSimplex, LinearAlgebra, SparseArrays
isdefined(@__MODULE__, :precision_recovery_fixture) || include("simplex_precision_recovery_helpers.jl")

@testset "Cancellation after the final original-type certificate" begin
    certificates, stopped = Ref(0), Ref(false)
    diagnostics = JSimplex.SimplexDiagnostics(; observer=(reason, ws)->begin
        if reason == :certification
            certificates[] += 1
            certificates[] == 3 && (stopped[] = true)
        end
    end)
    ws = precision_recovery_fixture(; diagnostics)
    budget = JSimplex.SimplexRunBudget(ws)
    run = JSimplex.solve_with_precision_recovery(ws, budget, ws.progress.numerical_policy, ()->stopped[])
    @test certificates[] == 3 && stopped[]
    @test run.status == JSimplex.TIME_LIMIT
    @test isnothing(run.primal) && isnothing(run.objective_value)
    @test budget.refactorizations == 3
end

@testset "Numerical callback and observer exceptions retain their provenance" begin
    ws = precision_recovery_fixture()
    budget = JSimplex.SimplexRunBudget(ws)
    failure = SingularException(7)
    caught = try
        JSimplex.solve_with_precision_recovery(ws, budget, ws.progress.numerical_policy,
            ()->budget.refactorizations > 1 ? throw(failure) : false)
    catch exception
        exception
    end
    @test caught === failure
    @test budget.refactorizations == 2
    diagnostics = JSimplex.SimplexDiagnostics(; observer=(reason, ws)->begin
        reason == :precision_boost && throw(failure)
    end)
    ws = precision_recovery_fixture(; diagnostics)
    budget = JSimplex.SimplexRunBudget(ws)
    caught = try
        JSimplex.solve_with_precision_recovery(ws, budget, ws.progress.numerical_policy, ()->false)
    catch exception
        exception
    end
    @test caught isa JSimplex.DiagnosticObserverFailure
    @test caught.cause === failure
    @test budget.refactorizations == 2
end

@testset "Precision recovery restores owned working perturbations" begin
    ws = precision_recovery_fixture()
    original_lower = copy(ws.lower)
    journal = JSimplex.PerturbationJournal(ws)
    journal.bounds = JSimplex.BoundPerturbationState(ws)
    journal.active_costs[1] = 1.0
    journal.active = true
    journal.bounds.active_lower[3] = Bound(5e15)
    journal.bounds.active = true
    ws.costs, ws.lower, ws.upper = journal.active_costs, journal.bounds.active_lower, journal.bounds.active_upper
    ws.scratch.perturbations = journal
    ws.perturbed = true
    run = JSimplex.solve_with_precision_recovery(ws, JSimplex.SimplexRunBudget(ws),
        ws.progress.numerical_policy, ()->false)
    @test run.status == JSimplex.OPTIMAL
    @test run.primal == [0.5, 1.0]
    @test all(iszero, ws.costs) && !ws.perturbed
    @test ws.lower == original_lower
    @test ws.problem.objective == [0.0, 0.0]
    @test bound_value(ws.problem.row_lower[1]) == 5e15+1
end

@testset "Enabling precision recovery never converts rational arithmetic" begin
    for T in (Rational{Int64}, Rational{BigInt}), algorithm in (:primal, :dual)
        p = LinearProblem(sparse(T[1;;]), T[1]; row_lower=T[1])
        policy = JSimplex.NumericalPolicy(T; precision_boosting=true)
        diagnostics = JSimplex.SimplexDiagnostics()
        options = SolverOptions(T; algorithm, verbose=false, presolve=false, scaling=:off)
        solution = JSimplex._solve_diagnosed(p, diagnostics; options, numerical_policy=policy)
        @test solution isa Solution{T}
        @test solution.status == JSimplex.OPTIMAL && solution.primal == T[1]
        @test JSimplex.event_count(diagnostics, :precision_boost) == 0
    end
end

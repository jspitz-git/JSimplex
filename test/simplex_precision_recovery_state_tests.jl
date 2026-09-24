using Test, JSimplex, SparseArrays, LinearAlgebra

include("simplex_precision_recovery_helpers.jl")

@testset "Precision recovery certifies the rounded original-type point" begin
    levels = Int[]
    diagnostics = JSimplex.SimplexDiagnostics(; observer=(reason, ws)->begin
        reason == :precision_boost && push!(levels, precision(first(ws.primal)))
    end)
    ws = precision_recovery_fixture(; diagnostics)
    saved_A, saved_costs = copy(ws.problem.A), copy(ws.problem.objective)
    exact_A = Matrix(Rational{BigInt}.(ws.problem.A))
    exact_rhs = Rational{BigInt}.(bound_value.(ws.problem.row_lower))
    @test exact_A \ exact_rhs == Rational{BigInt}[1//2, 1]
    @test JSimplex._internal_solution(ws, JSimplex.OPTIMAL, "initial replay").status == JSimplex.NUMERICAL_ERROR
    budget = JSimplex.SimplexRunBudget(ws)
    # An exhausted step budget still permits zero-step factorization/certification.
    budget.iterations = budget.iteration_limit = 9
    budget.refactorizations = 12
    run = JSimplex.run_from_basis!(ws, budget, ws.progress.numerical_policy, ()->false)
    @test run isa JSimplex.DualRunResult{Float64}
    @test run.status == JSimplex.OPTIMAL
    @test run.primal == [0.5, 1.0]
    @test run.objective_value === 0.0
    @test levels == [128, 256]
    @test run.iterations == budget.iterations == 9
    @test run.refactorizations == budget.refactorizations == 14
    @test ws.problem.A == saved_A && ws.problem.objective == saved_costs
end

@testset "Precision ceiling and memory rejection preserve consumed work" begin
    for ceiling in (53, 128)
        policy = JSimplex.NumericalPolicy(Float64; simplex_strategy=:adaptive,
            precision_boosting=true, max_precision_bits=ceiling, refactor_timing=false)
        diagnostics = JSimplex.SimplexDiagnostics()
        ws = precision_recovery_fixture(; policy, diagnostics)
        budget = JSimplex.SimplexRunBudget(ws)
        before = budget.refactorizations
        run = JSimplex.solve_with_precision_recovery(ws, budget, policy, ()->false)
        @test run.status == JSimplex.NUMERICAL_ERROR
        @test isnothing(run.primal) && isnothing(run.objective_value)
        @test JSimplex.event_count(diagnostics, :precision_boost) == (ceiling == 128 ? 1 : 0)
        @test budget.refactorizations == before + (ceiling == 128 ? 1 : 0)
    end
    for allowance in (0, 1024)
        policy = JSimplex.NumericalPolicy(Float64; precision_boosting=true,
            max_precision_memory_bytes=allowance)
        ws = precision_recovery_fixture(; policy)
        budget = JSimplex.SimplexRunBudget(ws)
        before = budget.refactorizations
        run = JSimplex.solve_with_precision_recovery(ws, budget, policy, ()->false)
        @test run.status == JSimplex.NUMERICAL_ERROR
        @test occursin("memory", lowercase(run.message))
        @test budget.refactorizations == before
    end
end

@testset "Precision recovery shares deadlines and preserves callback errors" begin
    ws = precision_recovery_fixture()
    budget = JSimplex.SimplexRunBudget(ws)
    budget.time_limit_seconds = 0.0
    before = budget.refactorizations
    run = JSimplex.solve_with_precision_recovery(ws, budget, ws.progress.numerical_policy, ()->false)
    @test run.status == JSimplex.TIME_LIMIT
    @test budget.refactorizations == before
    budget.time_limit_seconds = Inf
    failure = ErrorException("precision recovery callback")
    caught = try
        JSimplex.solve_with_precision_recovery(ws, budget, ws.progress.numerical_policy,
            ()->throw(failure))
    catch exception
        exception
    end
    @test caught === failure
    stopped = Ref(false)
    diagnostics = JSimplex.SimplexDiagnostics(; observer=(reason, trial)->begin
        reason == :precision_boost && (stopped[] = true)
    end)
    ws = precision_recovery_fixture(; diagnostics)
    budget = JSimplex.SimplexRunBudget(ws)
    before = budget.refactorizations
    run = JSimplex.solve_with_precision_recovery(ws, budget, ws.progress.numerical_policy,
        ()->stopped[])
    @test run.status == JSimplex.TIME_LIMIT
    @test budget.refactorizations == before + 1
    @test JSimplex.event_count(diagnostics, :precision_boost) == 1
end

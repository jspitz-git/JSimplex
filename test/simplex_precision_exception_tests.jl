using Test, JSimplex, LinearAlgebra
isdefined(@__MODULE__, :precision_recovery_fixture) || include("simplex_precision_recovery_helpers.jl")

@testset "A numerical certificate exception advances to the next precision" begin
    injected = Ref(false)
    levels = Int[]
    diagnostics = JSimplex.SimplexDiagnostics(; observer=(reason, ws)->begin
        if reason == :precision_boost
            push!(levels, precision(first(ws.primal)))
        elseif reason == :certification && eltype(ws.primal) === BigFloat && !injected[]
            # Corrupt only the candidate factor, after its primal has been
            # recomputed. A fresh higher-precision factor can recover the basis.
            injected[] = true
            fill!(ws.factorization.base.factorization.factors, zero(BigFloat))
        end
    end)
    ws = precision_recovery_fixture(; diagnostics)
    budget = JSimplex.SimplexRunBudget(ws)
    run = JSimplex.solve_with_precision_recovery(ws, budget, ws.progress.numerical_policy, ()->false)
    @test injected[]
    @test run.status == JSimplex.OPTIMAL
    @test run.primal == [0.5, 1.0]
    @test levels == [128, 256]
    @test run.refactorizations == budget.refactorizations == 3
end

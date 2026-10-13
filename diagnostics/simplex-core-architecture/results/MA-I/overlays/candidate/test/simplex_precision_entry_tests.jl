using Test, JSimplex, SparseArrays
isdefined(@__MODULE__, :precision_recovery_fixture) || include("simplex_precision_recovery_helpers.jl")

@testset "Legacy dual final certification can request precision recovery" begin
    policy = JSimplex.NumericalPolicy(Float64; precision_boosting=true)
    diagnostics = JSimplex.SimplexDiagnostics()
    ws = precision_recovery_fixture(; policy, diagnostics)
    run = JSimplex._solve_continuous_dual!(ws, ()->false)
    @test run.status == JSimplex.OPTIMAL
    @test run.primal == [0.5, 1.0]
    @test JSimplex.event_count(diagnostics, :precision_boost) == 2
end

@testset "Precision recovery covers initialization overflow without a false certificate" begin
    p = LinearProblem(sparse([1e308 -1e308]), [1.0, 0.0];
        column_lower=[2.0, 2.0], column_upper=[2.0, 2.0],
        row_lower=[0.0], row_upper=[0.0])
    @test Matrix(Rational{BigInt}.(p.A)) * Rational{BigInt}[2, 2] == [0//big(1)]
    @test JSimplex._original_primal_feasible(p, [2.0, 2.0], 1e-10)
    for algorithm in (:dual, :primal)
        options = SolverOptions(; algorithm, verbose=false, presolve=false, scaling=:off,
            primal_tolerance=1e-10, dual_tolerance=1e-10)
        policy = JSimplex.NumericalPolicy(Float64; simplex_strategy=:adaptive,
            precision_boosting=true, refactor_timing=false)
        diagnostics = JSimplex.SimplexDiagnostics()
        solution = JSimplex._solve_diagnosed(p, diagnostics; options, numerical_policy=policy)
        @test solution isa Solution{Float64}
        @test solution.status == JSimplex.OPTIMAL
        @test solution.primal == [2.0, 2.0]
        @test solution.objective_value === 2.0
        @test JSimplex.event_count(diagnostics, :precision_boost) >= 1
    end
end

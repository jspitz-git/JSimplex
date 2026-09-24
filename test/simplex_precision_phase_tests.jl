using Test, JSimplex, SparseArrays

@testset "Primal precision recovery leaves auxiliary columns behind" begin
    for modern_phase in (false, true)
        p = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
        injected = Ref(false)
        diagnostics = JSimplex.SimplexDiagnostics(; observer=(reason, ws)->begin
            if reason == :phase_one && eltype(ws.primal) === Float64 && !injected[]
                injected[] = true
                ws.primal[first(ws.basis.basic_indices)] = NaN
            end
        end)
        policy = JSimplex.NumericalPolicy(Float64; precision_boosting=true, phase_one=modern_phase)
        options = SolverOptions(; algorithm=:primal, verbose=false, presolve=false, scaling=:off,
            iteration_limit=10)
        progress = JSimplex.SimplexProgressContext(p; diagnostics, numerical_policy=policy,
            iteration_offset=7, refactorization_offset=11)
        run = JSimplex._solve_continuous_primal(p, options; progress)
        @test injected[]
        @test run isa JSimplex.DualRunResult{Float64}
        @test run.status == JSimplex.OPTIMAL && run.primal == [1.0]
        @test run.iterations == 1
        @test !isnothing(run.basis) && length(run.basis.states) == 2
        @test JSimplex.event_count(diagnostics, :precision_boost) == 1
        @test size(p.A) == (1, 1) && p.objective == [1.0]
    end
end

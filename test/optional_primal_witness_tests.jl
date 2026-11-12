using JSimplex, SparseArrays, Test

@testset "Legacy artificial phase II captures only requested original witnesses" begin
    JS = JSimplex
    for T in (Float32, Float64, BigFloat)
        # The initial x=0 violates the row lower bound, so legacy primal must
        # introduce an artificial. Phase I prices x at zero; phase II prices
        # it at one, making a reused phase-I dual fail the original witness.
        p = LinearProblem(sparse(reshape(T[1], 1, 1)), T[1];
            row_lower=T[1], column_lower=T[0], column_upper=T[2])
        o = SolverOptions(T; algorithm=:primal, presolve=true,
            presolve_row_sparsification=true, scaling=:off, verbose=false)
        policy = JS.NumericalPolicy(T, o)
        @test !policy.phase_one
        function run(witness_problem; options=o)
            artificial_count = Ref(0)
            original_progress = Ref(true)
            diagnostics = JS.SimplexDiagnostics(; observer=(reason, ws) -> begin
                if reason == :phase_one
                    artificial_count[] = size(ws.problem.A, 2) - size(p.A, 2)
                end
                original_progress[] &= ws.progress.witness_problem === witness_problem
                nothing
            end)
            progress = JS.SimplexProgressContext(p; numerical_policy=policy,
                diagnostics, witness_problem)
            result = JS._solve_continuous_primal(p, options; progress)
            @test artificial_count[] == 1
            @test original_progress[]
            @test result.status == JS.OPTIMAL
            @test result.primal == T[1]
            @test JS._original_primal_feasible(p, result.primal, o.primal_tolerance)
            result
        end
        captured = run(p)
        @test !isnothing(captured.dual)
        if !isnothing(captured.dual)
            @test captured.dual == T[1]
            @test JS._original_witness_certified(p, o, captured.basis,
                captured.primal, captured.dual)
        end
        plain = run(nothing)
        @test isnothing(plain.dual)
        @test plain.primal == captured.primal
        @test plain.iterations == captured.iterations
        @test plain.refactorizations == captured.refactorizations
        other = deepcopy(p)
        mismatch = run(other)
        @test isnothing(mismatch.dual)
        @test mismatch.primal == captured.primal
        disabled = SolverOptions(T; algorithm=:primal, scaling=:off, verbose=false)
        legacy = run(p; options=disabled)
        @test isnothing(legacy.dual)
        @test legacy.primal == captured.primal
        @test legacy.iterations == captured.iterations
        @test legacy.refactorizations == captured.refactorizations
        bypass = SolverOptions(T; algorithm=:primal, presolve=false,
            presolve_row_sparsification=true, scaling=:off, verbose=false)
        @test isnothing(run(p; options=bypass).dual)
        for flag in (:presolve_column_merging, :presolve_column_dominance)
            enabled = SolverOptions(T; algorithm=:primal, scaling=:off,
                verbose=false, NamedTuple{(flag,)}((true,))...)
            result = run(p; options=enabled)
            @test !isnothing(result.dual)
            if !isnothing(result.dual)
                @test JS._original_witness_certified(p, enabled, result.basis,
                    result.primal, result.dual)
            end
        end
    end
end

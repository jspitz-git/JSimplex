using JSimplex, Test, SparseArrays

@testset "Strategy selection preserves the numerical kernel" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        legacy = JSimplex.NumericalPolicy(T; simplex_strategy=:legacy)
        adaptive = JSimplex.NumericalPolicy(T; simplex_strategy=:adaptive)
        checked = JSimplex.NumericalPolicy(T; numerical_profile=:checked)
        for key in (:stable_ratio, :pivot_validation, :solve_refinement, :recovery,
                    :feasibility_recovery, :incremental_primal, :incremental_primal_pivots)
            @test getfield(checked, key)
            @test !getfield(legacy, key)
            @test getfield(adaptive, key) == getfield(legacy, key)
        end
    end
end

@testset "Only the strategy defers a numerically valid weak pivot" begin
    for T in (Float32, Float64), strategy in (:legacy, :adaptive),
        update in (:pfi, :bartels_golub, :forrest_tomlin, :suhl_suhl)
        small = sqrt(eps(T)) / T(100)
        problem = LinearProblem(sparse(T[small -1; 1 0]), T[-2, -1];
            row_upper=T[0, Inf], column_upper=T[1, 1])
        options = SolverOptions(T; algorithm=:primal, simplex_strategy=strategy,
            basis_update=update, pricing=:dantzig, verbose=false)
        ws = JSimplex.initialize_workspace(problem, options)
        @test JSimplex._legacy_primal_row_validation_enabled(ws)
        @test isnothing(JSimplex._primal_iteration!(ws, ()->false, options.dual_tolerance))
        if strategy == :legacy
            @test ws.basis.basic_indices == [1, 4]
            @test ws.primal[1:2] == T[0, 0]
        else
            @test ws.basis.basic_indices == [3, 4]
            @test ws.primal[1:2] == T[0, 1]
        end
        @test JSimplex._legacy_primal_point_certified(ws)
        @test ws.refactorizations == 0
        @test isempty(ws.scratch.rejected_entering)
    end
end

@test_throws ArgumentError JSimplex.NumericalPolicy(Float64; numerical_profile=:unknown)

@testset "Weak-pivot preference follows its policy override" begin
    for strategy in (:legacy, :adaptive), prefer in (false, true)
        p = LinearProblem(sparse([1e-10 -1.0; 1.0 0.0]), [-2.0,-1.0];
            row_upper=[0.0,Inf], column_upper=[1.0,1.0])
        policy = JSimplex.NumericalPolicy(Float64; simplex_strategy=strategy,
            adaptive_pricing=prefer, partial_pricing=false, adaptive_refactor=false)
        ws = JSimplex.initialize_workspace(p, SolverOptions(algorithm=:primal,
            simplex_strategy=strategy, pricing=:dantzig, verbose=false);
            progress=JSimplex.SimplexProgressContext(p; numerical_policy=policy))
        @test isnothing(JSimplex._primal_iteration!(ws, ()->false, ws.options.dual_tolerance))
        @test ws.basis.basic_indices == (prefer ? [3,4] : [1,4])
    end
end

@testset "Native primal cleanup uses primal safeguards under dual options" begin
    p = LinearProblem(sparse([-7e-8 -0.01]), [0.0,-1.0]; row_lower=[0.0],
        column_lower=[1.0,0.0], column_upper=[1.0,Inf])
    for strategy in (:legacy, :adaptive)
        options = SolverOptions(algorithm=:dual, simplex_strategy=strategy,
            verbose=false, iteration_limit=20)
        ws = JSimplex.initialize_workspace(p, options)
        ws.costs[2] = 0.0
        ws.perturbed = true
        JSimplex.recompute!(ws)
        original_row = ws.primal[3]
        result = JSimplex.run_from_basis!(ws, JSimplex.SimplexRunBudget(ws),
            ws.progress.numerical_policy, ()->false)
        @test result.status == OPTIMAL
        @test abs(result.primal[2]) <= eps(Float64)
        @test ws.primal[3] == original_row
        @test JSimplex._original_primal_feasible(ws, result.primal)
        @test ws.options === options
    end
end

@testset "Native zero-row resumption cannot certify a working-cost ray" begin
    p = LinearProblem(spzeros(0,1), [1.0])
    ws = JSimplex.initialize_workspace(p, SolverOptions(verbose=false))
    journal = JSimplex.PerturbationJournal(ws)
    journal.active = true
    journal.active_costs[1] = -1.0
    ws.scratch.perturbations = journal
    ws.costs = journal.active_costs
    ws.perturbed = true
    JSimplex.recompute!(ws)
    @test !ws.progress.numerical_policy.adaptive_stalling
    result = JSimplex._solve_continuous_dual!(ws, ()->false)
    @test result.status == OPTIMAL && result.objective_value == 0.0
    @test result.primal == [0.0]
    @test isnothing(ws.scratch.perturbations)
    @test JSimplex._original_costs_active(ws)
end

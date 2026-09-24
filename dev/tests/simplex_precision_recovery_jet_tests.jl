using Test, JSimplex, JET
include("precision_inference_helpers.jl")

@testset "JET precision recovery orchestration" begin
    for T in (Float32, Float64, BigFloat)
        p = LinearProblem(JSimplex.sparse(T[2 1; 1 3]), T[1, 2]; row_lower=T[1, 2])
        options = SolverOptions(T; verbose=false, pricing=:devex)
        policy = JSimplex.NumericalPolicy(T; simplex_strategy=:adaptive, precision_boosting=true)
        progress = JSimplex.SimplexProgressContext(p; numerical_policy=policy)
        ws = JSimplex.initialize_workspace(p, options; progress)
        budget = JSimplex.SimplexRunBudget(ws)
        stop = ()->false
        JET.@test_opt target_modules=(JSimplex,) JSimplex.next_working_precision(T, precision(T), policy)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._precision_memory_estimate(ws, BigFloat, 128)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._original_witness_certified(
            p, options, ws.basis, zeros(T, 2), zeros(T, 2))
        JET.@test_opt target_modules=(JSimplex,) JSimplex.solve_with_precision_recovery(ws, budget, policy, stop)
        signature = Tuple{typeof(ws), typeof(budget), typeof(policy), typeof(stop)}
        report = JET.report_opt(JSimplex.run_from_basis!, signature; target_modules=(JSimplex,))
        @test isempty(unexpected_precision_reports(report))
        @test count(is_precision_entry_dispatch, JET.get_reports(report)) == 1
        @test Base.infer_return_type(JSimplex.run_from_basis!, signature) === JSimplex.DualRunResult{T}
    end
end

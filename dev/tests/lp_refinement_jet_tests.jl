using Test,JSimplex,JET
isdefined(@__MODULE__,:unexpected_precision_reports) || include("precision_inference_helpers.jl")

@testset "JET correction formulation and typed recovery orchestration" begin
    for T in (Float32,Float64,BigFloat)
        p=LinearProblem(JSimplex.sparse(T[2 1;1 3]),T[1,2];row_lower=T[1,2])
        policy=JSimplex.NumericalPolicy(T;lp_refinement=true,precision_boosting=true)
        options=SolverOptions(T;verbose=false,presolve=false,scaling=:off)
        ws=JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        residuals=JSimplex._lp_residuals(ws,ws.primal,zeros(T,2))
        sp,sd=JSimplex._lp_correction_scales(ws,residuals)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._lp_residuals(ws,ws.primal,zeros(T,2))
        JET.@test_opt target_modules=(JSimplex,) JSimplex._lp_correction_scales(ws,residuals)
        JET.@test_opt target_modules=(JSimplex,) JSimplex.build_correction_problem(ws,residuals,sp,sd)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._lp_errors(ws,residuals)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._lp_auxiliary_policy(policy)
        budget=JSimplex.SimplexRunBudget(ws);stop=()->false
        signature=Tuple{typeof(ws),typeof(budget),typeof(policy),typeof(stop)}
        report=JET.report_opt(JSimplex.refine_lp!,signature;target_modules=(JSimplex,))
        @test isempty(unexpected_precision_reports(report))
        @test count(is_precision_entry_dispatch,JET.get_reports(report))==2
        @test Base.infer_return_type(JSimplex.refine_lp!,signature)===JSimplex.DualRunResult{T}
    end
end

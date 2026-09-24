using Test,JSimplex,JET

@testset "JET typed working precision transfer" begin
    for (T,S,bits) in ((Float32,Float64,53),(Float64,BigFloat,128))
        p=LinearProblem(JSimplex.sparse(T[2 1;1 3]),T[1,2];row_lower=T[1,2])
        options=SolverOptions(T;verbose=false,pricing=:devex)
        policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive)
        ws=JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        JET.@test_opt target_modules=(JSimplex,) JSimplex.copy_working_values(S,p.A;bits)
        JET.@test_opt target_modules=(JSimplex,) JSimplex.copy_working_values(S,p.row_lower;bits)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._copy_precision_policy(S,policy)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._copy_precision_options(S,options)
        JET.@test_opt target_modules=(JSimplex,) JSimplex.transfer_precision(ws,S,bits,JSimplex.SimplexRunBudget(ws),policy)
    end
end

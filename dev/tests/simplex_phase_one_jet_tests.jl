using Test,JSimplex,JET
@testset "JET phase-one mapping and removal" begin
    for T in (Float64,Rational{BigInt})
        p=LinearProblem(JSimplex.sparse(T[1 1]),T[2,1];row_lower=T[1])
        options=SolverOptions(T;algorithm=:primal,verbose=false)
        policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,phase_one=true)
        ws=JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        JET.@test_opt target_modules=(JSimplex,) JSimplex._phase_options(options,:primal)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._phase_one_workspace(ws,policy,()->false)
        JET.@test_opt target_modules=(JSimplex,) JSimplex.run_phase_one!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    end
end

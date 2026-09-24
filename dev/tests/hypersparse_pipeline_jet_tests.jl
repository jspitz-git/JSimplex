using JSimplex,Test,JET

@testset "JET hypersparse pipeline" begin
    for T in (Float32,Float64,Rational{BigInt}), method in (:pfi,:forrest_tomlin)
        p = LinearProblem(JSimplex.spdiagm(0=>ones(T,8)),zeros(T,8))
        policy = JSimplex.NumericalPolicy(T;hypersparse=true)
        ws = JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false,
            basis_update=method,basis_refactorization=:markowitz);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        rhs = JSimplex._pipeline_unit_rhs!(ws,1)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._pipeline_unit_rhs!(ws,1)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._pipeline_basis_solve!(ws.scratch.rho,ws,rhs;transposed=true)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._pipeline_price!(ws.scratch.tableau_row,ws,ws.scratch.rho)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._pipeline_weight_rhs!(ws,1,one(T))
    end
end

using Test, JSimplex, JET

@testset "JET guarded crash kernels" begin
    for T in (Float32,Float64,Rational{BigInt})
        p = LinearProblem(JSimplex.spdiagm(0=>T[2,3]),ones(T,2);row_lower=T[2,3])
        options = SolverOptions(T;verbose=false)
        policy = JSimplex.NumericalPolicy(T;crash=true)
        ws = JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        column = T[-2,0]
        rows = Int[]
        JET.@test_opt target_modules=(JSimplex,) JSimplex._start_primal_feasible(ws)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._crash_rows!(rows,ws,column,policy)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._crash_candidate_score(ws,column,1,1,T(2))
        JET.@test_opt target_modules=(JSimplex,) JSimplex._start_nonbasic_state(ws.lower[1],ws.upper[1],one(T))
        JET.@test_opt target_modules=(JSimplex,) JSimplex.crash_basis(p,options,policy,()->false)
        JET.@test_opt target_modules=(JSimplex,) JSimplex.initialize_from_basis(p,ws.basis,options;policy)
    end
end

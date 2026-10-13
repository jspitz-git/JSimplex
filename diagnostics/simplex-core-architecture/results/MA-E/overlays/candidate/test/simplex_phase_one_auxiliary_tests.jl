using Test,JSimplex,SparseArrays

@testset "Modern auxiliary dual owns its bound and cost model" begin
    for T in (Float64,Rational{BigInt})
        p=LinearProblem(sparse(T[1 1]),T[1,-2];
            column_lower=[Bound{T}(nothing),Bound(zero(T))],row_lower=T[1])
        policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,phase_one=true)
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        auxiliary=JSimplex._auxiliary_workspace(ws)
        @test auxiliary.problem !== p
        @test JSimplex._original_bounds_active(auxiliary)
        @test JSimplex._original_costs_active(auxiliary)
        saved_lower=copy(ws.lower)
        JSimplex._restore_original_costs!(auxiliary)
        @test auxiliary.lower == vcat(auxiliary.problem.column_lower,auxiliary.problem.row_lower)
        @test ws.lower == saved_lower
        @test p.row_lower == Bound.(T[1])
    end
end

@testset "Modern auxiliary dual preserves recession and feasibility proofs" begin
    for T in (Float64,Rational{BigInt}),algorithm in (:primal,:dual)
        policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,phase_one=true)
        options=SolverOptions(T;algorithm,verbose=false,presolve=false,scaling=:off)
        for (p,status) in (
            (LinearProblem(sparse(T[1 1]),T[-1,0];row_lower=T[1]),UNBOUNDED),
            (LinearProblem(sparse(T[0 1]),T[-1,0];row_lower=T[2],column_upper=[Bound{T}(nothing),Bound(one(T))]),INFEASIBLE),
            (LinearProblem(sparse(T[1 -1]),T[1,-2];row_lower=T[0],row_upper=T[0],column_upper=T[1,1]),OPTIMAL))
            result=JSimplex._solve_diagnosed(p,nothing;options,numerical_policy=policy)
            @test result.status == status
            status == OPTIMAL && @test result.objective_value ≈ -one(T)
        end
    end
end

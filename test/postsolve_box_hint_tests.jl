using Test, JSimplex, SparseArrays, LinearAlgebra

@testset "Postsolve projects an infeasible structural hint into original bounds" begin
    for T in (Float32, Float64), manager in (:pfi, :huangfu_hall, :forrest_tomlin, :suhl_suhl, :bartels_golub), side in (:lower, :upper)
        # A scaled solve can return a tolerated negative variable whose unscaled
        # value lies outside its original bound. Trying to make it basic first
        # blocks projection of the second column, which is needed for feasibility.
        upper = side == :upper ? T(1) : nothing
        p = LinearProblem(sparse(T[1 0; 0 1]), zeros(T,2);
            row_lower=T[0,1], row_upper=[upper,nothing],
            column_lower=T[0,0], column_upper=[upper,nothing])
        options = SolverOptions(T; algorithm=:primal, basis_update=manager,
            presolve=false, scaling=:off, verbose=false)
        ws = JSimplex.initialize_workspace(p,options)
        target = T[side == :lower ? -1//1000 : 1001//1000, 1]
        unchanged = copy(target)
        @test !JSimplex._original_primal_feasible(p,target,options.primal_tolerance)
        @test JSimplex.primal_infeasibility(ws) > options.primal_tolerance
        exchanges = JSimplex._project_postsolve_basis!(ws,target,()->false)
        @test !isnothing(exchanges)
        @test ws.primal[1:2] == T[side == :lower ? 0 : 1, 1]
        @test JSimplex._original_primal_feasible(p,ws.primal[1:2],options.primal_tolerance)
        @test target == unchanged
    end
end

@testset "Box hints without exchanges retain the original feasibility decision" begin
    for T in (Float32,Float64), row_lower in (T(0),T(1))
        p=LinearProblem(sparse(reshape(T[1],1,1)),T[0];row_lower=[row_lower],column_lower=T[0])
        options=SolverOptions(T;algorithm=:primal,verbose=false,presolve=false,scaling=:off)
        ws=JSimplex.initialize_workspace(p,options)
        before=deepcopy((ws.primal,ws.basis.basic_indices,ws.basis.states))
        target=T[-1//1000]
        result=JSimplex._project_postsolve_basis!(ws,target,()->false)
        @test row_lower==0 ? result==0 : isnothing(result)
        @test (ws.primal,ws.basis.basic_indices,ws.basis.states)==before
        @test target==T[-1//1000]
        @test JSimplex._original_primal_feasible(p,ws.primal[1:1],options.primal_tolerance)==(row_lower==0)
        if row_lower==0
            @test JSimplex._project_postsolve_basis!(ws,T[0],()->false)==0
            @test (ws.primal,ws.basis.basic_indices,ws.basis.states)==before
        end
        checked=JSimplex.initialize_workspace(p,options;progress=JSimplex.SimplexProgressContext(p;
            numerical_policy=JSimplex.NumericalPolicy(T;numerical_profile=:checked)))
        @test isnothing(JSimplex._project_postsolve_basis!(checked,target,()->false))
    end
end

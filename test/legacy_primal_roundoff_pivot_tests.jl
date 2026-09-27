using JSimplex,Test,SparseArrays

@testset "Refresh an unresolved pivot before updating a legacy basis" begin
    for T in (Float32,Float64),update in (:pfi,:bartels_golub,:forrest_tomlin,:suhl_suhl)
        scale=T(1e9)
        problem=LinearProblem(sparse(reshape(T[0,scale],2,1)),T[-1];
            row_upper=T[0,Inf],column_upper=T[1])
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=update,pricing=:steepest_edge,verbose=false)
        ws=JSimplex.initialize_workspace(problem,options)
        # The old history invents a pivot just above the absolute cutoff. Both
        # forward and transpose solves agree on it, and its row residual is tiny.
        drift=T(1.25)*options.zero_tolerance/scale
        ws.factorization.base=JSimplex._factorize_basis(sparse(T[-1 drift;0 -1]))
        JSimplex.replace_column!(ws.factorization,T[1,0],1)
        terminal=JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance)
        @test isnothing(terminal)
        @test ws.primal[1]≈one(T)
        @test ws.refactorizations==1
        @test ws.basis.basic_indices==[2,3]
        @test JSimplex._original_primal_feasible(problem,ws.primal[1:1],options.primal_tolerance)
        @test JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance).status==OPTIMAL
    end
end

@testset "A genuine small relative pivot remains available after fresh solves" begin
    for T in (Float32,Float64)
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=:pfi,pricing=:steepest_edge,verbose=false)
        small=T(1.25)*options.zero_tolerance
        problem=LinearProblem(sparse(reshape(T[small,1e9],2,1)),T[-1];
            row_upper=T[0,Inf],column_upper=T[1])
        ws=JSimplex.initialize_workspace(problem,options)
        JSimplex.replace_column!(ws.factorization,T[1,0],1)
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance))
        @test ws.primal[1]==zero(T)
        @test ws.basis.basic_indices==[1,3]
        @test JSimplex._original_primal_feasible(problem,ws.primal[1:1],options.primal_tolerance)
    end
end

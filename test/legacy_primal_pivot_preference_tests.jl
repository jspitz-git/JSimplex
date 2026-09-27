using JSimplex,Test,SparseArrays

@testset "Legacy primal prefers a stable alternative to a weak pivot" begin
    for T in (Float32,Float64),update in (:pfi,:bartels_golub,:forrest_tomlin,:suhl_suhl),pricing in (:dantzig,:steepest_edge)
        small=sqrt(eps(one(T)))/T(100)
        problem=LinearProblem(sparse(T[small -1;1 0]),T[-2,-1];
            row_upper=T[0,Inf],column_upper=T[1,1])
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=update,pricing,verbose=false)
        ws=JSimplex.initialize_workspace(problem,options)
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance))
        @test ws.primal[2]==one(T)
        @test ws.primal[1]==zero(T)
        @test ws.basis.basic_indices==[3,4]
        @test ws.refactorizations==0
        @test isempty(ws.scratch.rejected_entering)
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance))
        @test ws.primal[1:2]==T[1,1]
        @test JSimplex._original_primal_feasible(problem,ws.primal[1:2],options.primal_tolerance)
        terminal=JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance)
        @test !isnothing(terminal) && terminal.status==OPTIMAL
    end
end

@testset "A weak pivot remains usable when no stable alternative exists" begin
    for T in (Float32,Float64)
        small=sqrt(eps(one(T)))/T(100)
        problem=LinearProblem(sparse(reshape(T[small,1],2,1)),T[-1];
            row_upper=T[0,Inf],column_upper=T[1])
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,verbose=false)
        ws=JSimplex.initialize_workspace(problem,options)
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance))
        @test ws.basis.basic_indices==[1,3]
        @test ws.primal[1]==zero(T)
        @test ws.refactorizations==0
        @test isempty(ws.scratch.rejected_entering)
        terminal=JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance)
        @test !isnothing(terminal) && terminal.status==OPTIMAL
    end
end

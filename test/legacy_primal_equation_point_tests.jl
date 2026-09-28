using JSimplex, Test, SparseArrays

@testset "Legacy point preservation repairs equations despite feasible bounds" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        tolerance=T===Float32 ? T(1e-4) : T(1e-7)
        problem=LinearProblem(sparse(reshape(T[1],1,1)),T[0];row_lower=T[1],row_upper=T[1])
        ws=JSimplex.initialize_workspace(problem,SolverOptions(T;algorithm=:primal,
            basis_update=manager,simplex_strategy=:legacy,primal_tolerance=tolerance,verbose=false))
        ws.basis.basic_indices[1]=1
        ws.basis.states[1]=JSimplex.BASIC;ws.basis.states[2]=JSimplex.AT_LOWER
        JSimplex.recompute!(ws;refactorize=true)
        ws.primal[1]=one(T)+T(4)*tolerance
        candidate=T[1]
        @test JSimplex.primal_infeasibility(ws)<=tolerance
        @test !JSimplex._original_primal_feasible(problem,ws.primal[1:1],tolerance)
        @test JSimplex._restore_legacy_primal_point!(ws,candidate,()->false)
        @test ws.primal==T[1,1]
        @test JSimplex._legacy_primal_row_consistent(ws,tolerance)
        # Preserve a good reconstruction rather than replacing it gratuitously.
        @test !JSimplex._restore_legacy_primal_point!(ws,T[1]+T[tolerance/2],()->false)
        @test ws.primal==T[1,1]
        ws.primal[1]=one(T)+T(4)*tolerance
        before=copy(ws.primal)
        @test !JSimplex._restore_legacy_primal_point!(ws,candidate,()->true)
        @test ws.primal==before
        @test !JSimplex._restore_legacy_primal_point!(ws,T[2],()->false)
        @test ws.primal==before
    end
end

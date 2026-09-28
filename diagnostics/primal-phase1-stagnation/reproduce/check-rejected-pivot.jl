using JSimplex,Test,Serialization
length(ARGS)==1 || error("Expected: live rejected-pivot snapshot")
d=deserialize(ARGS[1])
@testset "Captured accurate runtime pivot reaches native correction" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        options=SolverOptions(algorithm=:primal,basis_update=manager,basis_refactorization=:native,
            pricing=:steepest_edge,simplex_strategy=:legacy,refactorization_interval=80,verbose=false)
        ws=JSimplex.initialize_workspace(d.problem,options)
        ws.basis=deepcopy(d.basis);ws.costs.=d.costs;ws.lower.=d.lower;ws.upper.=d.upper
        ws.primal.=d.primal;ws.reduced_costs.=d.prices
        JSimplex._validate_basis(ws)
        B=copy(JSimplex._basis_matrix!(ws));JSimplex.refactorize!(ws.factorization,B)
        column=copy(d.direction)
        @test JSimplex._legacy_primal_pivot_row_ok!(ws,d.entering,d.row,column[d.row],()->false;column)
        @test column==d.direction
        @test ws.basis.basic_indices==d.basis.basic_indices
        @test ws.primal==d.primal
        @test isempty(ws.factorization.updates)
    end
end

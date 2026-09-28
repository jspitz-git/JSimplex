using JSimplex,Test,Serialization
length(ARGS)==1 || error("Expected: captured pivot snapshot")
d=deserialize(ARGS[1])
@testset "Captured runtime false pivot is rejected by every manager" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        options=SolverOptions(algorithm=:primal,basis_update=manager,basis_refactorization=:native,
            pricing=:steepest_edge,simplex_strategy=:legacy,refactorization_interval=80,verbose=false)
        ws=JSimplex.initialize_workspace(d.problem,options)
        ws.basis=deepcopy(d.prior_basis);ws.costs.=d.costs;ws.lower.=d.lower;ws.upper.=d.upper
        ws.primal.=d.primal;ws.reduced_costs.=d.prices
        B=copy(JSimplex._basis_matrix!(ws));JSimplex.refactorize!(ws.factorization,B)
        column=copy(d.direction)
        @test !JSimplex._legacy_primal_pivot_row_ok!(ws,d.entering,d.row,column[d.row],()->false;column)
        @test column==d.direction
        @test ws.basis.basic_indices==d.prior_basis.basic_indices
        @test isempty(ws.factorization.updates)
        # The recorded point has many individually tolerated violations.
        # Harris must retain the largest safe pivot instead of their aggregate
        # rejecting it and forcing the false rounding-scale pivot above.
        step,row,state=JSimplex._primal_ratio(ws,d.entering,1.0,column)
        @test row==14325
        @test step==0.0
        @test abs(column[row])>10000.0
        @test JSimplex._primal_bound_snap_feasible(ws,d.entering,1.0,column,row)
    end
end

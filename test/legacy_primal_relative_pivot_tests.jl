using JSimplex,Test,SparseArrays

@testset "Tiny primal pivots require relative transpose agreement" begin
    for T in (Float32,Float64),update in (:pfi,:bartels_golub,:forrest_tomlin,:suhl_suhl),orientation in (-1,1)
        coefficient=T(orientation)*T(2e-12)
        problem=LinearProblem(sparse(reshape(T[coefficient,1],2,1)),T[-1];row_upper=T[0,Inf])
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=update,verbose=false)
        ws=JSimplex.initialize_workspace(problem,options)
        # The true transpose pivot is -coefficient. A quarter of its magnitude
        # is still below the old absolute agreement floor, but would amplify
        # the update error catastrophically when dividing by this tiny pivot.
        inaccurate=-coefficient*T(0.75)
        @test abs(inaccurate)>options.zero_tolerance
        @test !JSimplex._legacy_primal_pivot_row_ok!(ws,1,1,inaccurate,()->false)
        @test JSimplex._legacy_primal_pivot_row_ok!(ws,1,1,-coefficient,()->false)
        @test JSimplex._legacy_primal_pivot_row_ok!(ws,1,1,nextfloat(-coefficient),()->false)
    end
end

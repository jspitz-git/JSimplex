using SparseArrays

@testset "Dual weight update validates all state and recovery results" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        p=LinearProblem(sparse(T[1 0; -1 1]),T[1,1];row_lower=T[1,1])
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false))
        @test JSimplex.update_dual_pricing_weights!(ws,T[1,0],T[1,0,-1,0],T[1,0],1,one(T),one(T),()->false)
        @test !ws.dual_devex_fallback
        @test all(w->isfinite(w) && w>zero(T),ws.pricing_weights)
        T<:AbstractFloat || continue
        for field in (:primal,:reduced_costs,:costs),bad in (T(NaN),T(Inf),T(-Inf))
            invalid=JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false))
            getproperty(invalid,field)[end]=bad
            @test !JSimplex.update_dual_pricing_weights!(invalid,T[1,0],T[1,0,-1,0],T[1,0],1,one(T),one(T),()->false)
            @test !invalid.dual_devex_fallback
        end
    end
    p=LinearProblem(sparse(reshape([1.0,0.0],2,1)),[1.0])
    # Weight recovery does not excuse a non-finite primal iterate.
    ws=JSimplex.initialize_workspace(p,SolverOptions(verbose=false))
    ws.primal[end]=NaN
    @test !JSimplex.update_dual_pricing_weights!(ws,[1e150,0.0],[0.0,1.0,0.0],[1e10,1.0],1,1.0,1e300,()->false)
    @test ws.dual_devex_fallback
    # DSE recovery succeeds, but the current Devex update itself overflows.
    ws=JSimplex.initialize_workspace(p,SolverOptions(verbose=false))
    @test !JSimplex.update_dual_pricing_weights!(ws,[1e150,0.0],[0.0,1e200,0.0],[1e10,1.0],1,1.0,1e300,()->false)
    @test ws.dual_devex_fallback
    @test any(!isfinite,ws.pricing_weights)
end

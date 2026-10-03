using JSimplex, Test, SparseArrays
@testset "Markowitz all-scalar public solves" begin
    for mode in (:pfi, :forrest_tomlin, :bartels_golub, :suhl_suhl), T in (Float32, Float64, BigFloat, Rational{BigInt})
        p = LinearProblem(sparse(T[1 1; 1 0; 0 1]), T[-3, -2];
            objective_constant=T(1//3), row_upper=T[4, 2, 3])
        o = SolverOptions(T; basis_update=mode, basis_refactorization=:markowitz,
            refactorization_interval=1, verbose=false)
        ws = @inferred JSimplex.initialize_workspace(p, o)
        @test ws.factorization.base isa JSimplex.MarkowitzBackend
        @test all(isconcretetype, fieldtypes(typeof(ws)))
        r = solve(p; options=o)
        @test r.status == OPTIMAL
        @test r.statistics.refactorizations >= 2
        @test r.primal ≈ T[2, 2]
    end
end

using JSimplex, Serialization, Test
include("intervention.jl")
length(ARGS)==1 || error("Expected: first-loss snapshot prefix")
d=deserialize(ARGS[1]*".failed.bin");t=deserialize(ARGS[1]*".transition.bin")
@testset "Captured bound-feasible runtime point restores certified equations" begin
    ws=JSimplex.initialize_workspace(d.problem,d.options)
    ws.basis=deepcopy(d.basis);ws.factorization=d.factorization;ws.iterations=d.iteration
    ws.lower.=d.lower;ws.upper.=d.upper;ws.costs.=d.costs;ws.primal.=d.primal
    candidate=[r==t.row ? t.primal[t.entering]+t.step : t.primal[i]-t.step*t.direction[r] for (r,i) in enumerate(d.basis.basic_indices)]
    @test t.iteration==d.iteration && t.basis.basic_indices==d.basis.basic_indices
    @test JSimplex.primal_infeasibility(ws)<=ws.options.primal_tolerance
    @test !point_certified(ws,point_certificate(ws))
    @test JSimplex._restore_legacy_primal_point!(ws,candidate,()->false)
    @test point_certified(ws,point_certificate(ws))
    @test ws.primal[ws.basis.basic_indices]==candidate
    @test ws.basis.basic_indices==d.basis.basic_indices
    @test ws.iterations==d.iteration
end

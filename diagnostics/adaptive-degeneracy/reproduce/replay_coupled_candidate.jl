# Apply the complete coupled-point candidate patch before this one-pivot replay.
using JSimplex, Serialization, LinearAlgebra, Test, SHA
BLAS.set_num_threads(1)
include(joinpath(@__DIR__,"pricing_isolation.jl"))
isolate_pricing_trials!()
ws = deserialize(ARGS[1]*"-before.bin")
ws.scratch.perturbations.workspace_id = objectid(ws)
terminal = JSimplex._primal_iteration!(ws,()->false,zero(Float64))
failed = deserialize(ARGS[1]*".bin")
@testset "Captured pivot admits a jointly certified point" begin
    @test isnothing(terminal)
    @test ws.iterations == failed.iterations == 8464
    @test ws.basis.basic_indices == failed.basis.basic_indices
    @test ws.basis.states == failed.basis.states
    nonbasic = findall(!=(JSimplex.BASIC),ws.basis.states)
    @test isequal(ws.primal[nonbasic],failed.primal[nonbasic])
    @test JSimplex._legacy_primal_point_certified(ws)
    @test ws.scratch.row_solution == ws.primal[ws.basis.basic_indices]
end

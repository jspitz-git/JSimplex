using JSimplex,Test,LinearAlgebra,SparseArrays
const J=JSimplex
@assert realpath(pathof(J))=="/home/jspitz/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
const W=normpath(joinpath(@__DIR__,"..","..",".."))
include(joinpath(W,"experimental/dual_engine/ExperimentalDualEngine.jl"))
const E=ExperimentalDualEngine
include(joinpath(W,"experimental/dual_engine/test/fixtures.jl"))
@testset "Task1 source mask ownership regression" begin
    ws,clock=fixture()
    fill!(ws.scratch.basic_mask,true)
    before=copy(ws.scratch.basic_mask)
    e=E.import_phase(ws,clock,E.EnginePolicy(ws))
    @test ws.scratch.basic_mask==before
end

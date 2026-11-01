using JSimplex,Test,LinearAlgebra,SparseArrays
const J=JSimplex
@assert realpath(pathof(J))=="/home/jspitz/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
include(joinpath(@__DIR__,"..","ExperimentalDualEngine.jl"));const E=ExperimentalDualEngine
include("proposal_fixtures.jl")
@testset "Task3 completed proposal cannot revive after invalidation" begin
    e=proposal_case(reshape([1.],1,1),[1.],[1.]).e
    @test E.propose_step!(e).reason==E.Ready
    E.reject_leaving!(e,1)
    @test E.validate_proposal!(e).reason==E.InvalidState
    @test E.plan_writes!(e).reason==E.InvalidState
    e=proposal_case(reshape([1.],1,1),[1.],[1.]).e
    @test E.propose_step!(e).reason==E.Ready
    @test E.basis_solve!(e,:bfrt,ones(1)).reason==E.Ready
    @test E.validate_proposal!(e).reason==E.InvalidState
    @test E.plan_writes!(e).reason==E.InvalidState
end

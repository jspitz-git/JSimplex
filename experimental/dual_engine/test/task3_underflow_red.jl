using JSimplex,Test,LinearAlgebra,SparseArrays
const J=JSimplex
@assert realpath(pathof(J))=="/home/jspitz/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
include(joinpath(@__DIR__,"..","ExperimentalDualEngine.jl"));const E=ExperimentalDualEngine
include("proposal_fixtures.jl")
@testset "Task3 nonzero raw flip product cannot silently disappear" begin
    B=reshape([2.0^-1000],1,1);C=reshape([-2.0^-500,-2.0^-1000],1,2)
    e=general_proposal_case(B,C,[0.,0.,1.],[-2.0^-1000];upper=[2.0^-575,Inf]).e
    @test_throws ArgumentError E._column_rhs!(e,2,2.0^-575)
end

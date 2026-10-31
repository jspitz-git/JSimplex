using JSimplex,Test,LinearAlgebra,SparseArrays
const J=JSimplex
@assert realpath(pathof(J))=="/home/jspitz/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
include(joinpath(@__DIR__,"..","ExperimentalDualEngine.jl"))
const E=ExperimentalDualEngine
if ARGS==["red"]
    @testset "Task3 missing proposal interfaces" begin
        for name in (:choose_leaving,:propose_step!,:validate_proposal!,:plan_writes!)
            @test isdefined(E,name)
        end
    end
else
    @assert ARGS==["green"]
    include("fixtures.jl");include("state_tests.jl");include("invariant_tests.jl")
    include("kernel_fixtures.jl");include("kernel_tests.jl")
    include("proposal_fixtures.jl");include("ratio_tests.jl");include("proposal_tests.jl")
    println("DUAL_ENGINE_TASK3_COMPLETED")
end

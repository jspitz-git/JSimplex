using JSimplex,Test,LinearAlgebra,SparseArrays
const J=JSimplex
@assert realpath(pathof(J))=="/home/jspitz/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
include(joinpath(@__DIR__,"..","ExperimentalDualEngine.jl"));const E=ExperimentalDualEngine
if ARGS==["red"]
    @testset "Task4 missing publication and recovery interfaces" begin
        for name in (:commit_step!,:restore_journal!,:recover!,:run_phase!,:RecoveryStage,:PhaseResult)
            @test isdefined(E,name)
        end
    end
else
    @assert ARGS==["green"]
    include("fixtures.jl");include("state_tests.jl");include("invariant_tests.jl")
    include("kernel_fixtures.jl");include("kernel_tests.jl")
    include("proposal_fixtures.jl");include("ratio_tests.jl");include("proposal_tests.jl")
    include("commit_fixtures.jl");include("commit_tests.jl");include("recovery_tests.jl")
    println("DUAL_ENGINE_TASK4_COMPLETED")
end

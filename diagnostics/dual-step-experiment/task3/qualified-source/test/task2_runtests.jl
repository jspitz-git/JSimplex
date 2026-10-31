using JSimplex,Test,LinearAlgebra,SparseArrays
const J=JSimplex
@assert realpath(pathof(J))=="/home/jspitz/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
include(joinpath(@__DIR__,"..","ExperimentalDualEngine.jl"))
const E=ExperimentalDualEngine
if ARGS==["red"]
    @testset "Task2 missing kernel interfaces" begin
        for name in (:StepOutcome,:basis_solve!,:capture_output!,:price_row!,:check_row!,:check_direction!)
            @test isdefined(E,name)
        end
    end
else
    @assert ARGS==["green"]
    # Reuse ordinary Task1 unit tests, never its frozen runner/guard scripts.
    include("fixtures.jl");include("state_tests.jl");include("invariant_tests.jl")
    include("kernel_fixtures.jl");include("kernel_tests.jl")
    println("DUAL_ENGINE_TASK2_COMPLETED")
end

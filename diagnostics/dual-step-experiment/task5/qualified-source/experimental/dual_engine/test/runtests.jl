using JSimplex,Test,LinearAlgebra,SparseArrays
const J=JSimplex
@assert realpath(pathof(J))=="/home/jspitz/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
const ROOT=normpath(joinpath(@__DIR__,"..","..",".."))
if ARGS==["red"]
    include(joinpath(ROOT,"diagnostics/dual-step-experiment/task1/red/ExperimentalDualEngine.jl"))
else
    @assert ARGS==["state","invariants"]
    include(joinpath(@__DIR__,"..","ExperimentalDualEngine.jl"))
end
const E=ExperimentalDualEngine
if ARGS==["red"]
    @testset "Task1 missing interfaces" begin
        for name in (:eligible,:EnginePolicy,:import_phase,:EngineState,:rebuild_invariants!,:classify_variable!,:invalidate!,:assert_invariants,:SparseSet,:StampedScratch,:set_present!,:set_scratch!,:add_scratch!,:clear_scratch!,:compact_scratch!,:write_value!)
            @test isdefined(E,name)
        end
    end
else
    include("fixtures.jl")
    include("state_tests.jl")
    include("invariant_tests.jl")
    println("DUAL_ENGINE_TASK1_COMPLETED")
end

using JSimplex,Test,LinearAlgebra,SparseArrays
const J=JSimplex
@assert realpath(pathof(J))=="/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
include(joinpath(@__DIR__,"..","ExperimentalDualEngine.jl"))
const E=ExperimentalDualEngine
const TASK5_DIAGNOSTICS=joinpath(@__DIR__,"..","..","..","diagnostics","dual-step-experiment","task5")
include(joinpath(TASK5_DIAGNOSTICS,"recording-logger-helpers.jl"))
println("TASK5_PUBLIC_REGRESSIONS_BEGIN");flush(stdout)
include(joinpath(@__DIR__,"..","..","..","test","solver_tests.jl"))
println("DUAL_ENGINE_TASK5_PUBLIC_COMPLETED");flush(stdout)

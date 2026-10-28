using Test,JSimplex,LinearAlgebra
const ROOT="/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28/RED"
@assert realpath(pathof(JSimplex))==realpath(joinpath(ROOT,"src/JSimplex.jl"))
@assert Base.active_project()==joinpath(ROOT,"Project.toml")
BLAS.set_num_threads(1)
@assert Threads.nthreads()==BLAS.get_num_threads()==1
println("RPC_SOURCE ",pathof(JSimplex));flush(stdout)
@testset "Residual pivot crash RED" begin
 for file in ["generic_residual_pivot_crash_tests.jl"]
  println("INCLUDING ",file);flush(stdout)
  include(joinpath(ROOT,"test",file))
 end
end
println("RPC_COMPLETED RED");flush(stdout)

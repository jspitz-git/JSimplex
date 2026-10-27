using Test,JSimplex,LinearAlgebra
const ROOT="/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27/RED"
@assert realpath(pathof(JSimplex))==realpath(joinpath(ROOT,"src/JSimplex.jl"))
@assert Base.active_project()==joinpath(ROOT,"Project.toml")
BLAS.set_num_threads(1)
@assert Threads.nthreads()==BLAS.get_num_threads()==1
println("BNI_SOURCE ",pathof(JSimplex));flush(stdout)
@testset "Bounds norm infeasibility RED" begin
 for file in ["generic_bounds_norm_infeasibility_tests.jl"]
  println("INCLUDING ",file);flush(stdout)
  include(joinpath(ROOT,"test",file))
 end
end
println("BNI_COMPLETED RED");flush(stdout)

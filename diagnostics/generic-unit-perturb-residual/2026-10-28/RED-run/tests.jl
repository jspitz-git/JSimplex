using Test,JSimplex,LinearAlgebra
const ROOT="/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28/RED"
@assert realpath(pathof(JSimplex))==realpath(joinpath(ROOT,"src/JSimplex.jl"))
@assert Base.active_project()==joinpath(ROOT,"Project.toml")
BLAS.set_num_threads(1)
@assert Threads.nthreads()==BLAS.get_num_threads()==1
println("UPR_SOURCE ",pathof(JSimplex));flush(stdout)
@testset "Unit perturb residual RED" begin
 for file in ["generic_unit_perturb_residual_tests.jl"]
  println("INCLUDING ",file);flush(stdout)
  include(joinpath(ROOT,"test",file))
 end
end
println("UPR_COMPLETED RED");flush(stdout)

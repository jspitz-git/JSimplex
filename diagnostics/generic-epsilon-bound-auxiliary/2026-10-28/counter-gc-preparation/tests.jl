using Test,JSimplex,LinearAlgebra,TOML
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
println("COUNTER_SOURCE ",pathof(JSimplex));flush(stdout)
@testset "Legacy allocation counter capture" begin
 for file in ["/home/jspitz/JSimplex.jl/test/generic_epsilon_bound_auxiliary_tests.jl", "/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28/counter-gc-preparation/generic_unit_perturb_residual_tests.jl", "/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28/counter-gc-preparation/generic_dual_comparisons_tests.jl"]
  println("INCLUDING ",file);flush(stdout);started=time_ns()
  include(file)
  println("FILE_FINISHED ",file," elapsed_seconds=",(time_ns()-started)/1e9);flush(stdout)
 end
end
println("COUNTER_CAPTURE_COMPLETE")

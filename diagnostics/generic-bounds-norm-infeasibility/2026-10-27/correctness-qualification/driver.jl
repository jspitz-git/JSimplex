using Test,JSimplex,SparseArrays,LinearAlgebra
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
include("/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27/comparison-2/Reference.jl")
include("/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27/comparison-2/A.jl")
include("/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27/comparison-2/B.jl")
include("/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27/comparison-2/C.jl")
include("/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27/comparison-2/fixtures.jl")
include(joinpath(@__DIR__,"extra-corrected.jl"))
@testset "Bounds norm certificate correctness qualification" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do
    correctness(BigFloat);extra_correctness(BigFloat)
   end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);extra_correctness(T);end
end
println("BNI_CORRECTNESS_QUALIFICATION_COMPLETE");flush(stdout)

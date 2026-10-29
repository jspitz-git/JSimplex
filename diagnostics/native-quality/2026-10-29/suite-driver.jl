using JSimplex,Test,LinearAlgebra
@assert realpath(pathof(JSimplex)) == "/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
include("/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/test/runtests.jl")

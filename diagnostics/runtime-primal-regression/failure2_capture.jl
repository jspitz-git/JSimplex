# Run in the original Windows project, using its installed JSimplex unchanged.
# julia --project=PATH --startup-file=no --compiled-modules=existing failure2_capture.jl input.mps fresh-prefix
include(joinpath(@__DIR__, "capture.jl"))
using LinearAlgebra

length(ARGS) == 2 || error("Expected: input.mps output_prefix")
BLAS.set_num_threads(8)
@assert BLAS.get_num_threads() == 8
println("Failure2 capture: Julia=", VERSION, "; BLAS threads=", BLAS.get_num_threads(),
    "; Julia threads=", Threads.nthreads(), "; JSimplex=", pathof(RuntimePrimalCapture.JS))
flush(stdout)
RuntimePrimalCapture.main(ARGS...)

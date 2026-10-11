using Test,JSimplex,LinearAlgebra
@assert Threads.nthreads()==BLAS.get_num_threads()==1
include(joinpath(dirname(dirname(pathof(JSimplex))),"test","pipeline_canonical_support_tests.jl"))

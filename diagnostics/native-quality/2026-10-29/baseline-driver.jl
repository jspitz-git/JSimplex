using JSimplex,Test,LinearAlgebra
@assert realpath(pathof(JSimplex)) == "/home/jspitz/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
@testset "Unchanged235 legacy allocation baseline" begin
    include("/home/jspitz/JSimplex.jl/test/generic_unit_perturb_residual_tests.jl")
    include("/home/jspitz/JSimplex.jl/test/generic_dual_comparisons_tests.jl")
end

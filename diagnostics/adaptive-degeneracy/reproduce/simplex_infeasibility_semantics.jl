using JSimplex,Test,LinearAlgebra
BLAS.set_num_threads(1)
@testset "Simplex infeasibility tolerance and semantic regressions" begin
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test/simplex_infeasibility_tolerance_tests.jl"))
    include(joinpath(@__DIR__,"presolve_tolerance_semantics.jl"))
end

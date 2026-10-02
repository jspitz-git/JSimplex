using JSimplex,Test,LinearAlgebra
BLAS.set_num_threads(1)
@testset "Runtime failure repairs and simplex semantic regressions" begin
    root=dirname(dirname(pathof(JSimplex)))
    include(joinpath(root,"test/journal_price_repair_tests.jl"))
    include(joinpath(root,"test/native_phase_coupled_tests.jl"))
    include(joinpath(root,"test/native_dual_tableau_tests.jl"))
    include(joinpath(@__DIR__,"simplex_infeasibility_semantics.jl"))
end

using Test,JSimplex
@testset "Small-pivot flip and simplex semantic regressions" begin
    root=dirname(dirname(pathof(JSimplex)))
    include(joinpath(root,"test/primal_small_pivot_flip_tests.jl"))
    include(joinpath(root,"test/primal_simplex_tests.jl"))
    include(joinpath(@__DIR__,"phase_transfer_recovery_semantics.jl"))
end

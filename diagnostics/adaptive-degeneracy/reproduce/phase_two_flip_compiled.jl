using Test,JSimplex
@testset "Compiled small-pivot flip and allocation checks" begin
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test/primal_small_pivot_flip_tests.jl"))
    include(joinpath(@__DIR__,"structural_value_compiled.jl"))
end

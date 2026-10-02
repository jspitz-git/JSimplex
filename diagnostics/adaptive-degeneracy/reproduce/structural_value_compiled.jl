using Test,JSimplex
@testset "Compiled structural retention and allocation checks" begin
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test/legacy_primal_structural_value_tests.jl"))
    include(joinpath(@__DIR__,"representable_point_compiled.jl"))
end

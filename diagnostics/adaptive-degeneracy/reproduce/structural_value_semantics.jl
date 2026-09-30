using Test,JSimplex
@testset "Structural retention and simplex semantic regressions" begin
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test/legacy_primal_structural_value_tests.jl"))
    include(joinpath(@__DIR__,"representable_point_semantics.jl"))
end

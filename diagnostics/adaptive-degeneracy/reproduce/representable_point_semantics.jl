using Test, JSimplex
@testset "Representable recovery and adaptive interaction regressions" begin
    include(joinpath(@__DIR__,"joint_point_semantics.jl"))
    include(joinpath(@__DIR__,"representable_point_tests.jl"))
end

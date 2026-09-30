using Test
@testset "Coupled point candidate semantics" begin
    include(joinpath(@__DIR__,"coupled_point_candidate_tests.jl"))
    include(joinpath(@__DIR__,"row_value_semantics.jl"))
end

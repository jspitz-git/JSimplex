using Test
@testset "Compiled coupled point candidate and allocation checks" begin
    include(joinpath(@__DIR__,"coupled_point_candidate_tests.jl"))
    include(joinpath(@__DIR__,"row_value_compiled.jl"))
end

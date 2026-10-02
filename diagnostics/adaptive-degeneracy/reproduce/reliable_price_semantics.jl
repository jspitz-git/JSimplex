using Test,JSimplex
@testset "Reliable native price refinement and semantic regressions" begin
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test","native_reliable_price_tests.jl"))
    include(joinpath(@__DIR__,"artificial_bound_semantics.jl"))
end

using Test,JSimplex
@testset "Native driver reconstruction and semantic regressions" begin
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test","native_driver_reconstruction_tests.jl"))
    include(joinpath(@__DIR__,"reliable_price_semantics.jl"))
end

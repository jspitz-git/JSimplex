using Test,JSimplex
@testset "Native artificial-bound normalization and semantic regressions" begin
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test","native_artificial_bound_tests.jl"))
    include(joinpath(@__DIR__,"artificial_row_semantics.jl"))
end

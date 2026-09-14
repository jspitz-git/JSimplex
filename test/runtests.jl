using JSimplex
using Test

@testset "JSimplex" begin
    include("options_tests.jl")
    include("model_tests.jl")
end

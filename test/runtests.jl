using JSimplex
using Test

@testset "JSimplex" begin
    include("options_tests.jl")
    include("model_tests.jl")
    include("transformations_tests.jl")
end

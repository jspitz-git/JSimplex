using JSimplex
using Test

@testset "JSimplex" begin
    include("options_tests.jl")
    include("model_tests.jl")
    include("transformations_tests.jl")
    include("mps_parser_tests.jl")
    include("mps_build_tests.jl")
end

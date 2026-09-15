using JSimplex
using Test

@testset "JSimplex" begin
    include("numeric_tests.jl")
    include("options_tests.jl")
    include("model_tests.jl")
    include("transformations_tests.jl")
    include("mps_parser_tests.jl")
    include("mps_build_tests.jl")
    include("factorization_tests.jl")
    include("simplex_workspace_tests.jl")
    include("dual_simplex_tests.jl")
    include("solver_tests.jl")
    include("regression_tests.jl")
end

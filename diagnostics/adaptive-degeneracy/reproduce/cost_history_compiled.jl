using Test,JSimplex
@testset "Compiled dual feasibility history regressions" begin
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test","dual_stagnation_cost_tests.jl"))
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test","simplex_precision_state_tests.jl"))
    include(joinpath(@__DIR__,"intervention_compiled.jl"))
end

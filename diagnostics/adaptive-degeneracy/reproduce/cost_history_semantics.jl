using Test,JSimplex
@testset "Dual feasibility history regressions" begin
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test","dual_stagnation_cost_tests.jl"))
    include(joinpath(@__DIR__,"intervention_semantics.jl"))
end

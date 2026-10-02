using Test,JSimplex
@testset "Adaptive intervention regressions" begin
    for name in ("adaptive_progress_metric","adaptive_intervention_order")
        include(joinpath(dirname(dirname(pathof(JSimplex))),"test",name*"_tests.jl"))
    end
    include(joinpath(@__DIR__,"focused.jl"))
    include(joinpath(@__DIR__,"phase_one_interactions.jl"))
end

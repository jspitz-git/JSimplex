using Test,JSimplex
@testset "Compiled adaptive intervention regressions" begin
    for name in ("adaptive_progress_metric","adaptive_intervention_order")
        include(joinpath(dirname(dirname(pathof(JSimplex))),"test",name*"_tests.jl"))
    end
end

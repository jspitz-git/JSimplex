using JSimplex, Test

@testset "Primal core regressions" begin
    include(joinpath(@__DIR__, "..", "..", "primal-runtime-stability",
        "reproduce", "focused.jl"))
    for name in ("legacy_primal_direction_price", "legacy_primal_equation_point",
                 "legacy_primal_residual_probe", "legacy_primal_point_recovery")
        include(joinpath(dirname(dirname(pathof(JSimplex))), "test", name * "_tests.jl"))
    end
end

using JSimplex, Test
@testset "Native cleanup and numerical recovery" begin
    for name in ("native_cleanup_recovery", "simplex_driver", "simplex_refinement",
                 "simplex_strategy_separation", "simplex_handoff_atomicity",
                 "legacy_dual_correction", "legacy_dual_price_repair",
                 "legacy_primal_point_recovery", "simplex_phase_one")
        include(joinpath(pwd(),"test",name*"_tests.jl"))
    end
end

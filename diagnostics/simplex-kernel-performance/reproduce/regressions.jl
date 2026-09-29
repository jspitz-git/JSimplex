using JSimplex, Test
@testset "CSC pricing and simplex integration" begin
    for name in ("csc_pricing_performance", "sparse_pricing", "sparse_pricing_integration",
                 "sparse_pricing_edge", "sparse_pricing_storage", "dual_ratio",
                 "adaptive_pricing", "adaptive_pricing_integration", "partial_pricing",
                 "partial_pricing_integration", "partial_pricing_edge",
                 "primal_retry_pricing", "legacy_primal_direction_price",
                 "simplex_strategy_separation", "native_cleanup_recovery",
                 "simplex_driver", "simplex_phase_logging", "simplex_phase_one")
        if name in ("partial_pricing_integration", "partial_pricing_edge") && !("--extended" in ARGS)
            continue
        end
        include(joinpath(pwd(),"test",name*"_tests.jl"))
    end
end

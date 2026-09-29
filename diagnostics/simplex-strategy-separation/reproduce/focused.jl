using Test, JSimplex
const ROOT = dirname(dirname(pathof(JSimplex)))
@testset "Numerical core and strategy separation" begin
    for name in ("simplex_strategy_separation", "legacy_primal_pivot_preference",
                 "legacy_primal_preference_work", "legacy_correction_cycle",
                 "legacy_dual_price_repair", "simplex_perturbation",
                 "simplex_perturbation_integration", "primal_perturbation",
                 "primal_perturbation_integration")
        println("Checking ", name); flush(stdout)
        include(joinpath(ROOT, "test", name * "_tests.jl"))
    end
end

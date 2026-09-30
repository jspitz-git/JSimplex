using Test, JSimplex
const ROOT = dirname(dirname(pathof(JSimplex)))
@testset "Independent stagnation and pricing policies" begin
    for name in ("simplex_strategy_separation", "dual_core_policy",
                 "simplex_stalling", "simplex_stalling_integration", "simplex_stalling_edge",
                 "simplex_perturbation", "simplex_perturbation_integration",
                 "primal_perturbation", "primal_perturbation_integration",
                 "adaptive_pricing", "adaptive_pricing_integration", "adaptive_pricing_lifecycle",
                 "simplex_handoff_atomicity")
        println("Checking ", name); flush(stdout)
        include(joinpath(ROOT, "test", name * "_tests.jl"))
    end
end

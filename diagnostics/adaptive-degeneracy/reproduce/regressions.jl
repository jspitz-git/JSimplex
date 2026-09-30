using Test, JSimplex
const ROOT = dirname(dirname(pathof(JSimplex)))
@testset "Pricing phase and numerical recovery regressions" begin
    for name in ("basis_recovery", "pivot_retry", "pivot_application", "pivot_atomicity",
                 "simplex_phase_one", "simplex_phase_one_state", "simplex_phase_one_deadline",
                 "simplex_phase_one_guard", "simplex_phase_one_completion", "simplex_phase_one_auxiliary",
                 "simplex_phase_logging", "partial_pricing", "partial_pricing_integration",
                 "partial_pricing_edge", "primal_retry_pricing")
        println("Checking ", name); flush(stdout)
        include(joinpath(ROOT,"test",name * "_tests.jl"))
    end
end

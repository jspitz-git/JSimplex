using JSimplex, Test, SparseArrays, LinearAlgebra
const ROOT = dirname(dirname(pathof(JSimplex)))
for name in ("numeric", "simplex_numerics", "native_residual_mode",
             "solver_policy_precision", "refactorization_failure", "legacy_dual_correction",
             "legacy_dual_price_repair", "legacy_correction_cycle", "legacy_retry_edge",
             "adaptive_pricing", "adaptive_pricing_integration", "simplex_start",
             "simplex_start_guard", "simplex_phase_one", "simplex_phase_one_state",
             "triangular_selective_preparation", "triangular_preparation_lifecycle")
    println("Checking ", name); flush(stdout)
    include(joinpath(ROOT, "test", name * "_tests.jl"))
end

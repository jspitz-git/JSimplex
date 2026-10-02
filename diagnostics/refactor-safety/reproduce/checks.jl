using JSimplex, Test
root = dirname(dirname(pathof(JSimplex)))
@testset "Symmetric numerical refactorization protection" begin
    for name in ("refactorization_safety", "dual_simplex", "dual_core_policy",
        "legacy_dual_correction", "legacy_correction_cycle", "refactorization_policy",
        "refactorization_timing", "refactorization_factor", "refactorization_failure",
        "legacy_primal_pivot_row", "legacy_primal_correlated_pivot", "legacy_primal_direction_price",
        "legacy_primal_pivot_preference", "simplex_strategy_separation")
        include(joinpath(root, "test", name * "_tests.jl"))
    end
end

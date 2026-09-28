using JSimplex, Test
const ROOT = dirname(dirname(pathof(JSimplex)))
for name in ("primal_bound_snap", "legacy_primal_correlated_pivot",
             "legacy_primal_roundoff_pivot", "legacy_primal_relative_pivot",
             "legacy_primal_pivot_row", "legacy_primal_pivot_preference",
             "legacy_primal_preference_work", "legacy_hardware_guard",
             "primal_candidate_retry", "primal_retry_pricing",
             "legacy_primal_row_value", "legacy_harris_feasibility",
             "legacy_primal_point", "primal_initial_tolerance")
    include(joinpath(ROOT, "test", name * "_tests.jl"))
end

using Test,JSimplex
isdefined(JSimplex,:_round_primal_bound_trial_inward!) ||
    error("Apply working-row-rounded.patch to a separate baseline checkout first")
@testset "Owned row-value preservation regressions" begin
    # Apply working-row-rounded.patch before running these candidate regressions.
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test/legacy_primal_row_value_tests.jl"))
    include(joinpath(@__DIR__,"working_row_candidate_tests.jl"))
    include(joinpath(@__DIR__,"bound_roundoff_candidate_tests.jl"))
    include(joinpath(@__DIR__,"focused.jl"))
    for name in ("adaptive_progress_metric", "adaptive_intervention_order", "dual_stagnation_cost")
        include(joinpath(dirname(dirname(pathof(JSimplex))),"test",name*"_tests.jl"))
    end
    # The interaction runner installs process-local isolation overrides last.
    include(joinpath(@__DIR__,"balanced_point_semantics.jl"))
end

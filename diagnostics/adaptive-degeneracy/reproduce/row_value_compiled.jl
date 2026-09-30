using Test,JSimplex
isdefined(JSimplex,:_round_primal_bound_trial_inward!) ||
    error("Apply working-row-rounded.patch to a separate baseline checkout first")
@testset "Compiled row-value and allocation checks" begin
    # Apply working-row-rounded.patch before running these candidate regressions.
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test/legacy_primal_row_value_tests.jl"))
    include(joinpath(@__DIR__,"working_row_candidate_tests.jl"))
    include(joinpath(@__DIR__,"bound_roundoff_candidate_tests.jl"))
    include(joinpath(@__DIR__,"balanced_point_compiled.jl"))
end

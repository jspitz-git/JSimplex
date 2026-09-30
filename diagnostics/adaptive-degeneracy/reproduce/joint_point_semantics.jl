using Test,JSimplex
@testset "Joint point recovery and adaptive interaction regressions" begin
    include(joinpath(@__DIR__,"joint_point_candidate_tests.jl"))
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test/legacy_primal_row_value_tests.jl"))
    include(joinpath(@__DIR__,"working_row_candidate_tests.jl"))
    include(joinpath(@__DIR__,"focused.jl"))
    for name in ("adaptive_progress_metric","adaptive_intervention_order","dual_stagnation_cost")
        include(joinpath(dirname(dirname(pathof(JSimplex))),"test",name*"_tests.jl"))
    end
    include(joinpath(@__DIR__,"balanced_point_semantics.jl"))
end

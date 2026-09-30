using Test,JSimplex
@testset "Compiled joint point recovery and allocation checks" begin
    include(joinpath(@__DIR__,"joint_point_candidate_tests.jl"))
    include(joinpath(dirname(dirname(pathof(JSimplex))),"test/legacy_primal_row_value_tests.jl"))
    include(joinpath(@__DIR__,"working_row_candidate_tests.jl"))
    include(joinpath(@__DIR__,"balanced_point_compiled.jl"))
end

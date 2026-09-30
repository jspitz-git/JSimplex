using Test, JSimplex
root=dirname(dirname(pathof(JSimplex)))
@testset "Compiled representable recovery and allocation checks" begin
    include(joinpath(root,"test/legacy_primal_joint_point_tests.jl"))
    include(joinpath(root,"test/legacy_primal_row_value_tests.jl"))
    include(joinpath(root,"test/legacy_primal_working_row_scope_tests.jl"))
    include(joinpath(@__DIR__,"balanced_point_compiled.jl"))
end

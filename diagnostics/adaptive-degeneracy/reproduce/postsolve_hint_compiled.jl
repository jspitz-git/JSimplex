using Test,JSimplex
@testset "Compiled postsolve and allocation regressions" begin
    root=dirname(dirname(pathof(JSimplex)))
    include(joinpath(root,"test/postsolve_hint_tests.jl"))
    include(joinpath(root,"test/presolve_tests.jl"))
    include(joinpath(root,"test/postsolve_cleanup_performance_tests.jl"))
    include(joinpath(@__DIR__,"phase_two_flip_compiled.jl"))
end

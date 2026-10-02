using Test,JSimplex
@testset "Postsolve hints and simplex semantic regressions" begin
    root=dirname(dirname(pathof(JSimplex)))
    for name in ("postsolve_hint","postsolve_cleanup_performance")
        include(joinpath(root,"test",name*"_tests.jl"))
    end
    include(joinpath(@__DIR__,"phase_two_flip_semantics.jl"))
end

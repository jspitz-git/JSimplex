using Test,JSimplex
root=dirname(dirname(pathof(JSimplex)))
for name in ("dual_entry_phase","postsolve_cleanup_performance")
    @testset "$name" begin
        include(joinpath(root,"test",name*"_tests.jl"))
    end
end

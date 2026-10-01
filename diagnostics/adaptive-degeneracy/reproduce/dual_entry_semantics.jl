using Test,JSimplex
@testset "Dual entry phase and simplex semantic regressions" begin
    root=dirname(dirname(pathof(JSimplex)))
    for name in ("dual_entry_phase","postsolve_cleanup_performance","postsolve_hint","simplex_driver","simplex_precision_entry")
        println("CHECK ",name);flush(stdout)
        include(joinpath(root,"test",name*"_tests.jl"))
    end
    include(joinpath(@__DIR__,"driver_reconstruction_semantics.jl"))
end

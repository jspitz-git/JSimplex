using Test,JSimplex
@testset "Native phase transfer and simplex semantic regressions" begin
    root=dirname(dirname(pathof(JSimplex)))
    for name in ("native_phase_transfer","native_cleanup_recovery","simplex_phase_one",
                 "simplex_phase_one_auxiliary","simplex_phase_one_guard","simplex_phase_one_deadline")
        println("CHECK ",name);flush(stdout)
        include(joinpath(root,"test",name*"_tests.jl"))
    end
    include(joinpath(@__DIR__,"structural_value_semantics.jl"))
end

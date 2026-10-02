# Broad semantic checks for the artificial-exchange recovery integration.
using Test,JSimplex
@testset "Artificial exchange and phase-transition semantic regressions" begin
    include(joinpath(@__DIR__,"phase_transfer_recovery_semantics.jl"))
    root=dirname(dirname(pathof(JSimplex)))
    for name in ("simplex_phase_one_state","simplex_phase_one_completion",
                 "simplex_phase_logging","simplex_precision_phase")
        println("CHECK ",name);flush(stdout)
        include(joinpath(root,"test",name*"_tests.jl"))
    end
end
include(joinpath(@__DIR__,"mod010_phase_regression.jl"))

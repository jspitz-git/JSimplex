using Test,JSimplex
@testset "Native pricing recovery and simplex semantic regressions" begin
    include(joinpath(@__DIR__,"phase_transfer_recovery_semantics.jl"))
    root=dirname(dirname(pathof(JSimplex)))
    for name in ("legacy_primal_direction_price","legacy_primal_correlated_pivot",
                 "legacy_primal_residual_probe","simplex_phase_logging","simplex_precision_phase")
        println("CHECK ",name);flush(stdout)
        include(joinpath(root,"test",name*"_tests.jl"))
    end
end
include(joinpath(@__DIR__,"direction_price_regression.jl"))

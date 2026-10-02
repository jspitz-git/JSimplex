using Test,JSimplex
@testset "Dual pivot consistency and simplex semantic regressions" begin
    root=dirname(dirname(pathof(JSimplex)))
    for name in ("dual_pivot_consistency","legacy_dual_correction","legacy_dual_price_repair",
                 "legacy_correction_cycle","dual_core_policy","legacy_retry_edge",
                 "dual_small_pivot_price","dual_simplex","dual_ratio","pivot_retry","pivot_application")
        println("CHECK ",name);flush(stdout)
        include(joinpath(root,"test",name*"_tests.jl"))
    end
    include(joinpath(@__DIR__,"dual_entry_semantics.jl"))
end

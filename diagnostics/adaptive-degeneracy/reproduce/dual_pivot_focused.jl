using Test,JSimplex
@testset "Dual pivot consistency and native numerical guards" begin
    root=dirname(dirname(pathof(JSimplex)))
    for name in ("dual_pivot_consistency","legacy_dual_correction","legacy_dual_price_repair",
                 "dual_small_pivot_price","dual_core_policy")
        println("CHECK ",name);flush(stdout)
        include(joinpath(root,"test",name*"_tests.jl"))
    end
end

using Test, JSimplex
@testset "Core and strategy semantic regressions" begin
    include(joinpath(@__DIR__, "focused.jl"))
    include(joinpath(pwd(), "diagnostics/primal-phase1-stagnation/reproduce/focused-core.jl"))
    include(joinpath(pwd(), "diagnostics/primal-runtime-stability/reproduce/regressions.jl"))
    for name in ("refactorization_policy", "refactorization_timing", "refactorization_factor",
                 "simplex_stalling", "simplex_stalling_integration", "simplex_stalling_edge",
                 "dual_ratio", "pivot_retry", "pivot_application", "pivot_atomicity", "simplex_refinement", "basis_recovery", "simplex_driver", "simplex_handoff_atomicity",
                 "postsolve_cleanup_performance",
                 "primal_update", "benchmark_regression")
        println("Checking ", name); flush(stdout)
        include(joinpath(pwd(), "test", name * "_tests.jl"))
    end
end

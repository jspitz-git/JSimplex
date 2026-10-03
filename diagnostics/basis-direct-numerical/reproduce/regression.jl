using Test, JSimplex
const ROOT = dirname(dirname(pathof(JSimplex)))
@testset "Native primal and dual cleanup regressions" begin
    for file in ("native_dual_reconstruction_tests.jl", "native_cleanup_recovery_tests.jl",
                 "native_driver_reconstruction_tests.jl", "native_phase_transfer_tests.jl",
                 "native_phase_coupled_tests.jl", "native_primal_completion_tests.jl",
                 "native_reliable_price_tests.jl",
                 "native_residual_mode_tests.jl", "native_dual_tableau_tests.jl",
                 "simplex_driver_tests.jl", "dual_entry_phase_tests.jl",
                 "simplex_phase_logging_tests.jl", "solver_policy_precision_tests.jl")
        println("TEST ", file); flush(stdout)
        include(joinpath(ROOT, "test", file))
    end
end

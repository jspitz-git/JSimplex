using JSimplex, Test, SparseArrays, LinearAlgebra
const ROOT=dirname(dirname(pathof(JSimplex)))
@testset "Native terminal certificate semantic regressions" begin
    for file in (
        "native_certificate_recovery_tests.jl", "postsolve_native_projection_tests.jl", "postsolve_hint_tests.jl",
        "dual_simplex_tests.jl", "primal_simplex_tests.jl", "primal_update_tests.jl",
        "native_cleanup_recovery_tests.jl", "native_reliable_price_tests.jl",
        "native_driver_reconstruction_tests.jl", "native_dual_reconstruction_tests.jl",
        "simplex_driver_tests.jl", "simplex_start_tests.jl", "simplex_start_guard_tests.jl",
        "simplex_phase_one_tests.jl", "simplex_phase_one_state_tests.jl",
        "simplex_phase_logging_tests.jl", "simplex_precision_entry_tests.jl",
        "simplex_precision_exception_tests.jl", "simplex_precision_guard_tests.jl",
        "lp_refinement_terminal_tests.jl", "regression_tests.jl")
        println("TEST ",file);flush(stdout)
        include(joinpath(ROOT,"test",file))
    end
end

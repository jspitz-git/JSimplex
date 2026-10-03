using JSimplex, Test
root = dirname(dirname(pathof(JSimplex)))
# Keep interpreter verification separate from allocation-sensitive assertions.
@testset "Public manager integration and existing semantic regressions" begin
    for name in (
        "dual_entry_phase_tests.jl", "native_dual_reconstruction_tests.jl",
        "native_primal_completion_tests.jl", "native_phase_transfer_tests.jl",
        "options_tests.jl", "huangfu_hall_option_tests.jl", "huangfu_hall_integration_tests.jl",
        "factorization_tests.jl", "markowitz_tests.jl", "runtime_factorization_tests.jl",
        "simplex_workspace_tests.jl", "simplex_diagnostics_tests.jl", "solver_tests.jl",
        "primal_simplex_tests.jl", "dual_simplex_tests.jl", "regression_tests.jl",
        "simplex_strategy_separation_tests.jl", "simplex_phase_logging_tests.jl",
        "refactorization_policy_tests.jl", "refactorization_safety_tests.jl",
        "refactorization_factor_tests.jl", "refactorization_failure_tests.jl",
        "simplex_precision_tests.jl", "simplex_precision_state_tests.jl",
        "moi/optimizer_tests.jl", "moi/translation_tests.jl", "moi/result_tests.jl",
        "moi/conformance_tests.jl")
        println("START ",name);flush(stdout)
        path=joinpath(root,"test",name)
        if occursin("@allocated",read(path,String))
            println("SEPARATE NORMAL-COMPILE CHECK ",name);continue
        end
        include(path)
    end
end

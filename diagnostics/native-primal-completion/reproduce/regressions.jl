using JSimplex, Test

@testset "Native primal completion and pricing regressions" begin
    push!(ARGS, "--extended")
    include(joinpath(pwd(), "diagnostics/simplex-kernel-performance/reproduce/regressions.jl"))
    for name in ("native_primal_completion", "primal_update", "primal_simplex",
                 "pivot_retry", "pivot_atomicity", "pivot_application",
                 "primal_candidate_retry", "legacy_primal_point", "legacy_primal_point_recovery",
                 "legacy_primal_equation_point", "legacy_primal_row_value",
                 "legacy_primal_correlated_pivot", "legacy_primal_pivot_row",
                 "legacy_primal_relative_pivot", "legacy_primal_roundoff_pivot",
                 "legacy_primal_preference_work", "legacy_primal_pivot_preference",
                 "legacy_primal_residual_probe")
        println("Running ", name); flush(stdout)
        include(joinpath(pwd(), "test", name * "_tests.jl"))
    end
end

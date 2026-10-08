using Test, JSimplex, SparseArrays, LinearAlgebra, Logging
root=dirname(dirname(pathof(JSimplex)))
@testset "Legacy phase artificial bounds and transfer regressions" begin
    for file in ("native_artificial_bound_tests.jl", "legacy_phase_artificial_bound_tests.jl",
                 "simplex_phase_one_tests.jl", "simplex_phase_one_state_tests.jl",
                 "simplex_phase_one_auxiliary_tests.jl", "simplex_phase_logging_tests.jl",
                 "primal_simplex_tests.jl")
        get(ENV, "DEGEN3_FOCUSED", "false") == "true" && !(file in ("native_artificial_bound_tests.jl", "legacy_phase_artificial_bound_tests.jl")) && continue
        println("Testing ", file); flush(stdout)
        include(joinpath(root,"test",file))
    end
end

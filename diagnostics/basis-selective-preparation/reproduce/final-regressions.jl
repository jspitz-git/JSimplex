using JSimplex, Test, SparseArrays, LinearAlgebra
const ROOT = dirname(dirname(pathof(JSimplex)))
for name in ("triangular_selective_preparation_tests.jl", "legacy_dual_correction_tests.jl",
             "adaptive_pricing_tests.jl", "adaptive_pricing_integration_tests.jl",
             "simplex_start_tests.jl", "simplex_start_guard_tests.jl",
             "simplex_phase_one_tests.jl", "simplex_phase_one_state_tests.jl")
    include(joinpath(ROOT,"test",name))
end

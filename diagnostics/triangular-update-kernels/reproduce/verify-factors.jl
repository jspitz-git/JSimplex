using JSimplex, Test, Logging
const TEST_ROOT = joinpath(dirname(dirname(pathof(JSimplex))), "test")
include(joinpath(TEST_ROOT, "triangular_prepared_spike_tests.jl"))
@testset "Triangular numerical baseline" begin
    for name in ("bartels_golub_incidence_tests.jl", "triangular_active_upper_tests.jl",
                 "bartels_golub_rows_tests.jl", "triangular_composed_rows_tests.jl",
                 "bartels_golub_rotation_tests.jl", "factorization_tests.jl",
                 "hypersparse_update_tests.jl", "hypersparse_update_sequence_tests.jl",
                 "hypersparse_update_edge_tests.jl", "hypersparse_update_overflow_tests.jl")
        include(joinpath(TEST_ROOT, name))
    end
end

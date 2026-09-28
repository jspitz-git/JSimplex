using JSimplex, Test, Logging

# Pure correctness checks; also suitable for --compile=min. Allocation checks
# belong to a separate normally compiled run.
const TEST_ROOT = joinpath(dirname(dirname(pathof(JSimplex))), "test")
for name in ("triangular_row_spike_tests.jl", "triangular_prepared_spike_tests.jl",
             "bartels_golub_incidence_tests.jl", "bartels_golub_rows_tests.jl",
             "triangular_active_upper_tests.jl", "triangular_composed_rows_tests.jl",
             "bartels_golub_rotation_tests.jl", "hypersparse_update_tests.jl",
             "hypersparse_update_sequence_tests.jl", "hypersparse_update_edge_tests.jl",
             "hypersparse_update_overflow_tests.jl", "stable_upper_indices_tests.jl")
    include(joinpath(TEST_ROOT, name))
end

using JSimplex, Test, Logging
@testset "Composed BG and factorization regressions" begin
    for name in (
        "bartels_golub_incidence_tests.jl", "triangular_active_upper_tests.jl", "bartels_golub_rows_tests.jl", "triangular_composed_rows_tests.jl", "bartels_golub_rotation_tests.jl", "factorization_tests.jl",
        "triangular_reset_allocation_tests.jl", "triangular_column_reuse_allocation_tests.jl",
        "triangular_history_reuse_allocation_tests.jl", "factorization_allocation_tests.jl",
        "hypersparse_update_tests.jl", "hypersparse_update_sequence_tests.jl",
        "hypersparse_update_edge_tests.jl", "hypersparse_update_allocation_tests.jl",
        "hypersparse_update_overflow_tests.jl", "pivot_atomicity_tests.jl")
        println("FILE ",name);flush(stdout)
        include(joinpath(pwd(),"test",name))
    end
end

using JSimplex,Test,SparseArrays,LinearAlgebra,Random,Logging
root=dirname(dirname(pathof(JSimplex)))
@testset "Triangular stability and lifecycle regressions" begin
    for file in ("triangular_stability_tests.jl","factorization_tests.jl",
        "triangular_row_spike_tests.jl","triangular_composed_rows_tests.jl",
        "triangular_active_upper_tests.jl","triangular_prepared_spike_tests.jl",
        "triangular_selective_preparation_tests.jl","triangular_incremental_metadata_tests.jl",
        "triangular_preparation_lifecycle_tests.jl","triangular_capacity_tests.jl",
        "triangular_reset_allocation_tests.jl","triangular_column_reuse_allocation_tests.jl",
        "triangular_history_reuse_allocation_tests.jl","triangular_transpose_allocation_tests.jl",
        "hypersparse_update_tests.jl","hypersparse_update_edge_tests.jl",
        "hypersparse_factorization_safety_tests.jl","runtime_solver_tests.jl")
        println("TEST ",file);flush(stdout)
        include(joinpath(root,"test",file))
    end
end

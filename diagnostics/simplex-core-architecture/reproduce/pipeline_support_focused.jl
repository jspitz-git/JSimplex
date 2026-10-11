using Test,JSimplex,SparseArrays,LinearAlgebra
@assert Threads.nthreads()==BLAS.get_num_threads()==1
root=dirname(dirname(pathof(JSimplex)))
@testset "Canonical output producer and consumer regressions" begin
    for file in ("indexed_vector_tests.jl", "sparse_pricing_tests.jl", "sparse_pricing_integration_tests.jl", "sparse_pricing_edge_tests.jl",
        "sparse_pricing_signed_zero_tests.jl", "hypersparse_factorization_tests.jl",
        "hypersparse_factorization_edge_tests.jl", "hypersparse_factorization_safety_tests.jl",
        "hypersparse_update_tests.jl", "hypersparse_update_edge_tests.jl",
        "hypersparse_update_sequence_tests.jl", "hypersparse_update_overflow_tests.jl",
        "hypersparse_pipeline_tests.jl", "hypersparse_pipeline_storage_tests.jl",
        "hypersparse_pipeline_kernel_tests.jl", "hypersparse_pipeline_integration_tests.jl",
        "hypersparse_pipeline_edge_tests.jl", "hypersparse_pipeline_accounting_tests.jl",
        "hypersparse_pipeline_solver_tests.jl", "hypersparse_pipeline_recovery_tests.jl", "hypersparse_pipeline_subtraction_tests.jl")
        println("Starting ",file);flush(stdout)
        include(joinpath(root,"test",file))
    end
    include("pipeline_support_hh_tests.jl")
end

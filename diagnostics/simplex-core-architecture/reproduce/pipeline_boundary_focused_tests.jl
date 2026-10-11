using Test,JSimplex,SparseArrays,LinearAlgebra
@assert Threads.nthreads()==BLAS.get_num_threads()==1
root=dirname(dirname(pathof(JSimplex)))
mode=isempty(ARGS) ? "all" : only(ARGS)
@assert mode in ("all","lp-state")
files=mode=="lp-state" ? ("lp_refinement_recovery_tests.jl","lp_refinement_state_tests.jl") : ("hypersparse_pipeline_tests.jl", "hypersparse_pipeline_storage_tests.jl",
        "hypersparse_pipeline_kernel_tests.jl", "hypersparse_pipeline_integration_tests.jl",
        "hypersparse_pipeline_edge_tests.jl", "hypersparse_pipeline_accounting_tests.jl",
        "hypersparse_pipeline_solver_tests.jl", "hypersparse_pipeline_recovery_tests.jl",
        "hypersparse_pipeline_subtraction_tests.jl", "simplex_refinement_tests.jl",
        "lp_refinement_projection_tests.jl", "lp_refinement_diagnostic_tests.jl",
        "lp_refinement_limit_tests.jl", "lp_refinement_recovery_tests.jl", "lp_refinement_state_tests.jl")
@testset "Pipeline boundary focused integration" begin
    for file in files
        println("Starting ",file);flush(stdout)
        include(joinpath(root,"test",file))
    end
end

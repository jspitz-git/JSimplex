using JSimplex,Test,SparseArrays,LinearAlgebra,Random,Logging
root=dirname(dirname(pathof(JSimplex)))
@testset "BFRT tie stability and ratio regressions" begin
    for file in ("dual_bfrt_tie_tests.jl","dual_breakpoint_queue_tests.jl","runtime_solver_tests.jl","dual_ratio_tests.jl",
                 "iteration_kernel_allocation_tests.jl","hypersparse_pipeline_solver_tests.jl")
        println("TEST ",file);flush(stdout)
        include(joinpath(root,"test",file))
    end
end

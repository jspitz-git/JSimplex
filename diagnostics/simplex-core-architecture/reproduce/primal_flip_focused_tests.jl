using Test,JSimplex,SparseArrays,LinearAlgebra
@assert Threads.nthreads()==BLAS.get_num_threads()==1
root=dirname(dirname(pathof(JSimplex)))
@testset "Primal flip existing guard regressions" begin
    for file in ("primal_update_tests.jl", "legacy_primal_direction_price_tests.jl",
        "legacy_primal_point_tests.jl", "primal_point_storage_tests.jl",
        "legacy_primal_equation_point_tests.jl", "legacy_primal_point_recovery_tests.jl",
        "legacy_primal_perturbed_point_tests.jl", "legacy_primal_balanced_point_tests.jl",
        "legacy_primal_joint_point_tests.jl")
        println("Starting ",file);flush(stdout)
        include(joinpath(root,"test",file))
    end
end

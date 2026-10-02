using JSimplex,Test,LinearAlgebra
BLAS.set_num_threads(1)
@testset "Legacy bound snap and candidate retry controls" begin
    root=dirname(dirname(pathof(JSimplex)))
    @info "Loaded source" root
    include(joinpath(root,"test/primal_bound_snap_tests.jl"))
    include(joinpath(root,"test/primal_candidate_retry_tests.jl"))
end

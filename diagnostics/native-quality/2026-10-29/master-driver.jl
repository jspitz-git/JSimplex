using JSimplex,Test,LinearAlgebra
const MASTER_ROOT="/home/jspitz/JSimplex.jl"
@assert realpath(pathof(JSimplex)) == joinpath(MASTER_ROOT,"src/JSimplex.jl")
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
@testset "Master native quality and affected regressions" begin
    include(joinpath(MASTER_ROOT,"test/native_quality_finite_tests.jl"))
    include(joinpath(MASTER_ROOT,"test/generic_quality_devex_tests.jl"))
    include(joinpath(MASTER_ROOT,"test/numeric_tests.jl"))
    include(joinpath(MASTER_ROOT,"test/compensated_transpose_work_tests.jl"))
    include(joinpath(MASTER_ROOT,"test/generic_quality_local_tests.jl"))
    include(joinpath(MASTER_ROOT,"test/generic_unit_perturb_residual_tests.jl"))
    include(joinpath(MASTER_ROOT,"test/generic_dual_comparisons_tests.jl"))
    include(joinpath(MASTER_ROOT,"test/simplex_numerics_tests.jl"))
    include(joinpath(MASTER_ROOT,"test/native_residual_tests.jl"))
    include(joinpath(MASTER_ROOT,"test/native_residual_mode_tests.jl"))
end

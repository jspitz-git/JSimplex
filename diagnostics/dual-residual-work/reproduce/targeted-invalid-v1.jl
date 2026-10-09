using JSimplex,Test,SparseArrays,LinearAlgebra
@testset "Native residual and correction integration" begin
 for file in ("compensated_transpose_work_tests.jl","native_residual_tests.jl","native_residual_mode_tests.jl","simplex_numerics_tests.jl","native_dual_reprice_tests.jl","native_dual_tableau_tests.jl","native_kernel_dimension_tests.jl","native_certificate_recovery_tests.jl","native_cleanup_recovery_tests.jl")
  include(joinpath("test",file))
 end
end

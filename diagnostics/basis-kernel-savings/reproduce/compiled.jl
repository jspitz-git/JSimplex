using JSimplex,Test,LinearAlgebra,SparseArrays
root=dirname(dirname(pathof(JSimplex)))
@testset "Basis kernel compiled regressions" begin
 for file in ("pfi_kernel_safety_tests.jl","upper_kernel_order_tests.jl",
              "factorization_tests.jl","factorization_allocation_tests.jl",
              "pfi_history_reuse_allocation_tests.jl","triangular_transpose_allocation_tests.jl",
              "hypersparse_update_allocation_tests.jl","lu_allocation_tests.jl")
  println("TEST ",file);flush(stdout);include(joinpath(root,"test",file))
 end
end

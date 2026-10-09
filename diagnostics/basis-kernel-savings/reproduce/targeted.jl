using JSimplex, Test, LinearAlgebra, SparseArrays
root=dirname(dirname(pathof(JSimplex)))
@testset "Basis kernel safety" begin
 include(joinpath(root,"test/pfi_kernel_safety_tests.jl"))
 include(joinpath(root,"test/upper_kernel_order_tests.jl"))
end

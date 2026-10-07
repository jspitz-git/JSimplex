using Test,JSimplex,SparseArrays,LinearAlgebra
const ROOT=dirname(dirname(pathof(JSimplex)))
@testset "Fresh dual rows and bounded native reselection" begin
    include(joinpath(ROOT,"test/dual_fresh_row_tests.jl"))
    include(joinpath(ROOT,"test/native_dual_reprice_tests.jl"))
end

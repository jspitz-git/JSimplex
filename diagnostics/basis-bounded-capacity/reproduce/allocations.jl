using Test, JSimplex, SparseArrays, LinearAlgebra, Random
const ROOT=dirname(dirname(pathof(JSimplex)))
@testset "Bounded upper capacity allocation and public reset regressions" begin
    for file in ("factorization_tests.jl", "triangular_reset_allocation_tests.jl", "triangular_column_reuse_allocation_tests.jl",
                 "triangular_history_reuse_allocation_tests.jl", "basis_restore_allocation_tests.jl")
        println("TEST ",file);flush(stdout)
        include(joinpath(ROOT,"test",file))
    end
end

using Test, JSimplex, SparseArrays, LinearAlgebra, Random
const ROOT=dirname(dirname(pathof(JSimplex)))
const FILES=("triangular_capacity_tests.jl",
    "triangular_composed_rows_tests.jl", "triangular_active_upper_tests.jl",
    "triangular_prepared_spike_tests.jl", "triangular_selective_preparation_tests.jl",
    "triangular_incremental_metadata_tests.jl", "triangular_preparation_lifecycle_tests.jl",
    "triangular_row_spike_tests.jl",
    "stable_upper_indices_tests.jl", "refactorization_safety_tests.jl")
@testset "Bounded upper capacity semantic regressions" begin
    for file in FILES
        println("TEST ",file);flush(stdout)
        include(joinpath(ROOT,"test",file))
    end
end

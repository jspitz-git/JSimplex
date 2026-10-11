using JSimplex, Test, LinearAlgebra, SparseArrays
const TEST_ROOT=joinpath(@__DIR__,"../../../test")
# Split the known multi-type precision-recovery inference workload from normal
# allocation tests. Print each boundary even if a later compilation times out.
files = isempty(ARGS) ?
    ("simplex_state_validity_tests.jl", "dual_weight_validation_tests.jl",
     "native_residual_tests.jl", "primal_certificate_reuse_tests.jl",
     "dual_entry_phase_tests.jl") : Tuple(ARGS)
for file in files
    println("START ",file);flush(stdout)
    @testset "$file" begin
        include(joinpath(TEST_ROOT,file))
    end
    println("DONE ",file);flush(stdout)
end

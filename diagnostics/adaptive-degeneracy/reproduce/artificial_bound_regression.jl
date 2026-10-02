# Production-only replay, accepting saved boundary or first-rejection prefixes.
using Test,JSimplex,Serialization,LinearAlgebra
BLAS.set_num_threads(1)
@testset "Captured degen3 artificial-bound completion" begin
    for prefix in ARGS
        phase=deserialize(prefix*"-phase.bin");map=deserialize(prefix*"-map.bin")
        original=deserialize(prefix*"-original.bin")
        @test JSimplex._legacy_primal_point_certified(phase)
        @test maximum(abs,phase.primal[map.artificial_columns])>phase.options.primal_tolerance
        @test JSimplex.remove_artificials!(phase,map,original,phase.progress.numerical_policy,()->false)
        @test JSimplex._legacy_primal_point_certified(original)
        @test JSimplex._recomputed_basis_reliable(original)
        @test JSimplex._original_primal_feasible(original,original.primal[1:size(original.problem.A,2)])
        println("COMPLETED ",prefix," iteration=",original.iterations)
    end
end

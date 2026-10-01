# Production-only regression at a captured artificial-removal boundary.
using JSimplex,Serialization,LinearAlgebra,Test,TOML
BLAS.set_num_threads(1)
prefix,output=ARGS
phase=deserialize(prefix*"-phase.bin")
original=deserialize(prefix*"-original.bin")
mapping=deserialize(prefix*"-map.bin")
policy=phase.progress.numerical_policy
report=Dict{String,Any}()
@testset "Captured mod010 artificial removal" begin
    @test phase.iterations==324
    @test count(j->mapping.phase_to_original[j]==0,phase.basis.basic_indices)==1
    @test JSimplex._legacy_primal_point_certified(phase)
    accepted=JSimplex.remove_artificials!(phase,mapping,original,policy,()->false)
    report["accepted"]=accepted
    @test accepted
    if accepted
        @test original.iterations==325
        @test JSimplex._recomputed_basis_reliable(original)
        @test JSimplex._legacy_primal_point_certified(original)
        @test JSimplex._original_primal_feasible(original,original.primal[1:size(original.problem.A,2)])
        report["iterations"]=original.iterations
        report["original_primal_feasible"]=true
    end
end
open(output,"w") do io;TOML.print(io,report);end

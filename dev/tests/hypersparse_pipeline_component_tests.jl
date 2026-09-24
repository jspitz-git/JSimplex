using Test,JSimplex,SparseArrays
include("../simplex_pipeline_components.jl")

@testset "Bounded pipeline components and interruption" begin
    B = sparse([2.0 0 0;1 3 0;0 0 4])
    result = JSimplexPipelineComponents.probe(B)
    @test result["basis_dimension"] == 3
    @test !result["simplex_solve"] && !result["full_sized_factorization"]
    @test !result["interrupted"]
    @test length(result["methods"]) == 8
    @test all(m["reference_verified"] for m in result["methods"])
    @test all(length(m["profiles"]) == 8 for m in result["methods"])
    @test_throws ArgumentError JSimplexPipelineComponents.probe(spdiagm(0=>ones(33)))
    @test_throws ArgumentError JSimplexPipelineComponents.probe(sparse([Inf;;]))
    calls = Ref(0)
    stopped = JSimplexPipelineComponents.probe(B;stop=()->(calls[]+=1)>4)
    @test stopped["interrupted"]
    @test sum(length(m["profiles"]) for m in stopped["methods"];init=0) < 64
end

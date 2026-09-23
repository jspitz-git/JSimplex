using Test,JSimplex,SparseArrays
const FACTOR_COMPONENT_PATH = joinpath(@__DIR__,"..","simplex_factor_components.jl")
@testset "Bounded factor extraction selects occupied rows" begin
    @test isfile(FACTOR_COMPONENT_PATH)
    if isfile(FACTOR_COMPONENT_PATH)
        include(FACTOR_COMPONENT_PATH)
        A = sparse([900,901,902],[400,401,402],[2.0,-3.0,4.0],1000,1000)
        block,metadata = JSimplexFactorComponents.extract(A)
        @test size(block) == (3,3)
        @test nnz(block) == 3
        @test metadata["selected_rows"] == [900,901,902]
        @test metadata["selected_columns"] == [400,401,402]
        @test metadata["scanned_stored_entries"] == 3
        report = JSimplexFactorComponents.probe(block)
        @test !report["simplex_solve"]
        @test !report["full_sized_factorization"]
        @test report["basis_dimension"] == 3
        @test all(b["reference_verified"] for b in report["backends"])
        @test length(report["backends"]) == 2
        large = sparse(ones(300,300))
        block,metadata = JSimplexFactorComponents.extract(large)
        @test all(size(block) .<= 64)
        @test metadata["scanned_stored_entries"] <= 50000
        @test_throws ArgumentError JSimplexFactorComponents.probe(spzeros(65,65))
        @test JSimplexFactorComponents.probe(spzeros(0,0))["basis_dimension"] == 0
    end
end

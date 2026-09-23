using Test,JSimplex,SparseArrays
const UPDATE_COMPONENT_PATH = joinpath(@__DIR__,"..","simplex_update_components.jl")
@testset "Bounded update chains verify copies and refactor resets" begin
    @test isfile(UPDATE_COMPONENT_PATH)
    if isfile(UPDATE_COMPONENT_PATH)
        include(UPDATE_COMPONENT_PATH)
        for B in (spdiagm(0=>ones(4)),sparse([3.0 1;1 4]),spzeros(0,0))
            report = JSimplexUpdateComponents.probe(B)
            @test report["basis_dimension"] <= 32
            @test !report["simplex_solve"]
            @test !report["full_sized_factorization"]
            @test length(report["methods"]) == 8
            for method in report["methods"]
                @test method["reference_verified"]
                @test method["checkpoint_verified"]
                @test method["refactor_reset_verified"]
                @test method["cache_storage_bytes"] >= 0
            end
        end
        @test_throws ArgumentError JSimplexUpdateComponents.probe(spzeros(33,33))
        @test_throws DimensionMismatch JSimplexUpdateComponents.probe(spzeros(2,3))
        setprecision(BigFloat,24) do
            @test all(m["reference_verified"] for m in JSimplexUpdateComponents.probe(sparse([3.0 1;1 4]))["methods"])
            @test precision(BigFloat) == 24
        end
    end
end

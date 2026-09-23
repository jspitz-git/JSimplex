using Test, JSimplex, SparseArrays
const SPARSE_COMPONENT_PATH = joinpath(@__DIR__,"..","simplex_sparse_components.jl")
@testset "Bounded sparse component probe has no simplex workspace" begin
    @test isfile(SPARSE_COMPONENT_PATH)
    if isfile(SPARSE_COMPONENT_PATH)
        include(SPARSE_COMPONENT_PATH)
        for A in (sparse([1.0 -1.0;2.0 3.0]),spzeros(0,3),spzeros(3,0))
            report = JSimplexSparseComponents.probe(A)
            @test report["row_index_bytes"] >= 0
            @test report["row_index_seconds"] >= 0
            @test report["cancellation_verified"]
            @test length(report["pricing_profiles"]) == 3
            @test all(p["reference_verified"] for p in report["pricing_profiles"])
            @test all(p["seconds"] >= 0 && p["allocated_bytes"] >= 0 for p in report["pricing_profiles"])
        end
        @test_throws ArgumentError JSimplexSparseComponents.probe(spzeros(257,1))
        @test_throws ArgumentError JSimplexSparseComponents.probe(sparse(ones(256,256)))
    end
end

if !isdefined(Main,:JSimplexBenchmarks)
    include(joinpath(@__DIR__,"..","simplex_benchmarks.jl"))
end
using .JSimplexBenchmarks
using TOML
@testset "Stress CLI records sparse components and never solves excluded names" begin
    mktempdir() do root
        path,output = joinpath(root,"big.mps"),joinpath(root,"report.toml")
        write(path,"NAME COMPONENT\nROWS\n N COST\n E R1\nCOLUMNS\n X COST 1 R1 1\nRHS\n RHS1 R1 1\nENDATA\n")
        args=["--source="*normpath(joinpath(@__DIR__,"../..")),"--file="*path,
            "--mode=stress","--stress-operation=components","--time-limit=120",
            "--memory-limit-mib=4096","--read-limit-mib=1","--output="*output]
        @test JSimplexBenchmarks.benchmark_main(args) == 0
        report=TOML.parsefile(output)
        case=only(report["cases"])
        @test case["outcome"] == "component_completed"
        @test case["stage"] == "components"
        @test case["sparse_pricing"]["cancellation_verified"]
        @test !case["sparse_pricing"]["simplex_solve"]
        @test !case["sparse_pricing"]["full_sized_factorization"]
        @test !haskey(case,"samples")
        @test haskey(report["runner_sha256"],"simplex_sparse_components.jl")
        @test haskey(report["runner_sha256"],"simplex_factor_components.jl")
        @test haskey(report["runner_sha256"],"simplex_update_components.jl")
        @test haskey(case,"update_components")
        if haskey(case,"update_components")
            @test case["update_components"]["basis_dimension"] <= 32
            @test !case["update_components"]["full_sized_factorization"]
            @test !case["update_components"]["simplex_solve"]
            @test all(m["reference_verified"] && m["checkpoint_verified"] &&
                m["refactor_reset_verified"] for m in case["update_components"]["methods"])
        end
        @test haskey(case,"factor_components")
        if haskey(case,"factor_components")
            @test case["factor_components"]["basis_dimension"] <= 64
            @test !case["factor_components"]["full_sized_factorization"]
            @test !case["factor_components"]["simplex_solve"]
            @test all(b["reference_verified"] for b in case["factor_components"]["backends"])
        end
        write(path,"NAME OVERFLOW\nROWS\n N COST\n E R1\n E R2\nCOLUMNS\n X COST 1 R1 1e308\n X R2 1e308\nRHS\n RHS1 R1 1 R2 1\nENDATA\n")
        @test JSimplexBenchmarks.benchmark_main(args) == 1
        case=only(TOML.parsefile(output)["cases"])
        @test case["outcome"] == "component_error"
        @test !haskey(case,"samples")
    end
end

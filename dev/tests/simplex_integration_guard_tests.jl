module SimplexIntegrationGuardTests
using Test, TOML
include("../simplex_benchmarks.jl")
using .JSimplexBenchmarks

@testset "Excluded corpus hardlinks cannot enter solves or replays" begin
    mktempdir() do root
        excluded = joinpath(root,"big.mps")
        alias = joinpath(root,"ordinary.mps")
        write(excluded,"not a model")
        hardlink(excluded,alias)
        options=parse_benchmark_args(["--file="*alias,"--mps-root="*root])
        @test_throws ArgumentError JSimplexBenchmarks.select_cases(options)
        @test validate_selection(alias,"stress") == realpath(alias)
        snapshot=joinpath(root,"snapshot.bin")
        write(snapshot,"not a snapshot")
        open(snapshot*".toml","w") do io
            TOML.print(io,Dict("original_path"=>alias))
        end
        replay=parse_benchmark_args(["--replay="*snapshot,"--mps-root="*root])
        @test_throws ArgumentError JSimplexBenchmarks.select_cases(replay)
        ordinary=joinpath(root,"medium.mps")
        write(ordinary,"not a model")
        @test length(JSimplexBenchmarks.select_cases(parse_benchmark_args([
            "--file="*ordinary,"--mps-root="*root]))) == 1
    end
end
end

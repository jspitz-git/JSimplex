module RefactorizationPolicyTests
using Test, JSimplex, TOML
include("../simplex_replay.jl")
include("../simplex_benchmarks.jl")
using .JSimplexBenchmarks

@testset "Refactorization benchmarks select the basis update method" begin
    @test parse_benchmark_args(String[])["basis-update"] == "pfi"
    for method in ("pfi","forrest_tomlin","bartels_golub","suhl_suhl")
        @test parse_benchmark_args(["--basis-update="*method])["basis-update"] == method
    end
    @test_throws ArgumentError parse_benchmark_args(["--basis-update=unknown"])
    @test_throws ArgumentError parse_benchmark_args(["--basis-update=forrest_tomlin","--replay=unused.bin"])
    mktempdir() do root
        output = joinpath(root,"triangular.toml")
        config = joinpath(root,"policy.toml")
        write(config,"refactor_timing = false\n")
        input = joinpath(@__DIR__,"../../test/fixtures/solver/afiro.mps")
        @test benchmark_main(["--file="*input,"--samples=1","--algorithm=both",
            "--time-limit=30","--basis-update=forrest_tomlin","--kernel-timing=on",
            "--simplex-strategy=adaptive","--policy="*config,"--output="*output]) == 0
        result = only(TOML.parsefile(output)["cases"])
        for algorithm in ("primal","dual")
            @test result["solver_options_"*algorithm]["basis_update"] == "forrest_tomlin"
            @test result["numerical_policy_"*algorithm]["adaptive_refactor"]
            @test !result["numerical_policy_"*algorithm]["refactor_timing"]
        end
        @test all(s -> s["status"] == "OPTIMAL" && s["original_primal_certified"],result["samples"])
    end
end

@testset "Refactorization replay disables timing adaptation" begin
    mktempdir() do root
        p = LinearProblem(JSimplex.sparse([1.0;;]),[-1.0];row_upper=[1.0])
        policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive)
        options = SolverOptions(verbose=false,refactorization_interval=7)
        ws = JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        path = joinpath(root,"refactor.bin")
        JSimplexReplay.save_snapshot(path,ws;original_hash=repeat("a",64))
        restored,metadata = JSimplexReplay.load_snapshot(path)
        @test metadata["numerical_policy"]["refactor_timing"]
        @test restored.progress.numerical_policy.adaptive_refactor
        @test !restored.progress.numerical_policy.refactor_timing
        @test !restored.scratch.refactorization.timing_enabled
        @test restored.scratch.refactorization.initial_interval == 7
        @test restored.scratch.refactorization.factor_samples == 0
    end
end
end

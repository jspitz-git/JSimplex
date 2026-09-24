module SimplexPolicyTests
using Test, JSimplex, TOML
include("../simplex_benchmarks.jl")
include("../simplex_replay.jl")
using .JSimplexBenchmarks

@testset "Policy configuration is a read-only input" begin
    mktempdir() do root
        policy = joinpath(root,"policy.toml")
        contents = "max_refinements = 7\n"
        write(policy,contents)
        @test benchmark_main(["--file="*joinpath(root,"absent.mps"),
            "--policy="*policy,"--output="*policy]) == 1
        @test read(policy,String) == contents
    end
end

@testset "Numerical policy benchmark and replay configuration" begin
    @test parse_benchmark_args(["--simplex-strategy=adaptive"])["simplex-strategy"] == "adaptive"
    @test_throws ArgumentError parse_benchmark_args(["--simplex-strategy=unknown"])
    @test parse_benchmark_args(["--pricing=auto"])["pricing"] == "auto"
    @test_throws ArgumentError parse_benchmark_args(["--pricing=unknown"])
    @test_throws ArgumentError parse_benchmark_args(["--replay=snapshot.bin","--pricing=auto"])
    mktempdir() do root
        policy = JSimplex.NumericalPolicy(Float64; max_refinements=7,adaptive_dual_perturbation=true,adaptive_primal_perturbation=true,adaptive_pricing=true,partial_pricing=true,sparse_pricing=true,hypersparse=true,crash=true)
        problem = LinearProblem(JSimplex.sparse([1.0 1.0]), [1.0,2.0]; row_lower=[1.0])
        progress = JSimplex.SimplexProgressContext(problem; numerical_policy=policy)
        ws = JSimplex.initialize_workspace(problem,SolverOptions(verbose=false,pricing=:auto);progress)
        path = joinpath(root,"snapshot.bin")
        JSimplexReplay.save_snapshot(path,ws;original_hash=repeat("b",64))
        restored, metadata = JSimplexReplay.load_snapshot(path)
        @test restored.progress.numerical_policy.max_refinements == 7
        @test restored.progress.numerical_policy.adaptive_dual_perturbation
        @test restored.progress.numerical_policy.adaptive_primal_perturbation
        @test restored.progress.numerical_policy.adaptive_pricing
        @test restored.progress.numerical_policy.sparse_pricing
        @test restored.progress.numerical_policy.partial_pricing
        @test restored.progress.numerical_policy.hypersparse
        @test restored.progress.numerical_policy.crash
        @test restored.options.pricing == :auto
        @test metadata["numerical_policy"]["max_refinements"] == 7

        config = joinpath(root,"policy.toml")
        write(config,"max_refinements = 7\nadaptive_dual_perturbation = false\nadaptive_primal_perturbation = false\nadaptive_pricing = false\npartial_pricing = false\nsparse_pricing = false\n")
        output = joinpath(root,"report.toml")
        input = joinpath(@__DIR__,"../../test/fixtures/solver/afiro.mps")
        @test benchmark_main(["--file="*input,"--samples=1","--algorithm=dual",
            "--time-limit=30","--diagnostics=off","--simplex-strategy=adaptive","--pricing=auto",
            "--policy="*config,"--output="*output]) == 0
        result = only(TOML.parsefile(output)["cases"])
        @test result["solver_options_dual"]["simplex_strategy"] == "adaptive"
        @test result["solver_options_dual"]["pricing"] == "auto"
        @test result["numerical_policy_dual"]["max_refinements"] == 7
        @test result["numerical_policy_dual"]["stable_ratio"]
        @test result["numerical_policy_dual"]["pivot_validation"]
        @test result["numerical_policy_dual"]["solve_refinement"]
        @test result["numerical_policy_dual"]["recovery"]
        @test !result["numerical_policy_dual"]["adaptive_dual_perturbation"]
        @test !result["numerical_policy_dual"]["adaptive_primal_perturbation"]
        @test !result["numerical_policy_dual"]["adaptive_pricing"]
        @test !result["numerical_policy_dual"]["partial_pricing"]
        @test !result["numerical_policy_dual"]["sparse_pricing"]
        @test only(result["samples"])["status"] == "OPTIMAL"
        write(config,"unknown_switch = true\n")
        @test benchmark_main(["--policy="*config,"--output="*output]) == 1
        write(config,"hypersparse = true\n")
        @test benchmark_main(["--file="*input,"--policy="*config,
                             "--algorithm=dual","--samples=1","--time-limit=30",
                             "--output="*output]) == 0
        result = only(TOML.parsefile(output)["cases"])
        @test result["numerical_policy_dual"]["hypersparse"]
        @test only(result["samples"])["status"] == "OPTIMAL"
        write(config,"crash = true\n")
        @test benchmark_main(["--file="*input,"--policy="*config,
                             "--algorithm=primal","--samples=1","--time-limit=30",
                             "--kernel-timing=on","--output="*output]) == 0
        result = only(TOML.parsefile(output)["cases"])
        @test result["numerical_policy_primal"]["crash"]
        sample = only(result["samples"])
        @test sample["status"] == "OPTIMAL"
        @test haskey(sample["phase_seconds"],"phase_crash")
        @test haskey(sample["phase_iterations"],"phase_crash")
        @test sum(values(sample["phase_iterations"])) == sample["iterations"]
        write(config,"crash = false\n")
        phase_input = joinpath(@__DIR__,"../../test/fixtures/solver/generated/phase-one.mps")
        @test benchmark_main(["--file="*phase_input,"--policy="*config,
                             "--algorithm=primal","--presolve=off","--simplex-strategy=adaptive",
                             "--samples=1","--time-limit=30","--output="*output]) == 0
        phase_sample = only(only(TOML.parsefile(output)["cases"])["samples"])
        @test phase_sample["status"] == "OPTIMAL"
        @test phase_sample["iterations"] == 2
        @test phase_sample["phase_iterations"]["phase_one"] == 2
        @test sum(values(phase_sample["phase_iterations"])) == phase_sample["iterations"]
        write(config,"phase_one = true\ncrash = false\n")
        @test benchmark_main(["--file="*phase_input,"--policy="*config,
                             "--algorithm=primal","--presolve=off","--simplex-strategy=adaptive",
                             "--samples=1","--time-limit=30","--output="*output]) == 0
        modern = only(TOML.parsefile(output)["cases"])
        @test modern["numerical_policy_primal"]["phase_one"]
        modern_sample = only(modern["samples"])
        @test modern_sample["status"] == "OPTIMAL"
        @test modern_sample["phase_iterations"]["phase_one"] == 2
        @test sum(values(modern_sample["phase_iterations"])) == modern_sample["iterations"]
        write(config,"precision_boosting = true\n")
        @test benchmark_main(["--file="*input,"--policy="*config,"--output="*output]) == 1
    end
end
end

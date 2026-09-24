module SimplexPrecisionBenchmarkTests
using Test, JSimplex, TOML
include("../simplex_benchmarks.jl")
using .JSimplexBenchmarks

@testset "Precision benchmark metadata and diagnostics" begin
    @test parse_benchmark_args(["--scaling=off"])["scaling"] == "off"
    @test_throws ArgumentError parse_benchmark_args(["--scaling=unknown"])
    @test_throws ArgumentError parse_benchmark_args(["--replay=stored.bin", "--scaling=off"])
    @testset "Stored dual precision survives diagnostic evaluation" begin
        p = LinearProblem(JSimplex.sparse([1.0;;]), [1.0]; row_lower=[1.0])
        dual = setprecision(BigFloat, 600) do
            [BigFloat(1)+BigFloat(2)^(-500)]
        end
        errors = JSimplexBenchmarks.original_dual_errors(p, [1.0], dual)
        @test errors["dual_sign_error"] > 0
        @test get(errors, "dual_error_evaluation_bits", 0) >= 600
    end
    @testset "CLI records actual precision independently of input precision" begin
        mktempdir() do root
            input = joinpath(root, "precision.mps")
            write(input, """
NAME          PRECISION
ROWS
 N  COST
 E  BALANCE
COLUMNS
    X1        COST      1             BALANCE   1E308
    X2        BALANCE   -1E308
RHS
    RHS1      BALANCE   0
BOUNDS
 FX BND1      X1        2
 FX BND1      X2        2
ENDATA
""")
            policy = joinpath(root, "policy.toml")
            write(policy, "precision_boosting = true\nrefactor_timing = false\n")
            output = joinpath(root, "result.toml")
            code = benchmark_main(["--file="*input, "--policy="*policy, "--output="*output,
                "--samples=1", "--algorithm=dual", "--presolve=off", "--scaling=off",
                "--simplex-strategy=adaptive", "--time-limit=60"])
            @test code == 0
            if isfile(output)
                record = only(TOML.parsefile(output)["cases"])
                sample = only(record["samples"])
                @test record["precision_bits"] == 53
                @test record["solver_options_dual"]["scaling"] == "off"
                @test sample["status"] == "OPTIMAL"
                @test sample["original_primal_certified"]
                @test get(sample, "working_precision_available", false)
                @test get(sample, "working_precision_levels", Int[]) == [53, 128]
                @test get(sample, "working_precision_bits", 0) == 128
                @test sample["events"]["precision_boost"] == 1
                @test sample["dual_error_available"]
            end
        end
    end
end
end

module PrimalUpdateBenchmarkTests
using Test, TOML
include("../simplex_benchmarks.jl")
using .JSimplexBenchmarks

@testset "Boxed benchmarks can exercise simplex without presolve" begin
    parsed = try
        parse_benchmark_args(["--presolve=off"])
    catch e
        e
    end
    @test parsed isa Dict
    @test_throws ArgumentError parse_benchmark_args(["--presolve=unknown"])
    if parsed isa Dict
        mktempdir() do root
            input = joinpath(root, "boxed.mps")
            output = joinpath(root, "result.toml")
            write(input, """
            NAME BOXED
            ROWS
             N OBJ
             L R1
            COLUMNS
             X1 OBJ -1 R1 1
             X2 OBJ -1 R1 1
            RHS
             RHS1 R1 3
            BOUNDS
             UP BND1 X1 1
             UP BND1 X2 1
            ENDATA
            """)
            @test benchmark_main(["--file="*input, "--samples=1", "--algorithm=primal",
                "--time-limit=30", "--presolve=off", "--simplex-strategy=adaptive",
                "--output="*output]) == 0
            case = only(TOML.parsefile(output)["cases"])
            @test !case["solver_options_primal"]["presolve"]
            sample = only(case["samples"])
            @test sample["status"] == "OPTIMAL"
            @test sample["objective"] == -2.0
            @test sample["original_primal_certified"]
            @test sample["iterations"] == 2
            @test sample["events"]["flip_completed"] == 2
        end
    end
end
end

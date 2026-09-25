module SimplexScalingDiagnosticTests
using Test, TOML
include("../simplex_benchmarks.jl")
using .JSimplexBenchmarks

@testset "Scaled benchmark witnesses map to the original objective and rows" begin
    mktempdir() do root
        for (sense,cx,cy,objective) in (("MIN",-4,-1,3.0),("MAX",4,1,11.0))
            # The first row bounds 4*x+y by 4, attained at x=1, y=0.
            # The zero starting point is feasible, so primal needs no augmented
            # Phase I model. Scaling divides rows by 8 and 16, and column two by 1/4;
            # both row and cost checks must invert
            # these factors before accepting a mapped original-model witness.
            input=joinpath(root,"scaled-"*sense*".mps")
            write(input,"NAME SCALED\nOBJSENSE\n $sense\nROWS\n N COST\n L R1\n L R2\nCOLUMNS\n X COST $cx R1 8\n X R2 16\n Y COST $cy R1 2\n Y R2 0.5\nRHS\n RHS COST -7 R1 8\n RHS R2 16\nENDATA\n")
            output=joinpath(root,"report-"*sense*".toml")
            @test benchmark_main(["--file="*input,"--output="*output,
                "--algorithm=both","--samples=1","--time-limit=60",
                "--presolve=off","--scaling=on","--diagnostics=on"])==0
            samples=only(TOML.parsefile(output)["cases"])["samples"]
            @test length(samples)==2
            for sample in samples
                @test sample["status"]=="OPTIMAL"
                @test sample["objective"]==objective
                @test sample["original_primal_certified"]
                @test sample["dual_error_available"]
                if sample["dual_error_available"]
                    @test sample["primal_error"] <= 1e-10
                    @test sample["dual_sign_error"] <= 1e-10
                    @test sample["complementarity_error"] <= 1e-10
                end
            end
        end
    end
end
end

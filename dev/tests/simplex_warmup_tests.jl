module SimplexWarmupTests
using Test, TOML
include("../simplex_benchmarks.jl")
using .JSimplexBenchmarks

@testset "Benchmark warmups execute observers without contaminating samples" begin
    mktempdir() do root
        input=joinpath(@__DIR__,"..","..","test","fixtures","solver","generated","degenerate-box.mps")
        for diagnostics in ("off","on")
            output=joinpath(root,"report-"*diagnostics*".toml")
            @test benchmark_main(["--file="*input,"--output="*output,
                "--algorithm=dual","--samples=2","--time-limit=30",
                "--presolve=off","--diagnostics="*diagnostics]) == 0
            result=only(TOML.parsefile(output)["cases"])
            warmups=get(result,"warmups",[])
            @test length(warmups)==2
            @test length(result["samples"])==2
            for warmup in warmups
                @test warmup["status"]=="OPTIMAL"
                @test warmup["time_limit_seconds"]==30.0
                @test warmup["iterations"]==first(result["samples"])["iterations"]
                if diagnostics=="on"
                    @test warmup["observer_seconds"] > 0
                    @test sum(values(warmup["phase_iterations"]))==warmup["iterations"]
                    @test warmup["events"]["certification"] > 0
                end
            end
            if diagnostics=="on"
                samples=result["samples"]
                @test samples[1]["events"]==samples[2]["events"]
                @test samples[1]["phase_iterations"]==samples[2]["phase_iterations"]
                @test all(sum(values(s["phase_iterations"]))==s["iterations"] for s in samples)
                @test all(s["working_precision_levels"]==[53] for s in samples)
            end
        end
    end
end
end

include("profile-prefix.jl")
using Test
@testset "Reports preserve nonoptimal results without an objective" begin
    mktempdir() do dir
        for objective in (nothing, 1.5)
            report = Dict{String,Any}("status" => isnothing(objective) ? "TIME_LIMIT" : "OPTIMAL",
                "iterations" => 42, "samples" => [Dict("iteration" => 40, "seconds" => 3.0)])
            output = joinpath(dir, "report.toml")
            write_report(output, report, objective)
            @test TOML.parsefile(output) == report
            @test deserialize(output * ".report.bin") == report
            @test haskey(report, "objective") == !isnothing(objective)
        end
    end
end

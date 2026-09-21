using Test
include(joinpath(@__DIR__, "..", "allocations.jl"))
using .JSimplexAllocations

@testset "Allocation measurements exclude setup and reset mutable inputs" begin
    observed = Int[]
    result = measure_allocations(
        state -> (push!(observed, length(state)); pop!(state));
        setup=() -> zeros(100_000), samples=3,
    )
    @test all(==(100_000), observed)
    @test result["bytes"] < 10_000
    @test result["samples"] == 3
    @test result["seconds"] >= 0
    @test_throws ArgumentError measure_allocations(identity; samples=0)
end

@testset "Allocation profiles retain measured sites" begin
    audit = JSimplexAllocations
    sink = Ref{Any}(nothing)
    profile = audit.allocation_profile(_ -> (sink[] = zeros(1024)), () -> nothing;
                                       sample_rate=1.0)
    @test sum(site["sampled_bytes"] for site in profile) >= 8192
    @test sum(site["sampled_allocations"] for site in profile) > 0
    @test isempty(audit.Profile.Allocs.fetch().allocs)
    @test_throws ArgumentError audit.allocation_profile(identity, () -> nothing; sample_rate=0)
end

@testset "Allocation audit covers the solver pipeline" begin
    path = joinpath(@__DIR__, "..", "..", "test", "fixtures", "solver", "afiro.mps")
    audit = JSimplexAllocations
    source = audit.moi_source(audit.read_mps(path))
    translated = audit.JSimplex._translate_moi_model(audit.JSimplex.Optimizer(), source)
    translated_solution = audit.solve(translated.problem; options=audit.SolverOptions(verbose=false))
    @test translated_solution.status == audit.OPTIMAL
    @test translated_solution.objective_value ≈ -464.7531428571429
    report = audit_dataset(path; samples=1)
    stages = Dict(row["stage"] => row for row in report)
    @test all(haskey(stages, name) for name in (
        "read_mps", "moi_translation", "presolve", "scaling", "initialize",
        "recompute", "refactorize", "forward_solve", "transpose_solve",
        "postsolve", "solve_dual", "solve_primal", "solve_dual_no_presolve",
        "solve_primal_no_presolve"))
    for name in ("solve_dual", "solve_primal", "solve_dual_no_presolve", "solve_primal_no_presolve")
        @test stages[name]["status"] == "OPTIMAL"
        @test stages[name]["objective"] ≈ -464.7531428571429
    end
    @test all(row["bytes"] >= 0 && row["allocations"] >= 0 for row in report)
    mktemp() do output, io
        close(io)
        @test allocation_main(["afiro", "--samples=1", "--output=$output"]; io=devnull) == 0
        saved = JSimplexAllocations.TOML.parsefile(output)
        @test saved["julia_version"] == string(VERSION)
        @test saved["datasets"]["afiro"][1]["stage"] == "read_mps"
    end
    @test_throws ArgumentError allocation_main(["--samples=0"]; io=devnull)
    @test_throws ArgumentError allocation_main(["--unknown"]; io=devnull)
    @test_throws ArgumentError audit_dataset(path; samples=1, profile="absent")
end

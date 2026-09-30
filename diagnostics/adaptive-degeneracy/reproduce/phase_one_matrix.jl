# Run all four policies sequentially in one guarded process.
include(joinpath(@__DIR__, "phase_one_models.jl"))
length(ARGS) == 4 || error("Expected: model algorithm seconds output-directory")
model, algorithm, seconds, output_directory = ARGS
mkpath(output_directory)
for variant in ("none", "perturb", "pricing", "both")
    println("CASE ", model, " ", algorithm, " ", variant); flush(stdout)
    main([model, algorithm, variant, seconds,
          joinpath(output_directory, model * "-" * algorithm * "-" * variant * ".toml")])
    GC.gc()
end

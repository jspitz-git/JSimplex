# Opt-in only: julia --project=dev dev/benchmarks.jl [DATASET]
using BenchmarkTools
using JSimplex
include("datasets.jl")

function benchmark_main(args=ARGS)
    length(args) <= 1 || throw(ArgumentError("Usage: julia --project=dev dev/benchmarks.jl [DATASET]"))
    name = isempty(args) ? "afiro" : only(args)
    manifest = load_dataset_manifest(joinpath(@__DIR__, "datasets.toml"))
    path = resolve_dataset(manifest, name; repository_root=normpath(joinpath(@__DIR__, "..")))
    problem = read_mps(path)
    println("Benchmarking LP relaxation: $name")
    trial = @benchmark solve($problem; relax_integrality=true)
    show(stdout, MIME("text/plain"), trial)
    println()
    return trial
end

if abspath(PROGRAM_FILE) == @__FILE__
    benchmark_main()
end

# Run from the repository root; baseline replacement affects this process only.
using JSimplex, Logging, TOML
include(joinpath(pwd(), "dev", "allocations.jl"))
using .JSimplexAllocations: measure_allocations
mode = ARGS[1]
mode in ("before", "after") || throw(ArgumentError("mode must be before or after"))
if mode == "before"
    source = read(joinpath(pwd(), "src", "triangular_factorization.jl"), String)
    start = findfirst("function refactorize!(factor::AbstractTriangularBasisFactorization", source)
    finish = findnext("function copy_basis_factorization", source, last(start))
    current = source[first(start):prevind(source, first(finish))]
    baseline = replace(current, "_reset_identity_upper!(factor.upper, n)" =>
                                "factor.upper = _identity_upper(T, n)")
    baseline != current || error("reset call not found; review the baseline probe")
    Base.include_string(JSimplex, baseline, "before-triangular-reset-refactorize.jl")
end
rows = Dict{String,Any}[]
with_logger(NullLogger()) do
    for (name, path) in (("afiro", "test/fixtures/solver/afiro.mps"),
                         ("adlittle", "test/fixtures/solver/netlib/adlittle.mps"))
        p = read_mps(path)
        for method in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub), algorithm in (:dual, :primal), interval in (1,20)
            options = SolverOptions(; basis_update=method, algorithm, refactorization_interval=interval,
                                    presolve=false, scaling=:off, verbose=false, iteration_limit=10_000)
            run = _ -> solve(p; options)
            result = measure_allocations(run; samples=3)
            solution = run(nothing)
            result["refactorizations"] = solution.statistics.refactorizations
            merge!(result, Dict("dataset"=>name, "basis_update"=>string(method),
                "algorithm"=>string(algorithm), "refactorization_interval"=>interval))
            push!(rows, result)
        end
        println(name, " measured")
        flush(stdout)
    end
end
report = Dict("mode"=>mode, "julia_version"=>string(VERSION), "machine"=>Sys.MACHINE,
              "threads"=>Threads.nthreads(), "presolve"=>false, "scaling"=>"off", "rows"=>rows)
open(io -> TOML.print(io, report; sorted=true), ARGS[2], "w")

# Run from the repository root; baseline replacement affects this process only.
using JSimplex, Logging, TOML, SparseArrays, LinearAlgebra
include(joinpath(pwd(), "dev", "allocations.jl"))
using .JSimplexAllocations: measure_allocations
mode = ARGS[1]
mode in ("before", "after") || throw(ArgumentError("mode must be before or after"))
if mode == "before"
    source = read(joinpath(pwd(), "src", "factorization.jl"), String)
    start = findfirst("function replace_column!(", source)
    finish = findnext("function _refactorize_backend(backend::UMFPACKBackend", source, last(start))
    current = source[first(start):prevind(source, first(finish))]
    reuse_start = findfirst("    if !isempty(factor.recycled_updates)", current)
    reuse_end = findnext("    elseif tableau_column isa AbstractVector{T}", current, last(reuse_start))
    baseline = current[1:prevind(current, first(reuse_start))] *
        "    if tableau_column isa AbstractVector{T}" * current[nextind(current, last(reuse_end)):end]
    Base.include_string(JSimplex, baseline, "before-pfi-history-reuse.jl")
    Base.include_string(JSimplex, """
        function _recycle_pfi_updates!(factor::PFIFactorization)
            empty!(factor.updates)
            factor.shared_update_count = 0
            return nothing
        end
    """, "before-pfi-history-retirement.jl")
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
kernels = Dict{String,Any}[]
with_logger(NullLogger()) do
    for backend in (:native, :markowitz), n in (64, 512), count in (1, 20)
        B = spdiagm(0 => ones(n))
        column = ones(n)
        batch = f -> begin
            for _ in 1:count
                JSimplex.replace_column!(f, column, 1)
            end
            nothing
        end
        setup = () -> begin
            f = JSimplex.PFIFactorization(B, Val(backend))
            batch(f)
            JSimplex.refactorize!(f, B)
            f
        end
        result = measure_allocations(batch; setup, samples=3)
        merge!(result, Dict("dimension"=>n, "basis_refactorization"=>string(backend),
                            "updates"=>count))
        push!(kernels, result)
    end
end
report = Dict("mode"=>mode, "julia_version"=>string(VERSION), "machine"=>Sys.MACHINE,
              "threads"=>Threads.nthreads(), "presolve"=>false, "scaling"=>"off", "rows"=>rows, "kernels"=>kernels)
open(io -> TOML.print(io, report; sorted=true), ARGS[2], "w")

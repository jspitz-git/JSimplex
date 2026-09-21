# Run from the repository root; baseline replacement affects this process only.
using JSimplex, Logging, TOML, SparseArrays
include(joinpath(pwd(), "dev", "allocations.jl"))
using .JSimplexAllocations: measure_allocations
mode = ARGS[1]
mode in ("before", "after") || throw(ArgumentError("mode must be before or after"))
if mode == "before"
    source = read(joinpath(pwd(), "src", "simplex.jl"), String)
    for (start_marker, end_marker, current_call, previous_call) in (
        ("function recompute!(", "function initialize_workspace(",
         "B = _basis_matrix!(workspace)", "B = basis_matrix(workspace)"),
        ("function initialize_workspace(", "function primal_infeasibility_summary(",
         "    scratch.basis_matrix = initial_basis\n", ""))
        start = findfirst(start_marker, source)
        finish = findnext(end_marker, source, last(start))
        current = source[first(start):prevind(source, first(finish))]
        baseline = replace(current, current_call => previous_call)
        baseline != current || error("reuse call not found; review the baseline probe")
        Base.include_string(JSimplex, baseline, "before-basis-assembly-reuse.jl")
    end
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
    for n in (64, 512, 4096), method in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
        A = spdiagm(-1 => fill(-1.0, n-1), 0 => fill(4.0, n), 1 => fill(-1.0, n-1))
        p = LinearProblem(A, zeros(n); row_lower=zeros(n))
        options = SolverOptions(; basis_update=method, verbose=false)
        setup = () -> begin
            w = JSimplex.initialize_workspace(p, options)
            w.basis = JSimplex.Basis(collect(1:n), vcat(fill(JSimplex.BASIC, n), fill(JSimplex.AT_LOWER, n)))
            JSimplex.recompute!(w; refactorize=true)
            w
        end
        for (stage, run) in (("refactorize", w -> (JSimplex.recompute!(w; refactorize=true); nothing)),
                             ("assembly", w -> (mode == "before" ? JSimplex.basis_matrix(w) : JSimplex._basis_matrix!(w); nothing)))
            result = measure_allocations(run; setup, samples=3)
            merge!(result, Dict("dimension"=>n, "basis_update"=>string(method), "stage"=>stage))
            push!(kernels, result)
        end
    end
end
report = Dict("mode"=>mode, "julia_version"=>string(VERSION), "machine"=>Sys.MACHINE,
              "threads"=>Threads.nthreads(), "presolve"=>false, "scaling"=>"off", "rows"=>rows, "kernels"=>kernels)
open(io -> TOML.print(io, report; sorted=true), ARGS[2], "w")

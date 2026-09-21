# Run from the repository root; baseline replacement affects this process only.
using JSimplex, Logging, TOML, SparseArrays, LinearAlgebra
include(joinpath(pwd(), "dev", "allocations.jl"))
using .JSimplexAllocations: measure_allocations
mode = ARGS[1]
mode in ("before", "after") || throw(ArgumentError("mode must be before or after"))
if mode == "before"
    Base.include_string(JSimplex, """
        function _take_triangular_update_buffers!(factor::Union{ForrestTomlinFactorization{T},SuhlSuhlFactorization{T}}) where {T}
            return Int[], T[]
        end
        function _take_bartels_golub_steps!(factor::BartelsGolubFactorization{T}) where {T}
            return BartelsGolubStep{T}[]
        end
        function _recycle_triangular_updates!(factor::AbstractTriangularBasisFactorization)
            empty!(factor.updates)
            factor.shared_update_count = 0
            return nothing
        end
    """, "before-triangular-history-reuse.jl")
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
function varied_batch!(f, column, count)
    n = length(column)
    for step in 1:count
        row = mod1(step, n)
        fill!(column, 0.0)
        column[row] = 1.0
        column[mod1(row + 1, n)] = 0.25
        JSimplex.replace_column!(f, column, row)
    end
    return nothing
end
kernels = Dict{String,Any}[]
with_logger(NullLogger()) do
    for backend in (:native, :markowitz), (n, count) in ((4, 16), (64, 64)),
        (method, Factor) in ((:forrest_tomlin, JSimplex.ForrestTomlinFactorization),
                            (:suhl_suhl, JSimplex.SuhlSuhlFactorization),
                            (:bartels_golub, JSimplex.BartelsGolubFactorization))
        B = spdiagm(0 => ones(n))
        column = zeros(n)
        setup = () -> begin
            f = Factor(B, Val(backend))
            for _ in 1:3
                varied_batch!(f, column, count)
                JSimplex.refactorize!(f, B)
            end
            f
        end
        result = measure_allocations(f -> varied_batch!(f, column, count); setup, samples=3)
        merge!(result, Dict("dimension"=>n, "basis_refactorization"=>string(backend),
                            "updates"=>count, "basis_update"=>string(method)))
        push!(kernels, result)
    end
end
report = Dict("mode"=>mode, "julia_version"=>string(VERSION), "machine"=>Sys.MACHINE,
              "threads"=>Threads.nthreads(), "presolve"=>false, "scaling"=>"off", "rows"=>rows, "kernels"=>kernels)
open(io -> TOML.print(io, report; sorted=true), ARGS[2], "w")

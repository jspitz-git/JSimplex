# Run from the repository root; baseline replacement affects this process only.
using JSimplex, Logging, TOML, SparseArrays, LinearAlgebra
include(joinpath(pwd(), "dev", "allocations.jl"))
using .JSimplexAllocations: measure_allocations
mode = ARGS[1]
mode in ("before", "after") || throw(ArgumentError("mode must be before or after"))
if mode == "before"
    # Keep the new ownership container in both modes, but rebuild LU from scratch.
    Base.include_string(JSimplex, """
        function _refactorize_backend(backend::UMFPACKBackend, B::AbstractMatrix{Float64})
            sparse_basis = convert(SparseMatrixCSC{Float64,Int}, B)
            rows, columns = size(sparse_basis)
            rows == columns || throw(DimensionMismatch("basis matrix must be square"))
            candidate = iszero(rows) ? nothing : lu(sparse_basis)
            backend.factorization = candidate
            backend.dimension = rows
            backend.spare = nothing
            backend.shared = false
            return backend
        end
    """, "before-umfpack-storage-reuse.jl")
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
    for n in (64, 512, 4096), pattern in ("same", "changed"),
        method in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
        A = spdiagm(-1 => fill(-1.0, n-1), 0 => fill(4.0, n), 1 => fill(-1.0, n-1))
        B = copy(A)
        if pattern == "same"
            B.nzval .*= 2
        else
            B[1, n] = 0.25
        end
        setup = () -> begin
            f = JSimplex._basis_factorization(A, Val(method))
            JSimplex.refactorize!(f, A)
            JSimplex.refactorize!(f, A)
            f
        end
        result = measure_allocations(f -> (JSimplex.refactorize!(f, B); nothing); setup, samples=3)
        merge!(result, Dict("dimension"=>n, "pattern"=>pattern, "basis_update"=>string(method)))
        push!(kernels, result)
    end
end
report = Dict("mode"=>mode, "julia_version"=>string(VERSION), "machine"=>Sys.MACHINE,
              "threads"=>Threads.nthreads(), "presolve"=>false, "scaling"=>"off", "rows"=>rows, "kernels"=>kernels)
open(io -> TOML.print(io, report; sorted=true), ARGS[2], "w")

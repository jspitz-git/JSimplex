# Reproduction probe; the allocating baseline overrides one method in this process.
using JSimplex, Logging, TOML, SparseArrays, LinearAlgebra
include(joinpath(pwd(), "dev", "allocations.jl"))
using .JSimplexAllocations: measure_allocations
mode = ARGS[1]
mode in ("before", "after") || throw(ArgumentError("mode must be before or after"))
BLAS.set_num_threads(1)
if mode == "before"
    Base.include_string(JSimplex, """
        function _refactorize_backend(backend::Float32LUBackend, B::AbstractMatrix{Float32})
            rows, columns = size(B)
            rows == columns || throw(DimensionMismatch("basis matrix must be square"))
            candidate = lu!(Matrix{Float32}(B))
            backend.factorization = candidate
            backend.spare = candidate
            backend.has_spare = false
            backend.shared = false
            return backend
        end
    """, "before-float32-lu-reuse.jl")
end
rows = Dict{String,Any}[]
kernels = Dict{String,Any}[]
with_logger(NullLogger()) do
    problems = [("afiro", read_mps("test/fixtures/solver/afiro.mps"; value_type=Float32)),
                ("adlittle", read_mps("test/fixtures/solver/netlib/adlittle.mps"; value_type=Float32)),
                ("diagonal64", LinearProblem(spdiagm(0 => ones(Float32,64)), ones(Float32,64);
                                             row_lower=ones(Float32,64)))]
    for (name, problem) in problems
        for method in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub),
            algorithm in (:dual, :primal), interval in (1,20)
            options = SolverOptions(Float32; basis_update=method, algorithm,
                refactorization_interval=interval, presolve=false, scaling=:off,
                verbose=false, iteration_limit=10_000)
            run = _ -> solve(problem; options)
            row = measure_allocations(run; samples=3)
            solution = run(nothing)
            merge!(row, Dict("dataset"=>name, "basis_update"=>string(method),
                "algorithm"=>string(algorithm), "refactorization_interval"=>interval,
                "refactorizations"=>solution.statistics.refactorizations))
            push!(rows,row)
        end
        println(name, " measured"); flush(stdout)
    end
    for n in (64,512,1024), method in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        B=spdiagm(-1=>fill(-1f0,n-1),0=>fill(4f0,n),1=>fill(-1f0,n-1))
        setup=()->begin
            f=JSimplex._basis_factorization(B,Val(method))
            JSimplex.refactorize!(f,B)
            JSimplex.refactorize!(f,B)
            f
        end
        result=measure_allocations(f->(JSimplex.refactorize!(f,B);nothing);setup,samples=3)
        merge!(result,Dict("dimension"=>n,"basis_update"=>string(method)))
        push!(kernels,result)
    end
end
report=Dict("mode"=>mode,"julia_version"=>string(VERSION),"machine"=>Sys.MACHINE,
    "threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
    "value_type"=>"Float32","presolve"=>false,"scaling"=>"off","rows"=>rows,"kernels"=>kernels)
open(io->TOML.print(io,report;sorted=true),ARGS[2],"w")

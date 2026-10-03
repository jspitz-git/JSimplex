using TOML, SHA
root = normpath(joinpath(@__DIR__, "../../.."))
function source_digest()
    paths = ["Project.toml"]
    for (dir, _, files) in walkdir(joinpath(root, "src")), file in files
        endswith(file, ".jl") && push!(paths, relpath(joinpath(dir, file), root))
    end
    bytes = UInt8[]
    for path in sort!(paths)
        append!(bytes, codeunits(path * "\0"))
        append!(bytes, read(joinpath(root, path)))
    end
    return bytes2hex(sha256(bytes))
end
cached_before_load = Base.isprecompiled(Base.identify_package("JSimplex"); ignore_loaded=true)
@assert cached_before_load
loading = @timed @eval using JSimplex, SparseArrays
@assert realpath(dirname(dirname(pathof(JSimplex)))) == realpath(root)
precompile_tools = parentmodule(getfield(JSimplex, Symbol("@compile_workload")))
@assert precompile_tools.workload_enabled(JSimplex)
samples = Dict{String,Any}[]
for T in (Float64, Float32), algorithm in (:primal, :dual),
    update in (:pfi, :bartels_golub, :forrest_tomlin, :suhl_suhl, :huangfu_hall),
    backend in (:native,)
    update === :huangfu_hall && !(T === Float64 && backend === :native && Int === Int64) && continue
    # Different input coefficients and update interval from the precompile workload.
    p = LinearProblem(sparse(T[1 1; -1 1]), T[1, 3]; row_lower=T[4, 2], column_lower=T[0, 1])
    o = SolverOptions(T; algorithm, basis_update=update, basis_refactorization=backend,
        presolve=false, verbose=false, refactorization_interval=20)
    sample = @timed solve(p; options=o)
    r = sample.value
    @assert r.status == OPTIMAL
    @assert isapprox(r.objective_value, T(10); rtol=T(1e-5))
    @assert JSimplex._original_primal_feasible(p, r.primal, o.primal_tolerance)
    push!(samples, Dict("type"=>string(T), "algorithm"=>string(algorithm),
        "update"=>string(update), "backend"=>string(backend), "seconds"=>sample.time,
        "compile_seconds"=>sample.compile_time, "objective"=>Float64(r.objective_value)))
    println(last(samples)); flush(stdout)
end
backend_samples = Dict{String,Any}[]
for T in (Float64, Float32)
    matrices = (spdiagm(0 => T[3, 4, 5]), sparse(T[5 2 1; 1 6 2; 2 1 7]))
    expected = T[2, -1, 3]
    destination = zeros(T, 3)
    for (i, matrix) in enumerate(matrices)
        construction = @timed JSimplex._factorize_basis(matrix, Val(:markowitz))
        backend = construction.value
        @assert (backend.sparse_pivots > 0) == (i == 1)
        rhs = matrix * expected
        forward = @timed JSimplex._backend_forward_solve!(destination, backend, rhs)
        @assert destination ≈ expected
        rhs = transpose(matrix) * expected
        transposed = @timed JSimplex._backend_transpose_solve!(destination, backend, rhs)
        @assert destination ≈ expected
        replacement = matrices[3 - i]
        refactor = @timed JSimplex._refactorize_backend(backend, replacement)
        backend = refactor.value
        JSimplex._backend_forward_solve!(destination, backend, replacement * expected)
        @assert destination ≈ expected
        JSimplex._backend_transpose_solve!(destination, backend, transpose(replacement) * expected)
        @assert destination ≈ expected
        push!(backend_samples, Dict("type"=>string(T), "form"=>(i == 1 ? "sparse" : "dense"),
            "verified"=>true, "operations"=>[Dict("operation"=>name, "seconds"=>measurement.time,
                "compile_seconds"=>measurement.compile_time) for (name, measurement) in
                (("construct",construction), ("forward",forward), ("transpose",transposed), ("refactor",refactor))]))
        println(last(backend_samples)); flush(stdout)
    end
end
open(ARGS[1], "w") do io
    TOML.print(io, Dict("load_seconds"=>loading.time, "samples"=>samples, "backend_samples"=>backend_samples, "julia"=>string(VERSION),
        "debug_level"=>Int(Base.JLOptions().debug_level), "opt_level"=>Int(Base.JLOptions().opt_level),
        "cached_before_load"=>cached_before_load, "source_sha256"=>source_digest(),
        "harness_sha256"=>bytes2hex(sha256(read(@__FILE__))),
        "cache_builder_sha256"=>bytes2hex(sha256(read(joinpath(@__DIR__, "build-cache.jl")))),
        "environment_sha256"=>Dict(name=>bytes2hex(sha256(read(joinpath(dirname(Base.active_project()), name))))
            for name in ("Project.toml", "Manifest.toml", "LocalPreferences.toml")),
        "julia_threads"=>Threads.nthreads(),
        "precompile_workers"=>get(ENV, "JULIA_NUM_PRECOMPILE_TASKS", ""),
        "image_threads"=>get(ENV, "JULIA_IMAGE_THREADS", ""),
        "measurement"=>"Sequential configurations in one fresh process; earlier compilation is shared"))
end

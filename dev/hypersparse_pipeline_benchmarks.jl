module HypersparsePipelineBenchmarks
using JSimplex,SparseArrays,LinearAlgebra,TOML,SHA
include("hypersparse_update_benchmarks.jl")

function prepare(B,method,backend,enabled)
    n = size(B,1)
    p = LinearProblem(B,zeros(n))
    policy = JSimplex.NumericalPolicy(Float64;hypersparse=enabled)
    options = SolverOptions(verbose=false,basis_update=method,basis_refactorization=backend)
    ws = JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    ws.basis = JSimplex.Basis(collect(1:n),vcat(fill(JSimplex.BASIC,n),fill(JSimplex.FREE_NONBASIC,n)))
    JSimplex.recompute!(ws;refactorize=true)
    return ws
end

function pipeline!(ws,indices,mode)
    buffer = JSimplex._pipeline_rhs_buffer!(ws)
    for i in indices
        JSimplex._set_pipeline_rhs!(buffer,i,1.0)
    end
    rhs = JSimplex._pipeline_rhs_values(buffer)
    JSimplex._pipeline_basis_solve!(ws.scratch.rho,ws,rhs;transposed=true,kernel_mode=mode)
    JSimplex._pipeline_price!(ws.scratch.tableau_row,ws,ws.scratch.rho;kernel_mode=mode)
    JSimplex._pipeline_basis_solve!(ws.scratch.row_solution,ws,rhs;kernel_mode=mode)
    return nothing
end

function measure!(ws,indices,mode)
    for _ in 1:100
        pipeline!(ws,indices,mode)
    end
end

function benchmark()
    BLAS.set_num_threads(1)
    B = HypersparseUpdateBenchmarks.HypersparseFactorBenchmarks.fixture()
    n = size(B,1)
    profiles = Dict{String,Any}[]
    for method in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),backend in (:native,:markowitz),
        (label,enabled,mode) in (("baseline",false,:auto),("sparse",true,:sparse),("auto",true,:auto))
        # Warm compilation independently; measured setup always owns a fresh basis.
        warm = prepare(B,method,backend,enabled)
        pipeline!(warm,[1],mode)
        setup = @timed prepare(B,method,backend,enabled)
        ws = setup.value
        first = @timed pipeline!(ws,[1],mode)
        copied = @timed JSimplex._candidate_workspace(ws)
        for k in (1,16,n)
            indices = k == n ? collect(1:n) : collect(1:16:16k)
            rhs = zeros(n); rhs[indices] .= 1.0
            expected_forward,expected_transpose = B\rhs,transpose(B)\rhs
            expected_price = vcat(transpose(B)*expected_transpose,-expected_transpose)
            measure!(ws,indices,mode)
            @assert isapprox(ws.scratch.row_solution,expected_forward;rtol=512eps(Float64),atol=512eps(Float64))
            @assert isapprox(ws.scratch.rho,expected_transpose;rtol=512eps(Float64),atol=512eps(Float64))
            @assert isapprox(ws.scratch.tableau_row,expected_price;rtol=512eps(Float64),atol=512eps(Float64))
            samples = Dict{String,Any}[]
            for _ in 1:7
                measured = @timed measure!(ws,indices,mode)
                push!(samples,Dict("seconds_per_pipeline"=>measured.time/100,
                    "allocated_bytes_per_pipeline"=>measured.bytes/100))
            end
            cache = ws.scratch.hypersparse
            push!(profiles,Dict("basis_update"=>string(method),"backend"=>string(backend),
                "path"=>label,"rhs_support"=>k,"samples"=>samples,"reference_verified"=>true,
                "setup_seconds"=>setup.time,"setup_allocated_bytes"=>setup.bytes,
                "first_pipeline_seconds"=>first.time,"first_pipeline_allocated_bytes"=>first.bytes,
                "candidate_copy_seconds"=>copied.time,"candidate_copy_allocated_bytes"=>copied.bytes,
                "factor_storage_entries"=>JSimplex._factor_storage_count(ws.factorization),
                "factor_cache_bytes"=>Base.summarysize(ws.factorization.sparse),
                "pipeline_reachable_bytes"=>Base.summarysize(cache),
                "support_rebuilds"=>isnothing(cache) ? 0 : cache.support_rebuilds))
        end
    end
    return Dict("fixture"=>Dict("dimension"=>n,"nonzeros"=>nnz(B),
        "sha256"=>HypersparseUpdateBenchmarks.matrix_digest(B)),
        "runner_sha256"=>Dict(name=>bytes2hex(sha256(read(joinpath(@__DIR__,name))))
            for name in ("hypersparse_pipeline_benchmarks.jl","hypersparse_update_benchmarks.jl",
                         "hypersparse_factor_benchmarks.jl","simplex_benchmarks.jl")),
        "profiles"=>profiles,"calls_per_sample"=>100,"samples_per_profile"=>7,
        "scope"=>"RHS assembly, BTRAN, pricing, FTRAN on a fixed basis; not a complete simplex iteration")
end

if abspath(PROGRAM_FILE) == @__FILE__
    length(ARGS) == 1 || error("Usage: julia --project=dev dev/hypersparse_pipeline_benchmarks.jl OUTPUT.toml")
    include("simplex_benchmarks.jl")
    result = benchmark()
    result["source"] = JSimplexBenchmarks.source_identity(dirname(@__DIR__))
    open(io->TOML.print(io,result;sorted=true),only(ARGS),"w")
end
end

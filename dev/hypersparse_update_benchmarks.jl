module HypersparseUpdateBenchmarks
using JSimplex,SparseArrays,LinearAlgebra,TOML,SHA
include("hypersparse_factor_benchmarks.jl")

function history(n,restored)
    updates = Tuple{Int,Vector{Float64}}[]
    pivots = [1,17,33,49]
    for pivot in pivots
        values = zeros(n); values[pivot] = 2.0; values[pivot+1] = 0.25
        push!(updates,(pivot,values))
    end
    if restored
        for pivot in reverse(pivots)
            values = zeros(n); values[pivot] = 0.5; values[pivot+1] = -0.125
            push!(updates,(pivot,values))
        end
    end
    return updates
end

function prepare(Factor,B0,backend,updates)
    built = @timed Factor(B0,backend)
    factor = built.value
    update_seconds,update_bytes = 0.0,0
    for (pivot,tableau) in updates
        measured = @timed JSimplex.replace_column!(factor,tableau,pivot)
        update_seconds += measured.time; update_bytes += measured.bytes
    end
    cached = @timed begin
        cache = JSimplex._sparse_basis_workspace!(factor)
        JSimplex._sparse_base_view!(cache,factor)
        factor isa JSimplex.AbstractTriangularBasisFactorization && JSimplex._sparse_upper!(cache,factor)
    end
    rhs,dest = JSimplex.IndexedVector{Float64}(size(B0,1)),JSimplex.IndexedVector{Float64}(size(B0,1))
    JSimplex.set_entry!(rhs,1,1.0)
    first_solve = @timed JSimplex.forward_solve!(dest,factor,rhs;kernel_mode=:sparse)
    copied = @timed JSimplex.copy_basis_factorization(factor)
    return factor,Dict("factor_seconds"=>built.time,"factor_allocated_bytes"=>built.bytes,
        "updates_seconds"=>update_seconds,"updates_allocated_bytes"=>update_bytes,
        "cache_seconds"=>cached.time,"cache_allocated_bytes"=>cached.bytes,
        "first_indexed_solve_seconds"=>first_solve.time,"first_indexed_solve_allocated_bytes"=>first_solve.bytes,
        "copy_seconds"=>copied.time,"copy_allocated_bytes"=>copied.bytes)
end

function run_path!(path,dense,out,factor,rhs,values,transposed)
    if path == "dense"
        if transposed
            JSimplex.transpose_solve!(dense,factor,values)
        else
            JSimplex.forward_solve!(dense,factor,values)
        end
        return dense
    end
    path == "indexed_materialized" && JSimplex.load_indexed!(rhs,values)
    mode = path == "auto" ? :auto : :sparse
    if transposed
        JSimplex.transpose_solve!(out,factor,rhs;kernel_mode=mode)
    else
        JSimplex.forward_solve!(out,factor,rhs;kernel_mode=mode)
    end
    path == "indexed_materialized" && copyto!(dense,out.values)
    return out.values
end

function matrix_digest(B)
    io = IOBuffer()
    write(io,Int64(size(B,1)),Int64(size(B,2)),Int64.(B.colptr),Int64.(B.rowval),B.nzval)
    return bytes2hex(sha256(take!(io)))
end

function benchmark()
    BLAS.set_num_threads(1)
    B0 = HypersparseFactorBenchmarks.fixture()
    methods = Dict{String,Any}[]
    report = Dict{String,Any}("source"=>HypersparseFactorBenchmarks.JSimplexBenchmarks.source_identity(dirname(dirname(pathof(JSimplex)))),
        "script_sha256"=>bytes2hex(open(sha256,@__FILE__)),
        "fixture_script_sha256"=>bytes2hex(open(sha256,joinpath(@__DIR__,"hypersparse_factor_benchmarks.jl"))),
        "initial_matrix_sha256"=>matrix_digest(B0),"matrix_byte_order"=>string(Base.ENDIAN_BOM),
        "rows"=>1024,"initial_nonzeros"=>nnz(B0),"blas_threads"=>BLAS.get_num_threads(),
        "samples_per_profile"=>7,"repetitions_per_sample"=>100,
        "recipe"=>"F17 permuted disconnected 16x16 blocks; tableau pivots 1,17,33,49 have diagonal 2 and next entry 1/4; restored stage appends reverse inverse tableaus (1/2,-1/8)",
        "auto_dense_occupancy_threshold"=>0.5,"simplex_solve"=>false,"external_model_factorization"=>false)
    for (name,Factor) in (("pfi",JSimplex.PFIFactorization),
                         ("forrest_tomlin",JSimplex.ForrestTomlinFactorization),
                         ("suhl_suhl",JSimplex.SuhlSuhlFactorization),
                         ("bartels_golub",JSimplex.BartelsGolubFactorization)),
        backend in (:native,:markowitz), restored in (false,true)
        updates = history(1024,restored)
        B = copy(B0)
        for (pivot,tableau) in updates
            B[:,pivot] = B*tableau
        end
        restored && @assert B == B0
        prepare(Factor,B0,Val(backend),updates)
        prepared = [prepare(Factor,B0,Val(backend),updates) for _ in 1:7]
        factor = first(last(prepared))
        rhs,out = JSimplex.IndexedVector{Float64}(1024),JSimplex.IndexedVector{Float64}(1024)
        dense = zeros(1024)
        reference_factor = lu(B)
        profiles = Dict{String,Any}[]
        for step in (1024,64,1), transposed in (false,true)
            values = zeros(1024); values[1:step:1024] .= 1.0
            JSimplex.load_indexed!(rhs,values)
            reference = transposed ? transpose(reference_factor) \ values : reference_factor \ values
            paths = ("dense","indexed","auto","indexed_materialized")
            for path in paths
                observed = run_path!(path,dense,out,factor,rhs,values,transposed)
                @assert isapprox(observed,reference;atol=256eps(Float64),rtol=256eps(Float64))
            end
            samples = Dict{String,Any}[]
            for sample in 1:7, offset in 0:3
                path = paths[mod(sample+offset-1,4)+1]
                measured = @timed for _ in 1:100
                    run_path!(path,dense,out,factor,rhs,values,transposed)
                end
                observed = path == "dense" ? dense : out.values
                @assert isapprox(observed,reference;atol=256eps(Float64),rtol=256eps(Float64))
                push!(samples,Dict("path"=>path,"sample"=>sample,"seconds"=>measured.time/100,
                    "allocated_bytes"=>measured.bytes/100,"gc_seconds"=>measured.gctime/100))
            end
            push!(profiles,Dict("rhs_support"=>count(!iszero,values),"result_support"=>count(!iszero,reference),
                "transposed"=>transposed,"reference_verified"=>true,"samples"=>samples))
        end
        push!(methods,Dict("basis_update"=>name,"backend"=>string(backend),
            "stage"=>restored ? "restored" : "grown","updates"=>length(updates),
            "matrix_sha256"=>matrix_digest(B),"nonzeros"=>nnz(B),
            "setup_samples"=>[last(v) for v in prepared],"profiles"=>profiles,
            "cache_storage_bytes"=>Base.summarysize(factor.sparse),
            "factor_storage_entries"=>JSimplex._factor_storage_count(factor),
            "base_builds"=>factor.sparse.base_builds,"upper_rebuilds"=>factor.sparse.upper_rebuilds,
            "dense_fallbacks"=>factor.sparse.dense_fallbacks))
    end
    report["methods"] = methods
    return report
end
end

if abspath(PROGRAM_FILE) == @__FILE__
    length(ARGS) == 1 || error("Usage: julia --project=dev dev/hypersparse_update_benchmarks.jl OUTPUT.toml")
    report = HypersparseUpdateBenchmarks.benchmark()
    open(ARGS[1],"w") do io
        HypersparseUpdateBenchmarks.TOML.print(io,report;sorted=true)
    end
end

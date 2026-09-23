# Opt-in base-factor measurements; no simplex workspace or complete LP solve.
module HypersparseFactorBenchmarks
using JSimplex,SparseArrays,LinearAlgebra,TOML,SHA
include("simplex_benchmarks.jl")

function fixture()
    n,blocksize = 1024,16
    ii,jj,vv = Int[],Int[],Float64[]
    for i in 1:n
        push!(ii,i); push!(jj,i); push!(vv,4.0)
        if mod(i,blocksize) != 0
            push!(ii,i+1); push!(jj,i); push!(vv,-1.0)
            push!(ii,i); push!(jj,i+1); push!(vv,1.0)
        end
    end
    return sparse(ii,jj,vv,n,n)[vcat(2:n,1),n:-1:1]
end

function run_path!(path,dense,indexed,view,backend,rhs,values,transposed)
    if path == "dense"
        if transposed
            JSimplex._backend_transpose_solve!(dense,backend,values)
        else
            JSimplex._backend_forward_solve!(dense,backend,values)
        end
        return dense
    end
    path == "indexed_materialized" && JSimplex.load_indexed!(rhs,values)
    if transposed
        JSimplex.hypersparse_transpose_solve!(indexed,view,rhs)
    else
        JSimplex.hypersparse_forward_solve!(indexed,view,rhs)
    end
    path == "indexed_materialized" && copyto!(dense,indexed.values)
    return indexed.values
end

function benchmark()
    BLAS.set_num_threads(1)
    B = fixture()
    identity = IOBuffer()
    write(identity,Int64(size(B,1)),Int64(size(B,2)),Int64.(B.colptr),Int64.(B.rowval),B.nzval)
    report = Dict{String,Any}("source"=>JSimplexBenchmarks.source_identity(dirname(dirname(pathof(JSimplex)))),
        "script_sha256"=>bytes2hex(open(sha256,@__FILE__)),"matrix_sha256"=>bytes2hex(sha256(take!(identity))),
        "matrix_byte_order"=>string(Base.ENDIAN_BOM),"rows"=>1024,"nonzeros"=>nnz(B),
        "recipe"=>"1024x1024, disconnected 16x16 tridiagonal blocks (-1,4,1), rows [2:1024;1], columns 1024:-1:1",
        "blas_threads"=>BLAS.get_num_threads(),"samples_per_profile"=>7,"repetitions_per_sample"=>100,
        "simplex_solve"=>false,"external_model_factorization"=>false)
    backends = Dict{String,Any}[]
    for kind in (:native,:markowitz)
        JSimplex.sparse_solve_view(JSimplex._factorize_basis(B,Val(kind)))
        builds = [@timed(JSimplex._factorize_basis(B,Val(kind))) for _ in 1:7]
        backend = last(builds).value
        views = [@timed(JSimplex.sparse_solve_view(backend)) for _ in 1:7]
        view = last(views).value
        isnothing(view) && error("The fixed fixture did not produce a sparse solve view")
        rhs,out = JSimplex.IndexedVector{Float64}(1024),JSimplex.IndexedVector{Float64}(1024)
        dense = zeros(1024)
        profiles = Dict{String,Any}[]
        for step in (1024,64,1), transposed in (false,true)
            values = zeros(1024); values[1:step:1024] .= 1.0
            JSimplex.load_indexed!(rhs,values)
            matrix = transposed ? transpose(B) : B
            reference = matrix \ values
            paths = ("dense","indexed","indexed_materialized")
            for path in paths
                observed = run_path!(path,dense,out,view,backend,rhs,values,transposed)
                @assert isapprox(observed,reference;atol=128eps(Float64),rtol=128eps(Float64))
            end
            samples = Dict{String,Any}[]
            for sample in 1:7, offset in 0:2
                path = paths[mod(sample+offset-1,3)+1]
                measured = @timed for _ in 1:100
                    run_path!(path,dense,out,view,backend,rhs,values,transposed)
                end
                observed = path == "dense" ? dense : out.values
                @assert isapprox(observed,reference;atol=128eps(Float64),rtol=128eps(Float64))
                push!(samples,Dict("path"=>path,"sample"=>sample,"seconds"=>measured.time/100,
                    "allocated_bytes"=>measured.bytes/100,"gc_seconds"=>measured.gctime/100))
            end
            push!(profiles,Dict("rhs_support"=>count(!iszero,values),"result_support"=>count(!iszero,reference),
                "transposed"=>transposed,"reference_verified"=>true,"samples"=>samples))
        end
        push!(backends,Dict("backend"=>string(kind),
            "fresh_lu"=>[Dict("seconds"=>v.time,"allocated_bytes"=>v.bytes) for v in builds],
            "adapter_builds"=>[Dict("seconds"=>v.time,"allocated_bytes"=>v.bytes) for v in views],
            "adapter_storage_bytes"=>Base.summarysize(view),"base_storage_entries"=>JSimplex._backend_storage_count(backend),
            "profiles"=>profiles))
    end
    report["backends"] = backends
    return report
end
end

if abspath(PROGRAM_FILE) == @__FILE__
    length(ARGS) == 1 || error("Usage: julia --project=dev dev/hypersparse_factor_benchmarks.jl OUTPUT.toml")
    report = HypersparseFactorBenchmarks.benchmark()
    open(ARGS[1],"w") do io
        HypersparseFactorBenchmarks.TOML.print(io,report;sorted=true)
    end
end

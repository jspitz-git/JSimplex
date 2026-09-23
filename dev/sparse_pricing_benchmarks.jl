# Standalone component measurements; no factorization and no simplex solve.
module SparsePricingBenchmarks
using JSimplex, SparseArrays, TOML, SHA, LinearAlgebra
include("simplex_benchmarks.jl")

function fixture()
    m,n = 1024,2048
    rows,columns,values = Int[],Int[],Float64[]
    for column in 1:n, k in 1:8
        push!(rows,mod(97column+53k,m)+1)
        push!(columns,column)
        push!(values,(-1.0)^(column+k)*2.0^mod(k,4))
    end
    return sparse(rows,columns,values,m,n)
end

function row_call!(dense,A,values,rho,out,rows,ordered)
    JSimplex.load_indexed!(rho,values)
    JSimplex.sparse_price!(out,A,rho,rows;ordered_rows=ordered)
    copyto!(dense,out.values)
    return nothing
end

function benchmark()
    BLAS.set_num_threads(1)
    A = fixture()
    @assert size(A)==(1024,2048) && nnz(A)==16384
    source=dirname(dirname(pathof(JSimplex)))
    identity=IOBuffer()
    write(identity,Int64(size(A,1)),Int64(size(A,2)),Int64.(A.colptr),Int64.(A.rowval),A.nzval)
    matrix_hash=bytes2hex(sha256(take!(identity)))
    report=Dict{String,Any}("source"=>JSimplexBenchmarks.source_identity(source),
        "script_sha256"=>bytes2hex(open(sha256,@__FILE__)),
        "recipe"=>"1024x2048; k=1:8 per column j; row=mod(97j+53k,1024)+1; value=(-1)^(j+k)*2^mod(k,4)",
        "matrix_sha256"=>matrix_hash,"matrix_byte_order"=>string(Base.ENDIAN_BOM),
        "rows"=>1024,"columns"=>2048,"nonzeros"=>nnz(A),"repetitions_per_sample"=>100,
        "samples_per_profile"=>7,"blas_threads"=>BLAS.get_num_threads(),
        "full_sized_factorization"=>false,"simplex_solve"=>false)
    JSimplex.RowAccess(A)
    builds=[@timed(JSimplex.RowAccess(A)) for _ in 1:7]
    report["index_builds"]=[Dict("seconds"=>v.time,"allocated_bytes"=>v.bytes) for v in builds]
    rows=last(builds).value
    report["index_array_bytes"]=sizeof(rows.rowptr)+sizeof(rows.columns)+sizeof(rows.positions)
    rho,out=JSimplex.IndexedVector{Float64}(1024),JSimplex.IndexedVector{Float64}(3072)
    ordered=Int[]
    dense=zeros(3072)
    profiles=Dict{String,Any}[]
    for (name,step) in (("unit",1024),("sparse16",64),("dense",1))
        values=zeros(1024)
        for i in 1:step:1024
            values[i]=isodd(i) ? 1.0 : -1.0
        end
        reference=vcat(transpose(A)*values,-values)
        row_call!(dense,A,values,rho,out,rows,ordered)
        @assert dense==reference
        JSimplex._csc_price!(dense,A,values)
        @assert dense==reference
        samples=Dict{String,Any}[]
        # Alternate order to reduce a systematic first-path timing bias.
        for sample in 1:7, path in (isodd(sample) ? ("csc","indexed") : ("indexed","csc"))
            measured = if path=="csc"
                @timed for _ in 1:100
                    JSimplex._csc_price!(dense,A,values)
                end
            else
                @timed for _ in 1:100
                    row_call!(dense,A,values,rho,out,rows,ordered)
                end
            end
            @assert dense==reference
            push!(samples,Dict("path"=>path,"sample"=>sample,"seconds"=>measured.time/100,
                "allocated_bytes"=>measured.bytes/100,"gc_seconds"=>measured.gctime/100))
        end
        push!(profiles,Dict("name"=>name,"rhs_support"=>count(!iszero,values),
            "result_support"=>count(!iszero,reference),"reference_verified"=>true,"samples"=>samples))
    end
    report["profiles"]=profiles
    return report
end
end

if abspath(PROGRAM_FILE)==@__FILE__
    length(ARGS)==1 || error("Usage: julia --project=dev dev/sparse_pricing_benchmarks.jl OUTPUT.toml")
    report=SparsePricingBenchmarks.benchmark()
    open(ARGS[1],"w") do io
        SparsePricingBenchmarks.TOML.print(io,report;sorted=true)
    end
end

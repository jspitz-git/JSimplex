using JSimplex, SparseArrays, Statistics, TOML, Random, Test
include_string(Main, first(split(read(joinpath(@__DIR__, "../../../test/csc_pricing_performance_tests.jl"),String), "@testset")))

function candidate_price!(out::Vector{T}, A::SparseMatrixCSC{T,Int}, rho::Vector{T}) where T
    m,n=size(A)
    length(rho)>=m || throw(DimensionMismatch("pricing row multiplier dimensions"))
    length(out)>=m+n || throw(DimensionMismatch("pricing output dimensions"))
    @inbounds for j in 1:n
        value=zero(T)
        for p in A.colptr[j]:(A.colptr[j+1]-1)
            value += rho[A.rowval[p]] * A.nzval[p]
        end
        out[j]=value
    end
    @inbounds for i in 1:m
        out[n+i]=-rho[i]
    end
    nothing
end

function sample(f,out,A,rho,repetitions)
    f(out,A,rho)
    GC.gc()
    @timed for _ in 1:repetitions
        f(out,A,rho)
    end
end

function benchmark(output)
    cases=Dict{String,Any}[]
    for name in ("fast0507","runtime"), T in (Float32,Float64)
        A=SparseMatrixCSC{T,Int}(read_mps("/home/jspitz/mps/"*name*".mps").A)
        m,n=size(A)
        rho=rand(MersenneTwister(19),T,m)
        out=zeros(T,m+n); expected=similar(out)
        reference_csc_price!(expected,A,rho)
        candidate_price!(out,A,rho)
        @assert isequal(out,expected)
        JSimplex._csc_price!(out,A,rho)
        @assert isequal(out,expected)
        samples=Dict(label=>Dict{String,Any}[] for label in ("reference","candidate","production"))
        for round in 1:7
            entries=(("reference",reference_csc_price!),("candidate",candidate_price!),
                     ("production",JSimplex._csc_price!))
            for (label,f) in (isodd(round) ? entries : reverse(entries))
                t=sample(f,out,A,rho,200)
                push!(samples[label],Dict("seconds"=>t.time,"bytes"=>t.bytes,"compile_seconds"=>t.compile_time))
            end
        end
        push!(cases,Dict("input"=>name,"type"=>string(T),"rows"=>m,"columns"=>n,
            "nonzeros"=>nnz(A),"calls_per_sample"=>200,"samples"=>samples))
        println(name," ",T," ",Dict(k=>median(x["seconds"] for x in v) for (k,v) in samples));flush(stdout)
    end
    open(output,"w") do io; TOML.print(io,Dict("cases"=>cases)); end
end
benchmark(only(ARGS))

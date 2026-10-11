using JSimplex,LinearAlgebra,SparseArrays,TOML,SHA
const JS=JSimplex
include(joinpath(@__DIR__,"hh_triplet_reference.jl"))
function fixture(n,dense)
    B=spdiagm(0=>fill(Float64(n+2),n))
    for j in 1:n,i in 1:n
        if i!=j && (dense || abs(i-j)==1)
            B[i,j]=Float64(mod(3i+5j,7)-3)/16
        end
    end
    B
end
function sample(F,::Val{R},count) where R
    w=JS.HHExtractWorkspace()
    GC.gc(true)
    @timed for i in 1:count
        R ? original_markowitz_parts(F,w) : JS._hh_extract_parts(F,w)
    end
end
function exact(F)
    a=original_markowitz_parts(F,JS.HHExtractWorkspace())
    b=JS._hh_extract_parts(F,JS.HHExtractWorkspace())
    @assert all(isequal(x,y) for (x,y) in zip(a,b))
    for i in (1,2)
        @assert isequal(a[i].colptr,b[i].colptr)
        @assert isequal(a[i].rowval,b[i].rowval)
        @assert isequal(a[i].nzval,b[i].nzval)
    end
end
function main(output)
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    cases=Tuple{String,typeof(JS.MarkowitzBackend(fixture(8,true)))}[]
    for n in (64,256)
        for dense in (false,true)
            push!(cases,((dense ? "dense" : "sparse")*string(n),JS.MarkowitzBackend(fixture(n,dense))))
        end
        # A valid dense-core representation with few nonzeros stresses counting
        # cost without changing the backend's normal production selection rule.
        F=JS.MarkowitzBackend(fixture(n,true))
        F.core=lu(Matrix{Float64}(I,n,n))
        push!(cases,("mostly_zero_core"*string(n),F))
    end
    push!(cases,("mixed64",JS.MarkowitzBackend(blockdiag(fixture(32,false),fixture(32,true)))))
    rows=Dict[];meta=Dict[]
    out=Dict("source"=>dirname(pathof(JS)),"scope"=>"Markowitz HH extraction only; reference frozen before exact triplet allocation",
        "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
        "pairs"=>6,"calls_per_sample"=>16,"samples"=>rows,"fixtures"=>meta)
    save()=open(io->TOML.print(io,out),output,"w")
    for (name,F) in cases
        exact(F)
        push!(meta,Dict("case"=>name,"dimension"=>F.dimension,"sparse_pivots"=>F.sparse_pivots,
            "core_dimension"=>size(F.core.factors,1),"core_nonzeros"=>count(!iszero,F.core.factors)))
        sample(F,Val(true),16);sample(F,Val(false),16)
        for pair in 1:6,reference in (isodd(pair) ? (true,false) : (false,true))
            t=sample(F,Val(reference),16)
            push!(rows,Dict("case"=>name,"pair"=>pair,"side"=>reference ? "baseline" : "candidate",
                "seconds"=>t.time,"compile_seconds"=>t.compile_time,"gc_seconds"=>t.gctime,
                "bytes"=>t.bytes,"allocations"=>Base.gc_alloc_count(t.gcstats)))
            save();@assert t.compile_time==0
        end
        exact(F)
    end
    @assert length(rows)==84
    out["complete"]=true;save()
    println("Triplet cost passed: 84 samples, exact outputs, compile0")
end
Base.invokelatest(main,ARGS[1])

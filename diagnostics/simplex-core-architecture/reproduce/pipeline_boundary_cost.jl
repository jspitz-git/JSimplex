# Compare the unchanged whole-Vector kernel with its frozen pre-fix body.
# This is invalidation work only: no basis solve, rebuild, or whole-solver claim.
using JSimplex, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
@assert Threads.nthreads()==BLAS.get_num_threads()==1
const OUTPUT=only(ARGS)
const REPETITIONS=200000
function baseline_changed!(ws,values)::Nothing
    cache = ws.scratch.hypersparse
    isnothing(cache) && return nothing
    i = JS._pipeline_buffer_index(cache,values)
    i > 0 && (cache.valid[i] = false)
    return nothing
end
# Both paths cross the same barrier so repeated stores cannot be hoisted away.
Base.@noinline touch!(f,ws,values)=f(ws,values)
function batch!(f,ws,first,second,n)
    for i in 1:n
        touch!(f,ws,isodd(i) ? first : second)
    end
    nothing
end
function fixture(T,kind,cached)
    n=kind==:sparse ? 512 : 64
    A=kind==:sparse ? spdiagm(0=>ones(T,n)) : sparse(Matrix{T}(I,n,n) .+ T(1//100))
    p=JS.LinearProblem(A,zeros(T,n);row_lower=zeros(T,n))
    options=JS.SolverOptions(T;verbose=false)
    ws=JS.initialize_workspace(p,options)
    for values in (ws.scratch.rho,ws.scratch.tableau_row)
        fill!(values,kind==:dense ? one(T) : zero(T));values[1]=one(T)
    end
    cached && JS._hypersparse_workspace!(ws)
    return ws
end
function measure!(f,ws,first,second)
    GC.gc(true)
    m=@timed batch!(f,ws,first,second,REPETITIONS)
    Dict{String,Any}("seconds"=>m.time,"bytes"=>m.bytes,"allocations"=>Base.gc_alloc_count(m.gcstats),
         "compile_seconds"=>m.compile_time,"gc_seconds"=>m.gctime)
end
function main()
    rows=Dict[]
    for T in (Float32,Float64),kind in (:sparse,:dense),cached in (false,true)
        ws=fixture(T,kind,cached)
        @assert cached == !isnothing(ws.scratch.hypersparse)
        first,second=ws.scratch.rho,ws.scratch.tableau_row
        for f in (baseline_changed!,JS._pipeline_changed!)
            batch!(f,ws,first,second,REPETITIONS)
        end
        for pair in 1:6
            order=isodd(pair) ? (("baseline",baseline_changed!),("current",JS._pipeline_changed!)) :
                (("current",JS._pipeline_changed!),("baseline",baseline_changed!))
            for (variant,f) in order
                row=measure!(f,ws,first,second)
                merge!(row,Dict("type"=>string(T),"fixture"=>string(kind),"cached"=>cached,
                    "pair"=>pair,"variant"=>variant,"calls"=>REPETITIONS,"path"=>"whole_vector"))
                push!(rows,row)
            end
        end
        # The new conservative alias path is characterized separately, never
        # compared with the incorrect old view path as a claimed speedup.
        a,b=view(first,:),view(second,:)
        batch!(JS._pipeline_changed!,ws,a,b,REPETITIONS)
        for pair in 1:3
            row=measure!(JS._pipeline_changed!,ws,a,b)
            merge!(row,Dict("type"=>string(T),"fixture"=>string(kind),"cached"=>cached,
                "pair"=>pair,"variant"=>"current","calls"=>REPETITIONS,"path"=>"view"))
            push!(rows,row)
        end
    end
    root=dirname(dirname(pathof(JS)))
    hashes=Dict(f=>bytes2hex(sha256(read(joinpath(root,f)))) for f in
        ("src/hypersparse_pipeline.jl","src/lp_refinement_driver.jl"))
    open(io->TOML.print(io,Dict("samples"=>rows,"source_sha256"=>hashes,
        "semantics"=>"warm invalidation only; paired whole Vector; separate view characterization")),OUTPUT,"w")
    println("Saved ",length(rows)," warm invalidation samples")
end
main()

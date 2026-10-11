using JSimplex,SparseArrays,LinearAlgebra,TOML
const JS=JSimplex
@assert Threads.nthreads()==BLAS.get_num_threads()==1
const N=200000
noop!(ws,v)=nothing
Base.@noinline generic_barrier!(f,ws,v)=f(ws,v)
Base.@noinline specialized_barrier!(f::F,ws::W,v::V) where {F,W,V}=f(ws,v)
function generic_batch!(f,ws,a,b)
    for i in 1:N
        generic_barrier!(f,ws,isodd(i) ? a : b)
    end
end
function specialized_batch!(f::F,ws::W,a::V,b::V) where {F,W,V}
    for i in 1:N
        specialized_barrier!(f,ws,isodd(i) ? a : b)
    end
end
function direct_batch!(f::F,ws::W,a::V,b::V) where {F,W,V}
    for i in 1:N
        f(ws,isodd(i) ? a : b)
    end
end
function direct_single!(ws,a)
    JS._pipeline_changed!(ws,a)
end
function main()
    rows=Dict[]
    for T in (Float32,Float64),cached in (false,true)
        p=JS.LinearProblem(spdiagm(0=>ones(T,32)),zeros(T,32))
        ws=JS.initialize_workspace(p,JS.SolverOptions(T;verbose=false))
        cached && JS._hypersparse_workspace!(ws)
        @assert cached == !isnothing(ws.scratch.hypersparse)
        a,b=view(ws.scratch.rho,:),view(ws.scratch.tableau_row,:)
        for (name,batch) in (("generic",generic_batch!),("specialized",specialized_batch!),("direct",direct_batch!)),
            (label,f) in (("noop",noop!),("invalidate",JS._pipeline_changed!))
            batch(f,ws,a,b)
            GC.gc(true)
            m=@timed batch(f,ws,a,b)
            push!(rows,Dict("type"=>string(T),"cached"=>cached,"barrier"=>name,"function"=>label,
                "calls"=>N,"bytes"=>m.bytes,"allocations"=>Base.gc_alloc_count(m.gcstats),"compile_seconds"=>m.compile_time))
        end
        direct_single!(ws,a)
        m=@timed direct_single!(ws,a)
        push!(rows,Dict("type"=>string(T),"cached"=>cached,"barrier"=>"direct_single","function"=>"invalidate",
            "calls"=>1,"bytes"=>m.bytes,"allocations"=>Base.gc_alloc_count(m.gcstats),"compile_seconds"=>m.compile_time))
    end
    open(io->TOML.print(io,Dict("samples"=>rows)),only(ARGS),"w")
    for row in rows;println(row);end
end
main()

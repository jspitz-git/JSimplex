using JSimplex, Serialization, LinearAlgebra, SparseArrays, TOML
const JS=JSimplex
function mem(stage)
    status=read("/proc/self/status",String)
    println(stage," rss_kib=",match(r"VmRSS:\s+(\d+)",status).captures[1]," vm_kib=",match(r"VmSize:\s+(\d+)",status).captures[1]," live=",Base.gc_live_bytes());flush(stdout)
end
function main()
    d=deserialize(ARGS[1]);p=d.problem;x=d.target_primal;t=d.options.primal_tolerance
    lo,hi=JS._primal_row_bounds(p.A,x,JS._is_exact(Float64))
    rows=[i for i in eachindex(lo) if !JS._primal_interval_within_bounds(lo[i],hi[i],p.row_lower[i],p.row_upper[i],t)]
    needed=falses(size(p.A,2)); touched=falses(size(p.A,1));touched[rows].=true
    for j in axes(p.A,2), k in nzrange(p.A,j)
        touched[p.A.rowval[k]] && (needed[j]=true)
    end
    println("rows=",length(rows)," columns=",length(x)," contributing_columns=",count(needed));flush(stdout)
    JS._refined_primal_rows_feasible(p,x,t,rows)
    GC.gc(true);mem("warm")
    for i in 1:500
        a=@timed JS._refined_primal_rows_feasible(p,x,t,rows)
        i%50==0 && println("sample=",i," result=",a.value," bytes=",a.bytes," time=",a.time," gc=",a.gctime);flush(stdout)
        if i%50==0
            mem("before_gc");GC.gc(true);mem("after_gc")
        end
    end
    ccall(:malloc_trim,Cint,(Csize_t,),0);mem("after_trim")
end
main()

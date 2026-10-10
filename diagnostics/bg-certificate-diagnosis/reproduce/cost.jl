include("restore.jl")
if ARGS[1]=="baseline"
    Base.include(JS,joinpath(@__DIR__,"native_cleanup_recovery.jl.baseline"))
end
function costs(mode,snapshot,out)
    w=restore_bg(snapshot);saved=(copy(w.primal),copy(w.scratch.rho),copy(w.reduced_costs))
    rows=[]
    for sample in 0:9
        copyto!(w.primal,saved[1]);copyto!(w.scratch.rho,saved[2]);copyto!(w.reduced_costs,saved[3])
        GC.gc()
        t=@timed JS._try_native_cleanup_recompute!(w,()->false)
        push!(rows,Dict("sample"=>sample,"success"=>t.value,"seconds"=>t.time,
            "bytes"=>t.bytes,"allocations"=>Base.gc_alloc_count(t.gcstats),"compile_seconds"=>t.compile_time))
    end
    open(out,"w") do io;TOML.print(io,Dict("mode"=>mode,"samples"=>rows));end
end
Base.invokelatest(costs,ARGS[1:3]...)

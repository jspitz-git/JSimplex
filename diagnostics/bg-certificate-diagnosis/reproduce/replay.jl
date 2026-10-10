include("restore.jl")
function replay(snapshot,out)
    w=restore_bg(snapshot;diagnostics=JS.SimplexDiagnostics());before=summary(w);basis=copy(w.basis.basic_indices)
    t=@timed JS.run_from_basis!(w,JS.SimplexRunBudget(w),w.progress.numerical_policy,()->false)
    r=t.value
    report=Dict("before"=>before,"after"=>summary(w),"status"=>string(r.status),
        "message"=>r.message,"iterations"=>r.iterations,"seconds"=>t.time,
        "compile_seconds"=>t.compile_time,"bytes"=>t.bytes,"objective"=>r.objective_value,
        "same_basis"=>basis==w.basis.basic_indices,
        "original_feasible"=>JS._original_primal_feasible(w.problem,r.primal,w.options.primal_tolerance),
        "original_certificate"=>JS._original_optimality_certified(w,r.primal),
        "events"=>Dict(string(k)=>v for (k,v) in w.progress.diagnostics.counts))
    open(out,"w") do io;TOML.print(io,report);end
    println(report)
    @assert r.status==OPTIMAL && report["original_feasible"] && report["original_certificate"]
end
Base.invokelatest(replay,ARGS[1:2]...)

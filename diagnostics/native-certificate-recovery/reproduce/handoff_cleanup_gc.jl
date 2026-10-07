using JSimplex, Serialization, LinearAlgebra, SparseArrays, TOML, SHA
# Diagnostic process-memory control only. This does not modify solver source,
# arithmetic, pricing or tolerances; elapsed times include full collections.
const JS=JSimplex
function main(input,output,seconds="600")
    ispath(output) && error("Use a fresh report path")
    d=deserialize(input)
    limit=parse(Float64,seconds)
    options=JS._remaining_options(d.options;iterations=0,time_limit=limit)
    diag=JS.SimplexDiagnostics(;observer=(reason,ws)->begin
        if !isnothing(ws) && (reason in (:phase_primal,:phase_dual,:phase_cleanup,:phase_auxiliary,:certification_failed) || (reason==:pivot_completed && ws.iterations%100==0))
            println("EVENT ",reason," iteration=",ws.iterations," pinf=",JS.primal_infeasibility(ws)," dinf=",JS.dual_infeasibility(ws));flush(stdout)
            before=match(r"VmRSS:\s+(\d+)",read("/proc/self/status",String)).captures[1]
            GC.gc(true)
            after=match(r"VmRSS:\s+(\d+)",read("/proc/self/status",String)).captures[1]
            println("FULL_GC rss_before_kib=",before," rss_after_kib=",after);flush(stdout)
            f=ws.factorization
            println("MEMORY ", Dict("iteration"=>ws.iterations,"workspace_bytes"=>Base.summarysize(ws),
                "factor_bytes"=>Base.summarysize(f),"lower_nnz"=>nnz(f.base.lower),"upper_nnz"=>nnz(f.base.upper),
                "refactorizations"=>ws.refactorizations,"update_count"=>length(f.updates),"update_entries"=>sum((length(u.u_indices)+length(u.v_indices) for u in f.updates);init=0),
                "scratch_bytes"=>Base.summarysize(ws.scratch),"pool_entries"=>f.u_pool.entries+f.v_pool.entries));flush(stdout)
        end
    end)
    ctx=JS.SolveContext(time_ns(),limit,diag,JS.NumericalPolicy(Float64,options))
    timed=@timed Base.invokelatest(JS.cleanup_original,d.problem,d.basis,options,ctx,
        d.iterations,d.refactorizations;target_primal=d.target_primal)
    r=timed.value
    report=Dict{String,Any}("handoff_sha256"=>bytes2hex(open(sha256,input)),
        "algorithm"=>string(options.algorithm),"time_limit"=>options.time_limit,
        "explicit_full_gc"=>true,"context_time_limit"=>limit,"saved_time_limit"=>d.options.time_limit,"iteration_limit"=>options.iteration_limit,"julia_version"=>string(VERSION),
        "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
        "environment_sha256"=>Dict(f=>bytes2hex(open(sha256,joinpath(dirname(Base.active_project()),f))) for f in ("Project.toml","Manifest.toml","LocalPreferences.toml")),"status"=>string(r.status),"message"=>r.message,
        "seconds"=>timed.time,"compile_seconds"=>timed.compile_time,"iterations"=>r.iterations,
        "additional_iterations"=>r.iterations-d.iterations,
        "opt_level"=>Int(Base.JLOptions().opt_level),"debug_level"=>Int(Base.JLOptions().debug_level),
        "events"=>Dict(string(k)=>v for (k,v) in diag.counts if v!=0),
        "original_primal_feasible"=>r.status==OPTIMAL && JS._original_primal_feasible(d.problem,r.primal,d.options.primal_tolerance),
        "source_sha256"=>Dict(f=>bytes2hex(open(sha256,joinpath(dirname(pathof(JS)),f))) for f in ("solver.jl","native_certificate_recovery.jl")))
    if r.status==OPTIMAL
        objective=JS._restored_objective(d.problem,r.primal)
        report["original_objective_evaluable"]=!isnothing(objective)
        !isnothing(objective) && (report["objective"]=objective)
    end
    open(output,"w") do io;TOML.print(io,report;sorted=true);end
    println(report);flush(stdout)
    @assert r.status==OPTIMAL && report["original_primal_feasible"] && report["original_objective_evaluable"]
end
Base.invokelatest(main,ARGS...)

using JSimplex, SHA, TOML, Serialization, LinearAlgebra
const JS=JSimplex
function main(out)
    ispath(out) && error("Choose a fresh output directory")
    mkpath(out)
    input="/home/jspitz/NetLib/degen3.mps"
    p=read_mps(input)
    options=SolverOptions(algorithm=:primal,basis_update=:pfi,basis_refactorization=:native,
        refactorization_interval=80,pricing=:steepest_edge,simplex_strategy=:legacy,
        partial_pricing=false,time_limit=150.0,iteration_limit=1_000_000,verbose=true)
    trace=SHA.SHA2_256_CTX()
    sequence=Ref(0)
    last=Ref{Any}(nothing)
    observer=function(reason,ws)
        isnothing(ws) && return
        if reason==:pivot_completed
            SHA.update!(trace,reinterpret(UInt8,ws.basis.basic_indices))
            SHA.update!(trace,reinterpret(UInt8,ws.primal))
        end
        phase=reason in (:phase_one,:phase_primal,:phase_dual,:phase_cleanup,:certification,:certification_failed)
        bad=reason in (:pivot_completed,:flip_completed) && JS.primal_infeasibility(ws)>ws.options.primal_tolerance
        if phase || bad || (reason==:pivot_completed && ws.iterations in (2345,2116))
            sequence[]+=1
            data=(problem=ws.problem,options=ws.options,basis=deepcopy(ws.basis),
                primal=copy(ws.primal),costs=copy(ws.costs),prices=copy(ws.reduced_costs),
                lower=copy(ws.lower),upper=copy(ws.upper),B=JS.basis_matrix(ws),
                iteration=ws.iterations,offset=ws.progress.iteration_offset,reason,
                policy=ws.progress.numerical_policy,selected_entering=ws.scratch.selected_entering,
                selected_row=ws.scratch.selected_row,last_step=ws.scratch.last_primal_step)
            serialize(joinpath(out,"state-$(sequence[]).bin"),data)
            println("STATE ",sequence[]," ",reason," iter=",ws.iterations," offset=",ws.progress.iteration_offset,
                " pinf=",JS.primal_infeasibility(ws)," shape=",size(ws.problem.A));flush(stdout)
        end
        last[]=ws
    end
    diag=JS.SimplexDiagnostics(;observer)
    t=@timed JS._solve_diagnosed(p,diag;options,relax_integrality=true)
    r=t.value
    root=dirname(dirname(pathof(JS)))
    report=Dict("source_revision"=>strip(read(`git -C $root rev-parse HEAD`,String)),
        "input_sha256"=>bytes2hex(open(sha256,input)),"status"=>string(r.status),"message"=>r.message,
        "iterations"=>r.statistics.iterations,"seconds"=>t.time,"compile_seconds"=>t.compile_time,
        "trace_sha256"=>bytes2hex(SHA.digest!(trace)),"snapshots"=>sequence[],
        "events"=>Dict(string(k)=>v for (k,v) in diag.counts if v!=0))
    if r.status==OPTIMAL
        report["objective"]=r.objective_value
        report["original_primal_feasible"]=JS._original_primal_feasible(p,r.primal,options.primal_tolerance)
    end
    open(joinpath(out,"result.toml"),"w") do io;TOML.print(io,report;sorted=true);end
    println(report)
end
Base.invokelatest(main,ARGS...)

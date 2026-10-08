using JSimplex, SHA, TOML, LinearAlgebra, Logging
function main(output, manager="pfi", backend="markowitz")
    ispath(output) && error("Choose a fresh report")
    input="/home/jspitz/NetLib/pilotnov.mps"
    @assert bytes2hex(open(sha256,input))=="0885e278d768e76f1819416f7844eeebf39f7c4e965f5c376b75191253d21f8d"
    p=read_mps(input)
    options=SolverOptions(;algorithm=:dual,basis_update=Symbol(manager),basis_refactorization=Symbol(backend),
        refactorization_interval=80,pricing=:steepest_edge,simplex_strategy=:legacy,
        partial_pricing=false,time_limit=300.0,iteration_limit=1_000_000,verbose=false)
    maxpoint=Ref(0.0)
    observer=(reason,ws)->begin
        !isnothing(ws) && reason==:pivot_completed && (maxpoint[]=max(maxpoint[],maximum(abs,ws.primal)))
        nothing
    end
    diagnostics=JSimplex.SimplexDiagnostics(;observer)
    t=@timed JSimplex._solve_diagnosed(p,diagnostics;options,relax_integrality=true)
    r=t.value
    report=Dict{String,Any}("status"=>string(r.status),"message"=>r.message,"iterations"=>r.statistics.iterations,
        "seconds"=>t.time,"compile_seconds"=>t.compile_time,"manager"=>manager,"backend"=>backend,
        "maximum_completed_primal_magnitude"=>maxpoint[],"input_sha256"=>bytes2hex(open(sha256,input)),
        "events"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0))
    if r.status==OPTIMAL
        report["objective"]=r.objective_value
        report["original_primal_feasible"]=JSimplex._original_primal_feasible(p,r.primal,options.primal_tolerance)
        report["reference_matches"]=isapprox(r.objective_value,-4497.276188218871;atol=1e-6,rtol=1e-9)
    end
    open(output,"w") do io;TOML.print(io,report;sorted=true);end
    println(report)
end
if abspath(PROGRAM_FILE) == @__FILE__
    Base.invokelatest(main, ARGS...)
end

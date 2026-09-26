using JSimplex, Logging, TOML
function main()
    options=SolverOptions(algorithm=:primal,simplex_strategy=:legacy,time_limit=360.0,
        iteration_limit=1_000_000,verbose=false)
    latest=Ref{Any}(nothing)
    observer=(reason,state)->(state isa JSimplex.SimplexWorkspace && (latest[]=state);nothing)
    d=JSimplex.SimplexDiagnostics(;observer)
    result=with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(read_mps("/home/jspitz/mps/runtime.mps"),d;options,relax_integrality=true)
    end
    ws=latest[]
    report=Dict{String,Any}("status"=>string(result.status),"message"=>result.message,
        "iterations"=>result.statistics.iterations,"seconds"=>result.statistics.elapsed_seconds)
    if result.status==NUMERICAL_ERROR && ws isa JSimplex.SimplexWorkspace
        report["matrix_dimensions"]=collect(size(ws.problem.A))
        report["workspace_iterations"]=ws.iterations
        report["updates_before"]=length(ws.factorization.updates)
        report["primal_infeasibility_before"]=JSimplex.primal_infeasibility(ws)
        report["dual_infeasibility_before"]=JSimplex.dual_infeasibility(ws)
        JSimplex.recompute!(ws;refactorize=true)
        report["primal_infeasibility_after_fresh_factor"]=JSimplex.primal_infeasibility(ws)
        report["dual_infeasibility_after_fresh_factor"]=JSimplex.dual_infeasibility(ws)
        report["finite_after"]=JSimplex._finite_workspace(ws)
    end
    open(joinpath(@__DIR__,"primal-runtime-recovery-probe.toml"),"w") do io;TOML.print(io,report);end
    println(report);flush(stdout)
end
main()

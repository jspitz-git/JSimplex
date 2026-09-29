include("inspect.jl")
function replay_capture(path,seconds,output)
    ispath(output) && error("Choose a fresh output file")
    ws,saved=restore_capture(path)
    started=time_ns()
    stop=J._guard_stop_callback(()->(time_ns()-started)/1e9 >= parse(Float64,seconds))
    verified=J._verify_driver_basis!(ws,stop)
    println("VERIFIED ",verified," primal=",J.primal_infeasibility(ws)," dual=",J.dual_infeasibility(ws))
    flush(stdout)
    initial=ws.iterations
    result=J.run_from_basis!(ws,J.SimplexRunBudget(ws),ws.progress.numerical_policy,stop)
    report=Dict{String,Any}("verified"=>verified,"status"=>string(result.status),
        "message"=>result.message,"iterations"=>result.iterations,
        "added_iterations"=>ws.iterations-initial,"seconds"=>(time_ns()-started)/1e9,
        "original_costs"=>J._original_costs_active(ws),
        "original_bounds"=>J._original_bounds_active(ws))
    if result.status == OPTIMAL
        report["objective"]=result.objective_value
        report["primal_certified"]=J._original_primal_feasible(ws,result.primal)
        report["optimality_certified"]=J._original_optimality_certified(ws,result.primal)
    end
    open(output,"w") do io
        TOML.print(io,report)
    end
    println("RESULT ",report)
end
abspath(PROGRAM_FILE) == (@__FILE__) && replay_capture(ARGS...)

using JSimplex, Serialization, TOML, LinearAlgebra
function main()
    input,output=ARGS[1:2]
    data=deserialize(input)
    options=SolverOptions(algorithm=:dual,basis_update=:bartels_golub,
        pricing=:steepest_edge,refactorization_interval=80,time_limit=360.0,
        iteration_limit=parse(Int,get(ARGS,3,"5000")),verbose=true)
    # Isolated component experiment: this basis was obtained from HiGHS on
    # JSimplex's reduced LP, not from JSimplex's own simplex trajectory.
    context=JSimplex.SolveContext(time_ns(),options.time_limit)
    timed=@timed JSimplex.cleanup_original(data.problem,data.basis,options,
        context,0,0;target_primal=data.target)
    r=timed.value
    report=Dict("source"=>pathof(JSimplex),"status"=>string(r.status),
        "message"=>r.message,"seconds"=>timed.time,"iterations"=>r.iterations,
        "refactorizations"=>r.refactorizations,"peak_rss"=>Sys.maxrss(),
        "iteration_limit"=>options.iteration_limit,"time_limit"=>options.time_limit)
    if r.status==OPTIMAL
        report["objective"]=r.objective_value
        report["original_primal_certified"]=JSimplex._original_primal_feasible(data.problem,r.primal,options.primal_tolerance)
    end
    open(output,"w") do io;TOML.print(io,report);end
    println(report)
end
main()

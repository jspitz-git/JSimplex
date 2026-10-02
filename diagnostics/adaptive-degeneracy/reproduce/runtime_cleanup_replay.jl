# A detached observed cleanup workspace is not an outer-driver checkpoint.
using JSimplex,Serialization,LinearAlgebra,TOML
BLAS.set_num_threads(1)
function replay(args)
    input,output=args
    ws=deserialize(input)
    prior=ws.progress
    start_iteration=ws.iterations
    observer=(event,state)->begin
        if event in (:phase_one,:phase_auxiliary,:phase_dual,:phase_primal,:phase_cleanup) ||
           (event==:pivot_completed && state.iterations%1000==0)
            println("TRACE ",event," iteration=",state.iterations," pinf=",JSimplex.primal_infeasibility(state)," dinf=",JSimplex.dual_infeasibility(state));flush(stdout)
        end
    end
    progress=JSimplex.SimplexProgressContext(ws.problem;scaling=prior.scaling,
        numerical_policy=prior.numerical_policy,diagnostics=JSimplex.SimplexDiagnostics(;observer))
    ws=JSimplex.SimplexWorkspace((name==:progress ? progress : getfield(ws,name) for name in fieldnames(typeof(ws)))...)
    journal=ws.scratch.perturbations
    isnothing(journal) || (journal.workspace_id=objectid(ws))
    start=time_ns()
    result=JSimplex._solve_continuous_dual!(ws,()->(time_ns()-start)/1e9>600)
    record=Dict("start_iteration"=>start_iteration,"iterations"=>ws.iterations,
        "status"=>string(result.status),"message"=>result.message,
        "seconds"=>(time_ns()-start)/1e9,"original_costs_active"=>JSimplex._original_costs_active(ws),
        "original_primal_feasible"=>JSimplex._original_primal_feasible(ws.problem,
            ws.primal[1:size(ws.problem.A,2)],ws.options.primal_tolerance),
        "objective"=>dot(ws.problem.objective,ws.primal[1:size(ws.problem.A,2)])+ws.problem.objective_constant)
    println("RESULT ",record)
    open(output,"w") do io;TOML.print(io,record);end
end
replay(ARGS)

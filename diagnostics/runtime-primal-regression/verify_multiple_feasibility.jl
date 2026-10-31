# Replay a saved handoff through projection and actual production cleanup.
# Run from the isolated fixed package environment, at the original precision.
using JSimplex, LinearAlgebra, Serialization, SHA, TOML
const JS=JSimplex

function verify(input,output; blas_threads=8)
    ispath(output) && error("Use a fresh output path")
    BLAS.set_num_threads(blas_threads)
    @assert BLAS.get_num_threads()==blas_threads
    d=deserialize(input)
    @assert eltype(d.target_primal)==Float64
    ws=JS.initialize_workspace(JS._minimization_problem(d.problem),d.options)
    ws.iterations,ws.refactorizations=d.iterations,d.refactorizations
    ws.basis=JS.Basis(copy(d.basis.basic_indices),copy(d.basis.states))
    JS.recompute!(ws;refactorize=true)
    projection=@timed JS._project_postsolve_basis!(ws,d.target_primal,()->false;
        repair_feasibility=true)
    projection_feasible=JS._original_primal_feasible(d.problem,
        ws.primal[1:length(d.target_primal)],d.options.primal_tolerance)
    report=Dict{String,Any}("julia"=>string(VERSION),"cpu"=>Sys.CPU_NAME,
        "blas_threads"=>BLAS.get_num_threads(),"julia_threads"=>Threads.nthreads(),
        "source_path"=>pathof(JS),"input_sha256"=>bytes2hex(open(sha256,input)),
        "source_sha256"=>Dict(f=>bytes2hex(open(sha256,joinpath(dirname(pathof(JS)),f)))
            for f in readdir(dirname(pathof(JS))) if endswith(f,".jl")),
        "arithmetic_type"=>string(eltype(ws.primal)),"options_unchanged"=>ws.options===d.options,
        "primal_tolerance"=>d.options.primal_tolerance,"dual_tolerance"=>d.options.dual_tolerance,
        "zero_tolerance"=>d.options.zero_tolerance,
        "solve_tolerance"=>ws.progress.numerical_policy.solve_tolerance,
        "projection_accepted"=>!isnothing(projection.value),
        "projection_exchanges"=>something(projection.value,-1),
        "repair_iterations"=>ws.iterations-d.iterations,
        "projected_original_feasible"=>projection_feasible,
        "projected_infeasibility"=>JS.primal_infeasibility(ws),
        "projection_seconds"=>projection.time,"projection_compile_seconds"=>projection.compile_time)
    write_report()=open(output,"w") do io; TOML.print(io,report;sorted=true);end
    write_report()
    @assert report["options_unchanged"] && report["projection_accepted"] && projection_feasible
    println("Projection accepted after ",report["repair_iterations"]," repair pivots")
    flush(stdout)
    starts=Dict{String,Any}[]
    diag=JS.SimplexDiagnostics(;observer=(event,state)->begin
        if event==:phase_primal
            push!(starts,Dict("iterations"=>state.iterations,
                "infeasibility"=>JS.primal_infeasibility(state),
                "original_feasible"=>JS._original_primal_feasible(state.problem,
                    state.primal[1:length(d.target_primal)],state.options.primal_tolerance)))
        end
    end)
    cleanup=@timed JS.cleanup_original(d.problem,d.basis,d.options,
        JS.SolveContext(time_ns(),d.options.time_limit,diag),d.iterations,d.refactorizations;
        target_primal=d.target_primal)
    result=cleanup.value
    report["cleanup_status"]=string(result.status)
    report["cleanup_message"]=result.message
    report["cleanup_iterations"]=result.iterations-d.iterations
    report["final_iterations"]=result.iterations
    report["cleanup_seconds"]=cleanup.time
    report["cleanup_compile_seconds"]=cleanup.compile_time
    report["primal_starts"]=starts
    report["events"]=Dict(string(k)=>v for (k,v) in diag.counts)
    report["final_original_feasible"]=result.status==JS.OPTIMAL &&
        JS._original_primal_feasible(d.problem,result.primal,d.options.primal_tolerance)
    result.status==JS.OPTIMAL && (report["objective"]=result.objective_value)
    write_report()
    @assert result.status==JS.OPTIMAL && report["final_original_feasible"]
    @assert length(starts)==1 && only(starts)["original_feasible"]
    @assert JS.event_count(diag,:phase_auxiliary)==0
    @assert JS.event_count(diag,:precision_boost)==0 && JS.event_count(diag,:lp_refinement)==0
    println("Verified cleanup: ",result.status,"; iterations=",report["cleanup_iterations"],
        "; objective=",result.objective_value)
end

if abspath(PROGRAM_FILE)==@__FILE__
    length(ARGS)==2 || error("Expected: handoff.bin fresh-output.toml")
    verify(ARGS...)
end

# Diagnostic continuation from a detached Phase-II workspace, with a new clock.
# Rebuild and compare the input transforms, then retain the normal postsolve path.
using JSimplex, Serialization, SHA
length(ARGS)==6 || error("Expected model algorithm variant seconds output-prefix snapshot")
const SNAPSHOT_PATH=pop!(ARGS)
const SAVED_WORKSPACE=deserialize(SNAPSHOT_PATH)
const RESUME_PENDING=Ref(true)
setup_path=joinpath(@__DIR__,"phase_transfer_recovery_runtime.jl")
setup=read(setup_path,String)
call="main(vcat(ARGS[1:4],[OUTPUT_PREFIX*\".toml\"]))"
@assert count(call,setup)==1
Base.include_string(Main,replace(setup,call=>""),setup_path)
EXTRA_DIAGNOSTIC_METADATA["continuation_snapshot_sha256"]=bytes2hex(open(sha256,SNAPSHOT_PATH))
EXTRA_DIAGNOSTIC_METADATA["continuation_scope"]="New outer clock; retained Phase-II numerical state; rebuilt input transforms and normal postsolve"
function continue_saved_run(problem,options,progress,stop)
    ws=SAVED_WORKSPACE
    @assert all(f->isequal(getfield(problem,f),getfield(ws.problem,f)),fieldnames(typeof(problem)))
    @assert all(f->isequal(getfield(progress.numerical_policy,f),getfield(ws.progress.numerical_policy,f)),
        fieldnames(typeof(progress.numerical_policy)))
    @assert all(f->isequal(getfield(progress.scaling,f),getfield(ws.progress.scaling,f)),
        fieldnames(typeof(progress.scaling)))
    @assert JSimplex._original_costs_active(ws) && JSimplex._original_bounds_active(ws)
    @assert !JSimplex._has_active_perturbations(ws.scratch.perturbations)
    @assert JSimplex._finite_workspace(ws) && JSimplex._legacy_primal_point_certified(ws)
    @assert ws.progress.iteration_offset==ws.progress.refactorization_offset==0
    EXTRA_DIAGNOSTIC_METADATA["continuation_start_iterations"]=ws.iterations
    EXTRA_DIAGNOSTIC_METADATA["continuation_start_objective"]=dot(ws.costs,ws.primal)
    values=Base.map(fieldnames(typeof(ws))) do field
        field==:progress ? progress : field==:options ? options : getfield(ws,field)
    end
    ws=JSimplex.SimplexWorkspace(values...)
    journal=ws.scratch.perturbations
    isnothing(journal) || (journal.workspace_id=objectid(ws))
    history=ws.scratch.stagnation
    if !isnothing(history)
        # Rebind process-local model identity while retaining the numerical history.
        history.context_key=JSimplex._stagnation_context(ws,:primal)
        history.feasibility_context_key=JSimplex._stagnation_context(ws,:primal;include_costs=false)
    end
    RESUME_PENDING[]=false
    progress.diagnostics.observer(:continuation_start,ws)
    println("CONTINUATION_START iteration=",ws.iterations," objective=",dot(ws.costs,ws.primal));flush(stdout)
    return JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),progress.numerical_policy,stop)
end
source=read(joinpath(dirname(pathof(JSimplex)),"solver.jl"),String)
start=first(findfirst("function _solve_diagnosed(",source))
body=source[start:end]
needle="    run = algorithm(\n        working_problem,\n        typed_options;\n        stop_requested=() -> time_limit_reached(context),\n        progress,\n    )"
@assert count(needle,body)==1
replacement="""
    run = if Main.RESUME_PENDING[] && size(working_problem.A)==size(Main.SAVED_WORKSPACE.problem.A)
        Main.continue_saved_run(working_problem,typed_options,progress,() -> time_limit_reached(context))
    else
        algorithm(working_problem,typed_options;stop_requested=() -> time_limit_reached(context),progress)
    end
"""
body=replace(body,needle=>replacement)
EXTRA_DIAGNOSTIC_METADATA["continuation_driver_sha256"]=bytes2hex(sha256(body))
Base.include_string(JSimplex,body,"diagnostic_phase_continuation.jl")
main(vcat(ARGS[1:4],[OUTPUT_PREFIX*".toml"]))
@assert !RESUME_PENDING[]

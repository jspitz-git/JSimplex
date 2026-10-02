# Observe original-model reconstruction after the corrected Phase-II endpoint.
using JSimplex, Serialization, SHA
setup_path=joinpath(@__DIR__,"phase_transfer_recovery_continue.jl")
setup=read(setup_path,String)
call="main(vcat(ARGS[1:4],[OUTPUT_PREFIX*\".toml\"]))"
@assert count(call,setup)==1
setup=replace(setup,call=>"", "@assert !RESUME_PENDING[]"=>"")
Base.include_string(Main,setup,setup_path)
function capture_postsolve_target(problem,basis,options,context,iterations,refactorizations,target)
    size(problem.A,2)>10000 || return
    feasible=!isnothing(target) && JSimplex._original_primal_feasible(problem,target,options.primal_tolerance)
    objective=isnothing(target) ? NaN : JSimplex._restored_objective(problem,target)
    EXTRA_DIAGNOSTIC_METADATA["postsolve_target_feasible"]=feasible
    EXTRA_DIAGNOSTIC_METADATA["postsolve_target_objective"]=objective
    serialize(OUTPUT_PREFIX*"-target.bin",(;problem,basis,options,policy=context.numerical_policy,
        iterations,refactorizations,target))
    println("POSTSOLVE_TARGET feasible=",feasible," objective=",objective);flush(stdout)
end
function capture_projection(ws,stage,result=nothing)
    size(ws.problem.A,2)>10000 || return
    p=ws.progress
    progress=JSimplex.SimplexProgressContext(ws.problem;start_ns=p.start_ns,scaling=p.scaling,
        iteration_offset=p.iteration_offset,refactorization_offset=p.refactorization_offset,
        numerical_policy=p.numerical_policy)
    fields=Base.map(fieldnames(typeof(ws))) do f
        f==:progress ? progress : getfield(ws,f)
    end
    serialize(OUTPUT_PREFIX*"-projection-"*stage*".bin",JSimplex.SimplexWorkspace(fields...))
    EXTRA_DIAGNOSTIC_METADATA["projection_"*stage*"_pinf"]=JSimplex.primal_infeasibility(ws)
    if stage=="after"
        EXTRA_DIAGNOSTIC_METADATA["projection_result"]=isnothing(result) ? "nothing" : string(result)
    end
    println("POSTSOLVE_PROJECTION ",stage," result=",result," pinf=",JSimplex.primal_infeasibility(ws));flush(stdout)
end
source=read(joinpath(dirname(pathof(JSimplex)),"solver.jl"),String)
a=first(findfirst("function _cleanup_or_retry_original(",source));b=first(findnext("\nfunction ",source,a+1))-1
body=source[a:b]
needle="    run = cleanup_original(problem, basis, options, context,"
@assert count(needle,body)==1
body=replace(body,needle=>"    Main.capture_postsolve_target(problem,basis,options,context,prior_iterations,prior_refactorizations,target_primal)\n"*needle)
EXTRA_DIAGNOSTIC_METADATA["postsolve_target_method_sha256"]=bytes2hex(sha256(body))
Base.include_string(JSimplex,body,"diagnostic_postsolve_target.jl")
a=first(findfirst("function _project_postsolve_basis!(",source));b=first(findnext("\nfunction ",source,a+1))-1
body=replace(source[a:b],"function _project_postsolve_basis!("=>"function _observed_project_postsolve_basis!(")
body*="\nfunction _project_postsolve_basis!(ws::SimplexWorkspace{T},target::Vector{T},stop) where T\n Main.capture_projection(ws,\"before\")\n result=_observed_project_postsolve_basis!(ws,target,stop)\n Main.capture_projection(ws,\"after\",result)\n return result\nend"
EXTRA_DIAGNOSTIC_METADATA["postsolve_projection_method_sha256"]=bytes2hex(sha256(body))
Base.include_string(JSimplex,body,"diagnostic_postsolve_projection.jl")
main(vcat(ARGS[1:4],[OUTPUT_PREFIX*".toml"]))
@assert !RESUME_PENDING[]

# Capture the first locality-budget failure under the representable joint candidate.
using JSimplex, Serialization, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
isdefined(JSimplex,:_try_joint_primal_point_recovery!) || error("Apply the representable joint candidate first")
setup_path=joinpath(@__DIR__,"phase_one_first_failure.jl")
setup=read(setup_path,String)
call="main(vcat(ARGS[1:4], [OUTPUT_PREFIX * \".toml\"]))"
@assert count(call,setup)==1
Base.include_string(Main,replace(setup,call=>""),setup_path)
@assert ARGS[1:3]==["runtime","primal","both"]
const TARGET=14185
const CAPTURED=Ref(false)
function trace_point(tag,ws)
    ws.iterations in (TARGET,TARGET+1) || return
    path=OUTPUT_PREFIX*"-"*string(ws.iterations)*"-"*string(tag)*".bin"
    serialize(path,copy(ws.primal))
    tolerance=ws.options.primal_tolerance
    violations=[max(JSimplex._lower_violation(ws.lower[j],ws.primal[j]),
        JSimplex._upper_violation(ws.upper[j],ws.primal[j])) for j in eachindex(ws.primal)]
    println("POINT tag=",tag," iteration=",ws.iterations," maximum=",maximum(violations),
        " violating=",findall(>(tolerance),violations),
        " model=",JSimplex._legacy_primal_model_feasible(ws),
        " rows=",JSimplex._legacy_primal_row_consistent(ws,tolerance))
    flush(stdout)
end
function capture_before(ws)
    ws.iterations==TARGET && !CAPTURED[] || return
    p=ws.progress
    progress=JSimplex.SimplexProgressContext(ws.problem;start_ns=p.start_ns,scaling=p.scaling,
        iteration_offset=p.iteration_offset,refactorization_offset=p.refactorization_offset,
        numerical_policy=p.numerical_policy)
    values=map(fieldnames(typeof(ws))) do field
        field==:progress ? progress : getfield(ws,field)
    end
    # Remove the observer; this is a one-pivot numerical replay, not driver state.
    serialize(OUTPUT_PREFIX*"-before.bin",JSimplex.SimplexWorkspace(values...))
    CAPTURED[]=true
    trace_point(:before,ws)
end
function trace_ratio(ws,entering,direction,column,step,row,state)
    ws.iterations==TARGET || return
    leaving=row>0 ? ws.basis.basic_indices[row] : 0
    println("RATIO entering=",entering," direction=",direction," step=",step,
        " row=",row," leaving=",leaving," pivot=",row>0 ? column[row] : 0.0)
    serialize(OUTPUT_PREFIX*"-ratio.bin",(;entering,direction,column=copy(column),step,row,state,leaving))
    flush(stdout)
end
function instrument(file,signature,replacements,label)
    source=read(joinpath(ROOT,"src",file),String)
    i=first(findfirst(signature,source))
    following=findnext("\nfunction ",source,i+1)
    body=source[i:(isnothing(following) ? lastindex(source) : first(following)-1)]
    for (needle,replacement) in replacements
        @assert count(needle,body)==1 (label,needle,count(needle,body))
        body=replace(body,needle=>replacement)
    end
    EXTRA_DIAGNOSTIC_METADATA[label*"_sha256"]=bytes2hex(sha256(body))
    Base.include_string(JSimplex,body,label*".jl")
end
instrument("primal_simplex.jl","function _primal_iteration_unchecked!",[
    "    incremental_pivot = workspace.progress"=>"    Main.capture_before(workspace)\n    incremental_pivot = workspace.progress",
    "    leaving_row == -1 && return"=>"    Main.trace_ratio(workspace,entering,direction,tableau_column,step,leaving_row,leaving_state)\n    leaving_row == -1 && return"],"representable_pre_pivot")
instrument("legacy_primal_point.jl","function _restore_legacy_primal_point!",[
    "    computed = _pivot_quality_buffers"=>"    Main.trace_point(:reconstructed,workspace)\n    computed = _pivot_quality_buffers",
    "    accepted = false"=>"    Main.trace_point(:prediction,workspace)\n    accepted = false",
    "            _legacy_primal_point_certified(workspace) || return false"=>"            Main.trace_point(:balanced,workspace)\n            _legacy_primal_point_certified(workspace) || return false"],"representable_prediction")
instrument("legacy_primal_point.jl","function _try_native_primal_point_correction!",[
    "        _legacy_primal_point_certified(workspace) || return false"=>"        Main.trace_point(:correction,workspace)\n        _legacy_primal_point_certified(workspace) || return false"],"representable_correction")
main(vcat(ARGS[1:4],[OUTPUT_PREFIX*".toml"]))

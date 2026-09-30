# Capture the working-row-only experiment; apply working-row-only.patch to aa73565.
using JSimplex, Serialization, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
setup_path=joinpath(ROOT,"diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl")
setup=read(setup_path,String)
setup=replace(setup,"main(vcat(ARGS[1:4], [OUTPUT_PREFIX * \".toml\"]))"=>"")
Base.include_string(Main,setup,setup_path)
@assert ARGS[1:3] == ["runtime","primal","both"]
const TARGET=6798
const WATCH_ROW=28453
const CAPTURED=Ref(false)
function trace_point(tag,ws)
    TARGET <= ws.iterations <= TARGET+1 || return
    n=size(ws.problem.A,2); row=WATCH_ROW
    indices,coefficients=findnz(ws.problem.A[row,:])
    exact=sum(Rational{BigInt}(a)*Rational{BigInt}(ws.primal[j]) for (j,a) in zip(indices,coefficients))
    violation=maximum(max(JSimplex._lower_violation(ws.lower[j],ws.primal[j]),
        JSimplex._upper_violation(ws.upper[j],ws.primal[j])) for j in eachindex(ws.primal))
    println("POINT tag=",tag," iteration=",ws.iterations," bound_max=",violation,
        " stored_activity=",ws.primal[n+row]," exact_activity=",Float64(exact),
        " model_feasible=",JSimplex._legacy_primal_model_feasible(ws),
        " row_consistent=",JSimplex._legacy_primal_row_consistent(ws,ws.options.primal_tolerance))
    for j in vcat(indices,n+row)
        println("VARIABLE tag=",tag," index=",j," state=",ws.basis.states[j],
            " value=",ws.primal[j]," lower=",ws.lower[j]," upper=",ws.upper[j])
    end
    serialize(OUTPUT_PREFIX*"-point-"*string(tag)*".bin",copy(ws.primal))
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
    # Serialize shared arrays synchronously before the live workspace changes.
    # The observer is removed; progress.objective is rebuilt for this auxiliary LP.
    # This is a numerical pivot snapshot, not an outer-driver continuation.
    snapshot=JSimplex.SimplexWorkspace(values...)
    serialize(OUTPUT_PREFIX*"-before.bin",snapshot)
    CAPTURED[]=true
    trace_point(:before,ws)
end
function trace_ratio(ws,entering,direction,column,step,row,state)
    ws.iterations==TARGET || return
    leaving=row>0 ? ws.basis.basic_indices[row] : 0
    println("RATIO entering=",entering," direction=",direction," step=",step,
        " leaving_row=",row," leaving=",leaving," state=",state,
        " pivot=",row>0 ? column[row] : 0.0)
    serialize(OUTPUT_PREFIX*"-ratio.bin",(;entering,direction,column=copy(column),step,row,state,leaving))
    flush(stdout)
end
function instrument(file,signature,replacements,label)
    source=read(joinpath(ROOT,"src",file),String)
    first_index=first(findfirst(signature,source))
    next_function=findnext("\nfunction ",source,first_index+1)
    body=source[first_index:(isnothing(next_function) ? lastindex(source) : first(next_function)-1)]
    for (needle,replacement) in replacements
        @assert count(needle,body)==1 (label,needle,count(needle,body))
        body=replace(body,needle=>replacement)
    end
    EXTRA_DIAGNOSTIC_METADATA[label*"_sha256"]=bytes2hex(sha256(body))
    Base.include_string(JSimplex,body,label*".jl")
end
instrument("primal_simplex.jl","function _primal_iteration_unchecked!",[
    "    incremental_pivot = workspace.progress"=>"    Main.capture_before(workspace)\n    incremental_pivot = workspace.progress",
    "    leaving_row == -1 && return"=>"    Main.trace_ratio(workspace,entering,direction,tableau_column,step,leaving_row,leaving_state)\n    leaving_row == -1 && return"],"diagnostic_pre_pivot")
instrument("legacy_primal_point.jl","function _restore_legacy_primal_point!",[
    "    accepted = false"=>"    Main.trace_point(:prediction,workspace)\n    accepted = false"],"diagnostic_prediction")
instrument("legacy_primal_point.jl","function _try_native_primal_point_correction!",[
    "        _legacy_primal_point_certified(workspace)"=>"        Main.trace_point(:correction,workspace)\n        _legacy_primal_point_certified(workspace)"],"diagnostic_correction")
main(vcat(ARGS[1:4],[OUTPUT_PREFIX*".toml"]))

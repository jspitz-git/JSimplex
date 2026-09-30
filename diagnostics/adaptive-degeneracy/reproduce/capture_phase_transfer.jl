# Observe the failing Phase-I export without changing its numerical operations.
using JSimplex, Serialization, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
setup_path=joinpath(@__DIR__,"phase_one_first_failure.jl")
setup=read(setup_path,String)
call="main(vcat(ARGS[1:4], [OUTPUT_PREFIX * \".toml\"]))"
@assert count(call,setup)==1
Base.include_string(Main,replace(setup,call=>""),setup_path)
@assert ARGS[1:3]==["runtime","primal","both"]
const TRANSFER_CAPTURED=Ref(false)
function detached_transfer_workspace(ws)
    p=ws.progress
    progress=JSimplex.SimplexProgressContext(ws.problem;start_ns=p.start_ns,scaling=p.scaling,
        iteration_offset=p.iteration_offset,refactorization_offset=p.refactorization_offset,
        numerical_policy=p.numerical_policy)
    values=Base.map(fieldnames(typeof(ws))) do field
        field==:progress ? progress : getfield(ws,field)
    end
    # No observer closure: this snapshot supports a local boundary replay,
    # not an exact restart of the outer solve and its budget.
    return JSimplex.SimplexWorkspace(values...)
end
function capture_transfer_before(phase,mapping,original,policy)
    phase.iterations>=100_000 && !TRANSFER_CAPTURED[] || return
    serialize(OUTPUT_PREFIX*"-before.bin",(;phase=detached_transfer_workspace(phase),
        original=detached_transfer_workspace(original),mapping,policy))
    TRANSFER_CAPTURED[]=true
    println("TRANSFER_BEFORE iteration=",phase.iterations,
        " artificial_sum=",sum(phase.primal[mapping.artificial_columns]),
        " basic_artificials=",count(j->phase.basis.states[j]==JSimplex.BASIC,mapping.artificial_columns))
    flush(stdout)
end
function capture_transfer_fresh(phase,fresh)
    TRANSFER_CAPTURED[] && phase.iterations>=100_000 || return
    serialize(OUTPUT_PREFIX*"-fresh.bin",detached_transfer_workspace(fresh))
    println("TRANSFER_FRESH iteration=",fresh.iterations,
        " pinf=",JSimplex.primal_infeasibility_summary(fresh))
    flush(stdout)
end
source=read(joinpath(ROOT,"src/simplex_phase_one.jl"),String)
i=first(findfirst("function _remove_artificials!",source))
j=first(findnext("\nfunction ",source,i+1))-1
body=source[i:j]
for (needle,replacement) in (
    "    m = length(phase.basis.basic_indices)"=>
        "    Main.capture_transfer_before(phase,map,original,policy)\n    m = length(phase.basis.basic_indices)",
    "    _phase_refactor!(fresh,original,stop)"=>
        "    _phase_refactor!(fresh,original,stop)\n    Main.capture_transfer_fresh(phase,fresh)")
    @assert count(needle,body)==1 needle
    global body=replace(body,needle=>replacement)
end
EXTRA_DIAGNOSTIC_METADATA["transfer_capture_method_sha256"]=bytes2hex(sha256(body))
write(OUTPUT_PREFIX*"-method.jl",body)
Base.include_string(JSimplex,body,"diagnostic_phase_transfer_capture.jl")
main(vcat(ARGS[1:4],[OUTPUT_PREFIX*".toml"]))

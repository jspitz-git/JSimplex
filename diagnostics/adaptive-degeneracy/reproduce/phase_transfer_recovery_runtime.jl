# Run the production export and preserve the final observed workspace for diagnosis.
# The detached snapshot is not an exact restart of the outer solver or its budget.
using JSimplex, Serialization, SHA
setup_path=joinpath(@__DIR__,"phase_one_first_failure.jl")
setup=read(setup_path,String)
call="main(vcat(ARGS[1:4], [OUTPUT_PREFIX * \".toml\"]))"
@assert count(call,setup)==1
Base.include_string(Main,replace(setup,call=>""),setup_path)
@assert ARGS[1:3]==["runtime","primal","both"]
function save_final_workspace(ws)
    isnothing(ws) && return
    p=ws.progress
    progress=JSimplex.SimplexProgressContext(ws.problem;start_ns=p.start_ns,scaling=p.scaling,
        iteration_offset=p.iteration_offset,refactorization_offset=p.refactorization_offset,
        numerical_policy=p.numerical_policy)
    values=Base.map(fieldnames(typeof(ws))) do field
        field==:progress ? progress : getfield(ws,field)
    end
    serialize(OUTPUT_PREFIX*"-final.bin",JSimplex.SimplexWorkspace(values...))
end
model_path=joinpath(@__DIR__,"phase_one_models.jl")
source=read(model_path,String)
start=first(findfirst("function main(",source))
finish=first(findfirst("\nif abspath(PROGRAM_FILE)",source))-1
body=source[start:finish]
needle="    result = timed.value\n"
@assert count(needle,body)==1
body=replace(body,needle=>needle*"    save_final_workspace(last_workspace[])\n")
EXTRA_DIAGNOSTIC_METADATA["final_snapshot_method_sha256"]=bytes2hex(sha256(body))
Base.include_string(Main,body,model_path)
main(vcat(ARGS[1:4],[OUTPUT_PREFIX*".toml"]))

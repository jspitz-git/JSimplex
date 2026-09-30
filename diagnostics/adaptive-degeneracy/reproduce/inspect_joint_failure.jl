using JSimplex, Serialization, SHA, TOML, LinearAlgebra
include(joinpath(@__DIR__,"joint_point_probe.jl"))
const TRACE=Dict{String,Any}[]
function inspect_trial(tag,ws)
    n=size(ws.problem.A,2);tol=ws.options.primal_tolerance
    bounds=[j for j in eachindex(ws.primal) if max(JSimplex._lower_violation(ws.lower[j],ws.primal[j]),JSimplex._upper_violation(ws.upper[j],ws.primal[j]))>tol]
    record=Dict("tag"=>string(tag),"bound_failures"=>bounds,
        "nonbasic_bound_failures"=>[j for j in bounds if ws.basis.states[j]!=JSimplex.BASIC],
        "model"=>JSimplex._legacy_primal_model_feasible(ws),
        "equations"=>JSimplex._legacy_primal_row_consistent(ws,tol))
    push!(TRACE,record);println(record);flush(stdout)
    serialize(ARGS[2]*"-"*string(tag)*".bin",copy(ws.primal))
    false
end
source=read(length(ARGS)>2 ? ARGS[3] : joinpath(ROOT,"src/legacy_primal_joint_point.jl"),String)
lines=split(source,'\n')
for (number,line) in enumerate(lines)
    occursin("return false",line) || continue
    lines[number]=replace(line,"return false"=>"return Main.inspect_trial(:line_$(number), workspace)")
end
source=join(lines,'\n')
source=replace(source,"            if _legacy_primal_point_certified(workspace)"=>"            Main.inspect_trial(Symbol(\"sweep_\",length(Main.TRACE)+1),workspace)\n            if _legacy_primal_point_certified(workspace)")
Base.include_string(JSimplex,source,"joint_failure_trace.jl")
ws=point_workspace(ARGS[1]);original=copy(ws.primal)
accepted=JSimplex._try_joint_primal_point_recovery!(ws,()->false)
@assert accepted || isequal(ws.primal,original)
println("RESULT accepted=",accepted," restored=",isequal(ws.primal,original))
open(ARGS[2]*".toml","w") do io
    TOML.print(io,Dict("accepted"=>accepted,"restored"=>isequal(ws.primal,original),
        "snapshot_sha256"=>bytes2hex(open(sha256,ARGS[1])),"method_sha256"=>bytes2hex(sha256(source)),"records"=>TRACE))
end

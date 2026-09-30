# Keep the recovery algorithm and radius fixed; vary only the captured starting point.
using JSimplex, Serialization, SHA, TOML
include(joinpath(@__DIR__,"joint_point_probe.jl"))
prefix,output=ARGS
ws=point_workspace(prefix*".bin")
reconstructed=copy(ws.primal);nonbasic=ws.basis.states.!=JSimplex.BASIC
records=Dict{String,Any}[]
for tag in ("reconstructed","prediction","balanced","correction")
    path=prefix*"-14186-"*tag*".bin"
    start=deserialize(path)
    @assert isequal(start[nonbasic],reconstructed[nonbasic])
    ws.primal .= start
    initial_bounds=JSimplex.primal_infeasibility(ws)
    initial_model=JSimplex._legacy_primal_model_feasible(ws)
    initial_equations=JSimplex._legacy_primal_row_consistent(ws,ws.options.primal_tolerance)
    accepted=JSimplex._try_joint_primal_point_recovery!(ws,()->false)
    @assert accepted || isequal(ws.primal,start)
    @assert isequal(ws.primal[nonbasic],reconstructed[nonbasic])
    record=Dict("tag"=>tag,"initial_pinf"=>initial_bounds,"initial_model"=>initial_model,
        "initial_equations"=>initial_equations,"accepted"=>accepted,
        "certified"=>JSimplex._legacy_primal_point_certified(ws),
        "maximum_change_from_anchor"=>maximum(abs.(ws.primal-start)),
        "maximum_change_from_reconstruction"=>maximum(abs.(ws.primal-reconstructed)),
        "input_sha256"=>bytes2hex(open(sha256,path)))
    push!(records,record);println(record);flush(stdout)
    accepted && serialize(output*"-"*tag*".bin",copy(ws.primal))
end
open(output*".toml","w") do io
    TOML.print(io,Dict("scope"=>"Captured anchor diagnostic, identical native recovery and eight-tolerance locality limit", "records"=>records))
end

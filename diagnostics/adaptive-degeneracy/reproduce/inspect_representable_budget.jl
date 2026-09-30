using JSimplex, Serialization, TOML, SHA
include(joinpath(@__DIR__,"joint_point_probe.jl"))
ws=point_workspace(ARGS[1]);tol=ws.options.primal_tolerance
records=Dict{String,Any}[]
for j in eachindex(ws.primal)
    lo,hi=JSimplex._joint_primal_interval(ws.lower[j],ws.upper[j],tol)
    radius=8max(tol,eps(Float64)*max(1,abs(ws.primal[j])))
    violation=max(JSimplex._lower_violation(ws.lower[j],ws.primal[j]),JSimplex._upper_violation(ws.upper[j],ws.primal[j]))
    if violation>tol
        push!(records,Dict("index"=>j,"basic"=>ws.basis.states[j]==JSimplex.BASIC,
            "value"=>ws.primal[j],"interval_lower"=>lo,"interval_upper"=>hi,"radius"=>radius,
            "bound_violation"=>violation,"minimum_repair"=>abs(clamp(ws.primal[j],lo,hi)-ws.primal[j]),
            "empty_local_interval"=>max(lo,ws.primal[j]-radius)>min(hi,ws.primal[j]+radius)))
    end
end
open(ARGS[2],"w") do io
    TOML.print(io,Dict("snapshot_sha256"=>bytes2hex(open(sha256,ARGS[1])),"records"=>records))
end
foreach(println,records)

# Controlled probe: retain the same projection budget and locality bounds.
using JSimplex, Serialization, SHA, TOML, LinearAlgebra
include(joinpath(@__DIR__,"joint_point_probe.jl"))
source=read(joinpath(ROOT,"src/legacy_primal_joint_point.jl"),String)
needle="margin = min(tolerance/T(4), (hi-lo)/T(4))"
@assert count(needle,source)==2
records=Dict{String,Any}[]
for (tag,replacement) in (("quarter_tolerance",needle),
                          ("zero_margin","margin = zero(T)"),
                          ("native_roundoff","margin = min(T(8)*eps(T)*max(one(T),abs(clamp(value_for_margin,lo,hi))), tolerance/T(4), (hi-lo)/T(4))"))
    body=source
    if tag=="native_roundoff"
        body=replace(body,"                margin ="=>"                value_for_margin = workspace.primal[index]\n                margin =";count=1)
        # The second margin is for the compensated row activity.
        marker="                lo, hi = row_lower[row], row_upper[row]"
        body=replace(body,marker=>marker*"\n                value_for_margin = value")
    end
    body=replace(body,needle=>replacement)
    Base.include_string(JSimplex,body,"joint_margin_"*tag*".jl")
    ws=point_workspace(ARGS[1]);original=copy(ws.primal)
    accepted=JSimplex._try_joint_primal_point_recovery!(ws,()->false)
    certified=JSimplex._legacy_primal_point_certified(ws)
    @assert accepted || isequal(ws.primal,original)
    record=Dict("tag"=>tag,"accepted"=>accepted,"certified"=>certified,
        "maximum_change"=>maximum(abs.(ws.primal-original)),"method_sha256"=>bytes2hex(sha256(body)))
    push!(records,record);println(record);flush(stdout)
end
open(ARGS[2],"w") do io
    TOML.print(io,Dict("records"=>records,"scope"=>"Margin-only diagnostic variation, unchanged eight-sweep and locality limits"))
end

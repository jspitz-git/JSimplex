# Native diagnostic: compare nearest and directional representable row updates.
using JSimplex, Serialization, SHA, TOML, LinearAlgebra
include(joinpath(@__DIR__,"joint_point_probe.jl"))
source_path=ARGS[1]
source=read(source_path,String)
needle="                    projected = clamp(value,lower[index],upper[index])"
@assert count(needle,source)==1
records=Dict{String,Any}[]
for (tag,body) in (("nearest",source),("directional",replace(source,needle=>"                    value = direction > zero(T) ? nextfloat(value) : prevfloat(value)\n"*needle)))
    Base.include_string(JSimplex,body,"representable_"*tag*".jl")
    write(ARGS[2]*"-"*tag*".jl",body)
    for path in ARGS[3:end]
        ws=point_workspace(path);original=copy(ws.primal)
        accepted=JSimplex._try_joint_primal_point_recovery!(ws,()->false)
        certified=JSimplex._legacy_primal_point_certified(ws)
        @assert accepted || isequal(ws.primal,original)
        @assert isequal(ws.primal[ws.basis.states.!=JSimplex.BASIC],original[ws.basis.states.!=JSimplex.BASIC])
        record=Dict("tag"=>tag,"snapshot"=>path,"snapshot_sha256"=>bytes2hex(open(sha256,path)),
            "accepted"=>accepted,"certified"=>certified,"maximum_change_after_return"=>maximum(abs.(ws.primal-original)),
            "method_sha256"=>bytes2hex(sha256(body)))
        push!(records,record);println(record);flush(stdout)
    end
end
open(ARGS[2]*".toml","w") do io
    TOML.print(io,Dict("source_sha256"=>bytes2hex(sha256(source)),"records"=>records,
        "scope"=>"Native point probes only; fixed nonbasic values, eight outer sweeps, same locality limits and certificate"))
end

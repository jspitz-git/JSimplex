# Controlled diagnostic: redistribute row correction after a coordinate saturates.
using JSimplex, Serialization, SHA, TOML, LinearAlgebra
include(joinpath(@__DIR__,"joint_point_probe.jl"))
source=read(joinpath(ROOT,"src/legacy_primal_joint_point.jl"),String)
start=findfirst("                multiplier = ((target-value)/scales[row])/norms[row]",source)
finish=findnext("            end\n            for row in axes(rows,2)",source,last(start))
replacement="""
                for pass in 1:length(nzrange(rows,row))+1
                    residual = target-_joint_primal_activity(rows,row,workspace.primal)
                    iszero(residual) && break
                    norm = zero(T)
                    for k in nzrange(rows,row)
                        index = rows.rowval[k]
                        basic[index] || continue
                        coefficient = rows.nzval[k]/scales[row]
                        direction = sign(residual)*sign(coefficient)
                        movable = direction > zero(T) ? workspace.primal[index] < upper[index] : workspace.primal[index] > lower[index]
                        movable || continue
                        norm += coefficient^2
                    end
                    iszero(norm) && break
                    multiplier = (residual/scales[row])/norm
                    isfinite(multiplier) || return false
                    clipped = false
                    for k in nzrange(rows,row)
                        index = rows.rowval[k]
                        basic[index] || continue
                        coefficient = rows.nzval[k]/scales[row]
                        direction = sign(residual)*sign(coefficient)
                        movable = direction > zero(T) ? workspace.primal[index] < upper[index] : workspace.primal[index] > lower[index]
                        movable || continue
                        value = workspace.primal[index]+multiplier*coefficient
                        isfinite(value) || return false
                        projected = clamp(value,lower[index],upper[index])
                        clipped |= value != projected
                        workspace.primal[index] = projected
                    end
                    clipped || break
                end
"""
records=Dict{String,Any}[]
for (tag,body) in (("clipped",source),("redistributed",source[1:first(start)-1]*replacement*source[first(finish):end]))
    write(ARGS[2]*"-"*tag*".jl",body)
    Base.include_string(JSimplex,body,"joint_clipping_"*tag*".jl")
    ws=point_workspace(ARGS[1]);original=copy(ws.primal)
    accepted=JSimplex._try_joint_primal_point_recovery!(ws,()->false)
    certified=JSimplex._legacy_primal_point_certified(ws)
    @assert accepted || isequal(ws.primal,original)
    record=Dict("tag"=>tag,"accepted"=>accepted,"certified"=>certified,
        "maximum_change"=>maximum(abs.(ws.primal-original)),"method_sha256"=>bytes2hex(sha256(body)))
    push!(records,record);println(record);flush(stdout)
end
open(ARGS[2],"w") do io
    TOML.print(io,Dict("records"=>records,"scope"=>"Clipping-only diagnostic; unchanged eight sweeps, margins and locality limits"))
end

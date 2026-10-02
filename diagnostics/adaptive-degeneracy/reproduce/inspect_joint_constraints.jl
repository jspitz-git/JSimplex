using JSimplex, Serialization, SHA, TOML, LinearAlgebra
include(joinpath(@__DIR__,"joint_point_probe.jl"))
source=read(joinpath(@__DIR__,"inspect_coupled_point.jl"),String)
Base.include_string(Main,first(split(source,"\nfunction main(")),joinpath(@__DIR__,"joint_exact_constraints.jl"))
ws=point_workspace(ARGS[1]);original=copy(ws.primal)
records=Dict{String,Any}[]
for tag in ("original","sweep_1","sweep_2","sweep_8")
    ws.primal .= tag=="original" ? original : deserialize(ARGS[2]*"-"*tag*".bin")
    record=inspect_point(ws,tag)
    for row in record["rows"]
        js=row["basic_columns"]
        row["original_basic_values"]=original[js]
        row["basic_changes"]=ws.primal[js]-original[js]
        row["basic_lower"]=[bound_number(ws.lower[j]) for j in js]
        row["basic_upper"]=[bound_number(ws.upper[j]) for j in js]
        row["basic_radius"]=[8max(ws.options.primal_tolerance,eps(Float64)*max(1,abs(original[j]))) for j in js]
    end
    push!(records,record)
end
open(ARGS[2]*"-constraints.toml","w") do io
    TOML.print(io,Dict("records"=>records,"scope"=>"Exact diagnostic checks of failed joint projection sweeps"))
end

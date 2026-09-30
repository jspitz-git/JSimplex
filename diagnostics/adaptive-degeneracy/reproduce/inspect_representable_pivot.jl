using JSimplex, Serialization, TOML, SHA, LinearAlgebra
source=read(joinpath(@__DIR__,"inspect_coupled_point.jl"),String)
Base.include_string(Main,first(split(source,"\nfunction main(")),joinpath(@__DIR__,"representable_exact.jl"))
prefix,output=ARGS
ws=deserialize(prefix*"-before.bin")
ws.scratch.perturbations.workspace_id=objectid(ws)
records=[inspect_point(ws,"before")]
before=copy(ws.primal)
terminal=JSimplex._primal_iteration!(ws,()->false,zero(Float64))
failed=deserialize(prefix*".bin")
@assert !isnothing(terminal) && terminal.status==NUMERICAL_ERROR
@assert ws.iterations==failed.iterations==14186
@assert isequal(ws.primal,failed.primal)
@assert ws.basis.basic_indices==failed.basis.basic_indices && ws.basis.states==failed.basis.states
println("REPLAY same_point=true same_basis=true iteration=",ws.iterations)
for tag in ("reconstructed","prediction","balanced","correction")
    ws.primal .= deserialize(prefix*"-14186-"*tag*".bin")
    record=inspect_point(ws,tag)
    record["maximum_change_from_before"]=maximum(abs.(ws.primal-before))
    push!(records,record)
end
ratio=deserialize(prefix*"-ratio.bin")
open(output,"w") do io
    TOML.print(io,Dict("records"=>records,"scope"=>"Exact inspection and one-pivot replay of the first locality-budget failure",
        "before_sha256"=>bytes2hex(open(sha256,prefix*"-before.bin")),
        "entering"=>ratio.entering,"leaving"=>ratio.leaving,"row"=>ratio.row,"step"=>ratio.step,
        "pivot"=>ratio.column[ratio.row]))
end

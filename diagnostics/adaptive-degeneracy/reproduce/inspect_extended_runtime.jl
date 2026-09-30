using JSimplex, Serialization, TOML, SHA, LinearAlgebra
source=read(joinpath(@__DIR__,"inspect_coupled_point.jl"),String)
Base.include_string(Main,first(split(source,"\nfunction main(")),joinpath(@__DIR__,"extended_exact.jl"))
prefix,output=ARGS
ws=deserialize(prefix*"-before.bin")
ws.scratch.perturbations.workspace_id=objectid(ws)
records=[inspect_point(ws,"before")]
before=copy(ws.primal)
terminal=JSimplex._primal_iteration!(ws,()->false,zero(Float64))
failed=deserialize(prefix*".bin")
@assert !isnothing(terminal) && terminal.status==NUMERICAL_ERROR
@assert ws.iterations==failed.iterations==19222
@assert isequal(ws.primal,failed.primal)
@assert ws.basis.basic_indices==failed.basis.basic_indices && ws.basis.states==failed.basis.states
println("REPLAY same_point=true same_basis=true iteration=",ws.iterations)
for tag in ("reconstructed","prediction","balanced","correction")
    ws.primal .= deserialize(prefix*"-19222-"*tag*".bin")
    record=inspect_point(ws,tag)
    record["maximum_change_from_before"]=maximum(abs.(ws.primal-before))
    push!(records,record)
end
ratio=deserialize(prefix*"-ratio.bin")

# Trace the actual recovery anchor, not a reconstruction-only surrogate.
ws.primal .= failed.primal
original=copy(ws.primal)
prediction=deserialize(prefix*"-19222-prediction.bin")[ws.basis.basic_indices]
const SWEEPS=Dict{String,Any}[]
const CONTEXT_PATH=output*"-context.bin"
function inspect_sweep(workspace,anchor,lower,upper,row_lower,row_upper)
    tag="sweep_"*string(length(SWEEPS)+1)
    record=inspect_point(workspace,tag)
    record["maximum_change_from_anchor"]=maximum(abs.(workspace.primal-anchor))
    record["nonbasic_unchanged"]=isequal(workspace.primal[workspace.basis.states.!=JSimplex.BASIC],
        anchor[workspace.basis.states.!=JSimplex.BASIC])
    push!(SWEEPS,record)
    serialize(output*"-"*tag*".bin",copy(workspace.primal))
    if length(SWEEPS)==1
        serialize(CONTEXT_PATH,(;anchor=copy(anchor),lower=copy(lower),upper=copy(upper),
            row_lower=copy(row_lower),row_upper=copy(row_upper)))
    end
end
method=read(joinpath(dirname(pathof(JSimplex)),"legacy_primal_joint_point.jl"),String)
needle="            if _legacy_primal_point_certified(workspace)"
@assert count(needle,method)==1
method=replace(method,needle=>"            Main.inspect_sweep(workspace,anchor,lower,upper,row_lower,row_upper)\n"*needle)
Base.include_string(JSimplex,method,"extended_joint_trace.jl")
accepted=JSimplex._try_joint_primal_point_recovery!(ws,()->false,prediction)
@assert !accepted && isequal(ws.primal,original)
open(output,"w") do io
    TOML.print(io,Dict("records"=>records,"sweeps"=>SWEEPS,
        "scope"=>"Actual one-pivot replay and exact inspection of prediction-anchored native recovery",
        "before_sha256"=>bytes2hex(open(sha256,prefix*"-before.bin")),
        "method_sha256"=>bytes2hex(sha256(method)),"accepted"=>accepted,"restored"=>isequal(ws.primal,original),
        "entering"=>ratio.entering,"leaving"=>ratio.leaving,"row"=>ratio.row,"step"=>ratio.step,
        "pivot"=>ratio.column[ratio.row]))
end

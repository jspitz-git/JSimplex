# Counterfactual one-pivot probe only. Production source files are not modified.
using JSimplex, Serialization, SHA, TOML
include(joinpath(@__DIR__,"pricing_isolation.jl"))
isolate_pricing_trials!()
prefix,output=ARGS
function load_before(prefix)
    ws=deserialize(prefix*"-before.bin")
    ws.scratch.perturbations.workspace_id=objectid(ws)
    ws
end
ws=load_before(prefix)
ratio=deserialize(prefix*"-ratio.bin")
before=copy(ws.primal)
snap_accepted=JSimplex._primal_bound_snap_feasible(ws,ratio.entering,ratio.direction,ratio.column,ratio.row)
@assert snap_accepted
baseline=JSimplex._primal_iteration!(ws,()->false,zero(Float64))
@assert !isnothing(baseline) && baseline.status==NUMERICAL_ERROR
failed=deserialize(prefix*".bin")
@assert isequal(ws.primal,failed.primal)
source=read(joinpath(dirname(pathof(JSimplex)),"simplex.jl"),String)
i=first(findfirst("function _can_preserve_primal_row_value",source))
j=first(findnext("\nfunction ",source,i+1))-1
body=source[i:j]
needle="    index > columns || return false\n"
@assert count(needle,body)==1
body=replace(body,needle=>"")
needle="    checked_bound = state == AT_LOWER ? workspace.problem.row_lower[index - columns] :\n                                       workspace.problem.row_upper[index - columns]"
@assert count(needle,body)==1
body=replace(body,needle=>"    checked_bound = if index <= columns\n        state == AT_LOWER ? workspace.problem.column_lower[index] : workspace.problem.column_upper[index]\n    else\n        state == AT_LOWER ? workspace.problem.row_lower[index-columns] : workspace.problem.row_upper[index-columns]\n    end")
open(output*"-method.jl","w") do io;write(io,body);end
Base.include_string(JSimplex,body,"diagnostic_structural_preservation.jl")
ws=load_before(prefix)
terminal=JSimplex._primal_iteration!(ws,()->false,zero(Float64))
certified=JSimplex._legacy_primal_point_certified(ws)
@assert isnothing(terminal) && certified
result=Dict("scope"=>"Counterfactual single pivot; no driver continuation or production promotion",
    "before_sha256"=>bytes2hex(open(sha256,prefix*"-before.bin")),"method_sha256"=>bytes2hex(sha256(body)),
    "baseline_snap_guard_accepts"=>snap_accepted,"baseline_status"=>string(baseline.status),
    "candidate_pivot_completed"=>isnothing(terminal),"candidate_certified"=>certified,
    "same_captured_basis"=>ws.basis.basic_indices==failed.basis.basic_indices && ws.basis.states==failed.basis.states,
    "same_pre_pivot_point"=>isequal(ws.primal,before),"iteration"=>ws.iterations,
    "leaving_before"=>before[ratio.leaving],"leaving_after"=>ws.primal[ratio.leaving],
    "maximum_change"=>maximum(abs.(ws.primal-before)))
open(output,"w") do io;TOML.print(io,result);end
println(result)

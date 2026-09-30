# Run against pre-fix 2cf7d17 to reproduce the failure and probe certified blends.
using JSimplex, Serialization, SHA, LinearAlgebra
BLAS.set_num_threads(1)
const ROOT=dirname(dirname(pathof(JSimplex)))
include(joinpath(ROOT,"diagnostics/adaptive-degeneracy/reproduce/pricing_isolation.jl"))
isolate_pricing_trials!()
length(ARGS)==1 || error("Expected: snapshot-prefix")
prefix=ARGS[1]
ws=deserialize(prefix*"-before.bin")
ws.scratch.perturbations.workspace_id=objectid(ws)
r=deserialize(prefix*"-ratio.bin")
movement=-r.direction*r.column[r.row]
bound=r.state==JSimplex.AT_LOWER ? ws.lower[r.leaving] : ws.upper[r.leaving]
raw=(JSimplex.bound_value(bound)-ws.primal[r.leaving])/movement
println("LEAVING value=",ws.primal[r.leaving]," bound=",bound," raw_step=",raw,
    " snap_safe=",JSimplex._primal_bound_snap_feasible(ws,r.entering,r.direction,r.column,r.row),
    " direction_nonzeros=",count(!iszero,r.column))
terminal=JSimplex._primal_iteration!(ws,()->false,zero(Float64))
failed=deserialize(prefix*".bin")
println("REPLAY terminal=",terminal," same_point=",isequal(ws.primal,failed.primal),
    " same_basis=",ws.basis.basic_indices==failed.basis.basic_indices)
@assert isequal(ws.primal,failed.primal)
predicted=deserialize(prefix*"-point-prediction.bin")
reconstructed=copy(ws.primal)
for alpha in (0.0,0.25,0.5,0.75,1.0)
    for j in ws.basis.basic_indices
        ws.primal[j]=predicted[j]+alpha*(reconstructed[j]-predicted[j])
    end
    println("BLEND alpha=",alpha," certified=",JSimplex._legacy_primal_point_certified(ws),
        " model=",JSimplex._legacy_primal_model_feasible(ws),
        " rows=",JSimplex._legacy_primal_row_consistent(ws,ws.options.primal_tolerance),
        " pinf=",JSimplex.primal_infeasibility(ws))
end

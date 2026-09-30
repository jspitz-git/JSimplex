using JSimplex, Serialization, LinearAlgebra, Test, SHA
BLAS.set_num_threads(1)
const ROOT=dirname(dirname(pathof(JSimplex)))
include(joinpath(ROOT,"diagnostics/adaptive-degeneracy/reproduce/pricing_isolation.jl"))
isolate_pricing_trials!()
length(ARGS)==1 || error("Expected: snapshot-prefix")
prefix=ARGS[1]
ws=deserialize(prefix*"-before.bin")
ws.scratch.perturbations.workspace_id=objectid(ws)
terminal=JSimplex._primal_iteration!(ws,()->false,zero(Float64))
failed=deserialize(prefix*".bin")
@test isnothing(terminal)
@test ws.iterations==5443
@test ws.basis.basic_indices==failed.basis.basic_indices
@test JSimplex._legacy_primal_point_certified(ws)
@test ws.scratch.row_solution==ws.primal[ws.basis.basic_indices]
@test ws.primal[ws.basis.states .!= JSimplex.BASIC]==failed.primal[ws.basis.states .!= JSimplex.BASIC]
println("REPLAY_FIXED terminal=",terminal," iteration=",ws.iterations,
    " certified=",JSimplex._legacy_primal_point_certified(ws),
    " pinf=",JSimplex.primal_infeasibility(ws),
    " same_basis=",ws.basis.basic_indices==failed.basis.basic_indices)

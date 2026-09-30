using JSimplex,Serialization,LinearAlgebra,SHA
BLAS.set_num_threads(1)
include(joinpath(@__DIR__,"pricing_isolation.jl"))
isolate_pricing_trials!()
ws=deserialize(only(ARGS))
ws.scratch.perturbations.workspace_id=objectid(ws)
@assert ws.iterations==6798
terminal=JSimplex._primal_iteration!(ws,()->false,zero(Float64))
println("REPLAY terminal=",terminal," iteration=",ws.iterations,
    " certified=",JSimplex._legacy_primal_point_certified(ws),
    " corrected_value=",ws.primal[2297])
@assert isnothing(terminal)
@assert ws.iterations==6799
@assert JSimplex._legacy_primal_point_certified(ws)
@assert ws.primal[2297]==nextfloat(-1.8e-6)

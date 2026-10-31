"""Opt-in experimental dual engine. Task1/2 state and kernels only; no solver routing."""
module ExperimentalDualEngine
import JSimplex
const J=JSimplex
include("types.jl")
include("support.jl")
include("invariants.jl")
include("state.jl")
include("kernels.jl")
end

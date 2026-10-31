"""Opt-in experimental dual engine. Task1/2/3 state, kernels and pending proposals only; no solver routing."""
module ExperimentalDualEngine
import JSimplex
const J=JSimplex
include("types.jl")
include("support.jl")
include("invariants.jl")
include("state.jl")
include("kernels.jl")
include("ratio.jl")
include("proposal.jl")
end

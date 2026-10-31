"""Opt-in experimental dual engine. Task1 state only; no solver routing."""
module ExperimentalDualEngine
import JSimplex
const J=JSimplex
include("types.jl")
include("support.jl")
include("invariants.jl")
include("state.jl")
end

"""Opt-in experimental dual engine. Experimental owned dual phase, journaled publication and flat recovery; no solver routing."""
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
include("commit.jl")
include("recovery.jl")
include("driver.jl")
end

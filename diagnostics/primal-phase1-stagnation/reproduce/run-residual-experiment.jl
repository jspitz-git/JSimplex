using JSimplex
include("residual-intervention.jl")
isempty(ARGS) && error("Expected: script [script arguments...]")
script=abspath(popfirst!(ARGS))
install_residual_intervention()
include(script)
# The shared capture entry point normally runs only as PROGRAM_FILE.
if script==normpath(joinpath(@__DIR__,"..","..","primal-runtime-stability","reproduce","capture.jl"))
    capture_primal(ARGS)
end

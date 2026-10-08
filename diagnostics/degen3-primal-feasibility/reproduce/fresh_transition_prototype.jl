# Diagnostic-only prototype; production sources remain unchanged.
using JSimplex, SHA
source=read(joinpath(dirname(pathof(JSimplex)),"primal_simplex.jl"),String)
start=findfirst("function _solve_continuous_primal(",source).start
body=source[start:end]
needle="policy.feasibility_recovery || recompute!(workspace)"
@assert count(needle,body)==1
body=replace(body,needle=>"policy.feasibility_recovery || recompute!(workspace;refactorize=true,caller_guard=stop_requested)")
Base.include_string(JSimplex,body,"diagnostic-fresh-phase-transition")
include("capture.jl")
write(joinpath(ARGS[1],"override-source.jl"),body)

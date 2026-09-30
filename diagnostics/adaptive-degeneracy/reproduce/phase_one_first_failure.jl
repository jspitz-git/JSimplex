# Capture the first failed artificial-variable phase before the normal original-LP retry.
# The snapshot stores a portable mathematical basis, not the full factor/update or
# adaptive lifecycle state. Do not treat it as an exact continuation checkpoint.
using Serialization
include(joinpath(@__DIR__,"phase_one_models.jl"))
length(ARGS) == 5 || error("Expected: model algorithm variant seconds output-prefix")
const OUTPUT_PREFIX = ARGS[5]
const FAILED_PHASE=Ref{Any}(nothing)
const EXTRA_DIAGNOSTIC_METADATA=Dict{String,Any}("original_retry_enabled"=>false)
function phase_failure_hook(ws,terminal)
    FAILED_PHASE[]=ws
    println("PHASE_FAILURE status=",terminal.status," message=",terminal.message,
        " iteration=",ws.iterations," refactorizations=",ws.refactorizations,
        " objective=",dot(ws.costs,ws.primal)," pinf=",JSimplex.primal_infeasibility(ws));flush(stdout)
    serialize(OUTPUT_PREFIX * ".bin",(;problem=ws.problem,options=ws.options,
        policy=ws.progress.numerical_policy,basis=ws.basis,costs=ws.costs,lower=ws.lower,upper=ws.upper,
        primal=ws.primal,reduced_costs=ws.reduced_costs,iterations=ws.iterations,
        refactorizations=ws.refactorizations,pricing_weights=ws.pricing_weights,
        last_primal_step=ws.scratch.last_primal_step,last_dual_step=ws.scratch.last_dual_step,
        perturbations=ws.scratch.perturbations,pricing=ws.scratch.pricing))
end
source=read(joinpath(dirname(pathof(JSimplex)),"simplex_phase_one.jl"),String)
i=first(findfirst("function _run_phase_one!",source));j=first(findnext("\nfunction ",source,i+1))-1
body=source[i:j]
needle="terminal.status == OPTIMAL || return _phase_result(ws,terminal.status,terminal.message)"
@assert count(needle,body)==1
body=replace(body,needle=>"if terminal.status != OPTIMAL\n            Main.phase_failure_hook(phase,terminal)\n            return _phase_result(ws,terminal.status,terminal.message)\n        end")
EXTRA_DIAGNOSTIC_METADATA["phase_failure_method_sha256"] = bytes2hex(sha256(body))
Base.include_string(JSimplex,body,"diagnostic_phase_failure.jl")
source=read(joinpath(dirname(pathof(JSimplex)),"solver.jl"),String)
i=first(findfirst("function _retry_original(",source));j=first(findnext("\nfunction ",source,i+1))-1
body=source[i:j]
needle="    time_limit_reached(context) &&"
@assert count(needle,body)==1
body=replace(body,needle=>"    println(\"FIRST_FAILURE \",previous.status,\" \",previous.message);flush(stdout)\n    return previous\n"*needle)
EXTRA_DIAGNOSTIC_METADATA["no_original_retry_method_sha256"] = bytes2hex(sha256(body))
Base.include_string(JSimplex,body,"diagnostic_no_original_retry.jl")
main(vcat(ARGS[1:4], [OUTPUT_PREFIX * ".toml"]))

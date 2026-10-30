# Replay in a fresh process using a compatible Julia/JSimplex environment:
# julia --project=. replay.jl runtime-capture.handoff.bin fresh-output-prefix [cleanup]
# The default inspects raw projection. "cleanup" exercises recovery and the
# original-objective solve, with a fresh 300-second replay budget.
include(joinpath(@__DIR__, "capture.jl"))
using Serialization

length(ARGS) in (2,3) || error("Expected: handoff.bin output_prefix [cleanup]")
input, prefix = ARGS[1:2]
cleanup = length(ARGS)==3
cleanup && ARGS[3]!="cleanup" && error("Unknown replay mode")
for suffix in (".projection.bin", ".projection.toml", ".cleanup.toml")
    ispath(prefix * suffix) && error("Use a fresh output prefix: " * prefix)
end
mkpath(dirname(abspath(prefix)))
data=deserialize(input)
if cleanup
    J=RuntimePrimalCapture.JS
    options=J._remaining_options(data.options;iterations=0,time_limit=300.0)
    timed=@timed J.cleanup_original(data.problem,data.basis,options,
        J.SolveContext(time_ns(),300.0),data.iterations,data.refactorizations;
        target_primal=data.target_primal)
    result=timed.value
    report=Dict{String,Any}("status"=>string(result.status),"message"=>result.message,
        "iterations"=>result.iterations,"additional_iterations"=>result.iterations-data.iterations,
        "seconds"=>timed.time,"compile_seconds"=>timed.compile_time,"bytes"=>timed.bytes,
        "original_primal_feasible"=>result.status==J.OPTIMAL &&
            J._original_primal_feasible(data.problem,result.primal,options.primal_tolerance))
    result.status==J.OPTIMAL && (report["objective"]=result.objective_value)
    RuntimePrimalCapture.write_report(prefix*".cleanup.toml",report)
    println(report)
else
    RuntimePrimalCapture.inspect(data, prefix)
end

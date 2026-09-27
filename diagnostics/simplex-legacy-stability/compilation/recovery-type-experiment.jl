using Test, TOML
using JSimplex
# Diagnostic-only override: retain the known BigFloat scalar type on a
# successful transfer; no arithmetic, control flow, or options are changed.
@eval JSimplex function _next_bigfloat_workspace(source,bits::Int,budget,stop)
    while true
        fresh,reason,message = _precision_transfer_attempt(source,BigFloat,bits,budget,stop)
        !isnothing(fresh) && return (fresh::SimplexWorkspace{BigFloat}),bits,message
        reason == :numerical || return nothing,bits,message
        next = next_working_precision(BigFloat,bits,source.progress.numerical_policy)
        isnothing(next) && return nothing,bits,message
        bits = next
    end
end
stats = @timed include(joinpath(dirname(dirname(pathof(JSimplex))), "test/simplex_precision_recovery_state_tests.jl"))
report = Dict("seconds"=>stats.time,"compile_seconds"=>stats.compile_time,"recompile_seconds"=>stats.recompile_time,"gc_seconds"=>stats.gctime,"allocated_bytes"=>stats.bytes,"julia"=>string(VERSION),"source"=>pathof(JSimplex))
open(ARGS[1],"w") do io; TOML.print(io,report); end
println(report)

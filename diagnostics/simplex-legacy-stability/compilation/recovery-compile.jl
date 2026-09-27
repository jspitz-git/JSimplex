using Test, TOML
using JSimplex
stats = @timed include(joinpath(dirname(dirname(pathof(JSimplex))), "test/simplex_precision_recovery_state_tests.jl"))
report = Dict("seconds"=>stats.time,"compile_seconds"=>stats.compile_time,"recompile_seconds"=>stats.recompile_time,"gc_seconds"=>stats.gctime,"allocated_bytes"=>stats.bytes,"julia"=>string(VERSION),"source"=>pathof(JSimplex))
open(ARGS[1],"w") do io; TOML.print(io,report); end
println(report)

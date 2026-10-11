using JSimplex, LinearAlgebra, TOML, Logging
# Same guarded Julia process, two independent modules and workspace types.
# The source snapshot is pinned by the outer runner, not modified here.
module Reference
include(joinpath(ARGS[2],"JSimplex.jl"))
end
module BaselineBench
const JS=Main.Reference.JSimplex
include("entry_kernel_common.jl")
end
module CandidateBench
const JS=Main.JSimplex
include("entry_kernel_common.jl")
end
function main(output)
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    for bench in (BaselineBench,CandidateBench)
        @assert !bench.entry_stop(bench.JS.SolveContext(time_ns(),Inf))()
        @assert bench.entry_stop(bench.JS.SolveContext(time_ns(),0.0))()
    end
    records=Dict[]
    for kind in (:sparse,:dense),manager in (:pfi,:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        println("warm ",kind," ",manager);flush(stdout)
        problems=(BaselineBench.fixture(kind),CandidateBench.fixture(kind))
        benches=(BaselineBench,CandidateBench)
        traces=[benches[i].run_kernel(problems[i],manager;trace=true) for i in 1:2]
        for key in ("state_hash","entry_state_hash","events_hash","completion_states_hash","event_counts","steps","entry_iterations","event_count","refactorizations")
            @assert traces[1][key]==traces[2][key] key
        end
        for side in 1:2
            traces[side]["case"]=string(kind);traces[side]["side"]=side==1 ? "baseline" : "candidate"
            traces[side]["repeat"]=0;push!(records,traces[side])
            benches[side].run_kernel(problems[side],manager)
        end
        for repetition in 1:3
            pair=Dict[]
            for side in (isodd(repetition) ? (1,2) : (2,1))
                row=benches[side].run_kernel(problems[side],manager)
                row["case"]=string(kind);row["side"]=side==1 ? "baseline" : "candidate";row["repeat"]=repetition
                @assert row["compile_seconds"]==0
                for key in ("state_hash","entry_state_hash","steps","entry_iterations","refactorizations")
                    @assert row[key]==traces[side][key] key
                end
                push!(records,row);push!(pair,row)
            end
            @assert pair[1]["state_hash"]==pair[2]["state_hash"]
            @assert pair[1]["steps"]==pair[2]["steps"]
            println(kind," ",manager," pair ",repetition," ",[(r["side"],r["seconds"],r["steps"]) for r in pair]);flush(stdout)
            open(output,"w") do io;TOML.print(io,Dict("cases"=>records,"julia"=>string(VERSION)));end
        end
    end
end
with_logger(NullLogger()) do
    main(ARGS[1])
end

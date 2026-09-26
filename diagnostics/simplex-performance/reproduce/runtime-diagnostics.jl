using JSimplex, Logging, TOML
function main()
    problem=read_mps("/home/jspitz/mps/runtime.mps")
    options=SolverOptions(algorithm=:dual,simplex_strategy=:legacy,time_limit=360.0,
        iteration_limit=1_000_000,verbose=false)
    longest=Ref(0)
    dimensions=Set{Tuple{Int,Int}}()
    observer=function(reason,state)
        if reason==:pivot_completed && state isa JSimplex.SimplexWorkspace
            longest[]=max(longest[],length(state.factorization.updates))
            push!(dimensions,size(state.problem.A))
        end
    end
    diagnostics=JSimplex.SimplexDiagnostics(;observer,kernel_timing=true)
    warm=read_mps("test/fixtures/solver/afiro.mps")
    with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(warm,JSimplex.SimplexDiagnostics(;observer,kernel_timing=true);options,relax_integrality=true)
    end
    longest[]=0;empty!(dimensions)
    result=with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(problem,diagnostics;options,relax_integrality=true)
    end
    report=Dict("status"=>string(result.status),"message"=>result.message,
        "seconds"=>result.statistics.elapsed_seconds,"iterations"=>result.statistics.iterations,
        "refactorizations"=>result.statistics.refactorizations,"max_observed_update_chain"=>longest[],
        "observed_matrix_dimensions"=>[collect(d) for d in sort!(collect(dimensions))],
        "counts"=>Dict(string(k)=>v for (k,v) in diagnostics.counts),
        "kernel_calls"=>Dict(string(k)=>v for (k,v) in diagnostics.kernel_calls),
        "kernel_seconds"=>Dict(string(k)=>Float64(v)/1e9 for (k,v) in diagnostics.kernel_nanoseconds))
    open(joinpath(@__DIR__,"runtime-diagnostics.toml"),"w") do io;TOML.print(io,report);end
    println(report);flush(stdout)
end
main()

using JSimplex, Logging, TOML
function main()
    options = SolverOptions(iteration_limit=1_000_000, time_limit=360.0,
        pricing=:steepest_edge, basis_update=:bartels_golub,
        basis_refactorization=:native, refactorization_interval=80,
        algorithm=:primal, simplex_strategy=:legacy, verbose=false)
    latest = Ref{Any}(nothing)
    phases = Dict{String,Any}[]
    observer = function(reason, ws)
        ws isa JSimplex.SimplexWorkspace || return
        latest[] = ws
        if reason in (:phase_one, :phase_primal, :phase_dual, :phase_cleanup)
            phase = Dict("event"=>string(reason), "rows"=>size(ws.problem.A,1),
                "columns"=>size(ws.problem.A,2), "local_iterations"=>ws.iterations)
            push!(phases,phase); println(phase); flush(stdout)
        elseif reason == :pivot_completed && ws.iterations % 5000 == 0
            println("PRIMAL_PROGRESS iterations=",ws.iterations," refactorizations=",ws.refactorizations)
            flush(stdout)
        end
    end
    with_logger(NullLogger()) do
        solve(read_mps("test/fixtures/solver/afiro.mps"); options, relax_integrality=true)
    end
    problem = read_mps("/home/jspitz/mps/runtime.mps")
    diagnostics = JSimplex.SimplexDiagnostics(; observer, kernel_timing=true)
    result = with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(problem,diagnostics; options,relax_integrality=true)
    end
    report = Dict{String,Any}("status"=>string(result.status),"message"=>result.message,
        "seconds"=>result.statistics.elapsed_seconds,"iterations"=>result.statistics.iterations,
        "refactorizations"=>result.statistics.refactorizations,"phases"=>phases,
        "counts"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0),
        "kernel_seconds"=>Dict(string(k)=>Float64(v)/1e9 for (k,v) in diagnostics.kernel_nanoseconds if v!=0))
    if latest[] isa JSimplex.SimplexWorkspace
        ws=latest[]
        report["dimensions"]=collect(size(ws.problem.A))
        report["primal_infeasibility"]=JSimplex.primal_infeasibility(ws)
    end
    if result.status==OPTIMAL
        report["objective"]=result.objective_value
        report["original_primal_certified"]=JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
    end
    tag=get(ENV,"STABILITY_TAG","per-bound-harris")
    open(joinpath(@__DIR__,"primal-progress-$(tag).toml"),"w") do io
        TOML.print(io,report)
    end
    println(report);flush(stdout)
end
main()

using JSimplex, Serialization, Logging, SHA
struct HistoryComplete <: Exception end
function main()
    path,output=ARGS[1:2]
    lowercase(basename(realpath(path))) in ("big.mps","largo.mps","anymod.mps") && error("Excluded large model")
    seed=parse(Int,get(ARGS,3,"2000")); count=parse(Int,get(ARGS,4,"320"))
    digest=bytes2hex(open(sha256,path))
    initial=Ref{Any}(nothing); steps=Tuple{Int,Int}[]
    observer=function(reason,ws)
        reason==:pivot_completed || return
        if isnothing(initial[])
            ws.iterations>=seed || return
            initial[]=(A=ws.problem.A,basis=copy(ws.basis.basic_indices),iteration=ws.iterations)
            println("Capturing after iteration ",ws.iterations," dimensions=",size(ws.problem.A));flush(stdout)
        else
            ws.problem.A===initial[].A || error("Working model changed during capture")
            row=ws.scratch.selected_row
            1<=row<=length(ws.basis.basic_indices) || error("Invalid committed pivot row")
            push!(steps,(row,ws.basis.basic_indices[row]))
            if length(steps)==count
                serialize(output,(input=realpath(path),input_sha256=digest,A=initial[].A,basis=initial[].basis,
                    iteration=initial[].iteration,steps=steps))
                throw(HistoryComplete())
            end
        end
    end
    options=SolverOptions(algorithm=:dual,basis_update=:bartels_golub,
        basis_refactorization=:native,pricing=:steepest_edge,refactorization_interval=80,
        simplex_strategy=:legacy,time_limit=360.0,iteration_limit=seed+count+1000,verbose=false)
    problem=read_mps(path)
    try
        JSimplex._solve_diagnosed(problem,JSimplex.SimplexDiagnostics(;observer);
            options,relax_integrality=true)
        error("Solve stopped before capturing the requested history")
    catch e
        e isa JSimplex.DiagnosticObserverFailure && e.cause isa HistoryComplete || rethrow()
    end
    println("Saved ",length(steps)," real column exchanges to ",output)
end
main()

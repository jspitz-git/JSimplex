using JSimplex, SparseArrays

for flip in (false,true), event in (:pivot_proposed,:pivot_completed,:flip_completed)
    event == :pivot_completed && flip && continue
    event == :flip_completed && !flip && continue
    stopped = Ref(false)
    observations = []
    problem=LinearProblem(sparse(reshape([1.0],1,1)),[-1.0];row_upper=[flip ? 2.0 : 0.5],column_upper=[1.0])
    options=SolverOptions(algorithm=:primal,pricing=:dantzig,presolve=false,verbose=false)
    diagnostics=JSimplex.SimplexDiagnostics(observer=(reason,ws)->begin
        if reason == event
            push!(observations,(reason,copy(ws.primal),copy(ws.basis.states),copy(ws.reduced_costs)))
            stopped[]=true
        end
    end)
    ws=JSimplex.initialize_workspace(problem,options;progress=JSimplex.SimplexProgressContext(problem;diagnostics))
    result=JSimplex._primal_iteration!(ws,()->stopped[],ws.options.dual_tolerance)
    before=(copy(ws.primal),copy(ws.reduced_costs))
    JSimplex.recompute!(ws)
    println((;flip,event,status=isnothing(result) ? nothing : result.status,ws.iterations,observations,before,after=(ws.primal,ws.reduced_costs)))
end

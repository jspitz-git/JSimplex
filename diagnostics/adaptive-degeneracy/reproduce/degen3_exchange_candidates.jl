# Enumerate actual artificial-exchange steps without changing the workspace.
using JSimplex,Serialization,LinearAlgebra
BLAS.set_num_threads(1)
function probe(prefix)
    ws=deserialize(prefix*"-phase.bin");map=deserialize(prefix*"-map.bin")
    policy=ws.progress.numerical_policy;tol=ws.options.primal_tolerance
    m=length(ws.basis.basic_indices);rhs=zeros(m);column=zeros(m);unit=zeros(m);rho=zeros(m)
    row=findfirst(j->map.phase_to_original[j]==0 && abs(ws.primal[j])>tol,ws.basis.basic_indices)
    unit[row]=1;JSimplex._checked_basis_solve!(rho,ws,unit,()->false;transposed=true)
    B=JSimplex._basis_matrix!(ws)
    q=JSimplex.solve_quality!(JSimplex._pivot_quality_buffers(ws).row,B,rho,unit,policy;transposed=true)
    q.reliable || @assert JSimplex._native_cleanup_solve!(rho,ws,B,unit,()->false;transposed=true)
    prices=zeros(length(ws.basis.states));JSimplex._csc_price!(prices,ws.problem.A,rho)
    stats=Dict(:nonzero=>0,:entering_feasible=>0,:pivot_valid=>0,:point_feasible=>0)
    best=[]
    for j in map.original_to_phase
        ws.basis.states[j]==JSimplex.BASIC && continue
        abs(prices[j])>eps() || continue
        stats[:nonzero]+=1
        movement=ws.primal[ws.basis.basic_indices[row]]/prices[j]
        x=ws.primal[j]+movement
        max(JSimplex._lower_violation(ws.lower[j],x),JSimplex._upper_violation(ws.upper[j],x),0.0)<=tol || continue
        stats[:entering_feasible]+=1
        JSimplex._pivot_column!(rhs,ws,j)
        JSimplex._checked_basis_solve!(column,ws,rhs,()->false)
        println("DIRECTION j=",j," price=",prices[j]," pivot=",column[row]," norm=",maximum(abs,column)," movement=",movement)
        abs(column[row])>policy.pivot_error_tolerance*maximum(abs,column) || continue
        verdict=JSimplex.validate_pivot!(ws,JSimplex.PivotCandidate(j,row,prices[j],column,rho),policy)
        println("VALIDATION ",verdict)
        if verdict!=:accept
            repaired=JSimplex._native_cleanup_solve!(column,ws,B,rhs,()->false)
            verdict=JSimplex.validate_pivot!(ws,JSimplex.PivotCandidate(j,row,prices[j],column,rho),policy)
            println("REPAIRED ",repaired," validation=",verdict)
        end
        verdict==:accept || continue
        stats[:pivot_valid]+=1
        movement=ws.primal[ws.basis.basic_indices[row]]/column[row]
        worst=0.0;worstj=0
        for (i,k) in enumerate(ws.basis.basic_indices)
            i==row && continue
            x=ws.primal[k]-movement*column[i]
            v=max(JSimplex._lower_violation(ws.lower[k],x),JSimplex._upper_violation(ws.upper[k],x),0.0)
            v>worst && ((worst,worstj)=(v,k))
        end
        x=ws.primal[j]+movement
        v=max(JSimplex._lower_violation(ws.lower[j],x),JSimplex._upper_violation(ws.upper[j],x),0.0)
        v>worst && ((worst,worstj)=(v,j))
        worst<=tol && (stats[:point_feasible]+=1)
        push!(best,(worst,j,prices[j],movement,worstj))
    end
    println("PREFIX ",prefix," row=",row," value=",ws.primal[ws.basis.basic_indices[row]]," stats=",stats)
    sort!(best);println("BEST ",first(best,min(10,length(best))));flush(stdout)
end
foreach(probe,ARGS)

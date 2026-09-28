using JSimplex, Serialization, LinearAlgebra, Logging
const J=JSimplex
include("intervention.jl")
length(ARGS)==2 || error("Expected: before_snapshot after_snapshot")
function loadws(d)
    ws=J.initialize_workspace(d.problem,d.options)
    ws.basis=deepcopy(d.basis);ws.factorization=d.factorization
    ws.primal.=d.primal;ws.lower.=d.lower;ws.upper.=d.upper;ws.costs.=d.costs;ws.reduced_costs.=d.prices
    ws.iterations=d.iteration
    return ws
end
function inspect()
    a=deserialize(ARGS[1])
    b=deserialize(ARGS[2])
    ws=loadws(a);after=loadws(b)
    println("BEFORE iteration=",a.iteration," cert=",point_certificate(ws))
    println("AFTER iteration=",b.iteration," cert=",point_certificate(after)," entering=",b.entering," row=",b.row," step=",b.last_step)
    column=zeros(size(ws.problem.A,1));buffers=J._pivot_quality_buffers(ws)
    rhs=copy(J._pivot_column!(buffers.rhs,ws,b.entering))
    J._ordinary_forward_solve!(column,ws.factorization,rhs)
    q=J._compensated_solve_quality!(buffers.column,J._basis_matrix!(ws),column,rhs,ws.progress.numerical_policy,false)
    correction=similar(column);J._ordinary_forward_solve!(correction,ws.factorization,buffers.column.residual)
    println("SELECTED pivot=",column[b.row]," norm=",norm(column,Inf)," quality=",q," correction_inf=",norm(correction,Inf)," pivot_correction=",correction[b.row])
    leaving=a.basis.basic_indices[b.row]
    println("LEAVING index=",leaving," before=",a.primal[leaving]," after=",b.primal[leaving]," state=",b.basis.states[leaving]," candidate_state=",J._primal_ratio(ws,b.entering,1.0,column))
    after.primal.=a.primal
    after.primal[leaving]=b.primal[leaving]
    for (r,i) in enumerate(b.basis.basic_indices)
        after.primal[i]=r==b.row ? a.primal[b.entering]+b.last_step : a.primal[i]-b.last_step*column[r]
    end
    println("PREDICTED cert=",point_certificate(after))
    deltas=abs.(b.primal-after.primal)
    for i in sortperm(deltas;rev=true)[1:8]
        println("POINT index=",i," before=",a.primal[i]," predicted=",after.primal[i]," reconstructed=",b.primal[i]," lower=",b.lower[i]," upper=",b.upper[i])
    end
    println("PREDICTED violations:")
    violation=[max(0.,J._lower_violation(after.lower[i],after.primal[i]),J._upper_violation(after.upper[i],after.primal[i])) for i in eachindex(after.primal)]
    for i in sortperm(violation;rev=true)[1:5];println("BOUND index=",i," violation=",violation[i]);end
end
with_logger(NullLogger()) do;inspect();end

using JSimplex,Serialization,LinearAlgebra,Logging,SparseArrays
const J=JSimplex
include("intervention.jl")
length(ARGS)==1 || error("Expected: first-loss snapshot prefix")
function inspect(prefix)
    d=deserialize(prefix*".failed.bin");a=deserialize(prefix*".previous.bin");t=deserialize(prefix*".transition.bin")
    ws=J.initialize_workspace(d.problem,d.options)
    ws.basis=deepcopy(d.basis);ws.factorization=d.factorization;ws.iterations=d.iteration
    ws.lower.=d.lower;ws.upper.=d.upper;ws.costs.=d.costs;ws.primal.=d.primal
    J._validate_basis(ws)
    n=size(d.problem.A,2);m=size(d.problem.A,1);tol=ws.options.primal_tolerance
    println("FAILED iteration=",d.iteration," updates=",length(d.factorization.updates)," cert=",point_certificate(ws))
    isnothing(a) && error("Initial phase point failed; no preceding point")
    println("PREVIOUS iteration=",a.iteration," refs=",a.refactorizations," cert=",a.certificate)
    # Higher precision evaluates stored equations only; it never factors a basis.
    setprecision(BigFloat,256) do
        AA=BigFloat.(d.problem.A)
        for (label,x) in (("before",a.primal),("after",d.primal))
            activity=AA*BigFloat.(x[1:n]);residual=activity-BigFloat.(x[n+1:end])
            println("REFERENCE_POINT label=",label," residual_inf=",norm(residual,Inf))
            for r in sortperm(abs.(residual);rev=true)[1:4]
                println("ROW label=",label," row=",r," activity=",activity[r]," stored=",x[n+r]," residual=",residual[r]," lower=",d.problem.row_lower[r]," upper=",d.problem.row_upper[r])
            end
        end
    end
    if !isnothing(t)
        println("TRANSITION iteration=",t.iteration," event=",t.event," row=",t.row," entering=",t.entering," step=",t.step," pivot=",t.row>0 ? t.direction[t.row] : NaN," direction_norm=",norm(t.direction,Inf))
        if t.iteration==d.iteration && t.basis.basic_indices==d.basis.basic_indices
            for (r,i) in enumerate(d.basis.basic_indices)
                ws.primal[i]=r==t.row ? t.primal[t.entering]+t.step : t.primal[i]-t.step*t.direction[r]
            end
            println("PREDICTED cert=",point_certificate(ws)," delta_recomputed=",norm(ws.primal-d.primal,Inf))
        end
    end
    ws.primal.=d.primal
    buffers=J._pivot_quality_buffers(ws)
    # Include nonbasic contributions directly instead of a rounded assembled RHS.
    q=J._compensated_solve_quality!(buffers.column,d.problem.A,ws.primal[1:n],ws.primal[n+1:end],ws.progress.numerical_policy,false)
    println("FULL_NATIVE_QUALITY ",q)
    if !isnothing(q) && q.finite
        residual=copy(buffers.column.residual);correction=zeros(m)
        J._ordinary_forward_solve!(correction,ws.factorization,residual)
        println("FULL_NATIVE_CORRECTION norm=",norm(correction,Inf))
        for (r,i) in enumerate(ws.basis.basic_indices);ws.primal[i]+=correction[r];end
        println("CORRECTED cert=",point_certificate(ws))
        for i in sortperm(abs.(ws.primal-d.primal);rev=true)[1:5]
            println("CORRECTED_VALUE index=",i," before=",d.primal[i]," after=",ws.primal[i]," lower=",ws.lower[i]," upper=",ws.upper[i])
        end
    end
end
with_logger(NullLogger()) do;inspect(ARGS[1]);end

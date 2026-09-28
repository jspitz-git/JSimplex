using JSimplex, Serialization, LinearAlgebra, SparseArrays
function inspect(path)
    d=deserialize(path)
    ws=JSimplex.initialize_workspace(d.problem,d.options)
    ws.basis=deepcopy(hasproperty(d,:prior_basis) ? d.prior_basis : d.basis)
    ws.costs.=d.costs;ws.lower.=d.lower;ws.upper.=d.upper
    ws.primal.=d.primal;ws.reduced_costs.=d.prices
    B=copy(JSimplex._basis_matrix!(ws))
    println("SNAPSHOT ",path," event=",d.event," iteration=",d.iteration,
        " step=",d.last_step," pinf=",JSimplex.primal_infeasibility(ws),
        " working_objective=",dot(ws.costs,ws.primal))
    if hasproperty(d,:prior_basis)
        entering=d.entering;row=d.row
        a=copy(JSimplex._pipeline_column_rhs!(ws,entering))
        f=lu(B);fresh=f\a;unit=zeros(length(a));unit[row]=1.0;rho=f'\unit
        println("PIVOT row=",row," entering=",entering," stored=",d.direction[row],
            " fresh=",fresh[row]," stored_row=",d.tableau[entering],
            " fresh_row=",dot(rho,a)," direction_norm=",norm(d.direction,Inf),
            " residual=",norm(B*d.direction-a,Inf)," fresh_residual=",norm(B*fresh-a,Inf))
        cb=ws.costs[ws.basis.basic_indices]
        println("REDUCED_COST stored=",d.prices[entering],
            " direct=",ws.costs[entering]-dot(cb,d.direction),
            " fresh_direct=",ws.costs[entering]-dot(cb,fresh))
        direction=d.prices[entering]<0 ? 1.0 : -1.0
        println("RATIO stored=",JSimplex._primal_ratio(ws,entering,direction,d.direction),
            " fresh=",JSimplex._primal_ratio(ws,entering,direction,fresh))
        scratch=JSimplex.SolveQualityScratch(Float64,length(a))
        policy=JSimplex.NumericalPolicy(Float64,ws.options)
        x=copy(fresh)
        for k in 1:3
            quality=JSimplex._compensated_solve_quality!(scratch,B,x,a,policy,false)
            isnothing(quality) && break
            delta=f\scratch.residual
            old=x[row];x.+=delta
            println("NATIVE_CORRECTION k=",k," old=",old," delta=",delta[row],
                " corrected=",x[row]," norm_delta=",norm(delta,Inf),
                " residual=",quality.absolute_error,
                " ratio=",JSimplex._primal_ratio(ws,entering,direction,x))
        end
        # Diagnostic-only higher-precision residual reference, using the native
        # factor for corrections; this does not change solver working precision.
        for bits in (128,256)
            ref=setprecision(BigFloat,bits) do
                BB=BigFloat.(B);aa=BigFloat.(a);x=BigFloat.(fresh)
                for k in 1:8
                    residual=aa-BB*x
                    correction=f\Float64.(residual)
                    all(isfinite,correction) || break
                    x.+=BigFloat.(correction)
                end
                (pivot=x[row],residual=norm(BB*x-aa,Inf),
                    reduced_cost=BigFloat(ws.costs[entering])-dot(BigFloat.(cb),x))
            end
            println("REFERENCE bits=",bits," ",ref)
        end
    else
        try
            f=lu(B);println("CURRENT_BASIS native_factorization=success")
        catch e
            println("CURRENT_BASIS ",sprint(showerror,e))
        end
    end
    flush(stdout)
end
foreach(inspect,ARGS)

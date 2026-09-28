using JSimplex,Serialization,LinearAlgebra
function inspect_ratio(path)
    d=deserialize(path);ws=JSimplex.initialize_workspace(d.problem,d.options)
    ws.basis=deepcopy(hasproperty(d,:prior_basis) ? d.prior_basis : d.basis)
    ws.lower.=d.lower;ws.upper.=d.upper
    ws.primal.=d.primal;ws.costs.=d.costs;ws.reduced_costs.=d.prices
    println("SNAPSHOT ",path," iteration=",d.iteration," last_step=",d.last_step,
        " stored_primal_infeasibility=",JSimplex.primal_infeasibility(ws))
    d.entering>0 || return
    if ws.basis.states[d.entering]==JSimplex.BASIC
        println("Snapshot stopped after an exchange; selected column is now basic")
        return
    end
    B=copy(JSimplex._basis_matrix!(ws));a=copy(JSimplex._pipeline_column_rhs!(ws,d.entering));f=lu(B)
    precise=setprecision(BigFloat,256) do
        BB=BigFloat.(B);aa=BigFloat.(a);x=BigFloat.(f\a)
        for _ in 1:8;x.+=BigFloat.(f\Float64.(aa-BB*x));end
        residual=maximum(abs,aa-BB*x)
        println("REFERENCE residual_inf=",residual," solution_inf=",maximum(abs,x))
        if !all(isfinite,x) || residual>big"1e-30"*max(one(BigFloat),maximum(abs,aa))
            println("Reference refinement did not converge; no reference ratio is reported")
            return nothing
        end
        Float64.(x)
    end
    for (label,column) in (("stored",d.direction),("reference",precise))
        isnothing(column) && continue
        entering=d.entering;orientation=d.prices[entering]<0 ? 1.0 : -1.0
        println("PRICING label=",label," entering=",entering,
            " state=",ws.basis.states[entering]," stored_weight=",d.pricing_weights[entering],
            " direction_weight=",last(JSimplex._primal_direction_weight(column)),
            " stored_price=",d.prices[entering],
            " direction_price=",ws.costs[entering]-dot(ws.costs[ws.basis.basic_indices],column))
        opposite=orientation>0 ? ws.upper[entering] : ws.lower[entering]
        limit=isfinite(opposite) ? (JSimplex.bound_value(opposite)-ws.primal[entering])/orientation : Inf
        limiting_row=0;rows=[]
        for (row,index) in enumerate(ws.basis.basic_indices)
            move=-orientation*column[row];iszero(move) && continue
            bound=move>0 ? ws.upper[index] : ws.lower[index];isfinite(bound) || continue
            raw=(JSimplex.bound_value(bound)-ws.primal[index])/move
            relaxed=max(0.0,raw+ws.options.primal_tolerance/abs(move))
            if relaxed<limit;limit=relaxed;limiting_row=row;end
            push!(rows,(row=row,index=index,pivot=column[row],raw=raw,step=max(0.0,raw),value=ws.primal[index],bound=JSimplex.bound_value(bound)))
        end
        eligible=filter(x->x.step<=limit,rows);sort!(eligible;by=x->-abs(x.pivot))
        println("RATIO label=",label," relaxed_limit=",limit," limiting_row=",limiting_row,
            " eligible=",length(eligible)," chosen=",JSimplex._primal_ratio(ws,entering,orientation,column))
        for x in Iterators.take(eligible,12)
            safe=JSimplex._primal_bound_snap_feasible(ws,entering,orientation,column,x.row)
            values=copy(ws.primal)
            values[entering]+=orientation*x.raw
            for (r,i) in enumerate(ws.basis.basic_indices)
                values[i]=r==x.row ? x.bound : ws.primal[i]-orientation*column[r]*x.raw
            end
            violations=[max(0.0,JSimplex._lower_violation(ws.lower[i],values[i]),
                JSimplex._upper_violation(ws.upper[i],values[i])) for i in eachindex(values)]
            worst=argmax(violations)
            println("CANDIDATE ",x," snap_safe=",safe," max_violation=",violations[worst],
                " total_violation=",sum(violations)," worst_index=",worst,
                " entering_violation=",violations[entering])
        end
    end
end
foreach(inspect_ratio,ARGS)

using JSimplex,Serialization
function quality(ws,label)
    n=size(ws.problem.A,2);tol=ws.options.primal_tolerance
    println(label," pinf=",JSimplex.primal_infeasibility(ws),
        " original_feasible=",JSimplex._original_primal_feasible(ws.problem,ws.primal[1:n],tol),
        " row_consistent=",JSimplex._legacy_primal_row_consistent(ws,tol))
end
function main(path)
    data=deserialize(path);println("SNAPSHOT ",path," step=",data.last_step)
    ws=JSimplex.initialize_workspace(data.problem,data.options)
    ws.basis=deepcopy(data.basis);ws.costs.=data.costs
    ws.lower.=data.lower;ws.upper.=data.upper
    tol=ws.options.primal_tolerance
    for source in (:computed,:candidate),fraction in (0.0,0.5)
        ws.primal.=data.primal
        if source==:candidate
            for (row,index) in enumerate(ws.basis.basic_indices)
                ws.primal[index]=data.candidate[row]
            end
        end
        quality(ws,string(source)*" before")
        changed=0;large=0
        for index in ws.basis.basic_indices
            value=ws.primal[index]
            lo=JSimplex._lower_violation(ws.lower[index],value)
            hi=JSimplex._upper_violation(ws.upper[index],value)
            violation=max(lo,hi)
            violation>tol || continue
            if violation>2tol
                large+=1;continue
            end
            ws.primal[index]=lo>hi ? JSimplex.bound_value(ws.lower[index])-fraction*tol :
                JSimplex.bound_value(ws.upper[index])+fraction*tol
            changed+=1
        end
        println("fraction=",fraction," changed=",changed," large_violations=",large)
        quality(ws,string(source)*" after")
    end
end
foreach(main,ARGS)

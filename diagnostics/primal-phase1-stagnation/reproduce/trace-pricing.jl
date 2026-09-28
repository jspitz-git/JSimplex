using JSimplex, Serialization, LinearAlgebra, Logging
const J=JSimplex
include("intervention.jl")
length(ARGS)==4 || error("Expected: snapshot mode steps seconds")
install_intervention(ARGS[2])
function trace(path,steps,seconds)
    d=deserialize(path)
    basic_costs=zeros(eltype(d.costs),length(d.basis.basic_indices))
    selected=Ref((entering=0,weight=0.0,valid=false,price=0.0))
    accepted=Ref(0)
    observer=function(event,ws)
        if event==:pivot_proposed
            j=ws.scratch.selected_entering
            selected[]=(entering=j,weight=ws.pricing_weights[j],valid=ws.scratch.steepest_valid[j],price=ws.reduced_costs[j])
            for (r,i) in enumerate(ws.basis.basic_indices);basic_costs[r]=ws.costs[i];end
        elseif event==:pivot_completed
            accepted[]+=1
            if accepted[]>steps-150 || accepted[]<=3
                s=selected[];col=ws.scratch.row_solution
                actual=last(J._primal_direction_weight(col))
                println("ACCEPT k=",accepted[]," entering=",s.entering," cached=",s.valid,
                    " stored_weight=",s.weight," actual_weight=",actual," ratio=",max(s.weight/actual,actual/s.weight),
                    " price=",s.price," implied_price=",ws.costs[s.entering]-dot(basic_costs,col),
                    " step=",ws.scratch.last_primal_step," pivot=",col[ws.scratch.selected_row]," refs=",ws.refactorizations)
                flush(stdout)
            end
        end
    end
    diagnostics=J.SimplexDiagnostics(;observer)
    ws=J.initialize_workspace(d.problem,d.options;progress=J.SimplexProgressContext(d.problem;diagnostics))
    ws.basis=deepcopy(d.basis);ws.costs.=d.costs;ws.lower.=d.lower;ws.upper.=d.upper;ws.primal.=d.primal;ws.iterations=d.iteration
    point=copy(ws.primal[ws.basis.basic_indices]);J.recompute!(ws;refactorize=true);J._restore_legacy_primal_point!(ws,point,()->false)
    cert=point_certificate(ws);point_certified(ws,cert)||error("Uncertified initial point")
    ws.scratch.steepest_initialized=true;fill!(ws.scratch.steepest_valid,false)
    start=time_ns();stop=()->(time_ns()-start)/1e9>=seconds
    for k in 1:steps
        stop() && break
        J._finite_workspace(ws) && J.primal_infeasibility(ws)<=ws.options.primal_tolerance || error("Invalid point before iteration")
        terminal=J._primal_iteration!(ws,stop,0.0)
        if !isnothing(terminal);println("TERMINAL ",terminal);break;end
    end
    println("END objective=",dot(ws.costs,ws.primal)," certificate=",point_certificate(ws)," counts=",diagnostics.counts)
end
with_logger(NullLogger()) do
    trace(ARGS[1],parse(Int,ARGS[3]),parse(Float64,ARGS[4]))
end

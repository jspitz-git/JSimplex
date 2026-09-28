using JSimplex, Serialization, LinearAlgebra

# A reference continuation, not an exact replay: refresh the native factor and
# rebuild pricing weights before observing repeated bases. No widened arithmetic.
function replay_stall(path, steps, seconds)
    d=deserialize(path)
    selected=Ref((0,0.0,false,0.0))
    basic_costs=zeros(eltype(d.costs),length(d.basis.basic_indices))
    observer=function(event,ws)
        if event==:pivot_proposed
            entering=ws.scratch.selected_entering
            selected[]=(entering,ws.pricing_weights[entering],ws.scratch.steepest_valid[entering],ws.reduced_costs[entering])
            for (row,index) in enumerate(ws.basis.basic_indices)
                basic_costs[row]=ws.costs[index]
            end
        elseif event==:pivot_completed
            entering,weight,valid,price=selected[]
            actual=last(JSimplex._primal_direction_weight(ws.scratch.row_solution))
            ratio=max(weight/actual,actual/weight)
            products=basic_costs.*ws.scratch.row_solution
            println("WEIGHT entering=",entering," cached=",valid," stored=",weight,
                " actual=",actual," ratio=",ratio," price=",price,
                " direction_price=",ws.costs[entering]-sum(products),
                " cost_product_scale=",sum(abs,products))
        end
        nothing
    end
    diagnostics=JSimplex.SimplexDiagnostics(;observer)
    ws=JSimplex.initialize_workspace(d.problem,d.options;
        progress=JSimplex.SimplexProgressContext(d.problem;diagnostics))
    ws.basis=deepcopy(d.basis);ws.costs.=d.costs
    ws.lower.=d.lower;ws.upper.=d.upper;ws.primal.=d.primal
    ws.iterations=d.iteration
    start=time_ns();stop=()->(time_ns()-start)/1e9>=seconds
    point=copy(ws.primal[ws.basis.basic_indices])
    JSimplex.recompute!(ws;refactorize=true,caller_guard=stop)
    JSimplex._restore_legacy_primal_point!(ws,point,stop)
    ws.scratch.steepest_initialized=true
    fill!(ws.scratch.steepest_valid,false)
    seen=Dict{UInt,Vector{Tuple{Int,Vector{Int},Vector{JSimplex.VariableState}}}}()
    println("START iteration=",ws.iterations," objective=",dot(ws.costs,ws.primal),
        " pinf=",JSimplex.primal_infeasibility(ws));flush(stdout)
    for k in 1:steps
        stop() && break
        terminal=JSimplex._primal_iteration!(ws,stop,zero(eltype(ws.costs)))
        key=hash(ws.basis.basic_indices,hash(ws.basis.states,UInt(0)))
        bucket=get!(seen,key,Tuple{Int,Vector{Int},Vector{JSimplex.VariableState}}[])
        previous=findfirst(x->x[2]==ws.basis.basic_indices && x[3]==ws.basis.states,bucket)
        repeat=isnothing(previous) ? 0 : k-bucket[previous][1]
        isnothing(previous) && push!(bucket,(k,copy(ws.basis.basic_indices),copy(ws.basis.states)))
        println("STEP ",k," iteration=",ws.iterations," objective=",dot(ws.costs,ws.primal),
            " step=",ws.scratch.last_primal_step," refs=",ws.refactorizations,
            " repeat_distance=",repeat," pinf=",JSimplex.primal_infeasibility(ws),
            " terminal=",terminal)
        flush(stdout)
        isnothing(terminal) || break
    end
end
length(ARGS)==3 || error("Expected: snapshot steps seconds")
replay_stall(ARGS[1],parse(Int,ARGS[2]),parse(Float64,ARGS[3]))

using  SparseArrays, LinearAlgebra, Test, TOML, Logging, SHA
function fixture(kind,m=64,n=128)
    A=if kind==:sparse
        sparse([i for j in 1:n for i in (1+mod(j-1,m),1+mod(j,m))],
               [j for j in 1:n for _ in 1:2],repeat([4.0,-1.0],n),m,n)
    else
        sparse([i==j ? 256.0 : Float64(1+mod(3i+5j,3)) for i in 1:m,j in 1:n])
    end
    rhs=A*ones(n)
    return JS.LinearProblem(A,Float64[mod(7j,19)-9 for j in 1:n];
                         row_lower=rhs,row_upper=rhs,column_upper=fill(2.0,n))
end
function entry_stop(context)
    # Match each revision's real internal solve call site, including clock polls.
    return isdefined(JS,:_SolveDeadline) ? JS._SolveDeadline(context) :
        ()->JS.time_limit_reached(context)
end
function run_kernel(problem,manager;trace=false)
    options=JS.SolverOptions(;algorithm=:dual,basis_update=manager,basis_refactorization=:native,
                         verbose=false,pricing=:steepest_edge,iteration_limit=10000,
                         simplex_strategy=:legacy,refactorization_interval=320)
    events=SHA.SHA2_256_CTX();names=SHA.SHA2_256_CTX();event_count=Ref(0)
    capturing=Ref(false);event_counts=Dict{String,Int}()
    observer=(event,ws)->begin
        capturing[] || return nothing
        name=string(event)
        SHA.update!(names,codeunits(name*"\n"))
        event_counts[name]=get(event_counts,name,0)+1
        if event in (:pivot_completed,:flip_completed)
            event_count[]+=1
            SHA.update!(events,reinterpret(UInt8,[ws.iterations,ws.scratch.selected_row,ws.scratch.selected_entering]))
            SHA.update!(events,reinterpret(UInt8,[ws.scratch.last_primal_step,ws.scratch.last_dual_step]))
            for values in (ws.basis.basic_indices,ws.basis.states,ws.primal,ws.reduced_costs,ws.costs,ws.pricing_weights)
                SHA.update!(events,reinterpret(UInt8,values))
            end
        end
    end
    diagnostics=trace ? JS.SimplexDiagnostics(;observer) : nothing
    ws=JS.initialize_workspace(problem,options;progress=JS.SimplexProgressContext(problem;diagnostics))
    # Identical entry preparation outside timing, including any auxiliary phase.
    preparation=JS.make_dual_feasible!(ws,JS._guard_stop_callback(()->false))
    isnothing(preparation) || error("Kernel entry preparation failed: $preparation")
    before=ws.iterations;before_refactors=ws.refactorizations
    context=JS.SolveContext(time_ns(),Inf,diagnostics,ws.progress.numerical_policy)
    stop=JS._guard_stop_callback(entry_stop(context))
    entry_hash=state_hash(ws)
    GC.gc(true)
    capturing[]=trace
    measured=@timed JS._dual_optimize!(ws,stop)
    capturing[]=false
    @assert measured.value.status==JS.OPTIMAL
    @assert JS._original_primal_feasible(problem,ws.primal[1:size(problem.A,2)],options.primal_tolerance)
    @assert ws.iterations > before
    return Dict("trace"=>trace,"event_count"=>event_count[],"completion_states_hash"=>bytes2hex(SHA.digest!(events)),"events_hash"=>bytes2hex(SHA.digest!(names)),"event_counts"=>event_counts,"entry_state_hash"=>entry_hash,"refactorizations"=>ws.refactorizations-before_refactors,"manager"=>string(manager),"steps"=>ws.iterations-before,
                "entry_iterations"=>before,"seconds"=>measured.time,"compile_seconds"=>measured.compile_time,
                "bytes"=>measured.bytes,"allocations"=>Base.gc_alloc_count(measured.gcstats),
                "gc_seconds"=>measured.gctime,"state_hash"=>state_hash(ws))
end

function state_hash(ws)
    h=SHA.SHA2_256_CTX()
    for values in (ws.basis.basic_indices,ws.basis.states,ws.primal,ws.reduced_costs,ws.costs,ws.pricing_weights)
        SHA.update!(h,reinterpret(UInt8,values))
    end
    return bytes2hex(SHA.digest!(h))
end

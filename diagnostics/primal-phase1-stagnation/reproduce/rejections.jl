using JSimplex, Serialization, LinearAlgebra, Logging, TOML, SHA
const J=JSimplex
include("intervention.jl")
length(ARGS)==4 || error("Expected: snapshot steps seconds output_prefix")
const PREFIX=abspath(ARGS[4])
ispath(PREFIX*".toml") && error("Output exists")
const START=Ref(0)
const CURRENT=Ref{Any}(nothing)
const COUNTS=Dict{String,Int}()
const SAVED=Ref(false)
const TRACE_START=1110
function observe_candidate(ws,col)
    k=ws.iterations-START[]+1
    k<TRACE_START && return
    j=ws.scratch.selected_entering
    implied=ws.costs[j]
    for (r,i) in enumerate(ws.basis.basic_indices);implied-=ws.costs[i]*col[r];end
    CURRENT[]=(k=k,j=j,price=ws.reduced_costs[j],implied=implied,
        valid=ws.scratch.steepest_valid[j],weight=ws.pricing_weights[j],
        actual=last(J._primal_direction_weight(col)),norm=norm(col,Inf),
        refs=ws.refactorizations,updates=length(ws.factorization.updates))
end
function reject_probe(ws,col,reason,row=ws.scratch.selected_row)
    ws.iterations-START[]+1<TRACE_START && return
    label=string(reason)
    COUNTS[label]=get(COUNTS,label,0)+1
    s=CURRENT[]
    pivot=row>0 ? col[row] : NaN
    # No factor solves or pricing changes occur inside these probes.
    println("REJECT reason=",reason," candidate=",s," row=",row," pivot=",pivot,
        " tableau_pivot=",row>0 ? ws.scratch.tableau_row[s.j] : NaN)
    if !SAVED[] && s.k>=1140 && reason==:pivot_row
        saved=(problem=ws.problem,options=ws.options,basis=deepcopy(ws.basis),
            costs=copy(ws.costs),lower=copy(ws.lower),upper=copy(ws.upper),primal=copy(ws.primal),
            prices=copy(ws.reduced_costs),pricing_weights=copy(ws.pricing_weights),
            steepest_valid=copy(ws.scratch.steepest_valid),steepest_initialized=ws.scratch.steepest_initialized,
            factorization=ws.factorization,iteration=ws.iterations,entering=s.j,row=row,
            direction=copy(col),rho=copy(ws.scratch.rho),tableau=copy(ws.scratch.tableau_row),
            rejected_entering=copy(ws.scratch.rejected_entering),metadata=s)
        serialize(PREFIX*".rejected.bin",saved)
        SAVED[]=true
        println("SNAPSHOT ",PREFIX*".rejected.bin")
    end
end
function replace_once(s,old,new)
    count(old,s)==1 || error("Instrumentation anchor changed: "*old)
    replace(s,old=>new;count=1)
end
# Re-evaluate only two methods with observational hooks; production files stay unchanged.
source=read(joinpath(dirname(pathof(J)),"primal_simplex.jl"),String)
a=findfirst("function _legacy_primal_reject_candidate!",source).start
b=findfirst("function _primal_optimize!",source).start
instrumented=source[a:prevind(source,b)]
instrumented=replace_once(instrumented,
    "defer_weak::Bool, reason::Symbol, message::String) where {T}",
    "defer_weak::Bool, reason::Symbol, message::String) where {T}\n    Main.reject_probe(workspace,column,occursin(\"reduced cost\",message) ? :direction_price : reason==:refactor_pivot ? :unresolved_pivot : :pivot_row, occursin(\"reduced cost\",message) ? 0 : workspace.scratch.selected_row)")
instrumented=replace_once(instrumented,
    "    if _legacy_primal_row_validation_enabled(workspace) &&",
    "    Main.observe_candidate(workspace,tableau_column)\n    if _legacy_primal_row_validation_enabled(workspace) &&")
instrumented=replace_once(instrumented,
    "    leaving_row == -1 && return DualTermination(NUMERICAL_ERROR, \"primal ratio test is inconclusive\")",
    "    if leaving_row == -1\n        Main.reject_probe(workspace,tableau_column,:ratio,leaving_row)\n        return DualTermination(NUMERICAL_ERROR, \"primal ratio test is inconclusive\")\n    end")
instrumented=replace_once(instrumented,
    "            throw(_PivotRejection(leaving_row, entering, :defer_weak))",
    "            Main.reject_probe(workspace,tableau_column,:defer_weak,leaving_row)\n            throw(_PivotRejection(leaving_row, entering, :defer_weak))")
instrumented=replace_once(instrumented,
    "        if !checked_pivot && abs(tableau_column[leaving_row]) <= workspace.options.zero_tolerance",
    "        if !checked_pivot && abs(tableau_column[leaving_row]) <= workspace.options.zero_tolerance\n            Main.reject_probe(workspace,tableau_column,:zero_tolerance,leaving_row)")
install_intervention("preserve_structural")
Base.include_string(J,instrumented,"phase1-observational-hooks.jl")
function run(path,steps,seconds)
    d=deserialize(path)
    START[]=d.iteration
    observer=function(event,ws)
        if event==:pivot_completed && ws.iterations-START[]>=TRACE_START
            println("ACCEPT k=",ws.iterations-START[]," candidate=",CURRENT[]," step=",ws.scratch.last_primal_step," row=",ws.scratch.selected_row)
        end
    end
    diagnostics=J.SimplexDiagnostics(;observer)
    ws=J.initialize_workspace(d.problem,d.options;progress=J.SimplexProgressContext(d.problem;diagnostics))
    ws.basis=deepcopy(d.basis);ws.costs.=d.costs;ws.lower.=d.lower;ws.upper.=d.upper;ws.primal.=d.primal;ws.iterations=d.iteration
    point=copy(ws.primal[ws.basis.basic_indices]);J.recompute!(ws;refactorize=true);J._restore_legacy_primal_point!(ws,point,()->false)
    cert=point_certificate(ws);point_certified(ws,cert)||error("Uncertified initial point")
    ws.scratch.steepest_initialized=true;fill!(ws.scratch.steepest_valid,false)
    start=time_ns();stop=()->(time_ns()-start)/1e9>=seconds
    terminal=nothing
    for k in 1:steps
        stop() && break
        J._finite_workspace(ws) && J.primal_infeasibility(ws)<=ws.options.primal_tolerance || error("Invalid point before iteration")
        terminal=J._primal_iteration!(ws,stop,0.0)
        if k%100==0;println("PROGRESS k=",k," objective=",dot(ws.costs,ws.primal)," refs=",ws.refactorizations);flush(stdout);end
        isnothing(terminal)||break
    end
    cert=point_certificate(ws)
    report=Dict("input_snapshot_sha256"=>bytes2hex(open(sha256,path)),"script_sha256"=>bytes2hex(open(sha256,@__FILE__)),
        "objective"=>dot(ws.costs,ws.primal),"iterations"=>ws.iterations-START[],"refactorizations"=>ws.refactorizations,
        "terminal"=>isnothing(terminal) ? "STEP_LIMIT" : string(terminal.status),"certificate"=>Dict(string(k)=>v for (k,v) in pairs(cert)),
        "counts"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0),"rejection_reasons"=>COUNTS)
    open(PREFIX*".toml","w") do io;TOML.print(io,report);end
    println("FINAL ",report)
end
with_logger(NullLogger()) do
    run(ARGS[1],parse(Int,ARGS[2]),parse(Float64,ARGS[3]))
end

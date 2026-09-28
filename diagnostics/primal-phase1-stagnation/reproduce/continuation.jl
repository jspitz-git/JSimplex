using JSimplex, Serialization, LinearAlgebra, TOML, SHA, Logging
const J = JSimplex
include("intervention.jl")
length(ARGS)==5 || error("Expected: snapshot mode seconds steps output.toml")
install_intervention(ARGS[2])
function run(path,mode,seconds,steps,output)
    ispath(output) && error("Output exists")
    d=deserialize(path)
    diagnostics=J.SimplexDiagnostics()
    ws=J.initialize_workspace(d.problem,d.options;progress=J.SimplexProgressContext(d.problem;diagnostics))
    ws.basis=deepcopy(d.basis);ws.costs.=d.costs;ws.lower.=d.lower;ws.upper.=d.upper;ws.primal.=d.primal
    ws.iterations=d.iteration
    point=copy(ws.primal[ws.basis.basic_indices])
    before=point_certificate(ws);saved=copy(ws.primal)
    J.recompute!(ws;refactorize=true)
    restored=J._restore_legacy_primal_point!(ws,point,()->false)
    after=point_certificate(ws)
    println("RESTORE before=",before," after=",after," preserved=",restored," delta_inf=",norm(ws.primal-saved,Inf))
    point_certified(ws,after) || error("Uncertified restored point; no continuation")
    ws.scratch.steepest_initialized=true;fill!(ws.scratch.steepest_valid,false)
    start=time_ns();stop=()->(time_ns()-start)/1e9>=seconds
    initial=dot(ws.costs,ws.primal); terminal=nothing; completed=0
    println("START mode=",mode," objective=",initial);flush(stdout)
    for k in 1:steps
        if stop()
            terminal=J.DualTermination(TIME_LIMIT,"diagnostic time limit")
            break
        end
        if !J._finite_workspace(ws) || J.primal_infeasibility(ws)>ws.options.primal_tolerance
            terminal=J.DualTermination(NUMERICAL_ERROR,"invalid point before diagnostic iteration")
            break
        end
        terminal=J._primal_iteration!(ws,stop,0.0)
        completed=k
        if k<=4 || k%100==0 || !isnothing(terminal)
            println("STEP ",k," objective=",dot(ws.costs,ws.primal)," refs=",ws.refactorizations,
                " pinf=",J.primal_infeasibility(ws)," terminal=",terminal);flush(stdout)
        end
        isnothing(terminal) || break
    end
    certificate=point_certificate(ws)
    println("ENDPOINT ",certificate)
    report=Dict("mode"=>mode,"snapshot"=>abspath(path),"snapshot_sha256"=>bytes2hex(open(sha256,path)),
        "julia"=>string(VERSION),"source"=>pathof(J),"initial_objective"=>initial,
        "final_objective"=>dot(ws.costs,ws.primal),"seconds"=>(time_ns()-start)/1e9,
        "iterations"=>ws.iterations-d.iteration,"calls"=>completed,"refactorizations"=>ws.refactorizations,
        "terminal"=>isnothing(terminal) ? "STEP_LIMIT" : string(terminal.status),
        "phase_primal_certified"=>certificate.phase_primal,
        "row_consistent"=>certificate.row_consistent,"max_bound_violation"=>certificate.max_bound_violation,
        "finite"=>certificate.finite,"point_certified"=>point_certified(ws,certificate),
        "source_sha256"=>Dict(f=>bytes2hex(open(sha256,joinpath(dirname(pathof(J)),f))) for f in ("simplex.jl","primal_simplex.jl","legacy_primal_point.jl","legacy_primal_pivot.jl")),
        "diagnostic_sha256"=>Dict(f=>bytes2hex(open(sha256,joinpath(@__DIR__,f))) for f in ("continuation.jl","intervention.jl")),
        "counts"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0))
    serialize(output*".bin",(problem=ws.problem,options=ws.options,basis=ws.basis,costs=ws.costs,
        lower=ws.lower,upper=ws.upper,primal=ws.primal,iteration=ws.iterations,pricing_weights=ws.pricing_weights))
    open(output,"w") do io;TOML.print(io,report);end
    println("FINAL ",report)
end
with_logger(NullLogger()) do
    run(ARGS[1],ARGS[2],parse(Float64,ARGS[3]),parse(Int,ARGS[4]),ARGS[5])
end

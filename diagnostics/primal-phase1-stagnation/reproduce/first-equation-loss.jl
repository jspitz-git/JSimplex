using JSimplex, Serialization, Logging, LinearAlgebra, TOML, SHA
const J=JSimplex
include("../../ft-numerical-recovery/reproduce/capture-failure.jl")
include("intervention.jl")
include("residual-intervention.jl")
length(ARGS) in (4,5) || error("Expected: input baseline|finite_residual|finite_residual_before_fix seconds output_prefix [certified_iteration_limit]")
input,mode,seconds,prefix=ARGS[1:4]
target=length(ARGS)==5 ? parse(Int,ARGS[5]) : typemax(Int)
mode in ("baseline","finite_residual","finite_residual_before_fix") || error("Unknown diagnostic mode")
lowercase(basename(realpath(input))) in ("big.mps","largo.mps","anymod.mps") && error("Excluded model")
require_fresh_output(prefix)
startswith(mode,"finite_residual") && install_residual_intervention()
if mode=="finite_residual_before_fix"
    # Reproduce the old bound-only early return without editing solver files.
    @eval JSimplex _legacy_primal_equation_violation(workspace::SimplexWorkspace{T}) where {T<:Union{Float32,Float64}} = false
end
options=SolverOptions(algorithm=:primal,basis_update=:pfi,basis_refactorization=:native,
    pricing=:steepest_edge,simplex_strategy=:legacy,refactorization_interval=80,
    iteration_limit=1_000_000,time_limit=parse(Float64,seconds),verbose=false)
with_logger(NullLogger()) do
    solve(read_mps("test/fixtures/solver/afiro.mps");options,relax_integrality=true)
end
active=Ref{Any}(nothing);previous=Ref{Any}(nothing);transition=Ref{Any}(nothing)
checks=Ref(0);cert_seconds=Ref(0.0);found=Ref(false);phase_starts=Ref(0)
observer=function(event,ws)
    if event==:phase_one
        phase_starts[]+=1
        phase_starts[]==1 || error("Unexpected phase-I restart during first-loss capture")
        active[]=ws;previous[]=nothing
    end
    ws===active[] || return
    if event in (:pivot_completed,:flip_completed)
        # The basis has changed, but the primal vector still precedes recomputation.
        transition[]=(iteration=ws.iterations,event=event,row=ws.scratch.selected_row,
            entering=ws.scratch.selected_entering,step=ws.scratch.last_primal_step,
            direction=copy(ws.scratch.row_solution),basis=deepcopy(ws.basis),
            primal=copy(ws.primal))
    elseif event==:pricing
        started=time_ns();cert=point_certificate(ws);cert_seconds[]+=(time_ns()-started)/1e9
        checks[]+=1
        if !point_certified(ws,cert)
            capture_snapshot(prefix*".failed.bin",ws;reason=:first_equation_loss)
            serialize(prefix*".previous.bin",previous[])
            serialize(prefix*".transition.bin",transition[])
            report=Dict("mode"=>mode,"status"=>"FIRST_LOSS","iteration"=>ws.iterations,"refactorizations"=>ws.refactorizations,
                "checks"=>checks[],"certificate_seconds"=>cert_seconds[],"certificate"=>Dict(string(k)=>v for (k,v) in pairs(cert)),
                "objective"=>dot(ws.costs,ws.primal),"input_sha256"=>bytes2hex(open(sha256,input)),
                "source_revision"=>source_revision(),"script_sha256"=>bytes2hex(open(sha256,@__FILE__)))
            open(prefix*".toml","w") do io;TOML.print(io,report);end
            println("FIRST_LOSS ",report);flush(stdout);found[]=true
            error("Diagnostic first equation loss")
        end
        if ws.iterations>=target
            capture_snapshot(prefix*".limit.bin",ws;reason=:certified_iteration_limit)
            report=Dict("mode"=>mode,"status"=>"CERTIFIED_LIMIT","iteration"=>ws.iterations,
                "checks"=>checks[],"certificate_seconds"=>cert_seconds[],"refactorizations"=>ws.refactorizations,
                "certificate"=>Dict(string(k)=>v for (k,v) in pairs(cert)),"objective"=>dot(ws.costs,ws.primal),
                "input_sha256"=>bytes2hex(open(sha256,input)),"source_revision"=>source_revision(),
                "source_sha256"=>bytes2hex(open(sha256,joinpath(dirname(pathof(J)),"legacy_primal_point.jl"))),
                "script_sha256"=>bytes2hex(open(sha256,@__FILE__)))
            open(prefix*".toml","w") do io;TOML.print(io,report);end
            println("CERTIFIED_LIMIT ",report);flush(stdout);found[]=true
            error("Diagnostic certified iteration limit")
        end
        previous[]=(iteration=ws.iterations,refactorizations=ws.refactorizations,
            primal=copy(ws.primal),basis=deepcopy(ws.basis),certificate=cert)
        if ws.iterations%500==0
            println("CHECK iteration=",ws.iterations," checks=",checks[]," certificate_seconds=",cert_seconds[]);flush(stdout)
        end
    end
end
try
    result=J._solve_diagnosed(read_mps(input),J.SimplexDiagnostics(;observer);options,relax_integrality=true)
    println("TERMINAL status=",result.status," message=",result.message," checks=",checks[])
catch e
    found[] && e isa J.DiagnosticObserverFailure || rethrow()
    println("STOP ",e)
end
found[] || error("No loss captured within the diagnostic limit")

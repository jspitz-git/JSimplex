using JSimplex,Serialization,Logging,LinearAlgebra
const J=JSimplex
include("../../ft-numerical-recovery/reproduce/capture-failure.jl")
include("intervention.jl")
include("residual-intervention.jl")
install_residual_intervention(;trace=true)
length(ARGS)==3 || error("Expected: input seconds output_prefix")
input,seconds,prefix=ARGS
lowercase(basename(realpath(input))) in ("big.mps","largo.mps","anymod.mps") && error("Excluded model")
require_fresh_output(prefix)
options=SolverOptions(algorithm=:primal,basis_update=:pfi,basis_refactorization=:native,pricing=:steepest_edge,simplex_strategy=:legacy,refactorization_interval=80,iteration_limit=1_000_000,time_limit=parse(Float64,seconds),verbose=false)
with_logger(NullLogger()) do
    solve(read_mps("test/fixtures/solver/afiro.mps");options,relax_integrality=true)
end
saved=Ref(false)
latest=Ref{Any}(nothing)
observer=function(reason,ws)
    old=latest[];latest[]=ws
    if saved[] && !isnothing(old) && old !== ws && old.iterations>=3683
        old.iterations==3683 || error("Unexpected regression iteration")
        capture_snapshot(prefix*".after.bin",old;reason=:regression)
        error("Diagnostic stop before restart")
    elseif reason==:pricing && ws.iterations==3682 && !saved[]
        capture_snapshot(prefix*".before.bin",ws;reason=:before_regression)
        saved[]=true
        println("PRE_CERT ",point_certificate(ws));flush(stdout)
    elseif saved[] && reason==:pricing && ws.iterations>=3683
        ws.iterations==3683 || error("Unexpected target iteration")
        capture_snapshot(prefix*".after.bin",ws;reason=:after_target_pivot)
        error("Diagnostic stop after target pivot")
    end
end
try
    J._solve_diagnosed(read_mps(input),J.SimplexDiagnostics(;observer);options,relax_integrality=true)
catch e
    e isa J.DiagnosticObserverFailure && occursin("Diagnostic stop",sprint(showerror,e)) || rethrow()
    println("STOP ",e)
end

isfile(prefix*".before.bin") && isfile(prefix*".after.bin") || error("Target snapshot pair was not captured")

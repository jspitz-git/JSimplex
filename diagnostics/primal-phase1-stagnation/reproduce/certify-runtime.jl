using JSimplex, Serialization, Logging, LinearAlgebra, TOML, SHA
const J = JSimplex
include("../../ft-numerical-recovery/reproduce/capture-failure.jl")
include("intervention.jl")

length(ARGS) == 4 || error("Expected: runtime.mps manager seconds output_prefix")
input, manager, seconds, prefix = ARGS
require_fresh_output(prefix)
input_hash = bytes2hex(open(sha256, input))
input_hash == "d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68" ||
    error("This diagnostic requires the recorded runtime input")
options = SolverOptions(algorithm=:primal, basis_update=Symbol(manager),
    basis_refactorization=:native, pricing=:steepest_edge, simplex_strategy=:legacy,
    refactorization_interval=80, iteration_limit=1_000_000,
    time_limit=parse(Float64, seconds), verbose=false)
with_logger(NullLogger()) do
    solve(read_mps("test/fixtures/solver/afiro.mps"); options, relax_integrality=true)
end
checks = Ref(0)
certificate_seconds = Ref(0.0)
last_iteration = Ref(-1)
last_certificate = Ref{Any}(nothing)
latest = Ref{Any}(nothing)
failed = Ref(false)
phases = Dict{String,Any}[]
observer = function(event, ws)
    latest[] = ws
    if event in (:phase_primal, :phase_one, :phase_cleanup)
        push!(phases, Dict("phase"=>string(event), "iteration"=>ws.iterations,
            "rows"=>size(ws.problem.A,1), "columns"=>size(ws.problem.A,2)))
        println("PHASE ", last(phases)); flush(stdout)
    elseif event == :pricing
        # Include fresh-factor retries, not only completed pivot boundaries.
        started = time_ns()
        cert = point_certificate(ws)
        certificate_seconds[] += (time_ns()-started)/1e9
        checks[] += 1
        last_iteration[] = ws.iterations
        last_certificate[] = cert
        if !point_certified(ws, cert)
            capture_snapshot(prefix*".failed.bin", ws; reason=:uncertified_pricing_point)
            failed[] = true
            error("Uncertified point before primal pricing")
        end
        if checks[] % 5000 == 0
            println("CHECK iteration=", ws.iterations, " checks=", checks[],
                " objective=", dot(ws.costs,ws.primal)); flush(stdout)
        end
    end
end
problem = read_mps(input)
diagnostics = J.SimplexDiagnostics(; observer, kernel_timing=true)
result = try
    J._solve_diagnosed(problem, diagnostics; options, relax_integrality=true)
catch exception
    failed[] && exception isa J.DiagnosticObserverFailure || rethrow()
    nothing
end
report = Dict{String,Any}("manager"=>manager, "input_sha256"=>input_hash,
    "source_revision"=>source_revision(), "script_sha256"=>bytes2hex(open(sha256,@__FILE__)),
    "source_sha256"=>Dict(name=>bytes2hex(open(sha256,joinpath(dirname(pathof(J)),name)))
        for name in ("legacy_primal_pivot.jl", "legacy_primal_point.jl", "primal_simplex.jl")),
    "julia"=>string(VERSION), "architecture"=>string(Sys.ARCH),
    "julia_threads"=>Threads.nthreads(), "blas_threads"=>BLAS.get_num_threads(),
    "time_limit"=>options.time_limit, "phase_starts"=>phases,
    "checks"=>checks[], "all_pricing_points_certified"=>checks[]>0 && !failed[],
    "last_checked_iteration"=>last_iteration[], "certificate_seconds"=>certificate_seconds[],
    "counts"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0))
if !isnothing(last_certificate[])
    report["last_certificate"] = Dict(string(k)=>v for (k,v) in pairs(last_certificate[]))
end
if isnothing(result)
    report["status"] = "UNCERTIFIED_POINT"
else
    report["status"] = string(result.status)
    report["message"] = result.message
    report["iterations"] = result.statistics.iterations
    report["refactorizations"] = result.statistics.refactorizations
    report["seconds"] = result.statistics.elapsed_seconds
    if result.status == OPTIMAL
        report["objective"] = result.objective_value
        report["original_primal_certified"] = J._original_primal_feasible(
            problem,result.primal,options.primal_tolerance)
    end
end
if !isnothing(latest[])
    ws = latest[]
    report["last_working_objective"] = dot(ws.costs,ws.primal)
    # A deadline can interrupt reconstruction. Record this certificate
    # separately from those at points actually presented to pricing.
    terminal_cert = point_certificate(ws)
    report["terminal_point_certified"] = point_certified(ws,terminal_cert)
    report["terminal_certificate"] = Dict(string(k)=>v for (k,v) in pairs(terminal_cert))
    if !failed[]
        capture_snapshot(prefix*".terminal.bin", ws; reason=:diagnostic_terminal)
    end
end
open(prefix*".toml", "w") do io
    TOML.print(io, report)
end
println("FINAL ", report)
failed[] && error("Pricing-point certificate failed; see diagnostic report")

using JSimplex, LinearAlgebra, Logging, TOML, SHA
const J = JSimplex
include("../../ft-numerical-recovery/reproduce/capture-failure.jl")

function capture_runtime(input, seconds, prefix)
    require_fresh_output(prefix)
    input_hash = bytes2hex(open(sha256, input))
    @assert input_hash == "d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68"
    options = SolverOptions(algorithm=:dual, basis_update=:pfi,
        basis_refactorization=:native, pricing=:steepest_edge, simplex_strategy=:legacy,
        refactorization_interval=80, iteration_limit=1_000_000,
        time_limit=parse(Float64, seconds), verbose=true)
    environment = capture_environment()
    environment["input_sha256"] = input_hash
    environment["source_sha256"] = Dict(name=>bytes2hex(open(sha256,joinpath(dirname(pathof(J)),name)))
        for name in ("dual_simplex.jl", "simplex.jl", "simplex_driver.jl", "simplex_recovery.jl", "native_cleanup_recovery.jl")
        if isfile(joinpath(dirname(pathof(J)),name)))
    open(prefix*".environment.toml", "w") do io
        TOML.print(io, environment)
    end
    with_logger(NullLogger()) do
        solve(read_mps("test/fixtures/solver/afiro.mps"); options, relax_integrality=true)
    end
    latest = Ref{Any}(nothing)
    saved = Set{Tuple{Symbol,Int,Int}}()
    function record(ws, event)
        println("TRACE event=", event, " iter=", ws.iterations,
            " offset=",ws.progress.iteration_offset," algorithm=",ws.options.algorithm,
            " pinf=",J.primal_infeasibility_summary(ws),
            " dinf=",J.dual_infeasibility_summary(ws),
            " original_bounds=",J._original_bounds_active(ws),
            " original_costs=",J._original_costs_active(ws),
            " working_objective=",dot(ws.costs,ws.primal),
            " perturbed=",ws.perturbed," refs=",ws.refactorizations)
        flush(stdout)
    end
    function save(ws,event)
        key=(event,ws.progress.iteration_offset,ws.iterations)
        key in saved && return
        length(saved) >= 12 && return
        push!(saved,key)
        file=prefix*"."*string(event)*"."*string(key[2])*"."*string(key[3])*".bin"
        capture_snapshot(file,ws;reason=event,provenance=(input_sha256=input_hash,
            source_revision=source_revision(),scratch=ws.scratch,
            refactorizations=ws.refactorizations,devex_reference=ws.devex_reference,
            zero_dual_step_streak=ws.zero_dual_step_streak,
            dual_pricing_fallback=ws.dual_pricing_fallback,
            dual_devex_fallback=ws.dual_devex_fallback,
            dual_refactorization_interval=ws.dual_refactorization_interval,
            iteration_offset=ws.progress.iteration_offset,
            numerical_policy=ws.progress.numerical_policy,scaling=ws.progress.scaling,
            original_objective=ws.progress.objective,
            original_objective_constant=ws.progress.objective_constant))
        println("SNAPSHOT ",file); flush(stdout)
    end
    observer=function(event,ws)
        latest[]=ws
        if event in (:phase_dual,:phase_auxiliary,:phase_primal,:phase_cleanup,
                     :feasibility_recovery,:certification_failed)
            record(ws,event)
            event in (:phase_cleanup,:feasibility_recovery,:certification_failed) && save(ws,event)
        elseif event == :pricing && ws.progress.iteration_offset == 0 && ws.iterations == 62400
            record(ws,:before_terminal); save(ws,:before_terminal)
        end
    end
    diagnostics=J.SimplexDiagnostics(;observer)
    problem=read_mps(input)
    result=J._solve_diagnosed(problem,diagnostics;options,relax_integrality=true)
    if !isnothing(latest[])
        record(latest[],:terminal); save(latest[],:terminal)
    end
    report=Dict{String,Any}("status"=>string(result.status),"message"=>result.message,
        "iterations"=>result.statistics.iterations,"seconds"=>result.statistics.elapsed_seconds,
        "counts"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0))
    if result.status == OPTIMAL
        report["objective"]=result.objective_value
        report["original_primal_certified"]=J._original_primal_feasible(problem,result.primal,options.primal_tolerance)
    end
    open(prefix*".toml","w") do io
        TOML.print(io,report)
    end
    println("RESULT ",report)
end
abspath(PROGRAM_FILE) == (@__FILE__) && capture_runtime(ARGS...)

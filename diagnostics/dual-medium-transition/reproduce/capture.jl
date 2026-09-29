using JSimplex, LinearAlgebra, Logging, TOML, SHA
const J = JSimplex
include("../../ft-numerical-recovery/reproduce/capture-failure.jl")

struct TransitionCaptureComplete <: Exception end

function capture_transition(args=ARGS)
    length(args) == 4 || error("Expected: medium.mps manager seconds output_prefix")
    input, manager, seconds, prefix = args
    require_fresh_output(prefix)
    input_hash = bytes2hex(open(sha256, input))
    input_hash == "79c374a584b1463305cf4b0faee8920d0364df2dd5d0468a44ab58d9e9d49dc0" ||
        error("This diagnostic requires the recorded medium input")
    options = SolverOptions(algorithm=:dual, basis_update=Symbol(manager),
        basis_refactorization=:native, pricing=:steepest_edge, simplex_strategy=:legacy,
        refactorization_interval=80, iteration_limit=1_000_000,
        time_limit=parse(Float64, seconds), verbose=true)
    environment = capture_environment()
    merge!(environment, Dict("input_sha256"=>input_hash, "manager"=>manager,
        "time_limit"=>options.time_limit, "iteration_limit"=>options.iteration_limit,
        "algorithm"=>"dual", "strategy"=>"legacy", "pricing"=>"steepest_edge",
        "basis_refactorization"=>"native", "interval"=>80,
        "source_sha256"=>Dict(name=>bytes2hex(open(sha256,joinpath(dirname(pathof(J)),name)))
            for name in ("dual_simplex.jl", "simplex.jl", "simplex_pivot.jl"))))
    open(prefix*".environment.toml", "w") do io
        TOML.print(io, environment)
    end
    with_logger(NullLogger()) do
        solve(read_mps("test/fixtures/solver/afiro.mps"); options, relax_integrality=true)
    end
    records = Dict{String,Any}[]
    snapshots = String[]
    auxiliary = Ref{Any}(nothing)
    latest = Ref{Any}(nothing)
    saved_auxiliary = Ref(false)
    handoff_iteration = Ref(-1)
    completed = Ref(false)
    function record(ws, event)
        ps, pc = J.primal_infeasibility_summary(ws)
        ds, dc = J.dual_infeasibility_summary(ws)
        original_objective = J._progress_objective_value(ws.progress,
            J.unscale_primal(ws.progress.scaling,
                @view(ws.primal[1:length(ws.progress.objective)])))
        row = Dict{String,Any}("event"=>string(event), "iteration"=>ws.iterations,
            "workspace_id"=>string(objectid(ws)), "staged"=>J._is_staged_workspace(ws),
            "original_bounds"=>J._original_bounds_active(ws),
            "original_costs"=>J._original_costs_active(ws), "perturbed"=>ws.perturbed,
            "working_objective"=>dot(ws.costs,ws.primal),
            "logged_objective"=>original_objective,
            "primal_sum"=>ps, "primal_count"=>pc,
            "dual_sum"=>ds, "dual_count"=>dc,
            "primal_step"=>ws.scratch.last_primal_step,
            "dual_step"=>ws.scratch.last_dual_step,
            "pricing_effective"=>string(J._effective_pricing(ws,:dual)),
            "zero_dual_streak"=>ws.zero_dual_step_streak,
            "refactorizations"=>ws.refactorizations)
        push!(records,row)
        open(prefix*".trace.toml","w") do io
            TOML.print(io,Dict("records"=>records))
        end
        println("TRACE ",row); flush(stdout)
    end
    function save(ws, reason)
        path=prefix*"."*string(reason)*".bin"
        capture_snapshot(path,ws;reason,provenance=(input_sha256=input_hash,
            source_revision=source_revision(), effective_pricing=J._effective_pricing(ws,:dual),
            zero_dual_step_streak=ws.zero_dual_step_streak,
            dual_pricing_fallback=ws.dual_pricing_fallback,
            dual_devex_fallback=ws.dual_devex_fallback,
            dual_refactorization_interval=ws.dual_refactorization_interval,
            devex_reference=copy(ws.devex_reference),
            scaling=ws.progress.scaling, original_objective=copy(ws.progress.objective),
            original_objective_constant=ws.progress.objective_constant))
        push!(snapshots,path)
        println("SNAPSHOT ",path); flush(stdout)
    end
    observer = function(event,ws)
        latest[]=ws
        if event == :phase_auxiliary
            auxiliary[]=ws
        end
        if event in (:phase_dual,:phase_auxiliary,:phase_one,:phase_primal,:phase_cleanup,
                     :pricing_dantzig,:pricing_devex,:perturbation,:restore_perturbations,
                     :certification_failed)
            record(ws,event)
        end
        # A forwarded refactor event precedes reconstruction in the private
        # handoff candidate. Save the completed auxiliary workspace separately.
        if !isnothing(auxiliary[]) && ws !== auxiliary[] &&
           auxiliary[].iterations > 0 && !saved_auxiliary[]
            record(auxiliary[],:auxiliary_before_handoff)
            save(auxiliary[],:auxiliary_before_handoff)
            saved_auxiliary[]=true
            record(ws,:first_nonauxiliary_event_before_values)
        end
        if event == :pricing
            if !isnothing(auxiliary[]) && ws !== auxiliary[] && handoff_iteration[] < 0 &&
               J._original_bounds_active(ws)
                handoff_iteration[]=ws.iterations
                record(ws,:original_bounds_first_pricing)
                save(ws,:original_bounds_first_pricing)
            end
            if ws.iterations in (35040,35050,35051,35052)
                record(ws,:transition_window)
                # One pre-transition backup also covers a same-workspace failure.
                ws.iterations == 35040 && !isfile(prefix*".iteration_35040.bin") &&
                    save(ws,:iteration_35040)
            end
            if handoff_iteration[] >= 0 && ws.iterations >= handoff_iteration[]+2000
                record(ws,:original_bounds_after_2000)
                save(ws,:original_bounds_after_2000)
                completed[]=true
                throw(TransitionCaptureComplete())
            end
        elseif event == :pivot_completed && ws.iterations % 1000 == 0
            record(ws,:progress)
        end
    end
    problem=read_mps(input)
    diagnostics=J.SimplexDiagnostics(;observer,kernel_timing=true)
    result=try
        J._solve_diagnosed(problem,diagnostics;options,relax_integrality=true)
    catch exception
        exception isa J.DiagnosticObserverFailure &&
            exception.cause isa TransitionCaptureComplete || rethrow()
        nothing
    end
    if !completed[] && !isnothing(latest[])
        record(latest[],:terminal)
        save(latest[],:terminal)
    end
    report=merge(environment,Dict{String,Any}(
        "status"=>isnothing(result) ? "DIAGNOSTIC_STOP" : string(result.status),
        "handoff_iteration"=>handoff_iteration[], "snapshots"=>snapshots,
        "records"=>records, "counts"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0),
        "peak_rss"=>Sys.maxrss(),
        "kernel_seconds"=>Dict(string(k)=>v/1e9 for (k,v) in diagnostics.kernel_nanoseconds if v!=0)))
    if !isnothing(result)
        report["iterations"]=result.statistics.iterations
        report["seconds"]=result.statistics.elapsed_seconds
        report["message"]=result.message
    end
    open(prefix*".toml","w") do io
        TOML.print(io,report)
    end
    println("FINAL status=",report["status"]," handoff_iteration=",handoff_iteration[])
end
abspath(PROGRAM_FILE)==(@__FILE__) && capture_transition()

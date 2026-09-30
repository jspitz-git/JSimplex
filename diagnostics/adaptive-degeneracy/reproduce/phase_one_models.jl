using JSimplex, Logging, LinearAlgebra, SparseArrays, SHA, TOML
BLAS.set_num_threads(1)

include(joinpath(@__DIR__,"pricing_isolation.jl"))

const ISOLATED_METHOD_SHA256 = isolate_pricing_trials!()

function main(args=ARGS)
    name, method, variant, seconds_text, output = args
    @assert variant in ("none","perturb","pricing","both")
    perturb = variant in ("perturb","both")
    pricing = variant in ("pricing","both")
    name in ("runtime", "medium") || error("Unsupported model")
    algorithm = Symbol(method)
    algorithm in (:primal,:dual) || error("Unsupported algorithm")
    path = "/home/jspitz/mps/" * name * ".mps"
    digest = bytes2hex(open(sha256,path))
    @assert digest == (name == "runtime" ?
        "d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68" :
        "79c374a584b1463305cf4b0faee8920d0364df2dd5d0468a44ab58d9e9d49dc0")
    policy = JSimplex.NumericalPolicy(Float64;adaptive_stalling=true,adaptive_pricing=pricing,
        adaptive_primal_perturbation=perturb,adaptive_dual_perturbation=perturb,phase_one=true,
        refactor_timing=false)
    @assert all(s -> getfield(policy,s) == (s in (:adaptive_stalling,:phase_one) ||
        (pricing && s == :adaptive_pricing) ||
        (perturb && s in (:adaptive_primal_perturbation,:adaptive_dual_perturbation))),
        JSimplex.NUMERICAL_SWITCHES)
    probe = LinearProblem(sparse([1e-10 -1.0;1.0 0.0]),[-2.0,-1.0];
        row_upper=[0.0,Inf],column_upper=[1.0,1.0])
    check = JSimplex.initialize_workspace(probe,SolverOptions(algorithm=:primal,pricing=:dantzig,verbose=false);
        progress=JSimplex.SimplexProgressContext(probe;numerical_policy=policy))
    @assert isnothing(JSimplex._primal_iteration!(check,()->false,check.options.dual_tolerance))
    @assert check.basis.basic_indices == [1,4]
    options = SolverOptions(;algorithm,pricing=:steepest_edge,basis_update=:pfi,
        basis_refactorization=:native,refactorization_interval=80,
        iteration_limit=1_000_000,time_limit=parse(Float64,seconds_text),verbose=false,simplex_strategy=:adaptive)
    # Compile common solve paths separately. Timings are diagnostic, not a benchmark.
    with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(read_mps("test/fixtures/solver/afiro.mps"),nothing;
            options,numerical_policy=policy,relax_integrality=true)
    end
    problem = read_mps(path)
    records = Dict{String,Any}[]
    last = Ref{Any}(nothing)
    last_workspace = Ref{Any}(nothing)
    transitions = Set((:pricing_dantzig,:pricing_steepest_edge,:pricing_devex,
        :pricing_progress_return,:pricing_trial_expired,:pricing_phase_reset,
        :phase_one,:phase_auxiliary,:phase_primal,:phase_dual,:phase_cleanup,
        :perturbation,:restore_perturbations,:stagnation_stalled,:stagnation_cost_rebase))
    observer = function(event,ws)
        last_workspace[] = ws
        if event == :final_observed_workspace || event in transitions || (event == :pivot_completed && ws.iterations % 1000 == 0)
            state = ws.scratch.pricing
            active_algorithm = isnothing(state) || state.algorithm == :none ? ws.options.algorithm : state.algorithm
            mode = JSimplex._effective_pricing(ws,active_algorithm)
            ps,pc = JSimplex.primal_infeasibility_summary(ws)
            ds,dc = JSimplex.dual_infeasibility_summary(ws)
            record = Dict{String,Any}("event"=>string(event),"iteration"=>ws.iterations,
                "iteration_offset"=>ws.progress.iteration_offset,
                "total_iterations"=>ws.iterations+ws.progress.iteration_offset,
                "rows"=>size(ws.problem.A,1),"columns"=>size(ws.problem.A,2),
                "objective"=>dot(ws.costs,ws.primal),"pinf"=>ps,"pinf_count"=>pc,
                "dinf"=>ds,"dinf_count"=>dc,"pricing"=>string(mode),
                "active_algorithm"=>string(active_algorithm),
                "workspace"=>string(objectid(ws)),
                "observation_kind"=>(event == :final_observed_workspace ? "uncertified_after_termination" : "event"),
                "primal_perturbation_allowed"=>ws.scratch.primal_perturbation_allowed,
                "dual_perturbation_allowed"=>ws.scratch.dual_perturbation_allowed,
                "bound_perturbation_active"=>JSimplex._has_active_bound_perturbations(ws.scratch.perturbations),
                "original_bounds_active"=>JSimplex._original_bounds_active(ws),
                "seconds"=>(time_ns()-ws.progress.start_ns)/1e9)
            journal = ws.scratch.perturbations
            if !isnothing(journal)
                record["cost_level"] = journal.level
                record["bound_level"] = isnothing(journal.bounds) ? 0 : journal.bounds.level
            end
            history = ws.scratch.stagnation
            if !isnothing(history)
                record["monitor"] = string(objectid(history.monitor))
                record["monitor_observations"] = history.monitor.observations
                record["monitor_state"] = string(history.monitor.state)
                record["monitor_value_scale"] = history.value_scale
                record["monitor_cost_scale"] = history.cost_scale
                for field in (:window, :window_count, :stalled_windows, :insignificant_steps,
                              :tolerance, :objective_improvement, :primal_improvement,
                              :dual_improvement,:best_primal,:end_primal,:best_objective,:end_objective)
                    record["monitor_" * string(field)] = getfield(history.monitor, field)
                end
            end
            if !isnothing(state)
                record["temporary"] = state.temporary
                record["return_mode"] = string(state.return_mode)
                record["transition"] = string(state.last_transition)
                record["observations"] = state.observations
                record["trial_until"] = state.trial_until
                @assert !state.temporary || state.framework_valid
                @assert !state.temporary || state.observations <= state.trial_until
                event == :pricing_phase_reset && @assert !state.temporary && state.observations == 0
            end
            push!(records,record)
            println("TRACE ",record); flush(stdout)
            last[] = record
        end
    end
    d = JSimplex.SimplexDiagnostics(;observer)
    timed = @timed with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(problem,d;options,numerical_policy=policy,relax_integrality=true)
    end
    result = timed.value
    isnothing(last_workspace[]) || observer(:final_observed_workspace,last_workspace[])
    report = Dict{String,Any}("input"=>path,"input_sha256"=>digest,"algorithm"=>method,
        "mode"=>variant,"weak_pivot_preference"=>false,"diagnostic_method_sha256"=>ISOLATED_METHOD_SHA256,
        "julia"=>string(VERSION),"architecture"=>string(Sys.ARCH),
        "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
        "time_limit"=>options.time_limit,"status"=>string(result.status),
        "message"=>result.message,"iterations"=>result.statistics.iterations,
        "refactorizations"=>result.statistics.refactorizations,
        "seconds"=>result.statistics.elapsed_seconds,"allocated_bytes"=>timed.bytes,
        "process_peak_rss"=>Sys.maxrss(),"records"=>records,
        "original_retry_enabled"=>true,
        "policy"=>Dict(string(s)=>getfield(policy,s) for s in JSimplex.NUMERICAL_SWITCHES),
        "events"=>Dict(string(k)=>v for (k,v) in d.counts if v != 0))
    if isdefined(Main, :EXTRA_DIAGNOSTIC_METADATA)
        merge!(report, Main.EXTRA_DIAGNOSTIC_METADATA)
    end
    h = SHA.SHA2_256_CTX()
    root = dirname(dirname(pathof(JSimplex)))
    files = ["Project.toml"]
    for (dir,_,names) in walkdir(joinpath(root,"src")), file in names
        endswith(file,".jl") && push!(files,relpath(joinpath(dir,file),root))
    end
    for file in sort(files)
        SHA.update!(h,codeunits(file*"\0"))
        SHA.update!(h,read(joinpath(root,file)))
    end
    report["production_sha256"] = bytes2hex(SHA.digest!(h))
    if result.status == OPTIMAL
        report["objective"] = result.objective_value
        report["original_primal_feasible"] = JSimplex._original_primal_feasible(problem,
            result.primal,options.primal_tolerance)
        @assert report["original_primal_feasible"]
    end
    println("RESULT ",name," ",method," ",variant," ",result.status," iterations=",result.statistics.iterations, " refactorizations=",result.statistics.refactorizations," seconds=",result.statistics.elapsed_seconds); flush(stdout)
    open(output,"w") do io
        TOML.print(io,report)
    end
    println("RESULT ",name," ",method," ",result.status," iterations=",result.statistics.iterations,
        " seconds=",result.statistics.elapsed_seconds); flush(stdout)
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end

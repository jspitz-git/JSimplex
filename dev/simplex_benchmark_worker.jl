# Each job loads its selected source checkout in a separate process.
using TOML, SHA
include("simplex_benchmarks.jl")
using .JSimplexBenchmarks
using JSimplex
include("simplex_replay.jl")
include("simplex_sparse_components.jl")
include("simplex_factor_components.jl")
include("simplex_update_components.jl")
include("simplex_pipeline_components.jl")

function benchmark_solve(problem, options, diagnostics, ::Nothing)
    return isnothing(diagnostics) ? solve(problem;relax_integrality=true,options) :
        JSimplex._solve_diagnosed(problem,diagnostics;relax_integrality=true,options)
end
benchmark_solve(problem, options, diagnostics, policy) =
    JSimplex._solve_diagnosed(problem,diagnostics;relax_integrality=true,options,numerical_policy=policy)

# Dispatch selected operations at runtime. Inferring every solve/replay/component
# path through this orchestration function produces a very large LLVM unit and
# can exhaust the worker's startup allowance before it reads the selected input.
# Numerical kernels still compile normally for their concrete runtime arguments.
function worker_main(job_path)
    job = TOML.parsefile(job_path)
    options, entry = job["options"], job["case"]
    result = Dict{String,Any}("outcome" => "input_error", "relax_integrality" => true)
    stage = "input"
    try
        expected_source = realpath(joinpath(options["source"], "src", "JSimplex.jl"))
        realpath(pathof(JSimplex)) == expected_source || error("Selected source checkout was not loaded")
        result["loaded_source"] = expected_source
        excluded_paths = get(job,"excluded_paths",String[])
        path = validate_selection(entry["resolved_path"], options["mode"];excluded_paths)
        overrides = (; (Symbol(key)=>value for (key,value) in get(job,"numerical_policy",Dict()))...)
        if !isempty(options["replay"])
            metadata = TOML.parsefile(path * ".toml")
            JSimplexBenchmarks.stress_only(metadata["original_path"];excluded_paths) && error("Stress-only source cannot be replayed")
            metadata["original_model_sha256"] in get(get(job,"excluded_hashes",Dict()),"decompressed_sha256",[]) &&
                error("Known stress-only content cannot be replayed")
            ws, metadata = Base.inferencebarrier(JSimplexReplay.load_snapshot)(path)
            if !isempty(overrides)
                isdefined(JSimplex,:NumericalPolicy) || error("Selected source does not support numerical policy overrides")
                old = ws.progress
                stored = (; (key=>getfield(old.numerical_policy,key)
                             for key in fieldnames(typeof(old.numerical_policy)))...)
                policy = JSimplex.NumericalPolicy(eltype(ws.costs);
                    simplex_strategy=ws.options.simplex_strategy,merge(stored,overrides)...)
                if isdefined(JSimplex,:_install_driver_policy!)
                    JSimplex._install_driver_policy!(ws,policy)
                else
                    ws.progress = JSimplex.SimplexProgressContext(ws.problem;start_ns=old.start_ns,
                        scaling=old.scaling,iteration_offset=old.iteration_offset,
                        diagnostics=old.diagnostics,numerical_policy=policy)
                end
            end
            hasproperty(ws.progress,:numerical_policy) &&
                (result["numerical_policy"] = JSimplexReplay.policy_record(ws.progress.numerical_policy))
            stage = "solve"
            started = time_ns()
            deadline = () -> (time_ns() - started) / 1e9 >= options["time-limit"]
            # Preserve consumed counters; the replay command bounds additional work.
            before = ws.iterations
            limit = Base.checked_add(before, options["iteration-limit"])
            settings = (; (key => getfield(ws.options, key) for key in fieldnames(typeof(ws.options)))...)
            ws.options = SolverOptions(typeof(ws.options.primal_tolerance);
                merge(settings, (; iteration_limit=limit, time_limit=options["time-limit"]))...)
            stop = deadline
            run = Base.inferencebarrier(JSimplexReplay.run_replay!)(ws,stop)
            result["replay_metadata"] = metadata
            result["status"] = string(run.status)
            result["status_scope"] = "working snapshot model"
            result["iterations"] = run.iterations
            result["cumulative_iterations"] = run.iterations+ws.progress.iteration_offset
            result["refactorizations"] = run.refactorizations
            result["cumulative_refactorizations"] = run.refactorizations+
                (hasproperty(ws.progress,:refactorization_offset) ? ws.progress.refactorization_offset : 0)
            result["elapsed_seconds"] = (time_ns() - started) / 1e9
            result["outcome"] = "completed"
            JSimplexBenchmarks.write_report(job["result_path"], result)
            return 0
        end
        policy = if isdefined(JSimplex,:NumericalPolicy)
            JSimplex.NumericalPolicy(Float64;simplex_strategy=Symbol(options["simplex-strategy"]),overrides...)
        else
            isempty(overrides) && options["simplex-strategy"] == "legacy" ||
                error("Selected source does not support adaptive numerical policy")
            nothing
        end
        if options["mode"] == "stress" && options["stress-operation"] == "inspect"
            stage = "reader"
            merge!(result, JSimplexBenchmarks.inspect_prefix(path;
                byte_limit=min(options["read-limit-mib"], 256) * 1048576,
                seconds=min(options["time-limit"], 60.0)))
            JSimplexBenchmarks.write_report(job["result_path"], result)
            return 0
        end
        copy_budget = Base.checked_mul(options["decompression-limit-mib"], 1048576)
        if options["mode"] == "stress"
            stage = "reader"
            read_budget = Base.checked_mul(options["read-limit-mib"], 1048576)
            filesize(path) <= read_budget || throw(JSimplexBenchmarks.BenchmarkResourceLimit(
                "Source exceeds the stress read budget; full hashing and parsing were not started"))
            copy_budget = min(copy_budget, read_budget)
        end
        result["source_sha256"] = bytes2hex(open(sha256, path))
        options["mode"] == "solve" && result["source_sha256"] in
            get(get(job,"excluded_hashes",Dict()),"source_sha256",[]) && error("Known stress-only content cannot be solved")
        if haskey(entry, "source_sha256")
            result["source_sha256"] == entry["source_sha256"] || error("Source SHA-256 mismatch")
        end
        unpacked = joinpath(job["temporary"], "input.mps")
        metadata = bounded_copy(path, unpacked;
            byte_limit=copy_budget, seconds=60.0)
        merge!(result, metadata)
        options["mode"] == "solve" && result["decompressed_sha256"] in
            get(get(job,"excluded_hashes",Dict()),"decompressed_sha256",[]) && error("Known stress-only content cannot be solved")
        if haskey(entry, "decompressed_sha256")
            result["decompressed_sha256"] == entry["decompressed_sha256"] || error("Decompressed SHA-256 mismatch")
        end
        parse_started = time_ns()
        stage = "reader"
        result["stage"] = stage
        result["outcome"] = "running"
        JSimplexBenchmarks.write_report(job["result_path"],result)
        problem = read_mps(unpacked)
        result["parse_seconds"] = (time_ns() - parse_started) / 1e9
        result["rows"], result["columns"] = size(problem.A)
        result["nonzeros"] = length(problem.A.nzval)
        result["scalar_type"] = "Float64"
        result["precision_bits"] = 53
        if options["mode"] == "stress"
            result["outcome"] = "completed_parse"
            if options["stress-operation"] == "components"
                stage = "components"
                result["stage"] = stage
                # A tractable extracted block has a distinct identity; it is not
                # an LP solve or a basis factorization of the original model.
                rows, columns = min(size(problem.A, 1), 256), min(size(problem.A, 2), 256)
                block = problem.A[1:rows, 1:columns]
                while length(block.nzval) > 50000
                    columns -= 1
                    block = problem.A[1:rows, 1:columns]
                end
                priced = transpose(block) * ones(rows)
                all(isfinite, priced) || error("Nonfinite extracted-block pricing")
                result["component_id"] = entry["id"] * "/leading-block"
                result["extraction_recipe"] = "Leading at most 256 rows and columns, trim columns to at most 50000 stored entries"
                result["component_rows"], result["component_columns"] = size(block)
                result["component_nonzeros"] = length(block.nzval)
                result["component_operation"] = "transpose matrix-vector pricing"
                if isdefined(JSimplex,:RowAccess)
                    result["sparse_pricing"] = Base.inferencebarrier(JSimplexSparseComponents.probe)(block)
                    result["component_operation"] = "row indexing, sparse pricing, and support cancellation"
                end
                if isdefined(JSimplex,:sparse_solve_view)
                    JSimplex.BLAS.set_num_threads(1)
                    extracted = @timed Base.inferencebarrier(JSimplexFactorComponents.extract)(problem.A)
                    factor_block,metadata = extracted.value
                    metadata["seconds"] = extracted.time
                    metadata["allocated_bytes"] = extracted.bytes
                    metadata["rows"],metadata["columns"] = size(factor_block)
                    metadata["nonzeros"] = JSimplex.nnz(factor_block)
                    result["factor_extraction"] = metadata
                    result["factor_components"] = Base.inferencebarrier(JSimplexFactorComponents.probe)(factor_block)
                    result["component_operation"] *= ", bounded base LU extraction and sparse solves"
                    if isdefined(JSimplex,:SparseBasisWorkspace)
                        bounded_basis = JSimplexFactorComponents.component_basis(factor_block)
                        dimension = min(size(bounded_basis,1),32)
                        result["update_components"] = Base.inferencebarrier(JSimplexUpdateComponents.probe)(
                            bounded_basis[1:dimension,1:dimension])
                        result["update_components"]["basis_recipe"] =
                            "Leading at most 32x32 principal block of the normalized factor component"
                        result["component_operation"] *= ", bounded update chains and refactor resets"
                        if isdefined(JSimplex,:HypersparseWorkspace)
                            result["pipeline_components"] = Base.inferencebarrier(JSimplexPipelineComponents.probe)(
                                bounded_basis[1:dimension,1:dimension])
                            result["pipeline_components"]["basis_recipe"] =
                                "Leading at most 32x32 principal block of the normalized factor component"
                            result["component_operation"] *= ", bounded sparse/dense pipelines"
                        end
                    end
                end
                result["outcome"] = "component_completed"
            end
            JSimplexBenchmarks.write_report(job["result_path"], result)
            return 0
        end
        JSimplex.BLAS.set_num_threads(1)
        result["blas_threads"] = JSimplex.BLAS.get_num_threads()
        result["blas_config"] = string(JSimplex.BLAS.get_config())
        result["samples"] = Dict{String,Any}[]
        result["warmups"] = Dict{String,Any}[]
        stage = "solve"
        result["stage"] = stage
        JSimplexBenchmarks.write_report(job["result_path"],result)
        algorithms = options["algorithm"] == "both" ? [:primal, :dual] : [Symbol(options["algorithm"])]
        for algorithm in algorithms
            settings = (; algorithm, verbose=false,
                pricing=Symbol(get(options,"pricing","steepest_edge")),
                basis_update=Symbol(options["basis-update"]),
                scaling=Symbol(get(options,"scaling","auto")),
                presolve=options["presolve"] == "on",
                time_limit=options["time-limit"], iteration_limit=options["iteration-limit"])
            solver_options = isnothing(policy) ? SolverOptions(;settings...) :
                SolverOptions(;settings...,simplex_strategy=Symbol(options["simplex-strategy"]))
            isnothing(policy) || (result["numerical_policy_$(algorithm)"] = JSimplexReplay.policy_record(policy))
            result["solver_options_$(algorithm)"] = Dict(string(key) =>
                (getfield(solver_options, key) isa Union{Bool,Int,AbstractFloat} ?
                    getfield(solver_options, key) : string(getfield(solver_options, key)))
                for key in fieldnames(typeof(solver_options)))
            # Two complete fresh solves exercise the same observer body and type
            # as measured solves. Every iteration owns fresh diagnostic state.
            for repetition in -1:options["samples"]
                warming = repetition <= 0
                snapshot_root = warming ? joinpath(job["temporary"],"warmup-replays") :
                    abspath(options["output"]) * ".replays"
                snapshot_path = joinpath(snapshot_root,
                    replace(entry["id"], '/' => '_') * "-$(algorithm)-$(repetition).bin")
                captured = Ref(false)
                trace = options["trace"] == "on" ?
                    JSimplexReplay.TraceRecorder(snapshot_path * ".trace") : nothing
                observer_seconds = Ref(0.0)
                phase_seconds = Dict{String,Float64}()
                phase_iterations = Dict{String,Int}()
                observed_iterations = Ref(0)
                phase_start = Ref(time_ns())
                phase_name = Ref("initialization")
                phase_one_model = Ref{Any}(nothing)
                phase_one_objective = Ref{Any}(nothing)
                final_workspace = Ref{Any}(nothing)
                working_levels = Int[result["precision_bits"]]
                observer = function (reason, ws)
                    started = time_ns()
                    if reason == :precision_boost
                        # This event runs inside the actual working-precision
                        # context, after constructing its new typed factor.
                        T = eltype(ws.primal)
                        bits = T === BigFloat ? precision(BigFloat) : precision(T)
                        bits in working_levels || push!(working_levels,bits)
                    end
                    # Count published steps only: private refactorization observers
                    # can see a candidate that will subsequently be rolled back.
                    # Global offsets retain work consumed by original-model retries.
                    if reason in (:pivot_completed,:flip_completed,:crash_pivot,:artificial_removed)
                        total = ws.progress.iteration_offset + ws.iterations
                        key = phase_name[]
                        phase_iterations[key] = get(phase_iterations,key,0) +
                            max(0,total-observed_iterations[])
                        observed_iterations[] = max(observed_iterations[],total)
                    end
                    if reason in (:phase_crash, :phase_primal, :phase_dual, :phase_one, :phase_auxiliary, :phase_cleanup, :phase_lp_refinement)
                        if reason == :phase_one
                            phase_one_model[] = ws.problem
                            phase_one_objective[] = copy(ws.problem.objective)
                        end
                        # Primal/dual dispatch within the unchanged auxiliary LP
                        # is still Phase I. The original objective or a new model
                        # retires this identity, including original-model retries.
                        in_phase_one = ws.problem === phase_one_model[] &&
                            ws.problem.objective == phase_one_objective[]
                        if !in_phase_one
                            phase_one_model[] = nothing
                            phase_one_objective[] = nothing
                        end
                        key = phase_name[]
                        phase_seconds[key] = get(phase_seconds, key, 0.0) + (started - phase_start[]) / 1e9
                        phase_name[] = in_phase_one ? "phase_one" : string(reason)
                        get!(phase_iterations,phase_name[],0)
                        phase_start[] = started
                    end
                    if !isnothing(trace) && reason in (:refactor_initial, :phase_primal, :phase_dual,
                        :phase_one, :phase_auxiliary, :pivot_completed, :flip_completed,
                        :refactor_other, :refactor_limit, :refactor_residual, :refactor_pivot)
                        JSimplexReplay.record_trace!(trace, reason, ws)
                    end
                    if reason in (:repair,:feasibility_recovery) && !captured[]
                        JSimplexReplay.save_snapshot(snapshot_path, ws;
                            original_hash=result["decompressed_sha256"], original_path=path, reason)
                        captured[] = true
                    end
                    reason == :certification && (final_workspace[] = ws)
                    observer_seconds[] += (time_ns() - started) / 1e9
                    return nothing
                end
                diagnostics = options["diagnostics"] == "on" && isdefined(JSimplex, :SimplexDiagnostics) ? JSimplex.SimplexDiagnostics(;
                    observer, kernel_timing=options["kernel-timing"] == "on") : nothing
                phase_start[] = time_ns()
                measured = @timed Base.inferencebarrier(benchmark_solve)(problem,solver_options,diagnostics,policy)
                solution = measured.value
                sample = Dict{String,Any}("algorithm" => string(algorithm), "repetition" => repetition,
                    "status" => string(solution.status), "message" => solution.message,
                    "seconds" => measured.time, "allocated_bytes" => measured.bytes,
                    "gc_seconds" => measured.gctime, "iterations" => solution.statistics.iterations,
                    "refactorizations" => solution.statistics.refactorizations,
                    "solver_seconds" => solution.statistics.elapsed_seconds,
                    "diagnostics_enabled" => !isnothing(diagnostics),
                    "working_precision_available" => !isnothing(diagnostics),
                    "observer_seconds" => observer_seconds[], "phase_seconds" => phase_seconds,
                    "phase_iterations" => phase_iterations)
                if hasproperty(measured, :compile_time)
                    sample["compile_seconds"] = measured.compile_time
                    sample["recompile_seconds"] = measured.recompile_time
                end
                phase_seconds[phase_name[]] = get(phase_seconds, phase_name[], 0.0) + (time_ns() - phase_start[]) / 1e9
                if !isnothing(diagnostics)
                    sample["working_precision_levels"] = working_levels
                    sample["working_precision_bits"] = maximum(working_levels)
                    key = phase_name[]
                    phase_iterations[key] = get(phase_iterations,key,0) +
                        max(0,solution.statistics.iterations-observed_iterations[])
                end
                captured[] && (sample["repair_snapshot"] = snapshot_path)
                if !isnothing(trace)
                    sample["trace_path"] = trace.path
                    sample["trace_truncated"] = trace.truncated
                    sample["trace_bytes"] = trace.written
                end
                if warming
                    sample["time_limit_seconds"] = solver_options.time_limit
                    if !isnothing(diagnostics)
                        sample["events"] = Dict(string(k) => v for (k,v) in diagnostics.counts)
                    end
                    push!(result["warmups"],sample)
                    JSimplexBenchmarks.write_report(job["result_path"],result)
                    continue
                end
                isnothing(solution.objective_value) || (sample["objective"] = solution.objective_value)
                merge!(sample, JSimplexBenchmarks.original_primal_errors(problem, solution.primal, solution.objective_value))
                sample["dual_error_available"] = false
                sample["dual_error_note"] = "Public results do not expose a mapped original-model dual witness"
                ws = final_workspace[]
                if solution.status == OPTIMAL && !isnothing(ws) && size(ws.problem.A) == size(problem.A)
                    scaling = ws.progress.scaling
                    # Recreate the original input-type scaling arithmetic before
                    # comparing a binary-preserving higher-precision copy.
                    T = eltype(problem.A)
                    row_factors, column_factors = T.(scaling.row_factors), T.(scaling.column_factors)
                    exact_mapping = row_factors == scaling.row_factors && column_factors == scaling.column_factors
                    expected_A = copy(problem.A)
                    # Match scale_problem's row-then-column divisions. Forming
                    # reciprocal diagonal matrices can overflow for tiny factors
                    # even when each scaled coefficient remains representable.
                    for column in axes(expected_A,2), position in JSimplex.nzrange(expected_A,column)
                        row = expected_A.rowval[position]
                        expected_A.nzval[position] =
                            (problem.A.nzval[position] / row_factors[row]) / column_factors[column]
                    end
                    sense = problem.objective_sense == JSimplex.MAX_SENSE ? -1 : 1
                    expected_costs = sense .* (problem.objective ./ column_factors)
                    if exact_mapping && ws.problem.A == expected_A && ws.problem.objective == expected_costs
                        witness = JSimplexBenchmarks.benchmark_dual_witness(JSimplex,ws;
                            bits=max(256,maximum(working_levels)))
                        merge!(sample, JSimplexBenchmarks.original_dual_errors(problem, solution.primal, witness;
                            primal_tolerance=solver_options.primal_tolerance))
                        delete!(sample, "dual_error_note")
                    end
                end
                sample["peak_process_rss_bytes"] = Sys.maxrss()
                if solution.status == OPTIMAL
                    sample["original_primal_certified"] = JSimplex._original_primal_feasible(
                        problem, solution.primal, solver_options.primal_tolerance)
                    sample["original_primal_certified"] || (result["validation_failure"] = true)
                end
                if haskey(entry, "expected_status") && string(solution.status) != entry["expected_status"]
                    sample["reference_mismatch"] = "status"
                    result["validation_failure"] = true
                elseif solution.status == OPTIMAL && haskey(entry, "expected_objective") &&
                       !isapprox(solution.objective_value, entry["expected_objective"]; rtol=1e-7, atol=1e-7)
                    sample["reference_mismatch"] = "objective"
                    result["validation_failure"] = true
                end
                if !isnothing(diagnostics)
                    sample["events"] = Dict(string(k) => v for (k,v) in diagnostics.counts)
                    sample["recent_events"] = string.(JSimplex.recent_events(diagnostics))
                    sample["kernel_timing_enabled"] = diagnostics.kernel_timing
                    sample["kernel_calls"] = Dict(string(k) => v for (k,v) in diagnostics.kernel_calls)
                    sample["kernel_seconds"] = Dict(string(k) => Float64(v) / 1e9 for (k,v) in diagnostics.kernel_nanoseconds)
                end
                push!(result["samples"], sample)
                JSimplexBenchmarks.write_report(job["result_path"], result)
            end
        end
        result["outcome"] = get(result, "validation_failure", false) ? "validation_error" : "completed"
    catch exception
        exception isa InterruptException && rethrow()
        result["outcome"] = exception isa Union{JSimplexBenchmarks.BenchmarkResourceLimit,OutOfMemoryError} ?
            "resource_stop" : stage == "solve" ? "worker_error" :
            stage == "reader" && options["mode"] == "stress" ? "reader_error" :
            stage == "components" ? "component_error" : "input_error"
        result["error"] = sprint(showerror, exception)
    end
    JSimplexBenchmarks.write_report(job["result_path"], result)
    return result["outcome"] == "completed" ? 0 : 1
end

exit(worker_main(only(ARGS)))

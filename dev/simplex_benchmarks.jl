module JSimplexBenchmarks

using SHA, TOML

export parse_benchmark_args, stress_only, validate_selection, bounded_copy, benchmark_main

struct BenchmarkResourceLimit <: Exception
    message::String
end
Base.showerror(io::IO, exception::BenchmarkResourceLimit) = print(io,exception.message)

function _bounded_wait(process, cancelled)
    stopped = false
    try
        while process_running(process)
            if cancelled()
                stopped = true
                kill(process,Base.SIGTERM)
                break
            end
            sleep(0.02)
        end
        wait(process)
    finally
        # GNU timeout forwards termination to its worker process group.
        if process_running(process)
            kill(process,Base.SIGTERM)
            wait(process)
        end
    end
    return stopped
end

const DEFAULTS = Dict{String,Any}(
    "source" => normpath(joinpath(@__DIR__, "..")), "suite" => "quick",
    "algorithm" => "both", "samples" => 7, "time-limit" => 60.0,
    "iteration-limit" => 100000, "output" => "simplex-results.toml",
    "netlib-root" => "/home/jspitz/NetLib", "miplib-root" => "/home/jspitz/MIPLib",
    "mps-root" => "/home/jspitz/mps", "mode" => "solve",
    "memory-limit-mib" => 4096, "read-limit-mib" => 256,
    "decompression-limit-mib" => 2048, "stress-operation" => "inspect",
    "file" => "", "replay" => "", "policy" => "",
    "trace" => "off",
    "kernel-timing" => "off",
    "diagnostics" => "on",
    "simplex-strategy" => "legacy",
    "pricing" => "steepest_edge",
    "basis-update" => "pfi",
    "presolve" => "on",
)

const POLICY_KEYS = (
    "solve_tolerance", "pivot_error_tolerance", "max_refinements",
    "max_pivot_candidates", "max_recovery_rounds", "stagnation_window",
    "max_precision_bits", "max_lp_refinements", "stable_ratio", "pivot_validation", "solve_refinement", "recovery", "feasibility_recovery",
    "incremental_primal", "incremental_primal_pivots", "adaptive_refactor", "refactor_timing", "adaptive_stalling", "adaptive_dual_perturbation", "adaptive_primal_perturbation",
    "adaptive_pricing", "partial_pricing", "hypersparse", "crash", "phase_one",
    "precision_boosting", "lp_refinement",
)

"""Run a worker with an external deadline and an enforced address-space ceiling.

Unsupported hosts skip explicitly. A worker killed by a resource limit is not a
mathematical solver failure. The limit applies before parsing or package loading.
"""
function run_bounded(command::Cmd, log_path; seconds::Real, memory_mib::Integer, cancelled=()->false)
    isfinite(seconds) && seconds > 0 && 0 < memory_mib <= typemax(Int) ÷ 1048576 ||
        throw(ArgumentError("Invalid worker resource limits"))
    timeout, prlimit = Sys.which("timeout"), Sys.which("prlimit")
    if !Sys.islinux() || isnothing(timeout) || isnothing(prlimit)
        return Dict{String,Any}("outcome" => "skipped", "reason" => "OS resource controls unavailable")
    end
    bytes = memory_mib * 1048576
    bytes = min(bytes, Int(min(Sys.total_memory(), typemax(Int))))
    cgroup_limit_path = "/sys/fs/cgroup/memory.max"
    if isfile(cgroup_limit_path)
        cgroup_limit = tryparse(Int, strip(read(cgroup_limit_path, String)))
        isnothing(cgroup_limit) || cgroup_limit <= 0 || (bytes = min(bytes, cgroup_limit))
    end
    supervised = `$timeout --signal=TERM --kill-after=2 $(string(Float64(seconds))) $prlimit --as=$bytes -- $command`
    started = time_ns()
    process, stopped = open(log_path, "w") do log
        process = run(pipeline(ignorestatus(supervised), stdout=log, stderr=log); wait=false)
        return process, _bounded_wait(process,cancelled)
    end
    code = process.exitcode
    return Dict{String,Any}("outcome" => stopped ? "cancelled" : code == 0 ? "completed" :
        code in (124, 137) ? "resource_stop" : "worker_error", "exit_code" => code,
        "elapsed_seconds" => (time_ns() - started) / 1e9,
        "memory_limit_kind" => "RLIMIT_AS", "memory_limit_bytes" => bytes,
        "time_limit_seconds" => Float64(seconds))
end

function parse_benchmark_args(args)
    options = copy(DEFAULTS)
    seen = Set{String}()
    i = 1
    while i <= length(args)
        parts = split(args[i], '='; limit=2)
        startswith(parts[1], "--") || throw(ArgumentError("Expected --option, got $(args[i])"))
        key = parts[1][3:end]
        haskey(options, key) || throw(ArgumentError("Unknown option --$key"))
        key in seen && throw(ArgumentError("Repeated option --$key"))
        push!(seen, key)
        if length(parts) == 1
            i += 1
            i <= length(args) || throw(ArgumentError("Missing value for --$key"))
            value = args[i]
        else
            value = parts[2]
        end
        (isempty(value) || startswith(value, "--")) && throw(ArgumentError("Missing value for --$key"))
        default = DEFAULTS[key]
        options[key] = default isa Int ? parse(Int, value) :
                       default isa Float64 ? parse(Float64, value) : String(value)
        if default isa Real
            isfinite(options[key]) && options[key] > 0 ||
                throw(ArgumentError("--$key must be finite and positive"))
        end
        i += 1
    end
    options["algorithm"] in ("primal", "dual", "both") || throw(ArgumentError("Invalid algorithm"))
    options["mode"] in ("solve", "stress") || throw(ArgumentError("Invalid mode"))
    options["suite"] in ("quick", "degenerate", "ill_conditioned", "phase_one", "sparse_large", "holdout", "stress") ||
        throw(ArgumentError("Unknown suite"))
    if options["mode"] == "stress"
        options["suite"] == "stress" || !isempty(options["file"]) ||
            throw(ArgumentError("Stress mode requires --suite=stress or --file"))
        all(key in seen for key in ("time-limit", "memory-limit-mib", "read-limit-mib")) ||
            throw(ArgumentError("Stress mode requires explicit time, memory, and read limits"))
    elseif options["suite"] == "stress"
        throw(ArgumentError("The stress suite requires --mode=stress"))
    end
    options["stress-operation"] in ("inspect", "reader", "components") ||
        throw(ArgumentError("Invalid stress operation"))
    options["trace"] in ("on", "off") || throw(ArgumentError("--trace must be on or off"))
    options["kernel-timing"] in ("on", "off") || throw(ArgumentError("--kernel-timing must be on or off"))
    options["diagnostics"] in ("on", "off") || throw(ArgumentError("--diagnostics must be on or off"))
    options["presolve"] in ("on", "off") || throw(ArgumentError("--presolve must be on or off"))
    options["simplex-strategy"] in ("legacy", "adaptive") || throw(ArgumentError("Invalid simplex strategy"))
    options["pricing"] in ("steepest_edge","devex","dantzig","auto") ||
        throw(ArgumentError("Invalid pricing rule"))
    !isempty(options["replay"]) && options["pricing"] != "steepest_edge" &&
        throw(ArgumentError("The pricing rule is read from the replay snapshot"))
    options["basis-update"] in ("pfi","forrest_tomlin","bartels_golub","suhl_suhl") ||
        throw(ArgumentError("Invalid basis update method"))
    !isempty(options["replay"]) && options["basis-update"] != "pfi" &&
        throw(ArgumentError("The basis update method is read from the replay snapshot"))
    !isempty(options["replay"]) && options["simplex-strategy"] != "legacy" &&
        throw(ArgumentError("Replay retains its stored strategy; use --policy for numerical overrides"))
    options["diagnostics"] == "off" && (options["trace"] == "on" || options["kernel-timing"] == "on") &&
        throw(ArgumentError("Trace and kernel timing require diagnostics"))
    count(!isempty(options[key]) for key in ("file", "replay")) <= 1 ||
        throw(ArgumentError("Select either --file or --replay"))
    return options
end

function stress_name(path)
    name = lowercase(basename(path))
    endswith(name, ".gz") && (name = name[1:end-3])
    return name in ("big.mps", "largo.mps", "anymod.mps")
end

stress_only(path) = stress_name(path) || (ispath(path) && stress_name(realpath(path)))

function validate_selection(path, mode)
    isfile(path) || throw(ArgumentError("Missing input: $path"))
    mode in ("solve", "stress") || throw(ArgumentError("Invalid mode: $mode"))
    mode == "solve" && stress_only(path) &&
        throw(ArgumentError("Stress-only input cannot be solved: $path"))
    return realpath(path)
end

function select_cases(options; manifest_path=joinpath(@__DIR__, "simplex_cases.toml"))
    if !isempty(options["replay"])
        options["mode"] == "solve" || throw(ArgumentError("Replay is a solve operation"))
        return [Dict{String,Any}("id" => "replay/" * basename(options["replay"]),
            "resolved_path" => abspath(options["replay"]), "collection" => "replay")]
    end
    manifest = TOML.parsefile(manifest_path)
    cases = manifest["cases"]
    holdout = Set(get(c, "decompressed_sha256", "") for c in cases if "holdout" in c["suites"])
    for c in cases
        if !isempty(intersect(c["suites"], ["quick", "degenerate", "ill_conditioned", "phase_one", "sparse_large"]))
            get(c, "decompressed_sha256", "unavailable") in holdout &&
                throw(ArgumentError("Calibration case overlaps frozen holdout: $(c["id"])"))
        end
    end
    if !isempty(options["file"])
        path = abspath(options["file"])
        options["mode"] == "solve" && stress_only(path) &&
            throw(ArgumentError("Stress-only input cannot be solved: $path"))
        return [Dict{String,Any}("id" => "explicit/" * basename(path),
            "resolved_path" => path, "suites" => ["explicit"], "collection" => "explicit")]
    end
    selected = Dict{String,Any}[]
    seen = Set{String}()
    for c in cases
        options["suite"] in c["suites"] || continue
        checksum = get(c, "decompressed_sha256", "unavailable/" * c["id"])
        checksum in seen && continue
        push!(seen, checksum)
        entry = copy(c)
        root = c["collection"] == "generated" ?
            joinpath(@__DIR__, "..", "test", "fixtures", "solver", "generated") :
            options[c["collection"] * "-root"]
        entry["resolved_path"] = joinpath(root, c["path"])
        options["mode"] == "solve" && stress_only(entry["resolved_path"]) &&
            throw(ArgumentError("Solve suite contains stress-only input"))
        push!(selected, entry)
    end
    isempty(selected) && throw(ArgumentError("Empty suite: $(options["suite"])"))
    return selected
end

function corpus_inventory(options)
    result = Dict{String,Any}()
    for collection in ("netlib", "miplib", "mps")
        root = options[collection * "-root"]
        paths = String[]
        if isdir(root)
            for (directory, _, names) in walkdir(root), name in names
                occursin(r"(?i)\.mps(\.gz)?$", name) || continue
                path = joinpath(directory, name)
                isfile(path) && push!(paths, relpath(path, root))
            end
        end
        sort!(paths)
        compressed = count(path -> endswith(lowercase(path), ".gz"), paths)
        result[collection] = Dict("root" => root, "available" => isdir(root),
            "mps_count" => length(paths) - compressed, "gzip_count" => compressed,
            "paths" => paths)
    end
    return result
end

"""Copy/decompress an entire input within a byte quota and external gzip deadline.

An incomplete destination is always deleted. Source paths are subprocess arguments,
never shell code. The caller additionally supervises the whole worker deadline.
"""
function bounded_copy(source, destination; byte_limit::Integer, seconds::Real)
    byte_limit > 0 && isfinite(seconds) && seconds > 0 || throw(ArgumentError("Invalid copy limits"))
    abspath(source) != abspath(destination) || throw(ArgumentError("Output would overwrite input"))
    ispath(destination) && samefile(destination, source) &&
        throw(ArgumentError("Output aliases input"))
    started = time_ns()
    compressed = endswith(lowercase(source), ".gz")
    process = nothing
    input = if compressed
        gzip, timeout = Sys.which("gzip"), Sys.which("timeout")
        isnothing(gzip) || isnothing(timeout) ? throw(ArgumentError("gzip and timeout are required")) :
            open(`$timeout --signal=KILL $(string(Float64(seconds))) $gzip -dc -- $source`, "r")
    else
        open(source, "r")
    end
    compressed && (process = input)
    total = 0
    digest = SHA.SHA2_256_CTX()
    buffer = Vector{UInt8}(undef, 65536)
    try
        open(destination, "w") do output
            while !eof(input)
                (time_ns() - started) / 1e9 < seconds || throw(BenchmarkResourceLimit("Input deadline exceeded"))
                n = readbytes!(input, buffer, min(length(buffer), byte_limit - total + 1))
                total += n
                total <= byte_limit || throw(BenchmarkResourceLimit("Decompressed input exceeds byte quota"))
                bytes = @view buffer[1:n]
                write(output, bytes)
                SHA.update!(digest, bytes)
            end
        end
        close(input)
        if compressed
            wait(process)
            process.exitcode in (124,137) && throw(BenchmarkResourceLimit("Decompression deadline exceeded"))
            success(process) || error("gzip failed")
        end
        return Dict{String,Any}("complete" => true, "bytes" => total,
            "decompressed_sha256" => bytes2hex(SHA.digest!(digest)))
    catch
        if compressed && process_running(process)
            kill(process, Base.SIGKILL)
        end
        close(input)
        compressed && wait(process)
        isfile(destination) && rm(destination)
        rethrow()
    end
end

function write_report(path, report)
    mkpath(dirname(abspath(path)))
    temporary, io = mktemp(dirname(abspath(path)))
    try
        TOML.print(io,report;sorted=true)
        close(io)
        mv(temporary,path;force=true)
    finally
        isopen(io) && close(io)
        isfile(temporary) && rm(temporary)
    end
end

function source_identity(root)
    isfile(joinpath(root, "Project.toml")) && isfile(joinpath(root, "src", "JSimplex.jl")) ||
        throw(ArgumentError("Invalid source checkout: $root"))
    digest = SHA.SHA2_256_CTX()
    files = String["Project.toml"]
    for (directory, _, names) in walkdir(joinpath(root, "src"))
        append!(files, [relpath(joinpath(directory, name), root) for name in names if endswith(name, ".jl")])
    end
    for path in sort!(files)
        SHA.update!(digest, codeunits(path * "\0"))
        SHA.update!(digest, read(joinpath(root, path)))
    end
    revision = try
        isfile(joinpath(root,".source-revision")) ? strip(read(joinpath(root,".source-revision"),String)) :
            strip(read(`git -C $root rev-parse HEAD`, String))
    catch
        "unavailable"
    end
    return Dict("revision" => revision, "tree_sha256" => bytes2hex(SHA.digest!(digest)))
end

function original_primal_errors(problem, primal, objective)
    isnothing(primal) && return Dict{String,Any}("primal_error_available" => false)
    return setprecision(BigFloat, 256) do
        x = BigFloat.(primal)
        activity = zeros(BigFloat, size(problem.A, 1))
        for column in eachindex(x), position in problem.A.colptr[column]:problem.A.colptr[column+1]-1
            activity[problem.A.rowval[position]] += BigFloat(problem.A.nzval[position]) * x[column]
        end
        violation = zero(BigFloat)
        for (values, lower, upper) in ((x, problem.column_lower, problem.column_upper),
                                       (activity, problem.row_lower, problem.row_upper))
            for i in eachindex(values)
                isfinite(lower[i]) && (violation = max(violation, BigFloat(lower[i].value) - values[i]))
                isfinite(upper[i]) && (violation = max(violation, values[i] - BigFloat(upper[i].value)))
            end
        end
        expected = BigFloat(problem.objective_constant)
        for i in eachindex(x)
            expected += BigFloat(problem.objective[i]) * x[i]
        end
        return Dict{String,Any}("primal_error_available" => true,
            "primal_error" => Float64(violation),
            "objective_error" => Float64(abs(expected - BigFloat(objective))),
            "error_evaluation_bits" => 256, "error_units" => "original model")
    end
end

function original_dual_errors(problem, primal, dual; primal_tolerance=1e-7)
    return setprecision(BigFloat, 256) do
        x, y = BigFloat.(primal), BigFloat.(dual)
        activity = zeros(BigFloat, size(problem.A, 1))
        sign = string(problem.objective_sense) == "MAX_SENSE" ? -1 : 1
        costs = sign .* BigFloat.(problem.objective)
        for column in eachindex(x), position in problem.A.colptr[column]:problem.A.colptr[column+1]-1
            row, a = problem.A.rowval[position], BigFloat(problem.A.nzval[position])
            activity[row] += a * x[column]
            costs[column] -= a * y[row]
        end
        violation = zero(BigFloat)
        complementarity = zero(BigFloat)
        for (values, prices, lower, upper) in
            ((x, costs, problem.column_lower, problem.column_upper),
             (activity, y, problem.row_lower, problem.row_upper))
            for i in eachindex(values)
                has_lower, has_upper = isfinite(lower[i]), isfinite(upper[i])
                l = has_lower ? BigFloat(lower[i].value) : -BigFloat(Inf)
                u = has_upper ? BigFloat(upper[i].value) : BigFloat(Inf)
                l == u && continue
                value, price = values[i], prices[i]
                at_lower = has_lower && abs(value-l) <= primal_tolerance
                at_upper = has_upper && abs(value-u) <= primal_tolerance
                violation = max(violation, at_lower ? max(-price,0) :
                    at_upper ? max(price,0) : abs(price))
                if price > 0
                    complementarity = max(complementarity, has_lower ? abs(price*(value-l)) : BigFloat(Inf))
                elseif price < 0
                    complementarity = max(complementarity, has_upper ? abs(price*(u-value)) : BigFloat(Inf))
                end
            end
        end
        return Dict{String,Any}("dual_error_available" => true,
            "dual_sign_error" => Float64(violation),
            "complementarity_error" => Float64(complementarity))
    end
end

function inspect_prefix(path; byte_limit::Int, seconds::Float64)
    compressed = endswith(lowercase(path), ".gz")
    input = compressed ? open(`timeout --signal=KILL $seconds gzip -dc -- $path`, "r") : open(path, "r")
    digest = SHA.SHA2_256_CTX()
    buffer = Vector{UInt8}(undef, 65536)
    total, lines = 0, 0
    complete = false
    started = time_ns()
    try
        while total < byte_limit && (time_ns() - started) / 1e9 < seconds && !eof(input)
            n = readbytes!(input, buffer, min(length(buffer), byte_limit - total))
            bytes = @view buffer[1:n]
            SHA.update!(digest, bytes)
            lines += count(==(0x0a), bytes)
            total += n
        end
        complete = eof(input)
        if compressed
            complete || kill(input, Base.SIGKILL)
            wait(input)
            complete && !success(input) && error("Compressed inspection input is corrupt or timed out")
        end
    finally
        compressed && process_running(input) && kill(input, Base.SIGKILL)
        close(input)
    end
    result = Dict{String,Any}("outcome" => complete ? "completed_inspection" : "partial_inspection",
        "inspected_bytes" => total, "newline_count" => lines,
        "prefix_sha256" => bytes2hex(SHA.digest!(digest)), "prefix_first_byte" => 0,
        "prefix_end_byte_exclusive" => total, "full_hash_available" => complete)
    if complete
        result["source_sha256"] = compressed ? bytes2hex(open(sha256,path)) : result["prefix_sha256"]
        result["decompressed_sha256"] = result["prefix_sha256"]
    end
    return result
end

function benchmark_main(args=ARGS; err=stderr, manifest_path=joinpath(@__DIR__, "simplex_cases.toml"))
    options = nothing
    protected_output = false
    report = Dict{String,Any}("schema_version" => 1, "cases" => Dict{String,Any}[])
    failures = false
    try
        options = parse_benchmark_args(args)
        if isfile(options["output"])
            protected_output = occursin(r"(?i)\.mps(\.gz)?$",options["output"]) ||
                any(path -> !isempty(path) && isfile(path) && samefile(path,options["output"]),
                    (options["file"],options["policy"],options["replay"],isempty(options["replay"]) ? "" : options["replay"] * ".toml"))
            protected_output && throw(ArgumentError("Report output aliases a model or replay input"))
        end
        options["source"] = realpath(options["source"])
        report["options"] = options
        report["source"] = source_identity(options["source"])
        report["variant"] = options["simplex-strategy"] * "_diagnostics_" * options["diagnostics"]
        report["runner_sha256"] = Dict(name => bytes2hex(open(sha256,joinpath(@__DIR__,name)))
            for name in ("simplex_benchmarks.jl","simplex_benchmark_worker.jl","simplex_replay.jl"))
        report["inventory"] = corpus_inventory(options)
        policy = isempty(options["policy"]) ? Dict{String,Any}() : TOML.parsefile(options["policy"])
        all(key in POLICY_KEYS for key in keys(policy)) || throw(ArgumentError("Unknown numerical policy key"))
        report["policy_overrides"] = policy
        cases = select_cases(options; manifest_path)
        if isfile(options["output"])
            protected_output = any(c -> isfile(c["resolved_path"]) &&
                samefile(c["resolved_path"],options["output"]),cases)
            protected_output && throw(ArgumentError("Report output aliases a selected input"))
        end
        registry = TOML.parsefile(manifest_path)["cases"]
        excluded_hashes = Dict(key => unique(String[c[key] for c in registry
            if (stress_name(c["path"]) || get(c,"stress_only",false)) && haskey(c,key)])
            for key in ("source_sha256","decompressed_sha256"))
        for entry in cases
            result = Dict{String,Any}("id" => entry["id"], "path" => entry["resolved_path"],
                "mode" => options["mode"], "outcome" => "input_error")
            push!(report["cases"], result)
            try
                validate_selection(entry["resolved_path"], options["mode"])
                mktempdir() do temporary
                    job_path, result_path = joinpath(temporary, "job.toml"), joinpath(temporary, "result.toml")
                    job = Dict("options" => options, "case" => entry,
                               "result_path" => result_path, "temporary" => temporary,
                               "excluded_hashes" => excluded_hashes, "numerical_policy" => policy)
                    write_report(job_path, job)
                    command = `$(Base.julia_cmd()) --startup-file=no --project=$(options["source"]) $(joinpath(@__DIR__, "simplex_benchmark_worker.jl")) $job_path`
                    # Warmup and parsing have a separate bounded allowance; each
                    # measured solve still has the exact requested solver budget.
                    seconds = options["mode"] == "stress" ? min(options["time-limit"],
                        options["stress-operation"] == "reader" ? 300.0 : 60.0) :
                        180.0 + options["time-limit"] * (options["samples"] + 2) *
                        (options["algorithm"] == "both" ? 2 : 1)
                    execution = run_bounded(command, joinpath(temporary, "worker.log");
                        seconds, memory_mib=options["memory-limit-mib"])
                    merge!(result, execution)
                    if isfile(result_path)
                        merge!(result, TOML.parsefile(result_path))
                    end
                    if execution["outcome"] != "completed" &&
                       !(execution["outcome"] == "worker_error" && haskey(result, "error"))
                        result["outcome"] = execution["outcome"]
                        log = joinpath(temporary, "worker.log")
                        isfile(log) && (result["worker_log"] = read(log, String))
                    end
                end
            catch exception
                if exception isa InterruptException
                    result["outcome"] = "cancelled"
                    write_report(options["output"],report)
                    rethrow()
                end
                result["outcome"] = "input_error"
                result["error"] = sprint(showerror, exception)
            end
            failures |= !(result["outcome"] in ("completed", "completed_inspection", "completed_parse",
                "component_completed", "partial_inspection", "resource_stop", "skipped"))
            write_report(options["output"], report)
        end
    catch exception
        exception isa InterruptException && rethrow()
        println(err, sprint(showerror, exception))
        report["error"] = sprint(showerror, exception)
        isnothing(options) || protected_output || write_report(options["output"], report)
        return 1
    end
    return failures ? 1 : 0
end

end # module

if abspath(PROGRAM_FILE) == @__FILE__
    exit(JSimplexBenchmarks.benchmark_main())
end

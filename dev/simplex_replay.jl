module JSimplexReplay

using JSimplex, Serialization, SHA, TOML

policy_record(policy) = Dict(string(key) =>
    (getfield(policy,key) isa Union{Bool,Integer,Float16,Float32,Float64} ?
        getfield(policy,key) : string(getfield(policy,key))) for key in fieldnames(typeof(policy)))

function serialized_hash(value)
    buffer = IOBuffer()
    serialize(buffer, value)
    return bytes2hex(sha256(take!(buffer)))
end

function save_snapshot(path, ws; original_hash::String, original_path::String="", reason::Symbol=:repair)
    payload = (version=1, problem=ws.problem, options=ws.options,
        basis=ws.basis, costs=ws.costs, lower=ws.lower, upper=ws.upper,
        primal=ws.primal, reduced_costs=ws.reduced_costs,
        iterations=ws.iterations, refactorizations=ws.refactorizations,
        perturbed=ws.perturbed,
        numerical_policy=hasproperty(ws.progress,:numerical_policy) ? ws.progress.numerical_policy : nothing)
    mkpath(dirname(abspath(path)))
    open(path, "w") do io
        serialize(io, payload)
    end
    T = eltype(ws.costs)
    bits = T == BigFloat ? maximum(precision, ws.costs; init=precision(BigFloat)) :
           T <: AbstractFloat ? precision(T) : 0
    metadata = Dict{String,Any}("schema_version" => 1, "reason" => string(reason),
        "snapshot_sha256" => bytes2hex(open(sha256, path)),
        "original_model_sha256" => original_hash,
        "original_path" => original_path,
        "working_model_sha256" => serialized_hash(ws.problem),
        "scalar_type" => string(T), "precision_bits" => bits,
        "factorization_rebuilt" => true,
        "replay_limit" => "Fresh-factor replay does not reproduce accumulated update-chain drift",
        "counters" => isnothing(ws.progress.diagnostics) ? Dict{String,Int}() :
            Dict(string(k) => v for (k,v) in ws.progress.diagnostics.counts))
    isnothing(payload.numerical_policy) ||
        (metadata["numerical_policy"] = policy_record(payload.numerical_policy))
    open(path * ".toml", "w") do io
        TOML.print(io, metadata; sorted=true)
    end
    return metadata
end

function load_snapshot(path)
    metadata = TOML.parsefile(path * ".toml")
    bytes2hex(open(sha256, path)) == metadata["snapshot_sha256"] ||
        throw(ArgumentError("Snapshot SHA-256 mismatch"))
    # Only load task-owned local replay artifacts from the matching Julia/source
    # environment. The adjacent hash detects accidental corruption, not trust.
    payload = open(deserialize, path)
    payload.version == 1 || throw(ArgumentError("Unsupported snapshot version"))
    serialized_hash(payload.problem) == metadata["working_model_sha256"] ||
        throw(ArgumentError("Working-model SHA-256 mismatch"))
    return setprecision(BigFloat, max(precision(BigFloat), metadata["precision_bits"])) do
        diagnostics = JSimplex.SimplexDiagnostics()
        progress = if isdefined(JSimplex,:NumericalPolicy)
            policy = hasproperty(payload,:numerical_policy) && !isnothing(payload.numerical_policy) ?
                payload.numerical_policy : JSimplex.NumericalPolicy(eltype(payload.costs),payload.options)
            JSimplex.SimplexProgressContext(payload.problem; diagnostics, numerical_policy=policy)
        else
            JSimplex.SimplexProgressContext(payload.problem; diagnostics)
        end
        ws = JSimplex.initialize_workspace(payload.problem, payload.options; progress)
        ws.basis = JSimplex.Basis(payload.basis.basic_indices, payload.basis.states)
        copyto!(ws.costs, payload.costs)
        copyto!(ws.lower, payload.lower)
        copyto!(ws.upper, payload.upper)
        ws.perturbed = payload.perturbed
        JSimplex.recompute!(ws; refactorize=true)
        ws.iterations = payload.iterations
        ws.refactorizations = payload.refactorizations + 1
        return ws, metadata
    end
end

mutable struct TraceRecorder
    path::String
    byte_limit::Int
    written::Int
    truncated::Bool
end

function TraceRecorder(path; byte_limit::Int=16*1024*1024)
    byte_limit > 0 || throw(ArgumentError("Trace byte limit must be positive"))
    mkpath(dirname(abspath(path)))
    open(path, "w") do _ end
    return TraceRecorder(path, byte_limit, 0, false)
end

function record_trace!(trace::TraceRecorder, reason, ws)
    trace.truncated && return nothing
    # Retaining the actual factor state makes update-chain drift observable;
    # these opt-in records are larger than a fresh-factor repair snapshot.
    state = (problem=ws.problem, options=ws.options, basis=ws.basis,
        factorization=ws.factorization, costs=ws.costs, lower=ws.lower, upper=ws.upper,
        primal=ws.primal, reduced_costs=ws.reduced_costs,
        iterations=ws.iterations, refactorizations=ws.refactorizations,
        numerical_policy=hasproperty(ws.progress,:numerical_policy) ? ws.progress.numerical_policy : nothing)
    if Base.summarysize(state) > trace.byte_limit - trace.written
        trace.truncated = true
        return nothing
    end
    buffer = IOBuffer()
    serialize(buffer, (; reason, state))
    bytes = take!(buffer)
    if length(bytes) > trace.byte_limit - trace.written
        trace.truncated = true
        return nothing
    end
    open(trace.path, "a") do io
        write(io, bytes)
    end
    trace.written += length(bytes)
    return nothing
end

function read_trace(path; byte_limit::Int=16*1024*1024)
    filesize(path) <= byte_limit || throw(ArgumentError("Trace exceeds read budget"))
    records = []
    open(path, "r") do io
        while !eof(io)
            push!(records, deserialize(io))
        end
    end
    return records
end

end # module

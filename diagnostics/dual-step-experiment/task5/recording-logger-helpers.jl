mutable struct RecordingSimplexLogger <: JSimplex.Logging.AbstractLogger
    records::Vector{Any}
end

function repeated_feasibility_queries(workspace, repetitions)
    for _ in 1:repetitions
        JSimplex.primal_infeasibility(workspace)
        JSimplex.dual_infeasibility(workspace)
    end
    return nothing
end

JSimplex.Logging.min_enabled_level(::RecordingSimplexLogger) = JSimplex.Logging.Debug
JSimplex.Logging.shouldlog(::RecordingSimplexLogger, args...) = true
JSimplex.Logging.catch_exceptions(::RecordingSimplexLogger) = false
function JSimplex.Logging.handle_message(
    logger::RecordingSimplexLogger,
    level,
    message,
    args...;
    kwargs...,
)
    push!(logger.records, (; level, message, kwargs...))
    return nothing
end


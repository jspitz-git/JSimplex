@enum TerminationStatus::UInt8 begin
    OPTIMAL
    INFEASIBLE
    UNBOUNDED
    ITERATION_LIMIT
    TIME_LIMIT
    NUMERICAL_ERROR
    INVALID_MODEL
    MIP_NOT_SUPPORTED
    ALGORITHM_NOT_SUPPORTED
end

struct SolverOptions
    primal_tolerance::Float64
    dual_tolerance::Float64
    zero_tolerance::Float64
    iteration_limit::Int
    time_limit::Float64
    refactorization_interval::Int
    log_level::LogLevel

    algorithm::Symbol

    function SolverOptions(;
        primal_tolerance::Real=1.0e-7,
        dual_tolerance::Real=1.0e-7,
        zero_tolerance::Real=1.0e-12,
        iteration_limit::Integer=100_000,
        time_limit::Real=Inf,
        refactorization_interval::Integer=20,
        log_level::LogLevel=Logging.Debug,
        algorithm::Symbol=:dual,
    )
        primal_tolerance > 0 || throw(ArgumentError("primal_tolerance must be positive"))
        dual_tolerance > 0 || throw(ArgumentError("dual_tolerance must be positive"))
        zero_tolerance > 0 || throw(ArgumentError("zero_tolerance must be positive"))
        iteration_limit >= 0 || throw(ArgumentError("iteration_limit must be nonnegative"))
        time_limit >= 0 || throw(ArgumentError("time_limit must be nonnegative"))
        refactorization_interval > 0 || throw(ArgumentError("refactorization_interval must be positive"))
        return new(Float64(primal_tolerance), Float64(dual_tolerance),
                   Float64(zero_tolerance), Int(iteration_limit),
                   Float64(time_limit), Int(refactorization_interval),
                   log_level, algorithm)
    end
end

Base.@kwdef struct SolveStatistics
    iterations::Int = 0
    elapsed_seconds::Float64 = 0.0
    refactorizations::Int = 0
end

struct Solution
    status::TerminationStatus
    objective_value::Union{Nothing,Float64}
    primal::Union{Nothing,Vector{Float64}}
    statistics::SolveStatistics
    message::String
end

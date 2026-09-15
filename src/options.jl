"""
    TerminationStatus

Reason a solve stopped: `OPTIMAL`, `INFEASIBLE`, `UNBOUNDED`,
`ITERATION_LIMIT`, `TIME_LIMIT`, `NUMERICAL_ERROR`, `INVALID_MODEL`,
`MIP_NOT_SUPPORTED`, or `ALGORITHM_NOT_SUPPORTED`. Only `OPTIMAL` supplies
primal values and an objective in a [`Solution`](@ref).
"""
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

@doc "An optimal LP solution is available." OPTIMAL
@doc "The LP was classified as infeasible." INFEASIBLE
@doc "The LP objective was classified as unbounded." UNBOUNDED
@doc "The completed-pivot limit was reached." ITERATION_LIMIT
@doc "The wall-clock deadline was reached." TIME_LIMIT
@doc "A numerical failure prevented a reliable solution." NUMERICAL_ERROR
@doc "The supplied model failed validation at solve time." INVALID_MODEL
@doc "A non-continuous model requires explicit LP relaxation." MIP_NOT_SUPPORTED
@doc "The requested algorithm is not implemented; use `:dual`." ALGORITHM_NOT_SUPPORTED

"""
    SolverOptions(; primal_tolerance=1e-7, dual_tolerance=1e-7,
                    zero_tolerance=1e-12, iteration_limit=100_000,
                    time_limit=Inf, refactorization_interval=20,
                    log_level=Logging.Debug, algorithm=:dual)

Configure numerical tolerances, completed-pivot and wall-clock limits, basis
refactorization frequency, and the level used for Julia logging messages.
Tolerances and the refactorization interval must be positive; limits must be
nonnegative. `time_limit` is in seconds and `Inf` disables the deadline.
Only `algorithm=:dual` is implemented; other symbols return
`ALGORITHM_NOT_SUPPORTED` from [`solve`](@ref).
"""
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

"""
    SolveStatistics(; iterations=0, elapsed_seconds=0.0, refactorizations=0)

Solve counters retained for every termination status: completed simplex pivots,
elapsed wall-clock time in seconds, and full basis factorizations.
"""
Base.@kwdef struct SolveStatistics
    iterations::Int = 0
    elapsed_seconds::Float64 = 0.0
    refactorizations::Int = 0
end

"""
    Solution(status, objective_value, primal, statistics, message)

Result of [`solve`](@ref). `status` is a [`TerminationStatus`](@ref),
`statistics` is a [`SolveStatistics`](@ref), and `message` explains termination.
For `OPTIMAL`, `primal` contains the original structural variable values and
`objective_value` includes the original objective sense and constant. Both
fields are `nothing` for every other status, including resource limits.
"""
struct Solution
    status::TerminationStatus
    objective_value::Union{Nothing,Float64}
    primal::Union{Nothing,Vector{Float64}}
    statistics::SolveStatistics
    message::String
end

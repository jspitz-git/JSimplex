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
    SolverOptions(::Type{T}; primal_tolerance=nothing, dual_tolerance=nothing,
                  zero_tolerance=nothing, iteration_limit=100_000,
                  time_limit=Inf, refactorization_interval=20,
                  log_level=Logging.Debug, algorithm=:dual)

Configure numerical tolerances, completed-pivot and wall-clock limits, basis
refactorization frequency, and the level used for Julia logging messages.
Floating-point tolerances and the refactorization interval must be positive;
rational tolerances must be nonnegative. Limits must be nonnegative.
`time_limit` is in seconds and `Inf` disables the deadline.
Only `algorithm=:dual` is implemented; other symbols return
`ALGORITHM_NOT_SUPPORTED` from [`solve`](@ref).
"""
struct SolverOptions{T<:Real}
    primal_tolerance::T
    dual_tolerance::T
    zero_tolerance::T
    iteration_limit::Int
    time_limit::Float64
    refactorization_interval::Int
    log_level::LogLevel
    algorithm::Symbol
end

SolverOptions(; kwargs...) = SolverOptions(Float64; kwargs...)

function _positive_tolerance(::Type{T}, ratio) where {T<:AbstractFloat}
    tolerance = T(ratio)
    return iszero(tolerance) ? nextfloat(zero(T)) : tolerance
end

function SolverOptions(::Type{T};
    primal_tolerance=nothing, dual_tolerance=nothing, zero_tolerance=nothing,
    iteration_limit::Integer=100_000, time_limit::Real=Inf,
    refactorization_interval::Integer=20,
    log_level::LogLevel=Logging.Debug, algorithm::Symbol=:dual,
) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported solver value type $T"))
    defaults = _is_exact(T) === Val(true) ? (zero(T), zero(T), zero(T)) :
        (_positive_tolerance(T, 1 // 10^7), _positive_tolerance(T, 1 // 10^7),
         _positive_tolerance(T, 1 // 10^12))
    tolerances = map(T, (
        something(primal_tolerance, defaults[1]),
        something(dual_tolerance, defaults[2]),
        something(zero_tolerance, defaults[3]),
    ))
    all(isfinite, tolerances) || throw(ArgumentError("tolerances must be finite"))
    if _is_exact(T) === Val(true)
        all(>=(zero(T)), tolerances) ||
            throw(ArgumentError("rational tolerances must be nonnegative"))
    else
        all(>(zero(T)), tolerances) ||
            throw(ArgumentError("floating tolerances must be positive"))
    end
    iteration_limit >= 0 || throw(ArgumentError("iteration_limit must be nonnegative"))
    converted_time_limit = Float64(time_limit)
    (isfinite(converted_time_limit) || converted_time_limit == Inf) &&
        converted_time_limit >= 0 ||
        throw(ArgumentError("time_limit must be nonnegative and finite or positive Inf"))
    refactorization_interval > 0 ||
        throw(ArgumentError("refactorization_interval must be positive"))
    return SolverOptions{T}(tolerances..., Int(iteration_limit), converted_time_limit,
                            Int(refactorization_interval), log_level, algorithm)
end

SolverOptions(::Type{T}, options::SolverOptions) where {T<:Real} =
    SolverOptions(T;
                  primal_tolerance=options.primal_tolerance,
                  dual_tolerance=options.dual_tolerance,
                  zero_tolerance=options.zero_tolerance,
                  iteration_limit=options.iteration_limit,
                  time_limit=options.time_limit,
                  refactorization_interval=options.refactorization_interval,
                  log_level=options.log_level,
                  algorithm=options.algorithm)

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
struct Solution{T<:Real}
    status::TerminationStatus
    objective_value::Union{Nothing,T}
    primal::Union{Nothing,Vector{T}}
    statistics::SolveStatistics
    message::String
end

function Solution(status::TerminationStatus, objective::T,
                  primal::Vector{T}, statistics::SolveStatistics,
                  message::AbstractString) where {T<:Real}
    return Solution{T}(status, objective, primal, statistics, String(message))
end

function Solution(status::TerminationStatus, objective::T,
                  primal::Vector{T}, statistics::SolveStatistics,
                  message::String) where {T<:Real}
    return Solution{T}(status, objective, primal, statistics, message)
end

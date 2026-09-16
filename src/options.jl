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
@doc "The completed-simplex-step limit was reached." ITERATION_LIMIT
@doc "The wall-clock deadline was reached." TIME_LIMIT
@doc "A numerical failure prevented a reliable solution." NUMERICAL_ERROR
@doc "The supplied model failed validation at solve time." INVALID_MODEL
@doc "A non-continuous model requires explicit LP relaxation." MIP_NOT_SUPPORTED
@doc "The requested algorithm is not implemented; use `:dual` or `:primal`." ALGORITHM_NOT_SUPPORTED

"""
    SolverOptions(::Type{T}; primal_tolerance=nothing, dual_tolerance=nothing,
                  zero_tolerance=nothing, iteration_limit=100_000,
                  time_limit=Inf, refactorization_interval=20,
                  verbose=true, log_level=Logging.Debug, algorithm=:dual,
                  pricing=:steepest_edge, basis_update=:pfi,
                  basis_refactorization=:native)
    SolverOptions(; kwargs...)  # Float64 defaults
    SolverOptions(T, options::SolverOptions)

Configure numerical tolerances, completed-step and wall-clock limits, basis
refactorization frequency, progress output, and the level used for Julia logging
messages. With `verbose=true`, every completed basis refactorization emits an
`Info`-level, single-line progress record containing the iteration count, original
objective value, primal and dual infeasibility sums and counts, and elapsed time.
`SolverOptions(T; ...)` stores tolerances in the supported floating or rational
type `T`. Floating defaults are `T(1 // 10^7)` for primal/dual tolerances and
`T(1 // 10^12)` for zero tolerance; a positive default that rounds to zero is
clamped to `nextfloat(zero(T))`. Rational defaults are exactly zero.
`SolverOptions(T, options)` converts and validates existing tolerances, preserving
their supplied values and the remaining options. It does not reset tolerances
to `T`'s defaults. [`solve`](@ref) uses problem-typed defaults when options are
omitted and converts explicit options to the problem's scalar type.
Floating-point tolerances and the refactorization interval must be positive;
rational tolerances must be nonnegative. Tolerances must be finite.
Limits must be nonnegative. `time_limit` remains `Float64` seconds and `Inf`
disables the deadline; iteration/refactorization limits remain `Int`.
`algorithm=:dual` and `algorithm=:primal` are implemented; other symbols return
`ALGORITHM_NOT_SUPPORTED` from [`solve`](@ref).
`pricing` selects steepest-edge (`:steepest_edge`), Devex (`:devex`), or
Dantzig (`:dantzig`) pricing for either simplex algorithm. Primal steepest-edge
weights are recomputed for each pricing decision.
`basis_update` selects product-form (`:pfi`), Forrest–Tomlin
(`:forrest_tomlin`), Bartels–Golub (`:bartels_golub`), or Suhl–Suhl
(`:suhl_suhl`) basis updates.
`basis_refactorization` selects the existing backend (`:native`: UMFPACK for
`Float64`, dense LU otherwise) or sparse Markowitz elimination followed by a
dense trailing core (`:markowitz`).

```julia
using JSimplex
exact = SolverOptions(Rational{BigInt}; time_limit=2.5)
@assert exact.primal_tolerance == 0
@assert exact.time_limit === 2.5
single = SolverOptions(Float32, SolverOptions())
@assert single.dual_tolerance isa Float32
```
"""
struct SolverOptions{T<:Real,M,R}
    primal_tolerance::T
    dual_tolerance::T
    zero_tolerance::T
    iteration_limit::Int
    time_limit::Float64
    refactorization_interval::Int
    verbose::Bool
    log_level::LogLevel
    algorithm::Symbol
    pricing::Symbol
    basis_update::Symbol
    basis_refactorization::Symbol
end

SolverOptions(; kwargs...) = SolverOptions(Float64; kwargs...)

function _positive_tolerance(::Type{T}, ratio) where {T<:AbstractFloat}
    tolerance = T(ratio)
    return iszero(tolerance) ? nextfloat(zero(T)) : tolerance
end

Base.@constprop :aggressive function SolverOptions(::Type{T};
    primal_tolerance=nothing, dual_tolerance=nothing, zero_tolerance=nothing,
    iteration_limit::Integer=100_000, time_limit::Real=Inf,
    refactorization_interval::Integer=20,
    verbose::Bool=true, log_level::LogLevel=Logging.Debug, algorithm::Symbol=:dual,
    pricing::Symbol=:steepest_edge, basis_update::Symbol=:pfi,
    basis_refactorization::Symbol=:native,
) where {T}
    arguments = (primal_tolerance, dual_tolerance, zero_tolerance, iteration_limit,
                 time_limit, refactorization_interval, verbose, log_level,
                 algorithm, pricing)
    if basis_update === :pfi
        return _validated_refactorization(T, Val(:pfi), basis_refactorization, arguments...)
    elseif basis_update === :forrest_tomlin
        return _validated_refactorization(T, Val(:forrest_tomlin), basis_refactorization, arguments...)
    elseif basis_update === :bartels_golub
        return _validated_refactorization(T, Val(:bartels_golub), basis_refactorization, arguments...)
    elseif basis_update === :suhl_suhl
        return _validated_refactorization(T, Val(:suhl_suhl), basis_refactorization, arguments...)
    end
    throw(ArgumentError("basis_update must be :pfi, :forrest_tomlin, :bartels_golub, or :suhl_suhl"))
end

Base.@constprop :aggressive function _validated_refactorization(
    ::Type{T}, mode::Val, basis_refactorization::Symbol, arguments...,
) where {T}
    if basis_refactorization === :native
        return _validated_options(T, mode, Val(:native), arguments...)
    elseif basis_refactorization === :markowitz
        return _validated_options(T, mode, Val(:markowitz), arguments...)
    end
    throw(ArgumentError("basis_refactorization must be :native or :markowitz"))
end

function _validated_options(::Type{T}, ::Val{M}, ::Val{R}, primal_tolerance, dual_tolerance,
                            zero_tolerance, iteration_limit, time_limit,
                            refactorization_interval, verbose, log_level, algorithm,
                            pricing) where {T,M,R}
    _supported_value_type(T) || throw(ArgumentError("unsupported solver value type $T"))
    defaults = _is_exact(T) === Val(true) ? (zero(T), zero(T), zero(T)) :
        (_positive_tolerance(T, 1 // 10^7), _positive_tolerance(T, 1 // 10^7),
         _positive_tolerance(T, 1 // 10^12))
    # Already-typed BigFloat tolerances retain their stored value and precision.
    tolerances = map(value -> convert(T, value), (
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
    (isfinite(time_limit) || time_limit == Inf) && time_limit >= 0 ||
        throw(ArgumentError("time_limit must be nonnegative and finite or positive Inf"))
    converted_time_limit = Float64(time_limit)
    (isfinite(converted_time_limit) || converted_time_limit == Inf) &&
        converted_time_limit >= 0 ||
        throw(ArgumentError("time_limit must be nonnegative and finite or positive Inf"))
    refactorization_interval > 0 ||
        throw(ArgumentError("refactorization_interval must be positive"))
    pricing in (:steepest_edge, :devex, :dantzig) ||
        throw(ArgumentError("pricing must be :steepest_edge, :devex, or :dantzig"))
    return SolverOptions{T,M,R}(tolerances..., Int(iteration_limit), converted_time_limit,
                              Int(refactorization_interval), verbose, log_level,
                              algorithm, pricing, M, R)
end

SolverOptions(::Type{T}, options::SolverOptions{S,M,R}) where {T,S,M,R} =
    _validated_options(T, Val(M), Val(R), options.primal_tolerance, options.dual_tolerance,
                       options.zero_tolerance, options.iteration_limit,
                       options.time_limit, options.refactorization_interval,
                       options.verbose, options.log_level, options.algorithm,
                       options.pricing)

"""
    SolveStatistics(; iterations=0, elapsed_seconds=0.0, refactorizations=0)

Solve counters retained for every termination status: completed simplex steps
(basis pivots or primal bound flips),
elapsed wall-clock time in seconds, and full basis factorizations. Counters are
`Int` and `elapsed_seconds` is `Float64`, independent of model arithmetic.
"""
Base.@kwdef struct SolveStatistics
    iterations::Int = 0
    elapsed_seconds::Float64 = 0.0
    refactorizations::Int = 0
end

"""
    Solution(status, objective_value, primal, statistics, message)
    Solution{T}(status, objective_value, primal, statistics, message)

Result of [`solve`](@ref). `status` is a [`TerminationStatus`](@ref),
`statistics` is a [`SolveStatistics`](@ref), and `message` explains termination.
For `OPTIMAL`, `primal` contains the original structural variable values and
`objective_value` includes the original objective sense and constant. Both
fields are `nothing` for every other status, including resource limits.
Solving a `LinearProblem{T}` returns the same concrete `Solution{T}` on every
termination path: `objective_value::Union{Nothing,T}` and
`primal::Union{Nothing,Vector{T}}`. The constructor infers `T` from a supplied
objective and primal vector; use `Solution{T}` explicitly when both are `nothing`.
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

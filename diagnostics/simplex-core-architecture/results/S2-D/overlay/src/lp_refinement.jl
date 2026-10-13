"""Owned maps between the original working variables and a lifted correction LP."""
struct CorrectionMap{R<:Real}
    original_to_correction::Vector{Int}
    correction_to_original::Vector{Int}
    fixed_activities::Vector{Int}
    primal_scale::R
    dual_scale::R
end

struct LPResiduals{R<:Real}
    values::Vector{R}
    multipliers::Vector{R}
    primal::Vector{R}
    dual::Vector{R}
end

_lp_residual_bits(ws) = max(128, _transfer_bits(ws, ws.progress.numerical_policy, 2) + 64)

function _lp_residual_values(::Type{R}, ws, values, multipliers) where R
    m, n = size(ws.problem.A)
    length(values) == n+m && length(multipliers) == m ||
        throw(DimensionMismatch("LP residual coordinates do not match the original model"))
    v, y = _copy_working_values(R, values), _copy_working_values(R, multipliers)
    all(isfinite, v) && all(isfinite, y) || throw(ArgumentError("Nonfinite LP residual candidate"))
    primal = copy(v[n+1:end])
    dual = vcat(_copy_working_values(R, ws.problem.objective), copy(y))
    for j in 1:n, k in nzrange(ws.problem.A, j)
        i, a = ws.problem.A.rowval[k], R(ws.problem.A.nzval[k])
        primal[i] -= a*v[j]
        dual[j] -= a*y[i]
    end
    return LPResiduals(v, y, primal, dual)
end

function _lp_residuals(ws::SimplexWorkspace{T}, values, multipliers;
                       bits::Int=_lp_residual_bits(ws)) where T
    if _is_exact(T) === Val(true)
        return _lp_residual_values(T, ws, values, multipliers)
    end
    actual = max(bits, _working_value_bits(values), _working_value_bits(multipliers))
    return setprecision(BigFloat, actual) do
        _lp_residual_values(BigFloat, ws, values, multipliers)
    end
end

_lp_power_of_two(x::AbstractFloat) = isfinite(x) && x > 0 && significand(x) == 1
_lp_power_of_two(x::Rational) = x > 0 && ispow2(numerator(x)) && ispow2(denominator(x))

function _lp_round(::Type{T}, value, bits) where T
    rounded = T === BigFloat ? BigFloat(value; precision=bits) : T(value)
    isfinite(rounded) && (iszero(rounded) == iszero(value)) ||
        throw(ArgumentError("Correction coefficient is not representable at working precision"))
    return rounded === value && rounded isa BigFloat ? deepcopy(rounded) : rounded
end

function _lp_shifted_bound(::Type{T}, bound, value, scale, bits) where T
    isfinite(bound) || return Bound{T}(nothing)
    return Bound(_lp_round(T, scale*(typeof(value)(bound_value(bound))-value), bits))
end

function _build_correction_problem(ws::SimplexWorkspace{T}, residuals::LPResiduals{R},
                                   primal_scale::R, dual_scale::R) where {T,R}
    _lp_power_of_two(primal_scale) && _lp_power_of_two(dual_scale) ||
        throw(ArgumentError("Correction scales must be finite positive powers of two"))
    m, n = size(ws.problem.A)
    N = m+n
    length(residuals.values) == N && length(residuals.dual) == N &&
        length(residuals.primal) == m && length(residuals.multipliers) == m ||
        throw(DimensionMismatch("Correction residual dimensions do not match the original model"))
    bits = T <: AbstractFloat ? _precision_current_bits(ws) : 0
    costs = [_lp_round(T, dual_scale*r, bits) for r in residuals.dual]
    rhs = [_lp_round(T, primal_scale*r, bits) for r in residuals.primal]
    lower, upper = Vector{Bound{T}}(undef, N), Vector{Bound{T}}(undef, N)
    for j in 1:N
        lo = j <= n ? ws.problem.column_lower[j] : ws.problem.row_lower[j-n]
        hi = j <= n ? ws.problem.column_upper[j] : ws.problem.row_upper[j-n]
        lower[j] = _lp_shifted_bound(T, lo, residuals.values[j], primal_scale, bits)
        upper[j] = _lp_shifted_bound(T, hi, residuals.values[j], primal_scale, bits)
    end
    problem = _with_transfer_precision(T, bits) do
        A = _copy_working_values(T, ws.problem.A)
        ptr, rows, entries = A.colptr, A.rowval, A.nzval
        for i in 1:m
            push!(rows, i); push!(entries, -one(T)); push!(ptr, length(entries)+1)
        end
        matrix = SparseMatrixCSC(m, N, ptr, rows, entries)
        LinearProblem{T}(matrix, costs, zero(T), MIN_SENSE, Bound.(rhs), Bound.(rhs),
            lower, upper, fill(CONTINUOUS, N), "LP correction", String[], String[])
    end
    map = CorrectionMap(collect(1:N), vcat(collect(1:N), zeros(Int, m)),
        collect(N+1:N+m), primal_scale, dual_scale)
    return problem, map
end

"""Build M*z=s_p*r_p with shifted bounds and the complete lifted residual cost.

Original row activities are structural correction variables, with costs s_d*y.
The correction solver's extra activities are fixed at the scaled residual, which
can be nonzero; they must never be mistaken for zero artificials or original columns.
"""
function build_correction_problem(ws, residuals::LPResiduals{R}, primal_scale, dual_scale) where R
    bits = max(_working_value_bits(residuals.values), _working_value_bits(residuals.dual),
        _working_value_bits(residuals.primal), _working_value_bits(residuals.multipliers))
    return _with_transfer_precision(R, bits) do
        _build_correction_problem(ws, residuals, R(primal_scale), R(dual_scale))
    end
end

function _lp_bounded_scale(::Type{T}, residual, coefficients::Vector{R}, bits) where {T,R}
    nonzero = filter(!iszero, coefficients)
    isempty(nonzero) && return one(R)
    all(isfinite, nonzero) || throw(ArgumentError("Nonfinite correction scaling data"))
    smallest, largest = minimum(abs, nonzero), maximum(abs, nonzero)
    minimum_value, maximum_value = _with_transfer_precision(T, bits) do
        R(nextfloat(zero(T))), R(floatmax(T))
    end
    # Exponent differences use BigInt because MPFR permits an almost Int-wide
    # exponent range. Mantissas determine the one-bit endpoint adjustment.
    low = big(exponent(minimum_value))-exponent(smallest)
    high = big(exponent(maximum_value))-exponent(largest)
    significand(largest) > significand(maximum_value) && (high -= 1)
    low = max(low, exponent(nextfloat(zero(R))))
    high = min(high, exponent(floatmax(R)))
    low <= high || throw(ArgumentError("No representable correction scale exists"))
    magnitude = maximum(abs, residual; init=zero(R))
    wanted = iszero(magnitude) ? big(0) : -big(exponent(magnitude))
    scale = ldexp(one(R), Int(clamp(wanted, low, high)))
    for value in nonzero
        _lp_round(T, scale*value, bits)
    end
    return scale
end

function _lp_correction_scales(ws::SimplexWorkspace{T}, residuals::LPResiduals{R}) where {T,R}
    _is_exact(T) === Val(true) && return one(R), one(R)
    bits = max(_working_value_bits(residuals.values), _working_value_bits(residuals.primal),
        _working_value_bits(residuals.dual), _working_value_bits(residuals.multipliers))
    return _with_transfer_precision(R, bits) do
        m,n = size(ws.problem.A)
        coefficients = copy(residuals.primal)
        for j in eachindex(residuals.values)
            lo = j <= n ? ws.problem.column_lower[j] : ws.problem.row_lower[j-n]
            hi = j <= n ? ws.problem.column_upper[j] : ws.problem.row_upper[j-n]
            for bound in (lo,hi)
                isfinite(bound) && push!(coefficients,R(bound_value(bound))-residuals.values[j])
            end
        end
        working_bits = _precision_current_bits(ws)
        primal = _lp_bounded_scale(T,residuals.primal,coefficients,working_bits)
        dual = _lp_bounded_scale(T,residuals.dual,residuals.dual,working_bits)
        return primal,dual
    end
end

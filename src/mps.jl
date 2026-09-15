include("mps/records.jl")
include("mps/parser.jl")
include("mps/build.jl")

_parse_mps_file(path::AbstractString; format::Symbol=:auto) =
    _parse_mps_file(path, Float64; format)

function _parse_mps_file(path::AbstractString, ::Type{T}; format::Symbol=:auto) where {T<:Real}
    open(path, "r") do io
        return _parse_mps(io, String(path), T; format=format)
    end
end

"""
    read_mps(path; format=:auto, rhs_name=nothing, ranges_name=nothing,
             bounds_name=nothing, objective_name=nothing, value_type=Float64)

Read a fixed or free MPS file into `LinearProblem{T}`, where `T=value_type`.
The default is `Float64`; supported scalar families are concrete `AbstractFloat`
and `Rational` types. Floating tokens are parsed directly in `T`. For exact
input, use `Rational{BigInt}`: decimal and `E`/`D` exponent tokens are parsed
without floating intermediates (`1.25` becomes `5//4`, `-2e-3` becomes `-1//500`).
Rational parsing, duplicate aggregation, and range arithmetic use BigInt rational
intermediates with checked conversion to `T`. Fixed-width rational construction
overflow raises source-aware `MPSParseError`; later solve arithmetic retains
Julia's ordinary fixed-width overflow behavior. For `BigFloat`, wrap reading
and solving in the desired `setprecision` context.

All bounds are `Bound{T}` values. Unbounded endpoints use tags; inspect them with
`isfinite` and read finite values with [`bound_value`](@ref).

Named RHS, range, and bound sets default to the first set in file order.
The objective defaults to
`OBJNAME`, then the first `N` row; `objective_name` overrides either choice.
All `N` rows are excluded from the constraint matrix. Integer markers and
binary and semi-variable bounds retain their variable domains.

`format` accepts `:auto`, `:fixed`, or `:free`. Supported sections are `NAME`,
`OBJSENSE` (also `OBJSEN`), `OBJNAME`, `ROWS`, `COLUMNS`, `RHS`, `RANGES`,
`BOUNDS`, and `ENDATA`; row types are `N`, `E`, `L`, and `G`. Bounds support
`LO`, `UP`, `FX`, `FR`, `MI`, `PL`, `BV`, `LI`, `UI`, `SC`, and `SI`.
`INTORG`/`INTEND` preserve integer domains with default bounds `[0, 1]`.
Duplicate coefficients are summed; objective RHS values have their sign
reversed to form the objective constant. Without an `N` row the objective is zero.

Malformed or unsupported MPS data raises `MPSParseError`. A diagnostic for
an invalid named-set/objective selection uses line zero because it has no source
record. An invalid `format` raises `ArgumentError`; file access errors propagate.

```julia
using JSimplex
# Run from the repository root.
exact_mps = read_mps("test/fixtures/parser/exact-rational.mps";
                     value_type=Rational{BigInt})
@assert exact_mps.A[1, 1] == 3 // big(10)
@assert solve(exact_mps).objective_value == 11 // big(4)
```
"""
Base.@constprop :aggressive function read_mps(
    path::AbstractString; format::Symbol=:auto, rhs_name=nothing,
    ranges_name=nothing, bounds_name=nothing, objective_name=nothing,
    value_type::Type{T}=Float64,
) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported MPS value type $T"))
    records = _parse_mps_file(path, T; format)
    return _build_mps(records; rhs_name, ranges_name, bounds_name, objective_name)
end

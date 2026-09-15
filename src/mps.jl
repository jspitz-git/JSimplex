include("mps/records.jl")
include("mps/parser.jl")
include("mps/build.jl")

function _parse_mps_file(path::AbstractString; format::Symbol=:auto)
    open(path, "r") do io
        return _parse_mps(io, String(path); format=format)
    end
end

"""
    read_mps(path; format=:auto, rhs_name=nothing, ranges_name=nothing,
             bounds_name=nothing, objective_name=nothing)::LinearProblem

Read a fixed or free MPS file into a `LinearProblem`. Named RHS, range, and
bound sets default to the first set in file order. The objective defaults to
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
"""
function read_mps(
    path::AbstractString; format::Symbol=:auto, rhs_name=nothing,
    ranges_name=nothing, bounds_name=nothing, objective_name=nothing,
)::LinearProblem
    records = _parse_mps_file(path; format=format)
    return _build_mps(records; rhs_name, ranges_name, bounds_name, objective_name)
end

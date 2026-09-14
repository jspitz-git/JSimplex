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

Malformed or unsupported MPS data raises `MPSParseError`. A diagnostic for
an invalid keyword selection uses line zero because it has no source record.
"""
function read_mps(
    path::AbstractString; format::Symbol=:auto, rhs_name=nothing,
    ranges_name=nothing, bounds_name=nothing, objective_name=nothing,
)::LinearProblem
    records = _parse_mps_file(path; format=format)
    return _build_mps(records; rhs_name, ranges_name, bounds_name, objective_name)
end

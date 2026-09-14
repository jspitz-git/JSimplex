include("mps/records.jl")
include("mps/parser.jl")

function _parse_mps_file(path::AbstractString; format::Symbol=:auto)
    open(path, "r") do io
        return _parse_mps(io, String(path); format=format)
    end
end

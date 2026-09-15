"""
    MPSParseError(source, line, section, message)

Malformed or unsupported MPS input, reported with its source path, line number,
section symbol, and explanation. Line zero identifies a keyword selection with
no corresponding source record. Thrown by [`read_mps`](@ref).
"""
struct MPSParseError <: Exception
    source::String
    line::Int
    section::Symbol
    message::String
end

function Base.showerror(io::IO, error::MPSParseError)
    print(io, error.source, ':', error.line, " [", error.section, "] ", error.message)
end

struct BoundRecord
    kind::Symbol
    column::String
    value::Union{Nothing,Float64}
    line::Int
end

mutable struct MPSAccumulator
    source::String
    name::String
    objective_sense::ObjectiveSense
    objective_name::Union{Nothing,String}
    objective_name_line::Int
    row_order::Vector{String}
    row_types::Dict{String,Char}
    column_order::Vector{String}
    coefficients::Vector{Tuple{String,String,Float64,Int}}
    rhs_sets::Dict{String,Vector{Tuple{String,Float64,Int}}}
    rhs_order::Vector{String}
    ranges_sets::Dict{String,Vector{Tuple{String,Float64,Int}}}
    ranges_order::Vector{String}
    bounds_sets::Dict{String,Vector{BoundRecord}}
    bounds_order::Vector{String}
    marker_domains::Dict{String,VariableDomain}
end

function MPSAccumulator(source::AbstractString)
    return MPSAccumulator(
        String(source), "", MIN_SENSE, nothing, 0, String[], Dict{String,Char}(),
        String[], Tuple{String,String,Float64,Int}[],
        Dict{String,Vector{Tuple{String,Float64,Int}}}(), String[],
        Dict{String,Vector{Tuple{String,Float64,Int}}}(), String[],
        Dict{String,Vector{BoundRecord}}(), String[], Dict{String,VariableDomain}(),
    )
end

_mps_error(records, line, section, message) =
    throw(MPSParseError(records.source, line, section, message))

function _mps_number(token, records, line, section)
    value = tryparse(Float64, replace(token, 'D' => 'E', 'd' => 'e'))
    value === nothing && _mps_error(records, line, section, "expected a finite number, got '$token'")
    isfinite(value) || _mps_error(records, line, section, "number must be finite: '$token'")
    return value
end

const _MPS_SEPARATORS = (4, 13, 14, 23, 24, 37, 38, 39, 48, 49)

_mps_fixed_layout(text) = all(
    i -> i > ncodeunits(text) || codeunit(text, i) == UInt8(' '), _MPS_SEPARATORS,
)

function _mps_fields(text, format, records, line, section)
    if format == :auto
        # Fixed records must reach their last required field; short free records
        # can otherwise match every separator by accident.
        minimum_width = section == :ROWS ? 5 : section == :BOUNDS ? 15 : 25
        fixed = ncodeunits(rstrip(text)) >= minimum_width && _mps_fixed_layout(text)
        if fixed && section in (:COLUMNS, :RHS, :RANGES)
            fixed = codeunit(text, 2) == codeunit(text, 3) == UInt8(' ')
        end
        format = fixed ? :fixed : :free
    end
    format == :free && return String.(split(text)), false
    isascii(text) || _mps_error(records, line, section, "fixed records must contain ASCII characters")
    padded = rpad(text, 61)
    all(i -> padded[i] == ' ', _MPS_SEPARATORS) ||
        _mps_error(records, line, section, "nonblank fixed separator column")
    padded[1] == ' ' || _mps_error(records, line, section, "fixed data must start with a blank")
    isempty(strip(padded[62:end])) ||
        _mps_error(records, line, section, "unexpected data after fixed column 61")
    fields = [String(strip(padded[r])) for r in (2:3, 5:12, 15:22, 25:36, 40:47, 50:61)]
    if section == :ROWS
        all(isempty, fields[3:6]) || _mps_error(records, line, section, "unexpected ROWS fields")
        return fields[1:2], true
    elseif section == :BOUNDS
        all(isempty, fields[5:6]) || _mps_error(records, line, section, "unexpected BOUNDS fields")
        return isempty(fields[4]) ? fields[1:3] : fields[1:4], true
    end
    isempty(fields[1]) || _mps_error(records, line, section, "unexpected fixed record type")
    if section == :COLUMNS && fields[3] == "'MARKER'"
        isempty(fields[4]) && isempty(fields[6]) ||
            _mps_error(records, line, section, "invalid marker fields")
        return fields[[2, 3, 5]], true
    end
    if isempty(fields[5]) && isempty(fields[6])
        return fields[2:4], true
    end
    return fields[2:6], true
end

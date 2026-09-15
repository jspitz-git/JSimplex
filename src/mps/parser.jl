const _MPS_SECTIONS = (:NAME, :OBJSENSE, :OBJNAME, :ROWS, :COLUMNS, :RHS, :RANGES, :BOUNDS, :ENDATA)
const _MPS_BOUND_TYPES = (:LO, :UP, :FX, :FR, :MI, :PL, :BV, :LI, :UI, :SC, :SI)

function _mps_bound_error(kind, column, value, columns)
    column in columns || return "unknown column '$column'"
    if kind in (:FR, :MI, :PL)
        value === nothing || return "$kind does not accept a value"
    elseif kind == :BV
        value === nothing || value == 1.0 || return "BV accepts no value or the value 1"
    else
        value === nothing && return "$kind requires a value"
        kind in (:LI, :UI) && !isinteger(value) && return "$kind requires an integral value"
    end
    return nothing
end

function _mps_metadata!(records, section, fields, line)
    length(fields) == 1 || _mps_error(records, line, section, "expected one metadata value")
    if section == :OBJSENSE
        fields[1] in ("MIN", "MAX") || _mps_error(records, line, section, "invalid objective sense '$(fields[1])'")
        records.objective_sense = fields[1] == "MIN" ? MIN_SENSE : MAX_SENSE
    else
        records.objective_name = fields[1]
        records.objective_name_line = line
    end
end

function _mps_pairs!(records::MPSAccumulator{T}, section, fields, line) where {T}
    length(fields) in (3, 5) && all(!isempty, fields) ||
        _mps_error(records, line, section, "expected a name and one or two row/value pairs")
    name = fields[1]
    for i in 2:2:length(fields)
        row = fields[i]
        haskey(records.row_types, row) || _mps_error(records, line, section, "unknown row '$row'")
        value = _mps_number(records, fields[i + 1], line, section)
        if section == :COLUMNS
            push!(records.coefficients, (name, row, value, line))
        else
            sets, order = section == :RHS ? (records.rhs_sets, records.rhs_order) :
                                           (records.ranges_sets, records.ranges_order)
            if !haskey(sets, name)
                sets[name] = Tuple{String,T,Int}[]
                push!(order, name)
            end
            push!(sets[name], (row, value, line))
        end
    end
end

_parse_mps(io::IO, source::AbstractString; format::Symbol=:auto) =
    _parse_mps(io, source, Float64; format)

function _parse_mps(io::IO, source::AbstractString, ::Type{T};
                    format::Symbol=:auto) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported MPS value type $T"))
    format in (:auto, :fixed, :free) || throw(ArgumentError("format must be :auto, :fixed, or :free"))
    records = MPSAccumulator(source, T)
    section = :START
    seen = Set{Symbol}()
    columns = Set{String}()
    previous_names = Dict{Symbol,String}()
    integer_mode = false
    pending_metadata = false
    line_number = 0

    for (line, original) in enumerate(eachline(io))
        line_number = line
        stripped = strip(original)
        (isempty(stripped) || startswith(stripped, '*')) && continue
        # A dollar comment starts at a field boundary, not inside a name.
        text = replace(original, r"(?<!\S)\$.*$" => "")
        isempty(strip(text)) && continue
        section == :ENDATA && _mps_error(records, line, section, "data after ENDATA")
        words = String.(split(text))
        # Objective names may be section keywords, including in two-line metadata.
        if pending_metadata && section == :OBJNAME
            _mps_metadata!(records, section, words, line)
            pending_metadata = false
            continue
        end
        candidate = Symbol(words[1] == "OBJSEN" ? "OBJSENSE" : words[1])
        # A fixed continuation can have only two words, like an inline header.
        continuation = section in (:COLUMNS, :RHS, :RANGES) && format != :free &&
                       length(words) in (2, 4) && _mps_fixed_layout(text) &&
                       ncodeunits(text) >= 25 &&
                       all(i -> codeunit(text, i) == UInt8(' '), 1:14)
        header = !continuation && candidate in _MPS_SECTIONS &&
                 (length(words) == 1 ||
                  (length(words) == 2 && candidate in (:NAME, :OBJSENSE, :OBJNAME)))

        if header
            pending_metadata && _mps_error(records, line, section, "missing metadata value")
            section == :START && candidate != :NAME &&
                _mps_error(records, line, candidate, "NAME must be the first section")
            candidate in seen && _mps_error(records, line, candidate,
                "duplicate section or invalid section order")
            valid_order = if candidate == :NAME
                section == :START
            elseif candidate in (:OBJSENSE, :OBJNAME, :ROWS)
                section in (:NAME, :OBJSENSE, :OBJNAME)
            elseif candidate == :COLUMNS
                section == :ROWS
            elseif candidate == :RHS
                section == :COLUMNS
            elseif candidate == :RANGES
                section in (:COLUMNS, :RHS)
            elseif candidate == :BOUNDS
                section in (:COLUMNS, :RHS, :RANGES)
            else
                section in (:COLUMNS, :RHS, :RANGES, :BOUNDS)
            end
            valid_order || _mps_error(records, line, candidate, "invalid section order")
            push!(seen, candidate)
            section = candidate
            if section == :NAME
                length(words) <= 2 || _mps_error(records, line, section, "expected at most one problem name")
                records.name = length(words) == 2 ? words[2] : ""
            elseif section in (:OBJSENSE, :OBJNAME)
                pending_metadata = length(words) == 1
                pending_metadata || _mps_metadata!(records, section, words[2:end], line)
            elseif section == :ENDATA
                integer_mode && _mps_error(records, line, section, "unterminated INTORG marker block")
            end
            continue
        end

        if pending_metadata
            _mps_metadata!(records, section, words, line)
            pending_metadata = false
            continue
        end
        pair_record = section in (:COLUMNS, :RHS, :RANGES) && length(words) in (3, 5)
        if !continuation && (length(words) == 1 ||
           (!pair_record && candidate in (:QMATRIX, :QUADOBJ, :QSECTION, :SOS, :SOSORG, :CSECTION)))
            _mps_error(records, line, candidate, "unknown or unsupported section '$(words[1])'")
        end
        section in (:ROWS, :COLUMNS, :RHS, :RANGES, :BOUNDS) ||
            _mps_error(records, line, section, "unexpected data; expected an MPS section")
        fields, fixed = _mps_fields(text, format, records, line, section, columns)
        if section == :ROWS
            length(fields) == 2 && !isempty(fields[2]) || _mps_error(records, line, section, "expected row type and name")
            fields[1] in ("N", "E", "L", "G") || _mps_error(records, line, section, "invalid row type '$(fields[1])'")
            name = fields[2]
            haskey(records.row_types, name) && _mps_error(records, line, section, "duplicate row '$name'")
            records.row_types[name] = only(fields[1])
            push!(records.row_order, name)
            continue
        end

        if section == :COLUMNS && length(fields) >= 2 && fields[2] == "'MARKER'"
            length(fields) == 3 && !isempty(fields[1]) || _mps_error(records, line, section, "invalid marker record")
            if fields[3] == "'INTORG'"
                integer_mode && _mps_error(records, line, section, "nested INTORG marker")
                integer_mode = true
            elseif fields[3] == "'INTEND'"
                integer_mode || _mps_error(records, line, section, "INTEND without INTORG")
                integer_mode = false
            else
                _mps_error(records, line, section, "unknown marker '$(fields[3])'")
            end
            continue
        end

        name_index = section == :BOUNDS ? 2 : 1
        length(fields) >= name_index || _mps_error(records, line, section, "missing record name")
        if fixed && isempty(fields[name_index])
            haskey(previous_names, section) || _mps_error(records, line, section, "continuation has no preceding name")
            fields[name_index] = previous_names[section]
        end
        previous_names[section] = fields[name_index]

        if section == :BOUNDS
            length(fields) in (3, 4) && all(!isempty, fields) ||
                _mps_error(records, line, section, "expected bound type, set, column, and optional value")
            kind = Symbol(fields[1])
            kind in _MPS_BOUND_TYPES || _mps_error(records, line, section, "unsupported bound type '$kind'")
            name = fields[2]
            value = length(fields) == 4 ? _mps_number(records, fields[4], line, section) : nothing
            error = _mps_bound_error(kind, fields[3], value, columns)
            error === nothing || _mps_error(records, line, section, error)
            if !haskey(records.bounds_sets, name)
                records.bounds_sets[name] = BoundRecord{T}[]
                push!(records.bounds_order, name)
            end
            push!(records.bounds_sets[name], BoundRecord{T}(kind, fields[3], value, line))
        else
            _mps_pairs!(records, section, fields, line)
            if section == :COLUMNS
                name = fields[1]
                if !(name in columns)
                    push!(columns, name)
                    push!(records.column_order, name)
                end
                integer_mode && (records.marker_domains[name] = INTEGER)
            end
        end
    end
    section == :ENDATA || _mps_error(records, line_number, section, "missing ENDATA section")
    return records
end

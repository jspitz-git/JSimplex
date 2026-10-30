function _select_set(records, sets::Dict{String,V}, order, name, section) where {V}
    if name !== nothing
        haskey(sets, name) || _mps_error(records, 0, section, "unknown set '$name'")
        return sets[name]
    end
    return isempty(order) ? V() : sets[first(order)]
end

_mps_big(value::Rational) = BigInt(numerator(value)) // BigInt(denominator(value))

function _mps_checked_add(records::MPSAccumulator{T}, left::T, right::T,
                          line::Int, section::Symbol, message::F) where {T<:Rational,F}
    return _mps_checked_convert(T, _mps_big(left) + _mps_big(right),
                                records, line, section, message)
end

function _mps_checked_subtract(records::MPSAccumulator{T}, left::T, right::T,
                               line::Int, section::Symbol, message::F) where {T<:Rational,F}
    return _mps_checked_convert(T, _mps_big(left) - _mps_big(right),
                                records, line, section, message)
end

function _mps_checked_add(records::MPSAccumulator{T}, left::T, right::T,
                          line::Int, section::Symbol, message::F) where {T<:AbstractFloat,F}
    value = left + right
    isfinite(value) || _mps_error(records, line, section, message)
    return value
end

function _mps_checked_subtract(records::MPSAccumulator{T}, left::T, right::T,
                               line::Int, section::Symbol, message::F) where {T<:AbstractFloat,F}
    value = left - right
    isfinite(value) || _mps_error(records, line, section, message)
    return value
end

function _mps_range_endpoint(records::MPSAccumulator{T}, rhs::T, range::T,
                             subtract::Bool, line::Int, message::F) where {T<:Rational,F}
    # Check the completed endpoint: abs(typemin(I)) alone need not fit in T.
    magnitude = abs(_mps_big(range))
    endpoint = subtract ? _mps_big(rhs) - magnitude : _mps_big(rhs) + magnitude
    return _mps_checked_convert(T, endpoint, records, line, :RANGES, message)
end

function _mps_range_endpoint(records::MPSAccumulator{T}, rhs::T, range::T,
                             subtract::Bool, line::Int, message::F) where {T<:AbstractFloat,F}
    magnitude = abs(range)
    return subtract ? _mps_checked_subtract(records, rhs, magnitude, line, :RANGES, message) :
                      _mps_checked_add(records, rhs, magnitude, line, :RANGES, message)
end

function _mps_column_bounds(records::MPSAccumulator{T}, column_index, bounds) where {T}
    n = length(column_index)
    lower = fill(Bound(zero(T)), n)
    upper = fill(_unbounded_bound(T), n)
    domains = fill(CONTINUOUS, n)
    integral, semi, binary = falses(n), falses(n), falses(n)
    for column in keys(records.marker_domains)
        j = column_index[column]
        integral[j] = true
        upper[j] = Bound(one(T))
    end

    explicit_lower = Set(b.column for b in bounds if b.kind in (:LO, :LI, :FX, :FR, :MI, :BV))
    last_lines = zeros(Int, n)
    for bound in bounds
        kind, column, value, line = bound.kind, bound.column, bound.value, bound.line
        j = column_index[column]
        last_lines[j] = line
        if kind == :LO
            lower[j] = Bound(value)
        elseif kind == :UP
            upper[j] = Bound(value)
            value < zero(T) && !(column in explicit_lower) && (lower[j] = _unbounded_bound(T))
        elseif kind == :FX
            lower[j] = upper[j] = Bound(value)
        elseif kind == :FR
            lower[j], upper[j] = _unbounded_bound(T), _unbounded_bound(T)
        elseif kind == :MI
            lower[j] = _unbounded_bound(T)
        elseif kind == :PL
            upper[j] = _unbounded_bound(T)
        elseif kind == :BV
            semi[j] && _mps_error(records, line, :BOUNDS,
                "binary and semi-domain bounds conflict for column '$column'")
            binary[j] = integral[j] = true
            lower[j], upper[j] = Bound(zero(T)), Bound(one(T))
        elseif kind == :LI
            integral[j] = true
            lower[j] = Bound(value)
        elseif kind == :UI
            integral[j] = true
            upper[j] = Bound(value)
        elseif kind in (:SC, :SI)
            binary[j] && _mps_error(records, line, :BOUNDS,
                "binary and semi-domain bounds conflict for column '$column'")
            semi[j] = true
            integral[j] |= kind == :SI
            upper[j] = Bound(value)
            column in explicit_lower || (lower[j] = Bound(one(T)))
        else
            _mps_error(records, line, :BOUNDS, "unsupported bound type '$kind'")
        end
    end
    for (column, j) in column_index
        domains[j] = binary[j] ? BINARY : semi[j] ?
                     (integral[j] ? SEMI_INTEGER : SEMI_CONTINUOUS) :
                     (integral[j] ? INTEGER : CONTINUOUS)
        if isfinite(lower[j]) && isfinite(upper[j]) &&
           bound_value(lower[j]) > bound_value(upper[j])
            _mps_error(records, last_lines[j], :BOUNDS,
                "lower bound exceeds upper bound for column '$column'")
        end
        if domains[j] == BINARY
            (!isfinite(lower[j]) || bound_value(lower[j]) <= one(T)) &&
            (!isfinite(upper[j]) || bound_value(upper[j]) >= zero(T)) ||
                _mps_error(records, last_lines[j], :BOUNDS,
                "binary bounds for column '$column' must intersect [0, 1]")
        elseif domains[j] in (SEMI_CONTINUOUS, SEMI_INTEGER)
            (!isfinite(upper[j]) || bound_value(upper[j]) > zero(T)) ||
                _mps_error(records, last_lines[j], :BOUNDS,
                "semi-domain active upper bound for column '$column' must be positive")
        end
    end
    return lower, upper, domains
end

function _build_mps(
    records::MPSAccumulator{T}; rhs_name=nothing, ranges_name=nothing,
    bounds_name=nothing, objective_name=nothing,
) where {T}
    rhs = _select_set(records, records.rhs_sets, records.rhs_order, rhs_name, :RHS)
    ranges = _select_set(records, records.ranges_sets, records.ranges_order, ranges_name, :RANGES)
    bounds = _select_set(records, records.bounds_sets, records.bounds_order, bounds_name, :BOUNDS)

    selected_objective = objective_name === nothing ? records.objective_name : objective_name
    objective_line = objective_name === nothing ? records.objective_name_line : 0
    if selected_objective === nothing
        index = findfirst(row -> records.row_types[row] == 'N', records.row_order)
        index === nothing || (selected_objective = records.row_order[index])
    elseif get(records.row_types, selected_objective, nothing) != 'N'
        _mps_error(records, objective_line, :OBJNAME,
            "selected objective '$selected_objective' must name an N row")
    end

    row_names = [row for row in records.row_order if records.row_types[row] != 'N']
    row_index = Dict(row => i for (i, row) in enumerate(row_names))
    column_index = Dict(column => j for (j, column) in enumerate(records.column_order))
    m, n = length(row_names), length(records.column_order)
    objective = zeros(T, n)
    sums = Dict{Tuple{Int,Int},T}()
    for (column, row, value, line) in records.coefficients
        j = column_index[column]
        if row == selected_objective
            objective[j] = _mps_checked_add(records, objective[j], value, line, :COLUMNS,
                () -> "summed objective coefficient for column '$column' must be finite and representable as $T")
        elseif haskey(row_index, row)
            key = (row_index[row], j)
            sums[key] = _mps_checked_add(records, get(sums, key, zero(T)), value, line, :COLUMNS,
                () -> "summed matrix coefficient for column '$column', row '$row' must be finite and representable as $T")
        end
    end
    rows, columns, values = Int[], Int[], T[]
    for ((row, column), value) in sums
        push!(rows, row)
        push!(columns, column)
        push!(values, value)
    end
    A = sparse(rows, columns, values, m, n)

    rhs_values = zeros(T, m)
    objective_constant = zero(T)
    for (row, value, line) in rhs
        if row == selected_objective
            objective_constant = _mps_checked_subtract(records, zero(T), value, line, :RHS,
                () -> "objective constant must be finite and representable as $T")
        elseif haskey(row_index, row)
            rhs_values[row_index[row]] = value
        end
    end
    row_lower = fill(_unbounded_bound(T), m)
    row_upper = fill(_unbounded_bound(T), m)
    for (i, row) in enumerate(row_names)
        kind = records.row_types[row]
        kind != 'L' && (row_lower[i] = Bound(rhs_values[i]))
        kind != 'G' && (row_upper[i] = Bound(rhs_values[i]))
    end
    for (row, value, line) in ranges
        haskey(row_index, row) || continue
        i = row_index[row]
        kind, b = records.row_types[row], rhs_values[i]
        subtract = kind == 'L' || (kind == 'E' && value < zero(T))
        endpoint = _mps_range_endpoint(records, b, value, subtract, line,
            () -> "derived bounds for row '$row' must be finite and representable as $T")
        if subtract
            row_lower[i], row_upper[i] = Bound(endpoint), Bound(b)
        else
            row_lower[i], row_upper[i] = Bound(b), Bound(endpoint)
        end
    end
    column_lower, column_upper, domains = _mps_column_bounds(records, column_index, bounds)
    return LinearProblem(A, objective; value_type=T,
        objective_constant, objective_sense=records.objective_sense,
        row_lower, row_upper, column_lower, column_upper,
        variable_domains=domains, name=records.name, row_names,
        column_names=records.column_order,
    )
end

function _select_set(records, sets::Dict{String,V}, order, name, section) where {V}
    if name !== nothing
        haskey(sets, name) || _mps_error(records, 0, section, "unknown set '$name'")
        return sets[name]
    end
    return isempty(order) ? V() : sets[first(order)]
end

function _mps_column_bounds(records, column_index, bounds)
    n = length(column_index)
    lower, upper = zeros(n), fill(Inf, n)
    domains = fill(CONTINUOUS, n)
    for (column, domain) in records.marker_domains
        j = column_index[column]
        domains[j] = domain
        upper[j] = 1.0
    end

    explicit_lo = Set(b.column for b in bounds if b.kind == :LO)
    explicit_lower = Set(b.column for b in bounds if b.kind in (:LO, :LI, :FX, :FR, :MI, :BV))
    last_lines = zeros(Int, n)
    for bound in bounds
        kind, column, value, line = bound.kind, bound.column, bound.value, bound.line
        haskey(column_index, column) || _mps_error(records, line, :BOUNDS, "unknown column '$column'")
        if kind in (:FR, :MI, :PL)
            value === nothing || _mps_error(records, line, :BOUNDS, "$kind does not accept a value")
        elseif kind == :BV
            value === nothing || value == 1.0 ||
                _mps_error(records, line, :BOUNDS, "BV accepts no value or the value 1")
        else
            value === nothing && _mps_error(records, line, :BOUNDS, "$kind requires a value")
            kind in (:LI, :UI) && !isinteger(value) &&
                _mps_error(records, line, :BOUNDS, "$kind requires an integral value")
        end
        j = column_index[column]
        last_lines[j] = line
        if kind == :LO
            lower[j] = value
        elseif kind == :UP
            upper[j] = value
            value < 0 && !(column in explicit_lower) && (lower[j] = -Inf)
        elseif kind == :FX
            lower[j] = upper[j] = value
        elseif kind == :FR
            lower[j], upper[j] = -Inf, Inf
        elseif kind == :MI
            lower[j] = -Inf
        elseif kind == :PL
            upper[j] = Inf
        elseif kind == :BV
            domains[j] = BINARY
            lower[j], upper[j] = 0.0, 1.0
        elseif kind == :LI
            domains[j] = INTEGER
            lower[j] = value
        elseif kind == :UI
            domains[j] = INTEGER
            upper[j] = value
        elseif kind in (:SC, :SI)
            domains[j] = kind == :SC ? SEMI_CONTINUOUS : SEMI_INTEGER
            upper[j] = value
            column in explicit_lo || (lower[j] = 1.0)
        else
            _mps_error(records, line, :BOUNDS, "unsupported bound type '$kind'")
        end
    end
    for (column, j) in column_index
        lower[j] <= upper[j] || _mps_error(records, last_lines[j], :BOUNDS,
            "lower bound exceeds upper bound for column '$column'")
        if domains[j] == BINARY
            lower[j] <= 1.0 && upper[j] >= 0.0 || _mps_error(records, last_lines[j], :BOUNDS,
                "binary bounds for column '$column' must intersect [0, 1]")
        elseif domains[j] in (SEMI_CONTINUOUS, SEMI_INTEGER)
            upper[j] > 0.0 || _mps_error(records, last_lines[j], :BOUNDS,
                "semi-domain active upper bound for column '$column' must be positive")
        end
    end
    return lower, upper, domains
end

function _build_mps(
    records::MPSAccumulator; rhs_name=nothing, ranges_name=nothing,
    bounds_name=nothing, objective_name=nothing,
)
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
    objective = zeros(n)
    rows, columns, values = Int[], Int[], Float64[]
    for (column, row, value, line) in records.coefficients
        j = column_index[column]
        if row == selected_objective
            objective[j] += value
            isfinite(objective[j]) || _mps_error(records, line, :COLUMNS,
                "summed objective coefficient for column '$column' must be finite")
        elseif haskey(row_index, row)
            push!(rows, row_index[row])
            push!(columns, j)
            push!(values, value)
        end
    end
    A = sparse(rows, columns, values, m, n, +)
    if !all(isfinite, A.nzval)
        # Replay only on failure to locate the source record that overflowed.
        sums = Dict{Tuple{String,String},Float64}()
        for (column, row, value, line) in records.coefficients
            haskey(row_index, row) || continue
            key = (column, row)
            total = get(sums, key, 0.0) + value
            isfinite(total) || _mps_error(records, line, :COLUMNS,
                "summed matrix coefficient for column '$column', row '$row' must be finite")
            sums[key] = total
        end
    end

    rhs_values = zeros(m)
    objective_constant = 0.0
    for (row, value, _) in rhs
        if row == selected_objective
            objective_constant = -value
        elseif haskey(row_index, row)
            rhs_values[row_index[row]] = value
        end
    end
    row_lower, row_upper = copy(rhs_values), copy(rhs_values)
    for (i, row) in enumerate(row_names)
        kind = records.row_types[row]
        kind == 'L' && (row_lower[i] = -Inf)
        kind == 'G' && (row_upper[i] = Inf)
    end
    for (row, value, _) in ranges
        haskey(row_index, row) || continue
        i = row_index[row]
        kind, b = records.row_types[row], rhs_values[i]
        if kind == 'L' || (kind == 'E' && value < 0)
            row_lower[i], row_upper[i] = b - abs(value), b
        else
            row_lower[i], row_upper[i] = b, b + abs(value)
        end
    end
    column_lower, column_upper, domains = _mps_column_bounds(records, column_index, bounds)
    return LinearProblem(A, objective;
        objective_constant, objective_sense=records.objective_sense,
        row_lower, row_upper, column_lower, column_upper,
        variable_domains=domains, name=records.name, row_names,
        column_names=records.column_order,
    )
end

const BoundSource = Union{Nothing,Tuple{Int,VariableState}}

struct SingletonRowStep{T<:Real} <: AbstractPostsolveStep
    map::PresolveMap{T}
    lower_sources::Vector{BoundSource}
    upper_sources::Vector{BoundSource}
end

function _row_entries(A::SparseMatrixCSC{T,Int}) where {T}
    row_count = size(A, 1)
    # Counting storage is not worthwhile when most rows have very few entries.
    if nnz(A) <= row_count
        entries = [Tuple{Int,T}[] for _ in 1:row_count]
        for column in 1:size(A, 2)
            for position in A.colptr[column]:(A.colptr[column + 1] - 1)
                value = A.nzval[position]
                iszero(value) || push!(entries[A.rowval[position]], (column, value))
            end
        end
        return entries
    end

    counts = zeros(Int, row_count)
    for position in 1:nnz(A)
        iszero(A.nzval[position]) || (counts[A.rowval[position]] += 1)
    end
    entries = [Vector{Tuple{Int,T}}(undef, count) for count in counts]
    # Reuse the histogram as write positions while traversing columns in order.
    fill!(counts, 0)
    for column in 1:size(A, 2)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            value = A.nzval[position]
            iszero(value) && continue
            row = A.rowval[position]
            counts[row] += 1
            entries[row][counts[row]] = (column, value)
        end
    end
    return entries
end

function _row_result(problem::LinearProblem{T}, rows::Vector{Int};
                     column_lower=problem.column_lower,
                     column_upper=problem.column_upper) where {T}
    m, n = size(problem.A)
    length(rows) == m && column_lower == problem.column_lower &&
        column_upper == problem.column_upper && return identity_presolve(problem)
    # The model constructor copies its inputs. Avoid slicing unchanged rows first.
    all_rows = rows == axes(problem.A, 1)
    # A row slice also discards spare CSC storage; keep that behavior when needed.
    copy_matrix = all_rows && length(problem.A.rowval) == nnz(problem.A) &&
                  length(problem.A.nzval) == nnz(problem.A)
    reduced = LinearProblem{T}(
        copy_matrix ? problem.A : problem.A[rows, :],
        problem.objective, problem.objective_constant, problem.objective_sense,
        all_rows ? problem.row_lower : problem.row_lower[rows],
        all_rows ? problem.row_upper : problem.row_upper[rows],
        column_lower, column_upper, problem.variable_domains, problem.name,
        all_rows || isempty(problem.row_names) ? problem.row_names : problem.row_names[rows],
        problem.column_names,
    )
    step = PresolveMap{T}(rows, collect(1:n),
        Vector{Union{Nothing,T}}(nothing, n), fill(FREE_NONBASIC, n), m)
    return PresolveResult(reduced, (step,), n)
end

_bound_rational(bound::Bound) = isfinite(bound) ? _exact_rational(bound_value(bound)) : nothing

function _singleton_bound(::Type{T}, bound::Bound{T}, coefficient::Rational{BigInt}) where {T}
    !isfinite(bound) && return bound
    # Unit coefficients still need exact conversion at the working precision.
    exact = _exact_rational(bound_value(bound))
    value = _represent_exact(T, isone(coefficient) ? exact : exact / coefficient)
    return isnothing(value) ? nothing : Bound(value)
end

function _singleton_row_positions(A::SparseMatrixCSC)
    # Store (column, CSC position); column 0 means empty, -1 means multiple entries.
    positions = fill((0, 0), size(A, 1))
    for column in axes(A, 2)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            iszero(A.nzval[position]) && continue
            row = A.rowval[position]
            positions[row] = iszero(positions[row][1]) ? (column, position) : (-1, 0)
        end
    end
    return positions
end

function reduce_singleton_rows(problem::LinearProblem{T}) where {T}
    m, n = size(problem.A)
    positions = _singleton_row_positions(problem.A)
    lower, upper = problem.column_lower, problem.column_upper
    lower_sources = upper_sources = nothing
    keep = trues(m)
    for row in 1:m
        column, position = positions[row]
        column > 0 || continue
        stored = problem.A.nzval[position]
        coefficient = _exact_rational(stored)
        source_lower = coefficient > 0 ? (row, AT_LOWER) : (row, AT_UPPER)
        source_upper = coefficient > 0 ? (row, AT_UPPER) : (row, AT_LOWER)
        candidate_lower = _singleton_bound(T,
            coefficient > 0 ? problem.row_lower[row] : problem.row_upper[row],
            coefficient)
        candidate_upper = _singleton_bound(T,
            coefficient > 0 ? problem.row_upper[row] : problem.row_lower[row],
            coefficient)
        (isnothing(candidate_lower) || isnothing(candidate_upper)) && continue
        # Source maps are needed only when a row can actually be removed.
        if isnothing(lower_sources)
            lower_sources = Vector{BoundSource}(nothing, n)
            upper_sources = Vector{BoundSource}(nothing, n)
        end
        if isfinite(candidate_lower) &&
           (!isfinite(lower[column]) || bound_value(candidate_lower) > bound_value(lower[column]))
            lower === problem.column_lower && (lower = copy(lower))
            lower[column] = candidate_lower
            lower_sources[column] = source_lower
        end
        if isfinite(candidate_upper) &&
           (!isfinite(upper[column]) || bound_value(candidate_upper) < bound_value(upper[column]))
            upper === problem.column_upper && (upper = copy(upper))
            upper[column] = candidate_upper
            upper_sources[column] = source_upper
        end
        keep[row] = false
        if isfinite(lower[column]) && isfinite(upper[column]) &&
           bound_value(lower[column]) > bound_value(upper[column])
            rows = findall(keep)
            return PresolveFailure(INFEASIBLE, "singleton row $row contradicts column bounds",
                length(rows), n, count(!iszero, problem.A[rows, :].nzval))
        end
    end
    rows = findall(keep)
    result = _row_result(problem, rows; column_lower=lower, column_upper=upper)
    # _row_result returns either the identity tuple or one PresolveMap.
    result isa PresolveResult{T,Tuple{}} && return result
    step = SingletonRowStep(only(result.postsolve_stack), lower_sources, upper_sources)
    return PresolveResult(result.problem, (step,), n)
end

postsolve_primal(step::SingletonRowStep, primal::Vector) =
    postsolve_primal(step.map, primal)

function restore_basis(step::SingletonRowStep, basis::Basis)
    restored = restore_basis(step.map, basis)
    n = length(step.map.removed_values)
    for column in 1:n
        state = restored.states[column]
        source = state == AT_LOWER ? step.lower_sources[column] :
                 state == AT_UPPER ? step.upper_sources[column] : nothing
        isnothing(source) && continue
        row, row_state = source
        restored.basic_indices[row] = column
        restored.states[column] = BASIC
        restored.states[n + row] = row_state
    end
    return restored
end

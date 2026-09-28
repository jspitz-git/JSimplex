# Packed columns share this logical ordering while their stored identities stay
# stable. Logical indices remain sorted; only the moved row changes its slot.
struct UpperRowOrder
    order::Vector{Int}
    positions::Vector{Int}
end
UpperRowOrder(n::Int) = UpperRowOrder(collect(1:n), collect(1:n))

struct UpperRowIndices <: AbstractVector{Int}
    ids::Vector{Int}
    order::UpperRowOrder
end
Base.size(v::UpperRowIndices) = size(v.ids)
Base.IndexStyle(::Type{UpperRowIndices}) = IndexLinear()
Base.@propagate_inbounds function Base.getindex(v::UpperRowIndices, i::Int)
    id = v.ids[i]
    return v.order.positions[id]
end
Base.@propagate_inbounds function Base.setindex!(v::UpperRowIndices, row::Int, i::Int)
    v.ids[i] = v.order.order[row]
    return v
end
Base.copy(v::UpperRowIndices) = collect(v)
Base.similar(::UpperRowIndices, ::Type{T}, dims::Dims) where {T} = Array{T}(undef, dims)
Base.resize!(v::UpperRowIndices, n::Int) = (resize!(v.ids, n); v)
Base.empty!(v::UpperRowIndices) = (empty!(v.ids); v)
Base.sizehint!(v::UpperRowIndices, n::Int; kwargs...) = (sizehint!(v.ids, n; kwargs...); v)
function Base.push!(v::UpperRowIndices, row::Int)
    push!(v.ids, v.order.order[row])
    return v
end
function Base.insert!(v::UpperRowIndices, slot::Integer, row::Int)
    insert!(v.ids, slot, v.order.order[row])
    return v
end
Base.deleteat!(v::UpperRowIndices, slot::Integer) = (deleteat!(v.ids, slot); v)

function _rotate_upper_order!(order::UpperRowOrder, first::Int, last::Int)
    moved = order.order[first]
    for row in first:(last - 1)
        id = order.order[row + 1]
        order.order[row] = id
        order.positions[id] = row
    end
    order.order[last] = moved
    order.positions[moved] = last
    return nothing
end

# Called before changing the shared order. Only a stored occurrence of `first`
# has to move; every other stable identity keeps its slot and coefficient.
function _move_stable_upper_entry!(column, first::Int, last::Int)
    rows = column.indices
    start = searchsortedfirst(rows, first)
    (start > length(rows) || rows[start] != first) && return nothing
    finish = searchsortedlast(rows, last)
    id, value = rows.ids[start], column.values[start]
    copyto!(rows.ids, start, rows.ids, start + 1, finish - start)
    copyto!(column.values, start, column.values, start + 1, finish - start)
    rows.ids[finish] = id
    column.values[finish] = value
    return nothing
end

function _stable_rotate_upper_rows!(upper, first::Int, last::Int,
                                    columns=eachindex(upper))
    isempty(upper) && return false
    order = _upper_order(upper)
    isnothing(order) && return false
    first == last && return true
    for column in columns
        _move_stable_upper_entry!(upper[column], first, last)
    end
    _rotate_upper_order!(order, first, last)
    return true
end

Base.pushfirst!(v::UpperRowIndices, row::Int) = insert!(v, 1, row)

# Preserve the logical arithmetic order while indexing coefficients by stable
# identities. Mapping once per vector avoids a lookup for every nonzero.
function _stable_upper_backsolve!(work::Vector{T}, source::Vector{T}, upper,
                                  columns, order::UpperRowOrder) where {T}
    for row in eachindex(source)
        work[order.order[row]] = source[row]
    end
    return _stable_upper_backsolve_physical!(work, upper, columns, order)
end

function _stable_upper_backsolve_physical!(work, upper, columns, order)
    for column_index in Iterators.reverse(columns)
        column = upper[column_index]
        diagonal = order.order[column_index]
        value = work[diagonal] / _upper_diagonal(column, column_index)
        work[diagonal] = value
        ids = column.indices.ids
        @inbounds for slot in eachindex(ids)
            row = ids[slot]
            row == diagonal && continue
            work[row] -= column.values[slot] * value
        end
    end
    return work
end

function _stable_upper_transpose_solve!(work::Vector{T}, upper,
                                        columns, order::UpperRowOrder) where {T}
    for column_index in columns
        column = upper[column_index]
        diagonal = order.order[column_index]
        value = work[diagonal]
        ids = column.indices.ids
        @inbounds for slot in eachindex(ids)
            row = ids[slot]
            row == diagonal && continue
            value -= column.values[slot] * work[row]
        end
        work[diagonal] = value / _upper_diagonal(column, column_index)
    end
    return work
end

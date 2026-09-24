"""Row indexing for an immutable working CSC matrix.

The arrays are owned metadata, shared only for reading. Numeric values remain
in the referenced matrix; changing its structure or values invalidates this
index. No process-global matrix cache is used.
"""
struct RowAccess{T<:Real}
    matrix::SparseMatrixCSC{T,Int}
    rowptr::Vector{Int}
    columns::Vector{Int}
    positions::Vector{Int}
    stored_precision::Int
    ordered_csc::Bool
end

function RowAccess(A::SparseMatrixCSC{T,Int}) where {T<:Real}
    m,n = size(A)
    rowptr = ones(Int,m+1)
    # Match nzrange: buffers can be padded after CSC construction.
    for p in 1:nnz(A)
        rowptr[A.rowval[p]+1] += 1
    end
    for row in 1:m
        rowptr[row+1] += rowptr[row]-1
    end
    next = copy(rowptr)
    columns,positions = Vector{Int}(undef,nnz(A)),Vector{Int}(undef,nnz(A))
    bits,ordered = 2,true
    for column in 1:n
        previous_row = 0
        for p in nzrange(A,column)
            row,value = A.rowval[p],A.nzval[p]
            isfinite(value) || throw(ArgumentError("Row access requires finite matrix entries"))
            ordered &= row >= previous_row
            previous_row = row
            T === BigFloat && (bits = max(bits,precision(value)))
            destination = next[row]
            columns[destination],positions[destination] = column,p
            next[row] += 1
        end
    end
    return RowAccess(A,rowptr,columns,positions,bits,ordered)
end

function _finite_price_product(a,b)
    value = a*b
    isfinite(value) || throw(OverflowError("Sparse pricing product overflowed"))
    return value
end

function _sparse_price!(out,A,rho,rows,ordered_rows)
    clear!(out)
    if rows.ordered_csc
        # Match each CSC column's nonzero accumulation order, including for
        # fixed-width rationals whose intermediate overflow depends on order.
        resize!(ordered_rows,length(rho.indices))
        copyto!(ordered_rows,rho.indices)
        sort!(ordered_rows)
        for row in ordered_rows
            value = rho.values[row]
            iszero(value) && continue
            for p in rows.rowptr[row]:(rows.rowptr[row+1]-1)
                column = rows.columns[p]
                product = _finite_price_product(value,A.nzval[rows.positions[p]])
                add_entry!(out,column,product)
            end
        end
    else
        # Noncanonical custom CSC storage retains its original summation order.
        for column in axes(A,2)
            value = zero(eltype(A))
            for p in nzrange(A,column)
                value += _finite_price_product(rho.values[A.rowval[p]],A.nzval[p])
                isfinite(value) || throw(OverflowError("Sparse pricing sum overflowed"))
            end
            set_entry!(out,column,value)
        end
    end
    n = size(A,2)
    for row in rho.indices
        set_entry!(out,n+row,-rho.values[row])
    end
    compact_support!(out)
    return out
end

"""Compute rho' * [A,-I], omitting exact zeros only.

The result and optional ordered-row scratch are owned by this computation and
must not alias the RHS or row metadata. Input support order is preserved.
Overflow may leave a partial, coherent result that can be cleared and reused.
"""
function sparse_price!(out::IndexedVector{T},A::SparseMatrixCSC{T,Int},
                       rho::IndexedVector{T},rows::RowAccess{T};
                       ordered_rows::Vector{Int}=Int[]) where T
    m,n = size(A)
    length(out.values) == m+n && length(rho.values) == m ||
        throw(DimensionMismatch("Sparse pricing dimensions"))
    A === rows.matrix || throw(ArgumentError("Row access belongs to another working matrix"))
    (out === rho || Base.mightalias(out.values,rho.values) ||
     Base.mightalias(out.values,A.nzval) || ordered_rows === rho.indices ||
     ordered_rows === out.indices || ordered_rows === A.colptr ||
     ordered_rows === A.rowval || ordered_rows === rows.rowptr ||
     ordered_rows === rows.columns || ordered_rows === rows.positions) &&
        throw(ArgumentError("Sparse pricing buffers alias input or metadata"))
    if T === BigFloat
        bits = max(precision(BigFloat),rows.stored_precision,
                   maximum(i->precision(rho.values[i]),rho.indices;init=2))
        return setprecision(()->_sparse_price!(out,A,rho,rows,ordered_rows),BigFloat,bits)
    end
    return _sparse_price!(out,A,rho,rows,ordered_rows)
end


struct SparsePricingWorkspace{T<:Real}
    rows::RowAccess{T}
    rhs::IndexedVector{T}
    out::IndexedVector{T}
    ordered_rows::Vector{Int}
end

function SparsePricingWorkspace(rows::RowAccess{T}) where T
    m,n = size(rows.matrix)
    return SparsePricingWorkspace(rows,IndexedVector{T}(m),IndexedVector{T}(m+n),Int[])
end

_sparse_pricing_matches(cache,A) = !isnothing(cache) && cache.rows.matrix === A

function _sparse_pricing_workspace!(ws)
    cache = ws.scratch.sparse_pricing
    if !_sparse_pricing_matches(cache,ws.problem.A)
        rows = _timed_simplex(ws,:row_index) do
            RowAccess(ws.problem.A)
        end
        cache = SparsePricingWorkspace(rows)
        ws.scratch.sparse_pricing = cache
    end
    return cache
end

function _copy_sparse_pricing_cache!(destination,source)
    A = destination.problem.A
    old = destination.scratch.sparse_pricing
    _sparse_pricing_matches(old,A) && return nothing
    cache = source.scratch.sparse_pricing
    destination.scratch.sparse_pricing = _sparse_pricing_matches(cache,A) ?
        SparsePricingWorkspace(cache.rows) : nothing
    return nothing
end

function _invalidate_sparse_pricing_scratch!(scratch)
    scratch.sparse_pricing = nothing
    scratch.hypersparse = nothing
    isnothing(scratch.stage_scratch) ||
        _invalidate_sparse_pricing_scratch!(scratch.stage_scratch)
    return nothing
end

function _sparse_workspace_price!(tableau_row,ws,rho)
    length(tableau_row) == sum(size(ws.problem.A)) ||
        throw(DimensionMismatch("Sparse pricing output dimension"))
    Base.mightalias(tableau_row,ws.problem.A.nzval) &&
        throw(ArgumentError("Sparse pricing output aliases the working matrix"))
    cache = _sparse_pricing_workspace!(ws)
    load_indexed!(cache.rhs,rho)
    sparse_price!(cache.out,ws.problem.A,cache.rhs,cache.rows;ordered_rows=cache.ordered_rows)
    copyto!(tableau_row,cache.out.values)
    return nothing
end

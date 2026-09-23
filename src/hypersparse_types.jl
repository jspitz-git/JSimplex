"""Private DFS scratch; the returned order is borrowed until the next traversal."""
mutable struct ReachabilityWorkspace
    membership::Vector{UInt}
    generation::UInt
    stack::Vector{Int}
    cursors::Vector{Int}
    order::Vector{Int}
end

ReachabilityWorkspace(n::Int) =
    ReachabilityWorkspace(zeros(UInt,n),UInt(0),Int[],Int[],Int[])

"""Owned triangular coefficients, transpose indexing, and traversal scratch."""
struct SparseTriangularFactor{T<:Real}
    matrix::SparseMatrixCSC{T,Int}
    rows::RowAccess{T}
    diagonal::Vector{T}
    reach::ReachabilityWorkspace
end

function SparseTriangularFactor(A::SparseMatrixCSC{T,Int}) where {T<:Real}
    n,m = size(A)
    n == m || throw(DimensionMismatch("Sparse triangular factor must be square"))
    (istril(A) || istriu(A)) || throw(ArgumentError("Factor must be triangular"))
    owned = copy(A)
    rows = RowAccess(owned)
    diagonal = zeros(T,n)
    for column in 1:n
        previous = 0
        for p in nzrange(owned,column)
            row = owned.rowval[p]
            row > previous || throw(ArgumentError("Factor CSC indices must be canonical"))
            previous = row
            row == column && (diagonal[column] = owned.nzval[p])
        end
        iszero(diagonal[column]) && throw(SingularException(column))
    end
    return SparseTriangularFactor(owned,rows,diagonal,ReachabilityWorkspace(n))
end

_reach_start(g::SparseTriangularFactor,i,transposed) =
    transposed ? g.rows.rowptr[i] : g.matrix.colptr[i]
_reach_stop(g::SparseTriangularFactor,i,transposed) =
    transposed ? g.rows.rowptr[i+1] : g.matrix.colptr[i+1]
_reach_entry(g::SparseTriangularFactor,p,transposed) = transposed ?
    (g.rows.columns[p],g.matrix.nzval[g.rows.positions[p]]) :
    (g.matrix.rowval[p],g.matrix.nzval[p])

"""Return a borrowed topological order of the reachable triangular subgraph.

The factor owns the reusable DFS buffers. Consume the result before another
call on that factor. Only exact nonzero dependencies participate.
"""
function reachability_order(g::SparseTriangularFactor,seeds;transposed::Bool=false)
    w = g.reach
    if w.generation == typemax(UInt)
        fill!(w.membership,UInt(0))
        w.generation = UInt(1)
    else
        w.generation += UInt(1)
    end
    empty!(w.stack); empty!(w.cursors); empty!(w.order)
    for seed in seeds
        checkbounds(w.membership,seed)
        w.membership[seed] == w.generation && continue
        w.membership[seed] = w.generation
        push!(w.stack,seed); push!(w.cursors,_reach_start(g,seed,transposed))
        while !isempty(w.stack)
            node,p = last(w.stack),last(w.cursors)
            if p == _reach_stop(g,node,transposed)
                push!(w.order,pop!(w.stack)); pop!(w.cursors)
                continue
            end
            w.cursors[end] += 1
            child,value = _reach_entry(g,p,transposed)
            (child == node || iszero(value) || w.membership[child] == w.generation) && continue
            w.membership[child] = w.generation
            push!(w.stack,child); push!(w.cursors,_reach_start(g,child,transposed))
        end
    end
    reverse!(w.order)
    return w.order
end

# Convenience for isolated graph probes. Production retains the constructed graph.
reachability_order(A::SparseMatrixCSC,seeds;kwargs...) =
    reachability_order(SparseTriangularFactor(A),seeds;kwargs...)

function _finite_sparse_value(value)
    isfinite(value) || throw(OverflowError("Sparse factor solve overflowed"))
    return value
end

function _sparse_triangular_solve!(work::IndexedVector,g::SparseTriangularFactor,
                                   transposed::Bool)
    compact_support!(work)
    order = reachability_order(g,work.indices;transposed=transposed)
    for pivot in order
        value = work.values[pivot]
        iszero(value) && continue
        value = _finite_sparse_value(value/g.diagonal[pivot])
        set_entry!(work,pivot,value)
        for p in _reach_start(g,pivot,transposed):(_reach_stop(g,pivot,transposed)-1)
            row,coefficient = _reach_entry(g,p,transposed)
            (row == pivot || iszero(coefficient)) && continue
            add_entry!(work,row,_finite_sparse_value(-coefficient*value))
        end
    end
    return compact_support!(work)
end

"""Snapshot of one base LU with private indexed, graph, and dense-core scratch.

Rebuild after refactorization. Existing views remain valid when a backend reuses
its old factor buffers. Concurrent solves require separate views.
"""
struct SparseSolveView{T<:Real,C}
    lower::SparseTriangularFactor{T}
    upper::SparseTriangularFactor{T}
    row_order::Vector{Int}
    column_order::Vector{Int}
    row_positions::Vector{Int}
    column_positions::Vector{Int}
    scaling::Vector{T}
    divide_scaling::Bool
    core::C
    sparse_pivots::Int
    stored_precision::Int
    work::IndexedVector{T}
    core_work::Vector{T}
end

# Concrete cache storage preserves inference in all supported base backends.
const SparseBaseView{T} = Union{SparseSolveView{T,Nothing},
    SparseSolveView{T,LU{T,Matrix{T},Vector{Int}}}}

mutable struct SparseBasisWorkspace{T<:Real}
    base_view::Union{Nothing,SparseBaseView{T}}
    base_ready::Bool
    upper::Union{Nothing,SparseTriangularFactor{T}}
    work::IndexedVector{T}
    scratch::IndexedVector{T}
    dense::Vector{T}
    dense_result::Vector{T}
    stored_precision::Int
    history_scanned::Int
    upper_precision_dirty::Bool
    base_builds::Int
    upper_rebuilds::Int
    dense_fallbacks::Int
end

SparseBasisWorkspace{T}(n::Int) where {T<:Real} = SparseBasisWorkspace{T}(
    nothing,false,nothing,IndexedVector{T}(n),IndexedVector{T}(n),zeros(T,n),
    zeros(T,n),2,0,true,0,0,0)

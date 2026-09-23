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

function _sparse_solve_view(L::SparseMatrixCSC{T,Int},U::SparseMatrixCSC{T,Int},
                          p,q,scaling,core,sparse_pivots;divide_scaling=false) where T
    lower,upper = SparseTriangularFactor(L),SparseTriangularFactor(U)
    n = size(L,1)
    bits = max(lower.rows.stored_precision,upper.rows.stored_precision)
    if T === BigFloat
        bits = max(bits,maximum(precision,scaling;init=2))
        isnothing(core) || (bits = max(bits,maximum(precision,core.factors;init=2)))
    end
    return SparseSolveView(lower,upper,copy(p),copy(q),invperm(p),invperm(q),
        copy(scaling),divide_scaling,core,sparse_pivots,bits,IndexedVector{T}(n),zeros(T,n-sparse_pivots))
end

# Native dense backends retain their existing solve; callers must handle nothing.
sparse_solve_view(::Union{DenseLUBackend,Float32LUBackend}) = nothing

function _umfpack_scale_mode(F,L,U,p,q,scaling)
    all(==(1.0),scaling) && return false
    all(x->isfinite(x) && x>0,scaling) || return nothing
    # The public Rs accessor does not expose UMFPACK's reciprocal flag. Verify
    # its meaning with one public backend solve; do not read native pointers or
    # assume the documented multiplicative convention in extreme ranges.
    index = firstindex(scaling)
    for i in eachindex(scaling)
        abs(log2(scaling[i])) > abs(log2(scaling[index])) && (index = i)
    end
    coefficient = scaling[index]
    n = length(p)
    rhs = zeros(n)
    rhs[index] = min(1.0,coefficient)
    solution = F \ rhs
    all(isfinite,solution) && any(!iszero,solution) || return nothing
    transformed = L*(U*solution[q])
    scale = abs.(L)*(abs.(U)*abs.(solution[q]))
    all(isfinite,transformed) && all(isfinite,scale) || return nothing
    target = findfirst(==(index),p)
    multiply,divide = coefficient*rhs[index],rhs[index]/coefficient
    function matches(expected)
        isfinite(expected) && expected>0 || return false
        for i in eachindex(transformed)
            reference = i == target ? expected : 0.0
            allowance = 64n*eps(Float64)*max(scale[i],abs(reference))
            abs(transformed[i]-reference) <= allowance || return false
        end
        return true
    end
    multiplicative,divisive = matches(multiply),matches(divide)
    multiplicative == divisive && return nothing
    return divisive
end

function sparse_solve_view(backend::UMFPACKBackend)
    F = backend.factorization
    if isnothing(F)
        return _sparse_solve_view(spzeros(0,0),spzeros(0,0),Int[],Int[],Float64[],nothing,0)
    end
    issuccess(F) || throw(SingularException(0))
    L,U,p,q,scaling = F.L,F.U,F.p,F.q,F.Rs
    divide = _umfpack_scale_mode(F,L,U,p,q,scaling)
    isnothing(divide) && return nothing
    return _sparse_solve_view(L,U,p,q,scaling,nothing,backend.dimension;divide_scaling=divide)
end

function sparse_solve_view(backend::MarkowitzBackend{T}) where T
    n,k = backend.dimension,backend.sparse_pivots
    li,lj,lv = collect(1:n),collect(1:n),ones(T,n)
    ui,uj,uv = collect(1:n),collect(1:n),ones(T,n)
    for pivot in 1:k
        uv[pivot] = backend.diagonal[pivot]
        column,row = backend.lower[pivot],backend.upper[pivot]
        for p in eachindex(column.indices)
            push!(li,column.indices[p]); push!(lj,pivot); push!(lv,column.values[p])
        end
        for p in eachindex(row.indices)
            push!(ui,pivot); push!(uj,row.indices[p]); push!(uv,row.values[p])
        end
    end
    # The dense core is solved between the lower and upper operations, in
    # reverse order for transpose. Its graph block here is identity.
    return _sparse_solve_view(sparse(li,lj,lv,n,n),sparse(ui,uj,uv,n,n),
        backend.row_order,backend.column_order,ones(T,n),deepcopy(backend.core),k)
end

_sparse_core_solve!(view::SparseSolveView{T,Nothing},transposed) where {T<:Real} = nothing
function _sparse_core_solve!(view::SparseSolveView,transposed)
    k,work = view.sparse_pivots,view.work
    any(i->i>k && !iszero(work.values[i]),work.indices) || return nothing
    fill!(view.core_work,zero(eltype(view.core_work)))
    for i in work.indices
        i > k && (view.core_work[i-k] = work.values[i])
    end
    if transposed
        ldiv!(transpose(view.core),view.core_work)
    else
        ldiv!(view.core,view.core_work)
    end
    # A single reached core entry can populate its entire solution.
    for i in eachindex(view.core_work)
        set_entry!(work,k+i,_finite_sparse_value(view.core_work[i]))
    end
    return nothing
end

function _hypersparse_solve!(dest,view,rhs,transposed)
    work = view.work
    clear!(work)
    positions = transposed ? view.column_positions : view.row_positions
    for i in rhs.indices
        value = rhs.values[i]
        transposed || (value = _finite_sparse_value(view.divide_scaling ?
            value/view.scaling[i] : value*view.scaling[i]))
        set_entry!(work,positions[i],value)
    end
    if transposed
        _sparse_triangular_solve!(work,view.upper,true)
        _sparse_core_solve!(view,true)
        _sparse_triangular_solve!(work,view.lower,true)
    else
        _sparse_triangular_solve!(work,view.lower,false)
        _sparse_core_solve!(view,false)
        _sparse_triangular_solve!(work,view.upper,false)
    end
    # All RHS reads are complete, so the public destination may equal the RHS.
    clear!(dest)
    order = transposed ? view.row_order : view.column_order
    for i in work.indices
        target = order[i]
        value = work.values[i]
        transposed && (value = _finite_sparse_value(view.divide_scaling ?
            value/view.scaling[target] : value*view.scaling[target]))
        set_entry!(dest,target,value)
    end
    return compact_support!(dest)
end

function _checked_hypersparse_solve!(dest::IndexedVector{T},view::SparseSolveView{T},
                                    rhs::IndexedVector{T},transposed::Bool) where T
    n = length(view.row_order)
    length(dest.values) == n && length(rhs.values) == n ||
        throw(DimensionMismatch("Hypersparse solve dimensions"))
    (dest === view.work || rhs === view.work ||
     dest.indices === view.work.indices || rhs.indices === view.work.indices ||
     dest.membership === view.work.membership || rhs.membership === view.work.membership ||
     Base.mightalias(dest.values,view.work.values) ||
     Base.mightalias(rhs.values,view.work.values)) &&
        throw(ArgumentError("Hypersparse input/output aliases private scratch"))
    if T === BigFloat
        bits = max(precision(BigFloat),view.stored_precision,
            maximum(i->precision(rhs.values[i]),rhs.indices;init=2))
        return setprecision(()->_hypersparse_solve!(dest,view,rhs,transposed),BigFloat,bits)
    end
    return _hypersparse_solve!(dest,view,rhs,transposed)
end

hypersparse_forward_solve!(dest::IndexedVector,view::SparseSolveView,rhs::IndexedVector) =
    _checked_hypersparse_solve!(dest,view,rhs,false)
hypersparse_transpose_solve!(dest::IndexedVector,view::SparseSolveView,rhs::IndexedVector) =
    _checked_hypersparse_solve!(dest,view,rhs,true)

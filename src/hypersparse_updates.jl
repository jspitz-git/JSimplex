# Indexed overloads are separate from the ordinary dense simplex solve path.
_copy_sparse_graph(g::SparseTriangularFactor) = SparseTriangularFactor(
    g.matrix,g.rows,g.diagonal,ReachabilityWorkspace(length(g.diagonal)))
_copy_sparse_graph(::Nothing) = nothing
_copy_sparse_view(::Nothing) = nothing
function _copy_sparse_view(v::SparseSolveView{T}) where T
    return SparseSolveView(_copy_sparse_graph(v.lower),_copy_sparse_graph(v.upper),
        v.row_order,v.column_order,v.row_positions,v.column_positions,v.scaling,
        v.divide_scaling,v.core,v.sparse_pivots,v.stored_precision,
        IndexedVector{T}(length(v.row_order)),zeros(T,length(v.core_work)))
end

_copy_sparse_basis_cache(::Nothing) = nothing
function _copy_sparse_basis_cache(source::SparseBasisWorkspace{T}) where T
    destination = SparseBasisWorkspace{T}(length(source.work.values))
    destination.base_view = _copy_sparse_view(source.base_view)
    destination.base_ready = source.base_ready
    destination.upper = _copy_sparse_graph(source.upper)
    destination.stored_precision = source.stored_precision
    destination.history_scanned = source.history_scanned
    destination.upper_precision_dirty = source.upper_precision_dirty
    return destination
end

function _invalidate_sparse_upper!(factor)
    cache = factor.sparse
    if !isnothing(cache)
        cache.upper = nothing
        cache.upper_precision_dirty = true
    end
    return nothing
end

_backend_stored_precision(backend) = 2
_backend_stored_precision(backend::DenseLUBackend{BigFloat}) =
    maximum(precision,backend.factorization.factors;init=2)
function _backend_stored_precision(backend::MarkowitzBackend{BigFloat})
    return max(maximum(precision,backend.diagonal;init=2),
        maximum(precision,backend.core.factors;init=2),
        maximum(v->maximum(precision,v.values;init=2),backend.lower;init=2),
        maximum(v->maximum(precision,v.values;init=2),backend.upper;init=2))
end

function _sparse_basis_workspace!(factor::Union{PFIFactorization{T},
                                  AbstractTriangularBasisFactorization{T}}) where T
    cache = factor.sparse
    if isnothing(cache)
        cache = SparseBasisWorkspace{T}(_backend_dimension(factor.base))
        T === BigFloat && (cache.stored_precision = _backend_stored_precision(factor.base))
        factor.sparse = cache
    end
    return cache
end

function _sparse_base_view!(cache,factor)
    if !cache.base_ready
        cache.base_view = sparse_solve_view(factor.base)
        cache.base_ready = true
        cache.base_builds += 1
    end
    return cache.base_view
end

function _sparse_upper!(cache,factor)
    graph = cache.upper
    if isnothing(graph)
        n = length(factor.upper)
        ii,jj,vv = Int[],Int[],eltype(cache.dense)[]
        for column in 1:n
            packed = factor.upper[column]
            for p in eachindex(packed.indices)
                push!(ii,packed.indices[p]); push!(jj,column); push!(vv,packed.values[p])
            end
        end
        graph = SparseTriangularFactor(sparse(ii,jj,vv,n,n))
        cache.upper = graph
        cache.upper_rebuilds += 1
    end
    return graph
end

function _copy_indexed!(destination::IndexedVector,source::IndexedVector)
    destination === source && return destination
    clear!(destination)
    for i in source.indices
        set_entry!(destination,i,source.values[i])
    end
    return compact_support!(destination)
end

function _rotate_indexed!(vector,scratch,first,last,left::Bool)
    clear!(scratch)
    for i in vector.indices
        target = if left
            i == first ? last : first < i <= last ? i-1 : i
        else
            i == last ? first : first <= i < last ? i+1 : i
        end
        set_entry!(scratch,target,vector.values[i])
    end
    return _copy_indexed!(vector,scratch)
end

_update_last(update::ForrestTomlinUpdate,n) = n
_update_last(update::SuhlSuhlUpdate,n) = update.last
function _apply_row_update!(vector::IndexedVector,
                            update::Union{ForrestTomlinUpdate,SuhlSuhlUpdate},scratch)
    last = _update_last(update,length(vector.values))
    _rotate_indexed!(vector,scratch,update.pivot,last,true)
    for p in eachindex(update.indices)
        add_entry!(vector,last,_finite_sparse_value(update.multipliers[p]*vector.values[update.indices[p]]))
    end
    return compact_support!(vector)
end

function _apply_transposed_row_update!(vector::IndexedVector,
                            update::Union{ForrestTomlinUpdate,SuhlSuhlUpdate},scratch)
    last = _update_last(update,length(vector.values))
    bottom = vector.values[last]
    for p in eachindex(update.indices)
        add_entry!(vector,update.indices[p],_finite_sparse_value(update.multipliers[p]*bottom))
    end
    return _rotate_indexed!(vector,scratch,update.pivot,last,false)
end

function _apply_row_update!(vector::IndexedVector,update::BartelsGolubUpdate,scratch)
    for step in update.steps
        row = step.row
        if step.last > row
            _rotate_indexed!(vector,scratch,row,step.last+1,true)
        elseif step.swapped
            first,second = vector.values[row],vector.values[row+1]
            set_entry!(vector,row,second); set_entry!(vector,row+1,first)
        end
        iszero(step.multiplier) || add_entry!(vector,row+1,
            _finite_sparse_value(-step.multiplier*vector.values[row]))
    end
    return compact_support!(vector)
end

function _apply_transposed_row_update!(vector::IndexedVector,update::BartelsGolubUpdate,scratch)
    for step in Iterators.reverse(update.steps)
        row = step.row
        iszero(step.multiplier) || add_entry!(vector,row,
            _finite_sparse_value(-step.multiplier*vector.values[row+1]))
        if step.last > row
            _rotate_indexed!(vector,scratch,row,step.last+1,false)
        elseif step.swapped
            first,second = vector.values[row],vector.values[row+1]
            set_entry!(vector,row,second); set_entry!(vector,row+1,first)
        end
    end
    return compact_support!(vector)
end

function _apply_eta!(vector::IndexedVector,eta::PackedEta,transposed::Bool)
    if transposed
        value = zero(eltype(vector.values))
        for p in eachindex(eta.indices)
            value = _finite_sparse_value(value+eta.values[p]*vector.values[eta.indices[p]])
        end
        set_entry!(vector,eta.pivot_row,value)
    else
        pivot = vector.values[eta.pivot_row]
        set_entry!(vector,eta.pivot_row,zero(pivot))
        for p in eachindex(eta.indices)
            add_entry!(vector,eta.indices[p],_finite_sparse_value(pivot*eta.values[p]))
        end
    end
    return compact_support!(vector)
end

function _apply_eta!(vector::Vector,eta::PackedEta,transposed::Bool)
    if transposed
        value = zero(eltype(vector))
        for p in eachindex(eta.indices)
            value += eta.values[p]*vector[eta.indices[p]]
        end
        vector[eta.pivot_row] = value
    else
        pivot = vector[eta.pivot_row]
        vector[eta.pivot_row] = zero(pivot)
        for p in eachindex(eta.indices)
            vector[eta.indices[p]] += pivot*eta.values[p]
        end
    end
    return vector
end

_use_dense_updates(vector,mode) = mode == :auto && 2length(vector.indices)>length(vector.values)

function _load_indexed_solution!(destination,values)
    clear!(destination)
    for i in eachindex(values)
        set_entry!(destination,i,_finite_sparse_value(values[i]))
    end
    return destination
end

function _indexed_base_solve!(destination,cache,factor,rhs,transposed,mode)
    view = _use_dense_updates(rhs,mode) ? nothing : _sparse_base_view!(cache,factor)
    if isnothing(view)
        if transposed
            _backend_transpose_solve!(cache.dense_result,factor.base,rhs.values)
        else
            _backend_forward_solve!(cache.dense_result,factor.base,rhs.values)
        end
        cache.dense_fallbacks += 1
        return _load_indexed_solution!(destination,cache.dense_result)
    end
    return transposed ? hypersparse_transpose_solve!(destination,view,rhs) :
                        hypersparse_forward_solve!(destination,view,rhs)
end

function _indexed_factor_solve!(dest,factor::PFIFactorization,cache,rhs,transposed,mode)
    work = cache.work
    if transposed
        _copy_indexed!(work,rhs)
    else
        _indexed_base_solve!(work,cache,factor,rhs,false,mode)
    end
    updates = transposed ? Iterators.reverse(factor.updates) : factor.updates
    dense = false
    for eta in updates
        if !dense && _use_dense_updates(work,mode)
            copyto!(cache.dense,work.values)
            cache.dense_fallbacks += 1
            dense = true
        end
        _apply_eta!(dense ? cache.dense : work,eta,transposed)
    end
    dense && _load_indexed_solution!(work,cache.dense)
    return transposed ? _indexed_base_solve!(dest,cache,factor,work,true,mode) :
                        _copy_indexed!(dest,work)
end

function _indexed_factor_solve!(dest,factor::AbstractTriangularBasisFactorization,
                                cache,rhs,transposed,mode)
    work = cache.work
    dense = false
    if transposed
        clear!(work)
        for i in rhs.indices
            set_entry!(work,factor.positions[i],rhs.values[i])
        end
        _sparse_triangular_solve!(work,_sparse_upper!(cache,factor),true)
        for update in Iterators.reverse(factor.updates)
            if !dense && _use_dense_updates(work,mode)
                copyto!(cache.dense,work.values); dense = true
                cache.dense_fallbacks += 1
            end
            if dense
                _apply_transposed_row_update!(cache.dense,update)
            else
                _apply_transposed_row_update!(work,update,cache.scratch)
            end
        end
        dense && _load_indexed_solution!(work,cache.dense)
        return _indexed_base_solve!(dest,cache,factor,work,true,mode)
    end
    _indexed_base_solve!(work,cache,factor,rhs,false,mode)
    for update in factor.updates
        if !dense && _use_dense_updates(work,mode)
            copyto!(cache.dense,work.values); dense = true
            cache.dense_fallbacks += 1
        end
        if dense
            _apply_row_update!(cache.dense,update)
        else
            _apply_row_update!(work,update,cache.scratch)
        end
    end
    if !dense && _use_dense_updates(work,mode)
        copyto!(cache.dense,work.values); dense = true
        cache.dense_fallbacks += 1
    end
    if dense
        _upper_backsolve!(cache.dense,factor.upper)
        _load_indexed_solution!(work,cache.dense)
    else
        _sparse_triangular_solve!(work,_sparse_upper!(cache,factor),false)
    end
    clear!(dest)
    for i in work.indices
        set_entry!(dest,factor.column_order[i],work.values[i])
    end
    return compact_support!(dest)
end

_history_precision(update::PackedEta) = maximum(precision,update.values;init=2)
_history_precision(update::Union{ForrestTomlinUpdate,SuhlSuhlUpdate}) =
    maximum(precision,update.multipliers;init=2)
_history_precision(update::BartelsGolubUpdate) =
    maximum(step->precision(step.multiplier),update.steps;init=2)
_sparse_upper_precision(factor::PFIFactorization) = 2
_sparse_upper_precision(factor::AbstractTriangularBasisFactorization) =
    maximum(column->maximum(precision,column.values;init=2),factor.upper;init=2)
function _sparse_working_precision!(cache,factor,rhs)
    for i in (cache.history_scanned+1):length(factor.updates)
        cache.stored_precision = max(cache.stored_precision,_history_precision(factor.updates[i]))
    end
    cache.history_scanned = length(factor.updates)
    if cache.upper_precision_dirty
        cache.stored_precision = max(cache.stored_precision,_sparse_upper_precision(factor))
        cache.upper_precision_dirty = false
    end
    return max(precision(BigFloat),cache.stored_precision,
        maximum(i->precision(rhs.values[i]),rhs.indices;init=2))
end

function _check_indexed_basis_buffers(dest,cache,rhs,factor)
    (dest !== rhs && (Base.mightalias(dest.values,rhs.values) ||
        dest.indices === rhs.indices || dest.membership === rhs.membership)) &&
        throw(ArgumentError("Indexed basis inputs have partially shared storage"))
    for vector in (cache.work,cache.scratch)
        (dest === vector || rhs === vector || dest.indices === vector.indices ||
         rhs.indices === vector.indices || dest.membership === vector.membership ||
         rhs.membership === vector.membership || Base.mightalias(dest.values,vector.values) ||
         Base.mightalias(rhs.values,vector.values)) &&
            throw(ArgumentError("Indexed basis solve aliases private indexed scratch"))
    end
    for vector in (cache.dense,cache.dense_result,factor.work)
        (Base.mightalias(dest.values,vector) || Base.mightalias(rhs.values,vector)) &&
            throw(ArgumentError("Indexed basis solve aliases private dense scratch"))
    end
    return nothing
end

function _run_indexed_basis_solve!(dest,factor,cache,rhs,transposed,mode)
    if mode == :dense || _use_dense_updates(rhs,mode)
        if transposed
            transpose_solve!(cache.dense,factor,rhs.values)
        else
            forward_solve!(cache.dense,factor,rhs.values)
        end
        cache.dense_fallbacks += 1
        return _load_indexed_solution!(dest,cache.dense)
    end
    return _indexed_factor_solve!(dest,factor,cache,rhs,transposed,mode)
end

function _indexed_basis_solve!(dest::IndexedVector{T},factor,
                               rhs::IndexedVector{T},transposed,mode) where T
    mode in (:auto,:sparse,:dense) || throw(ArgumentError("Unknown indexed basis kernel mode"))
    n = _backend_dimension(factor.base)
    length(dest.values) == n && length(rhs.values) == n || throw(DimensionMismatch("Indexed basis solve dimensions"))
    cache = _sparse_basis_workspace!(factor)
    _check_indexed_basis_buffers(dest,cache,rhs,factor)
    if T === BigFloat
        bits = _sparse_working_precision!(cache,factor,rhs)
        return setprecision(()->_run_indexed_basis_solve!(dest,factor,cache,rhs,transposed,mode),BigFloat,bits)
    end
    return _run_indexed_basis_solve!(dest,factor,cache,rhs,transposed,mode)
end

"""Solve through indexed base factors and update history.

`:sparse` forces support propagation (the base backend may still require its
dense fallback); `:dense` uses the existing complete dense solve. Experimental
`:auto` materializes a dense branch above half occupancy. F19 owns measured-cost
selection and hysteresis. No small nonzero entry is removed by tolerance.
"""
forward_solve!(dest::IndexedVector{T},factor::Union{PFIFactorization{T},
    AbstractTriangularBasisFactorization{T}},rhs::IndexedVector{T};kernel_mode::Symbol=:auto) where T =
    _indexed_basis_solve!(dest,factor,rhs,false,kernel_mode)
transpose_solve!(dest::IndexedVector{T},factor::Union{PFIFactorization{T},
    AbstractTriangularBasisFactorization{T}},rhs::IndexedVector{T};kernel_mode::Symbol=:auto) where T =
    _indexed_basis_solve!(dest,factor,rhs,true,kernel_mode)

# These scopes are nested inside the ordinary timed solve. Explicit start/finish
# avoids recursively forwarding different closure types through that wrapper.
_pipeline_timer_start(::Nothing) = nothing
_pipeline_timer_start(d::SimplexDiagnostics) = d.kernel_timing ? time_ns() : nothing
_pipeline_timer_finish!(::Nothing,reason,started) = nothing
function _pipeline_timer_finish!(d::SimplexDiagnostics,reason,started)
    isnothing(started) && return nothing
    d.kernel_nanoseconds[reason] += time_ns()-started
    d.kernel_calls[reason] += 1
    return nothing
end

function _hypersparse_workspace!(ws::SimplexWorkspace{T})::HypersparseWorkspace{T} where T
    previous = ws.scratch.hypersparse
    matching = !isnothing(previous) && previous.matrix === ws.problem.A
    if matching
        same_buffers = true
        for i in 1:6
            same_buffers &= previous.buffers[i].values ===
                getfield(ws.scratch,HYPERSPARSE_BUFFER_FIELDS[i])
        end
        same_buffers && return previous
    end
    started = _pipeline_timer_start(ws.progress.diagnostics)
    cache = try
        HypersparseWorkspace(ws.problem.A,ws.scratch;
            modes=matching ? previous.modes : nothing,rows=matching ? previous.rows : nothing)
    finally
        _pipeline_timer_finish!(ws.progress.diagnostics,:hypersparse_setup,started)
    end
    ws.scratch.hypersparse = cache
    return cache
end

function _pipeline_buffer_index(cache,values)
    for i in 1:6
        cache.buffers[i].values === values && return i
    end
    return 0
end

# Unlike clear!, this preserves values written by a dense numerical consumer.
function _reset_pipeline_support!(vector)
    empty!(vector.indices)
    if vector.generation == typemax(UInt)
        fill!(vector.membership,UInt(0))
        vector.generation = UInt(1)
    else
        vector.generation += UInt(1)
    end
    return vector
end

function _rebuild_pipeline_support!(cache,index)
    vector = cache.buffers[index]
    cache.valid[index] = false
    _reset_pipeline_support!(vector)
    cache.support_rebuilds += 1
    for i in eachindex(vector.values)
        value = vector.values[i]
        isfinite(value) || throw(_UnreliableBasisSolve())
        if !iszero(value)
            push!(vector.indices,i)
            vector.membership[i] = vector.generation
        end
    end
    cache.valid[index] = true
    return vector
end

function _pipeline_vector!(ws::SimplexWorkspace{T},values)::IndexedVector{T} where T
    cache = _hypersparse_workspace!(ws)
    i = _pipeline_buffer_index(cache,values)
    i > 0 || throw(ArgumentError("Pipeline vector does not belong to this scratch workspace"))
    if !cache.valid[i]
        started = _pipeline_timer_start(ws.progress.diagnostics)
        try
            return _rebuild_pipeline_support!(cache,i)
        finally
            _pipeline_timer_finish!(ws.progress.diagnostics,:hypersparse_support,started)
        end
    end
    return compact_support!(cache.buffers[i])
end

function _pipeline_changed!(ws,values)::Nothing
    cache = ws.scratch.hypersparse
    isnothing(cache) && return nothing
    i = _pipeline_buffer_index(cache,values)
    i > 0 && (cache.valid[i] = false)
    return nothing
end

function _pipeline_rhs_buffer!(ws)
    rhs = ws.scratch.row_rhs
    if !ws.progress.numerical_policy.hypersparse
        _pipeline_changed!(ws,rhs)
        fill!(rhs,zero(eltype(rhs)))
        return rhs
    end
    cache = _hypersparse_workspace!(ws)
    vector = cache.buffers[1]
    if cache.valid[1]
        clear!(vector)
    else
        fill!(rhs,zero(eltype(rhs)))
        _reset_pipeline_support!(vector)
        cache.dense_resets += 1
    end
    cache.valid[1] = true
    return vector
end

_pipeline_rhs_values(vector::Vector) = vector
_pipeline_rhs_values(vector::IndexedVector) = (compact_support!(vector);vector.values)
_set_pipeline_rhs!(vector::Vector,i,value) = (vector[i] = value)
_set_pipeline_rhs!(vector::IndexedVector,i,value) = set_entry!(vector,i,value)
_add_pipeline_rhs!(vector::Vector,i,value) = (vector[i] += value)
_subtract_pipeline_rhs!(vector::Vector,i,value) = (vector[i] -= value)
_pipeline_difference(a,b) = a-b
_pipeline_difference(a::BigFloat,b::BigFloat) =
    setprecision(()->a-b,BigFloat,max(precision(BigFloat),precision(a),precision(b)))
function _subtract_pipeline_rhs!(vector::IndexedVector,i,value)
    isfinite(value) || throw(_UnreliableBasisSolve())
    try
        result = _pipeline_difference(vector.values[i],value)
        isfinite(result) || throw(_UnreliableBasisSolve())
        return set_entry!(vector,i,result)
    catch exception
        exception isa OverflowError && throw(_UnreliableBasisSolve())
        rethrow()
    end
end
function _add_pipeline_rhs!(vector::IndexedVector,i,value)
    isfinite(value) || throw(_UnreliableBasisSolve())
    try
        return add_entry!(vector,i,value)
    catch exception
        exception isa OverflowError && throw(_UnreliableBasisSolve())
        rethrow()
    end
end

function _pipeline_unit_rhs!(ws,row)
    buffer = _pipeline_rhs_buffer!(ws)
    _set_pipeline_rhs!(buffer,row,one(eltype(ws.costs)))
    return _pipeline_rhs_values(buffer)
end

function _fill_pipeline_column!(buffer,A,entering)
    if entering <= size(A,2)
        for p in nzrange(A,entering)
            _set_pipeline_rhs!(buffer,A.rowval[p],A.nzval[p])
        end
    else
        _set_pipeline_rhs!(buffer,entering-size(A,2),-one(eltype(A)))
    end
    return _pipeline_rhs_values(buffer)
end

_pipeline_column_rhs!(ws,entering) =
    _fill_pipeline_column!(_pipeline_rhs_buffer!(ws),ws.problem.A,entering)

_pipeline_weight_value(value,pivot,leaving) =
    (value-(leaving ? one(pivot) : zero(pivot)))/pivot
function _pipeline_weight_value(value::BigFloat,pivot::BigFloat,leaving)
    return setprecision(BigFloat,max(precision(BigFloat),precision(value),precision(pivot))) do
        (value-(leaving ? one(pivot) : zero(pivot)))/pivot
    end
end

function _pipeline_weight_rhs!(ws,leaving,pivot)
    direction = ws.scratch.row_solution
    buffer = if ws.progress.numerical_policy.hypersparse
        _pipeline_rhs_buffer!(ws)
    else
        _pipeline_changed!(ws,ws.scratch.row_rhs)
        ws.scratch.row_rhs
    end
    rows = buffer isa IndexedVector ? _pipeline_vector!(ws,direction).indices : eachindex(direction)
    for row in rows
        value = buffer isa IndexedVector ?
            _pipeline_weight_value(direction[row],pivot,row == leaving) :
            (direction[row]-(row == leaving ? one(pivot) : zero(pivot)))/pivot
        if !isfinite(value)
            # Preserve the existing weight-reset path for a nonfinite estimate.
            ws.scratch.row_rhs[row] = value
            _pipeline_changed!(ws,ws.scratch.row_rhs)
            return ws.scratch.row_rhs
        end
        _set_pipeline_rhs!(buffer,row,value)
    end
    if buffer isa IndexedVector && iszero(direction[leaving])
        value = _pipeline_weight_value(zero(pivot),pivot,true)
        if !isfinite(value)
            ws.scratch.row_rhs[leaving] = value
            _pipeline_changed!(ws,ws.scratch.row_rhs)
            return ws.scratch.row_rhs
        end
        _set_pipeline_rhs!(buffer,leaving,value)
    end
    return _pipeline_rhs_values(buffer)
end

function _pipeline_add!(ws,values,i,value)
    if ws.progress.numerical_policy.hypersparse
        cache = _hypersparse_workspace!(ws)
        index = _pipeline_buffer_index(cache,values)
        if index > 0
            cache.valid[index] || _rebuild_pipeline_support!(cache,index)
            _add_pipeline_rhs!(cache.buffers[index],i,value)
            return values
        end
    end
    _pipeline_changed!(ws,values)
    values[i] += value
    return values
end

# Values have already been copied by the existing transactional scratch copy.
function _copy_hypersparse_cache!(destination,source)::Nothing
    if !destination.progress.numerical_policy.hypersparse
        cache = destination.scratch.hypersparse
        isnothing(cache) || fill!(cache.valid,false)
        return nothing
    end
    old = source.scratch.hypersparse
    cache = destination.scratch.hypersparse
    if isnothing(old) || old.matrix !== destination.problem.A
        isnothing(cache) || fill!(cache.valid,false)
        return nothing
    end
    cache = _hypersparse_workspace!(destination)
    cache === old && return nothing
    cache.modes = old.modes
    isnothing(old.rows) || (cache.rows = old.rows)
    for i in 1:6
        cache.valid[i] = old.valid[i]
        old.valid[i] || continue
        vector,original = cache.buffers[i],old.buffers[i]
        _reset_pipeline_support!(vector)
        copyto!(resize!(vector.indices,length(original.indices)),original.indices)
        for index in vector.indices
            vector.membership[index] = vector.generation
        end
    end
    return nothing
end

function _pipeline_state(cache,operation)
    for i in 1:6
        HYPERSPARSE_OPERATIONS[i] == operation && return cache.modes[i]
    end
    throw(ArgumentError("Unknown pipeline operation"))
end

function _pipeline_mode!(state,support,dimension,forced)
    forced in (:auto,:sparse,:dense) || throw(ArgumentError("Unknown pipeline kernel mode"))
    state.calls = min(typemax(Int)-1,state.calls)+1
    if iszero(support)
        choose_kernel_mode!(state;support_size=0,dimension)
        return :empty
    end
    density = support/dimension
    previous = isfinite(state.output_density) ? clamp(state.output_density,0.0,1.0) : 1.0
    effective_support = max(support,min(dimension,ceil(Int,previous*dimension)))
    mode = forced == :auto ? choose_kernel_mode!(state;support_size=effective_support,dimension) : forced
    state.input_density = density
    # A probe substitutes one alternative call; it never solves the same RHS twice.
    # Persistent selection still requires two indications.
    if forced == :auto && iszero(state.calls % state.probe_interval) &&
       density <= state.sparse_threshold
        state.probes += 1
        return mode == :sparse ? :dense : :sparse
    end
    return mode
end

function _pipeline_note_call!(state,mode)
    state.last_mode = mode
    mode == :sparse && (state.sparse_calls += 1)
    mode == :dense && (state.dense_calls += 1)
    mode == :empty && (state.empty_calls += 1)
    return nothing
end

function _pipeline_empty_output!(cache,index,values)
    if index > 0
        vector = cache.buffers[index]
        if cache.valid[index]
            clear!(vector)
        else
            fill!(values,zero(eltype(values)))
            _reset_pipeline_support!(vector)
            cache.dense_resets += 1
        end
        cache.valid[index] = true
    else
        fill!(values,zero(eltype(values)))
    end
    return values
end

function _pipeline_indexed_output!(cache,index)
    vector = cache.buffers[index]
    cache.valid[index] || _pipeline_empty_output!(cache,index,vector.values)
    return vector
end

function _pipeline_sparse_available!(ws)
    factor = ws.factorization
    factor.base isa DenseLUBackend && return false
    cache = _sparse_basis_workspace!(factor)
    if !cache.base_ready
        started = _pipeline_timer_start(ws.progress.diagnostics)
        try
            _sparse_base_view!(cache,factor)
        finally
            _pipeline_timer_finish!(ws.progress.diagnostics,:hypersparse_base_graph,started)
        end
    end
    isnothing(cache.base_view) && return false
    if factor isa AbstractTriangularBasisFactorization && isnothing(cache.upper)
        started = _pipeline_timer_start(ws.progress.diagnostics)
        try
            _sparse_upper!(cache,factor)
        finally
            _pipeline_timer_finish!(ws.progress.diagnostics,:hypersparse_upper_graph,started)
        end
    end
    return true
end

function _pipeline_dense_basis!(destination,factor,rhs,transposed)
    if Base.mightalias(destination,rhs)
        cache = _sparse_basis_workspace!(factor)
        transposed ? transpose_solve!(cache.dense_result,factor,rhs) :
                     forward_solve!(cache.dense_result,factor,rhs)
        return copyto!(destination,cache.dense_result)
    end
    return transposed ? transpose_solve!(destination,factor,rhs) :
                        forward_solve!(destination,factor,rhs)
end

@inline function _pipeline_basis_precision(f::F,ws::SimplexWorkspace{T},rhs) where {F,T}
    T === BigFloat || return f()
    cache = _sparse_basis_workspace!(ws.factorization)
    bits = _sparse_working_precision!(cache,ws.factorization,rhs)
    return setprecision(f,BigFloat,bits)
end

@inline function _pipeline_price_precision(f::F,cache::HypersparseWorkspace{T},rhs) where {F,T}
    T === BigFloat || return f()
    bits = max(precision(BigFloat),cache.stored_precision,
        maximum(i->precision(rhs.values[i]),rhs.indices;init=2))
    return setprecision(f,BigFloat,bits)
end

function _pipeline_output_support!(ws,cache,index,values)
    if index > 0
        return length(_pipeline_vector!(ws,values).indices)
    end
    all(isfinite,values) || throw(OverflowError("Pipeline solve overflowed"))
    return count(!iszero,values)
end

_pipeline_diagnostic!(::Nothing,operation,mode,elapsed) = nothing
function _pipeline_diagnostic!(diagnostics::SimplexDiagnostics,operation,mode,elapsed)
    diagnostics.kernel_timing || return nothing
    for i in 1:6
        HYPERSPARSE_OPERATIONS[i] == operation || continue
        key = HYPERSPARSE_KERNEL_KEYS[i][mode == :sparse ? 1 : mode == :dense ? 2 : 3]
        diagnostics.kernel_calls[key] += 1
        diagnostics.kernel_nanoseconds[key] += elapsed
        break
    end
    return nothing
end

function _pipeline_basis_kernel!(destination,ws,rhs,cache,input_index,output_index,selected_mode,transposed)
    if selected_mode == :sparse
        out = _pipeline_indexed_output!(cache,output_index)
        cache.valid[output_index] = false
        # F18's intra-operation dense fallback also handles sudden fill.
        indexed_rhs = cache.buffers[input_index]
        transposed ? transpose_solve!(out,ws.factorization,indexed_rhs;kernel_mode=:auto) :
                     forward_solve!(out,ws.factorization,indexed_rhs;kernel_mode=:auto)
        cache.valid[output_index] = true
    else
        output_index > 0 && (cache.valid[output_index] = false)
        _pipeline_dense_basis!(destination,ws.factorization,rhs,transposed)
    end
    return destination
end

function _pipeline_price_kernel!(destination,ws,rho,cache,input_index,output_index,selected_mode)
    if selected_mode == :sparse
        if isnothing(cache.rows)
            started = _pipeline_timer_start(ws.progress.diagnostics)
            cache.rows = try
                RowAccess(ws.problem.A)
            finally
                _pipeline_timer_finish!(ws.progress.diagnostics,:row_index,started)
            end
        end
        out = _pipeline_indexed_output!(cache,output_index)
        cache.valid[output_index] = false
        sparse_price!(out,ws.problem.A,cache.buffers[input_index],cache.rows;
                      ordered_rows=cache.ordered_rows)
        cache.valid[output_index] = true
    else
        output_index > 0 && (cache.valid[output_index] = false)
        _csc_price!(destination,ws.problem.A,rho)
    end
    return nothing
end

function _pipeline_basis_solve!(destination,ws,rhs;transposed::Bool=false,
    operation::Symbol=transposed ? :btran : :ftran,kernel_mode::Symbol=:auto,clock=time_ns)
    kernel_mode in (:auto,:sparse,:dense) || throw(ArgumentError("Unknown pipeline kernel mode"))
    if !ws.progress.numerical_policy.hypersparse
        _pipeline_changed!(ws,destination)
        return transposed ? transpose_solve!(destination,ws.factorization,rhs) :
                            forward_solve!(destination,ws.factorization,rhs)
    end
    n = _backend_dimension(ws.factorization.base)
    length(destination) == length(rhs) == n || throw(DimensionMismatch("Pipeline basis solve dimensions"))
    started = clock()
    cache = _hypersparse_workspace!(ws)
    input_index,output_index = _pipeline_buffer_index(cache,rhs),_pipeline_buffer_index(cache,destination)
    input = input_index > 0 ? _pipeline_vector!(ws,rhs) : (values=rhs,indices=eachindex(rhs))
    support = input_index > 0 ? length(input.indices) : count(!iszero,rhs)
    state = _pipeline_state(cache,operation)
    mode = _pipeline_mode!(state,support,n,kernel_mode)
    successful = false
    try
        if mode == :empty
            _pipeline_empty_output!(cache,output_index,destination)
        else
            mode == :sparse && (input_index == 0 || output_index == 0 ||
                !_pipeline_sparse_available!(ws)) && (mode = :dense)
            selected_mode = mode
            if eltype(rhs) === BigFloat
                _pipeline_basis_precision(ws,input) do
                    _pipeline_basis_kernel!(destination,ws,rhs,cache,input_index,output_index,selected_mode,transposed)
                end
            else
                _pipeline_basis_kernel!(destination,ws,rhs,cache,input_index,output_index,selected_mode,transposed)
            end
        end
        result_support = _pipeline_output_support!(ws,cache,output_index,destination)
        state.output_density = iszero(n) ? 0.0 : result_support/n
        successful = true
        return destination
    catch exception
        output_index > 0 && (cache.valid[output_index] = false)
        exception isa OverflowError && throw(_UnreliableBasisSolve())
        rethrow()
    finally
        _pipeline_note_call!(state,mode)
        elapsed = clock()-started
        _pipeline_diagnostic!(ws.progress.diagnostics,operation,mode,elapsed)
        successful && mode != :empty && record_kernel_cost!(state,mode,Float64(elapsed)/1e9)
    end
end

function _pipeline_price!(destination,ws,rho;operation::Symbol=:pricing,
                          kernel_mode::Symbol=:auto,clock=time_ns)::Nothing
    kernel_mode in (:auto,:sparse,:dense) || throw(ArgumentError("Unknown pipeline kernel mode"))
    if !ws.progress.numerical_policy.hypersparse
        _pipeline_changed!(ws,destination)
        return _csc_price!(destination,ws.problem.A,rho)
    end
    m,n = size(ws.problem.A)
    length(rho) == m && length(destination) == m+n || throw(DimensionMismatch("Pipeline pricing dimensions"))
    started = clock()
    cache = _hypersparse_workspace!(ws)
    input_index,output_index = _pipeline_buffer_index(cache,rho),_pipeline_buffer_index(cache,destination)
    input = input_index > 0 ? _pipeline_vector!(ws,rho) : (values=rho,indices=eachindex(rho))
    support = input_index > 0 ? length(input.indices) : count(!iszero,rho)
    state = _pipeline_state(cache,operation)
    mode = _pipeline_mode!(state,support,m,kernel_mode)
    successful = false
    try
        if mode == :empty
            _pipeline_empty_output!(cache,output_index,destination)
        else
            mode == :sparse && (input_index == 0 || output_index == 0 ||
                Base.mightalias(destination,rho)) && (mode = :dense)
            selected_mode = mode
            if eltype(rho) === BigFloat
                _pipeline_price_precision(cache,input) do
                    _pipeline_price_kernel!(destination,ws,rho,cache,input_index,output_index,selected_mode)
                end
            else
                _pipeline_price_kernel!(destination,ws,rho,cache,input_index,output_index,selected_mode)
            end
        end
        result_support = _pipeline_output_support!(ws,cache,output_index,destination)
        state.output_density = iszero(m+n) ? 0.0 : result_support/(m+n)
        successful = true
        return nothing
    catch exception
        output_index > 0 && (cache.valid[output_index] = false)
        exception isa OverflowError && throw(_UnreliableBasisSolve())
        rethrow()
    finally
        _pipeline_note_call!(state,mode)
        elapsed = clock()-started
        _pipeline_diagnostic!(ws.progress.diagnostics,operation,mode,elapsed)
        successful && mode != :empty && record_kernel_cost!(state,mode,Float64(elapsed)/1e9)
    end
end

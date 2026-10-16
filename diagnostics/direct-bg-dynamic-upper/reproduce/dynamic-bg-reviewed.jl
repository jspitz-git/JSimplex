# Diagnostic Task2 candidate, UNEXECUTED. Dense Float64 direct BG only.
# Slot primitives are the accepted Task1 candidate. No old method is overwritten.
mutable struct DynamicBGFactor{F}
    base::F
    upper::BGSlotUpper
    updates::Vector{BartelsGolubUpdate{Float64}}
    work::Vector{Float64}
    spike::Vector{Float64}
    recycled_updates::Vector{BartelsGolubUpdate{Float64}}
    shared_update_count::Int
    row_cache::TriangularRowCache{Float64}
end

function _dynamic_bg_with_exporter(B::AbstractMatrix{Float64},backend::Val{R},
        policy::_NativePivotPolicy,exporter;normalize::Bool=true,
        factorize=_factorize_basis) where {R}
    ((R === :native && policy === _NATIVE_PIVOT_ONE) ||
     (R === :markowitz && policy === _NATIVE_PIVOT_DEFAULT)) ||
        throw(ArgumentError("unsupported dynamic BG backend/policy"))
    ordinary=factorize(B,backend,policy)
    parts=exporter(ordinary);F=typeof(ordinary)
    if isnothing(parts)
        n=_backend_dimension(ordinary)
        base=DirectLowerBackend{R,F}(spzeros(0,0),Int[],Float64[],false,nothing,
                                    normalize,policy,ordinary,Float64[])
        upper=_bg_slots(spdiagm(0=>ones(n)),collect(1:n))
    else
        D=normalize ? _direct_normalize_upper!(parts.upper) : nothing
        n=length(parts.rows)
        base=DirectLowerBackend{R,F}(parts.lower,parts.rows,parts.scaling,parts.divide_scaling,
                                    D,normalize,policy,nothing,zeros(n))
        upper=_bg_slots(parts.upper,parts.columns)
    end
    return DynamicBGFactor(base,upper,BartelsGolubUpdate{Float64}[],zeros(n),zeros(n),
        BartelsGolubUpdate{Float64}[],0,TriangularRowCache(Float64,n))
end
_dynamic_bg_factor(B::AbstractMatrix{Float64},backend::Val,policy::_NativePivotPolicy)=
    _dynamic_bg_with_exporter(B,backend,policy,_export_basis_lu)
_dynamic_bg_factor(B,backend,policy)=throw(ArgumentError("dynamic BG requires Float64 matrix"))
_dynamic_bg_mode(f::DynamicBGFactor)=!isnothing(f.base.fallback) ? :fallback :
    isnothing(f.base.diagonal) ? :direct : :normalized
_dynamic_bg_dimension(f::DynamicBGFactor)=_backend_dimension(f.base)
_dynamic_bg_storage_count(f::DynamicBGFactor)=_backend_storage_count(f.base)+f.upper.live_count+
    sum(_update_storage_count,f.updates;init=0)
# Cold diagnostic metadata only; scan live column links, never unused capacity.
function _dynamic_bg_growth(f::DynamicBGFactor)
    v=0.0;U=f.upper
    for cid in U.column_order
        s=U.column_head[cid]
        while s!=0;v=max(v,abs(U.value[s]));s=U.column_next[s];end
    end
    return v
end
function _dynamic_bg_finite(f::DynamicBGFactor)
    U=f.upper
    for cid in U.column_order
        s=U.column_head[cid]
        while s!=0;isfinite(U.value[s]) || return false;s=U.column_next[s];end
    end
    return true
end
function _dbg_dimensions(f,destination,rhs)
    n=_backend_dimension(f.base)
    length(rhs)==n || throw(DimensionMismatch("right-hand side length must match basis dimension"))
    length(destination)==n || throw(DimensionMismatch("destination length must match basis dimension"))
    return n
end

function _dbg_invalidate_destination!(f,destination)
    cache=f.row_cache.prepared
    isnothing(cache) && return nothing
    for entry in cache.entries
        if !isnothing(entry.destination) && Base.mightalias(entry.destination,destination)
            entry.destination=nothing
        end
    end
    return nothing
end
Base.@noinline function _dbg_begin_prepared!(f,destination)
    Base.mightalias(destination,f.spike) && return nothing
    cache=f.row_cache.prepared
    if isnothing(cache)
        entries=ntuple(_->PreparedTriangularSpike{Float64}(nothing,Float64[],Float64[]),2)
        cache=TriangularSpikeCache{Float64}(entries,1);f.row_cache.prepared=cache
    end
    for entry in cache.entries
        if !isnothing(entry.destination) && Base.mightalias(entry.destination,destination)
            entry.destination=nothing
        end
        resize!(entry.direction,length(destination));resize!(entry.spike,length(destination))
    end
    entry=cache.entries[cache.next];cache.next=3-cache.next;entry.destination=nothing
    return entry
end
Base.@noinline function _dbg_copy_prepared!(f,direction)
    cache=f.row_cache.prepared
    isnothing(cache) && return false
    for entry in cache.entries
        if entry.destination===direction && isequal(entry.direction,direction)
            copyto!(f.spike,entry.spike);return true
        end
    end
    return false
end
_dbg_save_prepared!(::Nothing,f)=nothing
function _dbg_save_prepared!(entry::PreparedTriangularSpike,f)
    resize!(entry.spike,length(f.work))
    for row in eachindex(f.work);entry.spike[row]=f.work[f.upper.row_order[row]];end
    return nothing
end
function _dbg_sync_rows!(f)
    c=f.row_cache
    for i in c.update_count+1:length(f.updates)
        _append_compiled_rows!(c,f.updates[i]);c.update_count=i
    end
    return c
end
function _dbg_begin_update!(f,position)
    c=f.row_cache;safe=c.upper_prefix_safe
    c.upper_dirty_from=c.upper_dirty ? min(c.upper_dirty_from,position) : position
    c.upper_dirty=true;c.upper_prefix_safe=false
    cache=c.prepared
    if !isnothing(cache)
        for entry in cache.entries;entry.destination=nothing;end
    end
    c.upper_prefix_candidate=safe
    return nothing
end
function _dbg_columns(f)
    c=f.row_cache;U=f.upper
    if c.upper_dirty
        first=c.upper_dirty_from
        resize!(c.active_upper,searchsortedfirst(c.active_upper,first)-1)
        for j in first:U.n
            cid=U.column_order[j];s=U.column_head[cid];t=U.column_tail[cid]
            identity=s!=0 && s==t && U.row_position[U.row_id[s]]==j && U.value[s]==1.0
            identity || push!(c.active_upper,j)
            if !identity && c.upper_prefix_safe &&
                    (t==0 || U.row_position[U.row_id[t]]!=j || iszero(U.value[t]))
                c.upper_prefix_safe=false
            end
        end
        c.upper_dirty=false;c.upper_dirty_from=U.n+1
    end
    return c.active_upper
end
# Hessenberg pivots are at the column tail or its predecessor. Other
# internal storage queries descend in logical-row order, never rescan a row.
@inline function _dbg_entry(U,row,col)
    s=U.column_tail[U.column_order[col]]
    while s!=0 && U.row_position[U.row_id[s]]>row;s=U.column_prev[s];end
    return s!=0 && U.row_position[U.row_id[s]]==row ? s : 0
end
@inline function _dbg_value(U,row,col)
    s=_dbg_entry(U,row,col)
    return s==0 ? 0.0 : U.value[s]
end
@inline function _dbg_diagonal(U,j)
    cid=U.column_order[j];s=U.column_tail[cid]
    return s!=0 && U.row_id[s]==U.row_order[j] ? U.value[s] : _dbg_value(U,j,j)
end
function _dbg_backsolve!(f,columns)
    U=f.upper;w=f.work
    for j in Iterators.reverse(columns)
        rid=U.row_order[j];value=w[rid]/_dbg_diagonal(U,j);w[rid]=value
        s=U.column_head[U.column_order[j]]
        while s!=0
            row=U.row_id[s]
            if row!=rid;w[row]-=U.value[s]*value;end
            s=U.column_next[s]
        end
    end
    return w
end
function _dbg_transpose_upper!(f,columns,first::Int=1)
    U=f.upper;w=f.work
    for k in first:length(columns)
        j=columns[k];rid=U.row_order[j];value=w[rid]
        s=U.column_head[U.column_order[j]]
        while s!=0
            row=U.row_id[s]
            if row!=rid;value-=U.value[s]*w[row];end
            s=U.column_next[s]
        end
        w[rid]=value/_dbg_diagonal(U,j)
    end
    return w
end
function _dbg_forward!(destination::Vector{Float64},f::DynamicBGFactor,
                        rhs::Vector{Float64},prepare::Bool)
    destination===f.work && throw(ArgumentError("destination must not alias factorization work storage"))
    n=_dbg_dimensions(f,destination,rhs)
    source=destination===rhs ? copyto!(f.work,rhs) : rhs
    _dbg_invalidate_destination!(f,destination)
    entry=_dbg_begin_prepared!(f,destination);prepared=prepare ? entry : nothing
    _backend_forward_solve!(destination,f.base,source)
    c=_dbg_sync_rows!(f)
    for (target,origin,m) in c.operations
        _compiled_row_operation!(destination,target,origin,m,Val(:subtract))
    end
    for row in 1:n;f.work[f.upper.row_order[row]]=destination[c.order[row]];end
    _dbg_save_prepared!(prepared,f)
    _dbg_backsolve!(f,_dbg_columns(f))
    for j in 1:n;destination[f.upper.column_order[j]]=f.work[f.upper.row_order[j]];end
    _finish_prepared_spike!(prepared,destination)
    return destination
end
# Any keyword is unsupported: reject before dimensions/backend work.
function forward_solve!(destination::Vector{Float64},f::DynamicBGFactor,rhs::Vector{Float64};kwargs...)
    isempty(kwargs) || throw(ArgumentError("dynamic BG supports dense calls without kernel_mode only"))
    return _dbg_forward!(destination,f,rhs,true)
end
_ordinary_forward_solve!(destination::Vector{Float64},f::DynamicBGFactor,rhs::Vector{Float64})=
    _dbg_forward!(destination,f,rhs,false)
forward_solve!(destination,f::DynamicBGFactor,rhs;kwargs...)=throw(ArgumentError("dynamic BG requires dense Float64 vectors"))
forward_solve(f::DynamicBGFactor,rhs::Vector{Float64})=forward_solve!(similar(rhs),f,rhs)
function _unit_transpose_rhs(f::DynamicBGFactor,rhs::Vector{Float64},row::Int)
    checkbounds(rhs,row);return _UnitTransposeRHS(rhs,row)
end
function _dbg_transpose_rhs!(f,rhs::Vector{Float64})
    U=f.upper
    for j in eachindex(f.work);f.work[U.row_order[j]]=rhs[U.column_order[j]];end
end
function _dbg_transpose_rhs!(f,rhs::_UnitTransposeRHS{Float64})
    fill!(f.work,0.0);U=f.upper
    f.work[U.row_order[U.column_position[rhs.row]]]=1.0
end
_dbg_transpose_start!(f,rhs,columns)=1
function _dbg_transpose_start!(f,rhs::_UnitTransposeRHS{Float64},columns)
    if f.row_cache.upper_prefix_safe
        split=searchsortedfirst(columns,f.upper.column_position[rhs.row])
        for k in 1:split-1
            j=columns[k];f.work[f.upper.row_order[j]]/=_dbg_diagonal(f.upper,j)
        end
        return split
    end
    return 1
end
function transpose_solve!(destination::Vector{Float64},f::DynamicBGFactor,
                          rhs::Union{Vector{Float64},_UnitTransposeRHS{Float64}};kwargs...)
    isempty(kwargs) || throw(ArgumentError("dynamic BG supports dense calls without kernel_mode only"))
    destination===f.work && throw(ArgumentError("destination must not alias factorization work storage"))
    _dbg_dimensions(f,destination,rhs);_dbg_invalidate_destination!(f,destination)
    source=rhs===f.work ? copyto!(f.spike,rhs) : rhs
    _dbg_transpose_rhs!(f,source);columns=_dbg_columns(f)
    _dbg_transpose_upper!(f,columns,_dbg_transpose_start!(f,source,columns))
    c=_dbg_sync_rows!(f)
    for row in eachindex(c.order);f.spike[c.order[row]]=f.work[f.upper.row_order[row]];end
    source=f.spike
    for (target,origin,m) in Iterators.reverse(c.operations)
        _compiled_row_operation!(source,origin,target,m,Val(:subtract))
    end
    destination===source && (source=copyto!(f.work,source))
    return _backend_transpose_solve!(destination,f.base,source)
end
transpose_solve!(destination,f::DynamicBGFactor,rhs;kwargs...)=throw(ArgumentError("dynamic BG requires dense Float64 vectors"))
transpose_solve(f::DynamicBGFactor,rhs::Vector{Float64})=transpose_solve!(similar(rhs),f,rhs)

function _dbg_prepare_spike!(f,direction,pivot_row,zero_tolerance)
    tolerance=convert(Float64,zero_tolerance)
    isfinite(tolerance) && tolerance>=0.0 || throw(ArgumentError("zero_tolerance must be finite and nonnegative"))
    n=_backend_dimension(f.base)
    length(direction)==n || throw(DimensionMismatch("tableau column length must match basis dimension"))
    pivot=Int(pivot_row);checkbounds(direction,pivot)
    _pivot_magnitude(direction[pivot])>tolerance || throw(LinearAlgebra.ZeroPivotException(pivot))
    U=f.upper;position=U.column_position[pivot]
    _dbg_copy_prepared!(f,direction) && return position
    fill!(f.spike,0.0)
    for j in 1:n
        value=direction[U.column_order[j]];s=U.column_head[U.column_order[j]]
        while s!=0
            f.spike[U.row_position[U.row_id[s]]]+=U.value[s]*value
            s=U.column_next[s]
        end
    end
    return position
end
function _dbg_replace_column!(f,position)
    U=f.upper;cid=U.column_order[position];s=U.column_head[cid]
    while s!=0
        next=U.column_next[s];_bg_unlink!(U,s);s=next
    end
    for row in 1:U.n
        value=f.spike[row];iszero(value) && continue
        _track_upper_value!(f,value);rid=U.row_order[row]
        p=0;t=U.row_head[rid]
        while t!=0 && U.column_id[t]<cid;p=t;t=U.row_next[t];end
        _bg_link!(U,rid,cid,value,p,t,U.column_tail[cid],0)
    end
    for j in position:U.n-1
        moved=U.column_order[j+1];U.column_order[j]=moved;U.column_position[moved]=j
    end
    U.column_order[U.n]=cid;U.column_position[cid]=U.n
    return nothing
end
function _dbg_last_pure(U,first)
    # Preserve the cheap immediate rejection before scanning the carried row.
    iszero(_dbg_value(U,first,first)) || return first-1
    lower=_dbg_value(U,first+1,first)
    _pivot_magnitude(lower)>zero(lower) || return first-1
    first==U.n-1 && return first
    # Only Float64 reads: find the first future nonzero in logical-column
    # order once. NaN/Inf are nonzero exactly as in the original predicate.
    blocker=U.n;s=U.row_head[U.row_order[first]]
    while s!=0
        col=U.column_position[U.column_id[s]]
        if first<col<blocker && !iszero(U.value[s]);blocker=col;end
        s=U.row_next[s]
    end
    for j in first+1:U.n-1
        j==blocker && return j-1
        lower=_dbg_value(U,j+1,j)
        _pivot_magnitude(lower)>zero(lower) || return j-1
    end
    return U.n-1
end
# Adjacent physical rows, stable-column merge. Source row never mutates.
# `visit` is a call-local test seam; normal calls specialize it to Nothing.
function _dbg_eliminate_row!(f,j,m,visit=nothing)
    U=f.upper;source=U.row_order[j];target=U.row_order[j+1]
    s=U.row_head[source];p=0;t=U.row_head[target]
    while s!=0
        next=U.row_next[s];cid=U.column_id[s]
        if U.column_position[cid]>j
            isnothing(visit) || visit(cid)
            while t!=0 && U.column_id[t]<cid;p=t;t=U.row_next[t];end
            present=t!=0 && U.column_id[t]==cid
            old=present ? U.value[t] : 0.0
            value=_track_upper_value!(f,old-m*U.value[s])
            if present
                after=U.row_next[t]
                if iszero(value);_bg_unlink!(U,t);else;U.value[t]=value;p=t;end
                t=after
            elseif !iszero(value)
                # Adjacent logical rows: source node is the column predecessor.
                p=_bg_link!(U,target,cid,value,p,t,s,U.column_next[s])
            end
        end
        s=next
    end
    return nothing
end
function _dynamic_bg_replace!(f,direction,pivot_row,zero_tolerance)
    position=_dbg_prepare_spike!(f,direction,pivot_row,zero_tolerance)
    _dbg_begin_update!(f,position);_dbg_replace_column!(f,position)
    # Same observable private scratch as the reference after packing.
    fill!(f.spike,0.0)
    steps=isempty(f.recycled_updates) ? BartelsGolubStep{Float64}[] : pop!(f.recycled_updates).steps
    run_start=0;run_last=0;completed_through=position-1;U=f.upper
    for j in position:U.n-1
        j<=completed_through && continue
        last_pure=_dbg_last_pure(U,j)
        if last_pure>j
            _bg_rotate_rows!(U,j,last_pure+1)
            run_start==0 && (run_start=j)
            run_last=last_pure;completed_through=last_pure;continue
        end
        swapped=_pivot_magnitude(_dbg_value(U,j+1,j))>_pivot_magnitude(_dbg_value(U,j,j))
        swapped && _bg_swap_rows!(U,j)
        pivot=_dbg_value(U,j,j)
        iszero(pivot) && throw(LinearAlgebra.ZeroPivotException(j))
        slot=_dbg_entry(U,j+1,j)
        old=slot==0 ? 0.0 : U.value[slot];multiplier=old/pivot
        slot==0 || _bg_unlink!(U,slot)
        iszero(multiplier) || _dbg_eliminate_row!(f,j,multiplier)
        if swapped && iszero(multiplier)
            run_start==0 && (run_start=j)
            run_last=j;continue
        end
        if run_start!=0
            push!(steps,BartelsGolubStep{Float64}(run_start,run_last,true,0.0));run_start=0
        end
        (swapped || !iszero(multiplier)) && push!(steps,BartelsGolubStep{Float64}(j,j,swapped,multiplier))
    end
    run_start==0 || push!(steps,BartelsGolubStep{Float64}(run_start,run_last,true,0.0))
    push!(f.updates,BartelsGolubUpdate{Float64}(steps))
    return _finish_upper_update!(f)
end
function replace_column!(f::DynamicBGFactor,direction::Vector{Float64},pivot_row::Integer;
                          zero_tolerance::Real=_positive_tolerance(Float64,1//10^12))
    return _dynamic_bg_replace!(f,direction,pivot_row,zero_tolerance)
end
replace_column!(f::DynamicBGFactor,direction,pivot_row;kwargs...)=throw(ArgumentError("dynamic BG requires dense Float64 direction"))
function copy_basis_factorization(f::DynamicBGFactor)
    f.shared_update_count=length(f.updates);U=f.upper
    upper=BGSlotUpper(copy(U.value),copy(U.row_id),copy(U.column_id),copy(U.row_prev),
        copy(U.row_next),copy(U.column_prev),copy(U.column_next),copy(U.row_order),
        copy(U.row_position),copy(U.column_order),copy(U.column_position),copy(U.row_head),
        copy(U.row_tail),copy(U.column_head),copy(U.column_tail),U.n,U.capacity,U.live_count,U.free_head)
    return DynamicBGFactor(_copy_backend(f.base),upper,copy(f.updates),similar(f.work),similar(f.spike),
        BartelsGolubUpdate{Float64}[],f.shared_update_count,_copy_triangular_row_cache(f))
end
function _dynamic_bg_refactor_with_exporter!(f::DynamicBGFactor,B::AbstractMatrix{Float64},exporter)
    candidate=_dynamic_bg_with_exporter(B,Val(_direct_requested_backend(f.base)),f.base.pivot_policy,
        exporter;normalize=f.base.normalize_requested)
    typeof(candidate)===typeof(f) || throw(ArgumentError("dynamic BG refactorization type changed"))
    for name in fieldnames(typeof(f));setfield!(f,name,getfield(candidate,name));end
    return f
end
refactorize!(f::DynamicBGFactor,B::AbstractMatrix{Float64})=_dynamic_bg_refactor_with_exporter!(f,B,_export_basis_lu)
refactorize!(f::DynamicBGFactor,B)=throw(ArgumentError("dynamic BG requires Float64 matrix"))

# Diagnostic Task2 block candidate, UNEXECUTED. Dense Float64 direct BG only.
# Frozen Task1 block primitives; explicit private methods, no production overwrite.
mutable struct ProbeSplitBGFactor{F}
    base::F
    upper::ProbeBGSplitUpper
    updates::Vector{BartelsGolubUpdate{Float64}}
    work::Vector{Float64}
    spike::Vector{Float64}
    recycled_updates::Vector{BartelsGolubUpdate{Float64}}
    shared_update_count::Int
    row_cache::TriangularRowCache{Float64}
end

function _probe_split_bg_with_exporter(B::AbstractMatrix{Float64},backend::Val{R},
        policy::_NativePivotPolicy,exporter;normalize::Bool=true,
        factorize=_factorize_basis,build=_probe_sbu_build,limit::Integer=typemax(Int32)) where {R}
    ((R === :native && policy === _NATIVE_PIVOT_ONE) ||
     (R === :markowitz && policy === _NATIVE_PIVOT_DEFAULT)) ||
        throw(ArgumentError("unsupported block BG backend/policy"))
    _probe_sbu_limit(Base.Checked.checked_add(size(B,1),1),limit)
    B isa SparseMatrixCSC && !(B isa SparseMatrixCSC{Float64,Int}) &&
        throw(ArgumentError("block BG requires Int CSC indices"))
    ordinary=factorize(B,backend,policy)
    parts=exporter(ordinary);F=typeof(ordinary)
    if isnothing(parts)
        n=_backend_dimension(ordinary)
        base=DirectLowerBackend{R,F}(spzeros(0,0),Int[],Float64[],false,nothing,
                                    normalize,policy,ordinary,Float64[])
        upper=build(spdiagm(0=>ones(n)),collect(1:n))
    else
        D=normalize ? _direct_normalize_upper!(parts.upper) : nothing
        n=length(parts.rows)
        base=DirectLowerBackend{R,F}(parts.lower,parts.rows,parts.scaling,parts.divide_scaling,
                                    D,normalize,policy,nothing,zeros(n))
        upper=build(parts.upper,parts.columns)
    end
    return ProbeSplitBGFactor(base,upper,BartelsGolubUpdate{Float64}[],zeros(n),zeros(n),
        BartelsGolubUpdate{Float64}[],0,TriangularRowCache(Float64,n))
end
_probe_split_bg_factor(B::AbstractMatrix{Float64},backend::Val,policy::_NativePivotPolicy)=
    _probe_split_bg_with_exporter(B,backend,policy,_export_basis_lu)
_probe_split_bg_factor(B,backend,policy)=throw(ArgumentError("block BG requires Float64 matrix"))
_probe_split_bg_mode(f::ProbeSplitBGFactor)=!isnothing(f.base.fallback) ? :fallback :
    isnothing(f.base.diagonal) ? :direct : :normalized
_probe_split_bg_dimension(f::ProbeSplitBGFactor)=_backend_dimension(f.base)
_probe_split_bg_storage_count(f::ProbeSplitBGFactor)=_backend_storage_count(f.base)+f.upper.live+
    sum(_update_storage_count,f.updates;init=0)
# Cold diagnostic metadata only. No full scan is called by a solve.
function _probe_split_bg_growth(f::ProbeSplitBGFactor)
    value=0.0;U=f.upper
    for cid in U.column_order
        b=Int(U.column_head[cid])
        while b!=0
            s=Int(U.slab[b]);a=Int(U.start[b]);v=U.values[s]
            for p in a:a+Int(U.count[b])-1;value=max(value,abs(v[p]));end
            b=Int(U.next[b])
        end
    end
    return value
end
function _probe_split_bg_finite(f::ProbeSplitBGFactor)
    U=f.upper
    for cid in U.column_order
        b=Int(U.column_head[cid])
        while b!=0
            s=Int(U.slab[b]);a=Int(U.start[b]);v=U.values[s]
            for p in a:a+Int(U.count[b])-1;isfinite(v[p]) || return false;end
            b=Int(U.next[b])
        end
    end
    return true
end
# Reject private new scratch before dimensions/backend. No slab-owner scan.
function _probe_sbg_destination(f,destination)
    (destination===f.work || destination===f.upper.scratch_value ||
     Base.mightalias(destination,f.work) || Base.mightalias(destination,f.upper.scratch_value)) &&
        throw(ArgumentError("destination must not alias factorization work storage"))
    return nothing
end
function _probe_sbg_dimensions(f,destination,rhs)
    n=_backend_dimension(f.base)
    length(rhs)==n || throw(DimensionMismatch("right-hand side length must match basis dimension"))
    length(destination)==n || throw(DimensionMismatch("destination length must match basis dimension"))
    return n
end

function _probe_sbg_invalidate_destination!(f,destination)
    cache=f.row_cache.prepared
    isnothing(cache) && return nothing
    for entry in cache.entries
        if !isnothing(entry.destination) && Base.mightalias(entry.destination,destination)
            entry.destination=nothing
        end
    end
    return nothing
end
Base.@noinline function _probe_sbg_begin_prepared!(f,destination)
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
Base.@noinline function _probe_sbg_copy_prepared!(f,direction)
    cache=f.row_cache.prepared
    isnothing(cache) && return false
    for entry in cache.entries
        if entry.destination===direction && isequal(entry.direction,direction)
            copyto!(f.spike,entry.spike);return true
        end
    end
    return false
end
_probe_sbg_save_prepared!(::Nothing,f)=nothing
function _probe_sbg_save_prepared!(entry::PreparedTriangularSpike,f)
    resize!(entry.spike,length(f.work))
    for row in eachindex(f.work);entry.spike[row]=f.work[f.upper.row_order[row]];end
    return nothing
end
function _probe_sbg_sync_rows!(f)
    c=f.row_cache
    for i in c.update_count+1:length(f.updates)
        _append_compiled_rows!(c,f.updates[i]);c.update_count=i
    end
    return c
end
function _probe_sbg_begin_update!(f,position)
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
function _probe_sbg_columns(f)
    c=f.row_cache;U=f.upper
    if c.upper_dirty
        first=c.upper_dirty_from
        resize!(c.active_upper,searchsortedfirst(c.active_upper,first)-1)
        for j in first:U.n
            cid=Int(U.column_order[j]);b=Int(U.column_head[cid]);t=Int(U.column_tail[cid])
            count=t==0 ? 0 : Int(U.count[t])
            tail=count==0 ? nothing : _probe_sbu_tuple(U,Int32((t-1)*32+count))
            identity=b!=0 && b==t && count==1 && U.row_position[Int(tail[2])]==j && tail[1]==1.0
            identity || push!(c.active_upper,j)
            if !identity && c.upper_prefix_safe &&
                    (t==0 || U.row_position[Int(tail[2])]!=j || iszero(tail[1]))
                c.upper_prefix_safe=false
            end
        end
        c.upper_dirty=false;c.upper_dirty_from=U.n+1
    end
    return c.active_upper
end
# Descend block prefixes in logical-row order for Hessenberg/missing-diagonal lookup.
@inline function _probe_sbg_entry(U,row,col)
    b=Int(U.column_tail[Int(U.column_order[col])])
    while b!=0
        s=Int(U.slab[b]);a=Int(U.start[b]);rows=U.row_ids[s]
        for k in Int(U.count[b]):-1:1
            logical=Int(U.row_position[Int(rows[a+k-1])])
            logical>row && continue
            return logical==row ? Int32((b-1)*32+k) : Int32(0)
        end
        b=Int(U.prev[b])
    end
    return Int32(0)
end
@inline function _probe_sbg_value(U,row,col)
    h=_probe_sbg_entry(U,row,col);return h==0 ? 0.0 : _probe_sbu_tuple(U,h)[1]
end
@inline function _probe_sbg_tail_diagonal(U,j)
    b=Int(U.column_tail[Int(U.column_order[j])])
    return b!=0 && U.row_ids[Int(U.slab[b])][Int(U.start[b])+Int(U.count[b])-1]==U.row_order[j]
end
@inline function _probe_sbg_diagonal(U,j)
    b=Int(U.column_tail[Int(U.column_order[j])])
    if b!=0
        s=Int(U.slab[b]);p=Int(U.start[b])+Int(U.count[b])-1
        U.row_ids[s][p]==U.row_order[j] && return U.values[s][p]
    end
    return _probe_sbg_value(U,j,j)
end
function _probe_sbg_backsolve!(f,columns)
    U=f.upper;w=f.work
    for j in Iterators.reverse(columns)
        rid=Int(U.row_order[j]);value=w[rid]/_probe_sbg_diagonal(U,j);w[rid]=value
        cid=Int(U.column_order[j]);tail=Int(U.column_tail[cid]);fast=_probe_sbg_tail_diagonal(U,j)
        b=Int(U.column_head[cid])
        while b!=0
            s=Int(U.slab[b]);a=Int(U.start[b]);values=U.values[s];rows=U.row_ids[s]
            count=Int(U.count[b])-(fast && b==tail ? 1 : 0)
            if fast
                for p in a:a+count-1;w[Int(rows[p])]-=values[p]*value;end
            else
                for p in a:a+count-1
                    row=Int(rows[p]);row==rid && continue;w[row]-=values[p]*value
                end
            end
            b=Int(U.next[b])
        end
    end
    return w
end
function _probe_sbg_transpose_upper!(f,columns,first::Int=1)
    U=f.upper;w=f.work
    for k in first:length(columns)
        j=columns[k];rid=Int(U.row_order[j]);value=w[rid]
        cid=Int(U.column_order[j]);tail=Int(U.column_tail[cid]);fast=_probe_sbg_tail_diagonal(U,j)
        b=Int(U.column_head[cid])
        while b!=0
            s=Int(U.slab[b]);a=Int(U.start[b]);values=U.values[s];rows=U.row_ids[s]
            count=Int(U.count[b])-(fast && b==tail ? 1 : 0)
            if fast
                for p in a:a+count-1;value-=values[p]*w[Int(rows[p])];end
            else
                for p in a:a+count-1
                    row=Int(rows[p]);row==rid && continue;value-=values[p]*w[row]
                end
            end
            b=Int(U.next[b])
        end
        w[rid]=value/_probe_sbg_diagonal(U,j)
    end
    return w
end
function _probe_sbg_forward!(destination::Vector{Float64},f::ProbeSplitBGFactor,
                        rhs::Vector{Float64},prepare::Bool)
    _probe_sbg_destination(f,destination)
    n=_probe_sbg_dimensions(f,destination,rhs)
    source=destination===rhs ? copyto!(f.work,rhs) : rhs
    _probe_sbg_invalidate_destination!(f,destination)
    entry=_probe_sbg_begin_prepared!(f,destination);prepared=prepare ? entry : nothing
    _backend_forward_solve!(destination,f.base,source)
    c=_probe_sbg_sync_rows!(f)
    for (target,origin,m) in c.operations
        _compiled_row_operation!(destination,target,origin,m,Val(:subtract))
    end
    for row in 1:n;f.work[f.upper.row_order[row]]=destination[c.order[row]];end
    _probe_sbg_save_prepared!(prepared,f)
    _probe_sbg_backsolve!(f,_probe_sbg_columns(f))
    for j in 1:n;destination[f.upper.column_order[j]]=f.work[f.upper.row_order[j]];end
    _finish_prepared_spike!(prepared,destination)
    return destination
end
# Any keyword is unsupported: reject before dimensions/backend work.
function forward_solve!(destination::Vector{Float64},f::ProbeSplitBGFactor,rhs::Vector{Float64};kwargs...)
    isempty(kwargs) || throw(ArgumentError("block BG supports dense calls without kernel_mode only"))
    return _probe_sbg_forward!(destination,f,rhs,true)
end
_ordinary_forward_solve!(destination::Vector{Float64},f::ProbeSplitBGFactor,rhs::Vector{Float64})=
    _probe_sbg_forward!(destination,f,rhs,false)
forward_solve!(destination,f::ProbeSplitBGFactor,rhs;kwargs...)=throw(ArgumentError("block BG requires dense Float64 vectors"))
forward_solve(f::ProbeSplitBGFactor,rhs::Vector{Float64})=forward_solve!(similar(rhs),f,rhs)
function _unit_transpose_rhs(f::ProbeSplitBGFactor,rhs::Vector{Float64},row::Int)
    checkbounds(rhs,row);return _UnitTransposeRHS(rhs,row)
end
function _probe_sbg_transpose_rhs!(f,rhs::Vector{Float64})
    U=f.upper
    for j in eachindex(f.work);f.work[U.row_order[j]]=rhs[U.column_order[j]];end
end
function _probe_sbg_transpose_rhs!(f,rhs::_UnitTransposeRHS{Float64})
    fill!(f.work,0.0);U=f.upper
    f.work[U.row_order[U.column_position[rhs.row]]]=1.0
end
_probe_sbg_transpose_start!(f,rhs,columns)=1
function _probe_sbg_transpose_start!(f,rhs::_UnitTransposeRHS{Float64},columns)
    if f.row_cache.upper_prefix_safe
        split=searchsortedfirst(columns,f.upper.column_position[rhs.row])
        for k in 1:split-1
            j=columns[k];f.work[f.upper.row_order[j]]/=_probe_sbg_diagonal(f.upper,j)
        end
        return split
    end
    return 1
end
function transpose_solve!(destination::Vector{Float64},f::ProbeSplitBGFactor,
                          rhs::Union{Vector{Float64},_UnitTransposeRHS{Float64}};kwargs...)
    isempty(kwargs) || throw(ArgumentError("block BG supports dense calls without kernel_mode only"))
    _probe_sbg_destination(f,destination)
    _probe_sbg_dimensions(f,destination,rhs);_probe_sbg_invalidate_destination!(f,destination)
    source=rhs===f.work ? copyto!(f.spike,rhs) : rhs
    _probe_sbg_transpose_rhs!(f,source);columns=_probe_sbg_columns(f)
    _probe_sbg_transpose_upper!(f,columns,_probe_sbg_transpose_start!(f,source,columns))
    c=_probe_sbg_sync_rows!(f)
    for row in eachindex(c.order);f.spike[c.order[row]]=f.work[f.upper.row_order[row]];end
    source=f.spike
    for (target,origin,m) in Iterators.reverse(c.operations)
        _compiled_row_operation!(source,origin,target,m,Val(:subtract))
    end
    destination===source && (source=copyto!(f.work,source))
    return _backend_transpose_solve!(destination,f.base,source)
end
transpose_solve!(destination,f::ProbeSplitBGFactor,rhs;kwargs...)=throw(ArgumentError("block BG requires dense Float64 vectors"))
transpose_solve(f::ProbeSplitBGFactor,rhs::Vector{Float64})=transpose_solve!(similar(rhs),f,rhs)

function _probe_sbg_prepare_spike!(f,direction,pivot_row,zero_tolerance)
    tolerance=convert(Float64,zero_tolerance)
    isfinite(tolerance) && tolerance>=0.0 || throw(ArgumentError("zero_tolerance must be finite and nonnegative"))
    n=_backend_dimension(f.base)
    length(direction)==n || throw(DimensionMismatch("tableau column length must match basis dimension"))
    pivot=Int(pivot_row);checkbounds(direction,pivot)
    _pivot_magnitude(direction[pivot])>tolerance || throw(LinearAlgebra.ZeroPivotException(pivot))
    U=f.upper;position=Int(U.column_position[pivot])
    _probe_sbg_copy_prepared!(f,direction) && return position
    fill!(f.spike,0.0)
    for j in 1:n
        value=direction[U.column_order[j]];b=Int(U.column_head[Int(U.column_order[j])])
        while b!=0
            s=Int(U.slab[b]);a=Int(U.start[b]);values=U.values[s];rows=U.row_ids[s]
            for p in a:a+Int(U.count[b])-1
                f.spike[Int(U.row_position[Int(rows[p])])]+=values[p]*value
            end
            b=Int(U.next[b])
        end
    end
    return position
end
# Remove whole column blocks without merging/repacking the old column.
function _probe_sbg_clear_column!(U,cid::Int)
    b=Int(U.column_head[cid])
    while b!=0
        following=Int(U.next[b]);count=Int(U.count[b])
        for k in 1:count
            h=Int32((b-1)*32+k);v,r,p=_probe_sbu_tuple(U,h);rid=Int(r)
            rank=Int(p)<U.gap_first[rid] ? Int(p) : Int(p)-Int(U.gap_length[rid])
            _probe_sbu_gap!(U,rid,rank)
            g=Int(U.gap_first[rid]);l=Int(U.gap_length[rid]);U.rows[rid][g+l]=0
            U.gap_length[rid]=Int32(l+1);U.live-=1;_probe_sbu_clear!(U,b,k)
        end
        _probe_sbu_unlink_block!(U,b);b=following
    end
    return nothing
end
function _probe_sbg_replace_column!(f,position,allocate,limit)
    U=f.upper;cid=Int(U.column_order[position]);_probe_sbg_clear_column!(U,cid)
    for row in 1:U.n
        value=f.spike[row];iszero(value) && continue
        _track_upper_value!(f,value);rid=Int(U.row_order[row]);rank,_=_probe_sbu_row_search(U,rid,cid)
        tail=Int(U.column_tail[cid]);pred=tail==0 ? Int32(0) : Int32((tail-1)*32+Int(U.count[tail]))
        _probe_sbu_insert_at!(U,rid,cid,value,rank,pred,allocate,limit)
    end
    for j in position:U.n-1
        moved=U.column_order[j+1];U.column_order[j]=moved;U.column_position[Int(moved)]=Int32(j)
    end
    U.column_order[U.n]=Int32(cid);U.column_position[cid]=Int32(U.n)
    return nothing
end
function _probe_sbg_last_pure(U,first)
    iszero(_probe_sbg_value(U,first,first)) || return first-1
    lower=_probe_sbg_value(U,first+1,first)
    _pivot_magnitude(lower)>zero(lower) || return first-1
    first==U.n-1 && return first
    blocker=U.n;rid=Int(U.row_order[first])
    for rank in 1:_probe_sbu_degree(U,rid)
        h=_probe_sbu_row_handle(U,rid,rank);col=Int(U.column_position[_probe_sbu_cid(U,h)])
        if first<col<blocker && !iszero(_probe_sbu_tuple(U,h)[1]);blocker=col;end
    end
    for j in first+1:U.n-1
        j==blocker && return j-1
        lower=_probe_sbg_value(U,j+1,j)
        _pivot_magnitude(lower)>zero(lower) || return j-1
    end
    return U.n-1
end
# Monotone stable-column merge. Source membership does not change, but handles
# can move on every edit: reload the next source and target from row buffers.
function _probe_sbg_eliminate_row!(f,j,m,visit=nothing;allocate=_probe_sbu_allocate,limit::Integer=typemax(Int32))
    U=f.upper;source=Int(U.row_order[j]);target=Int(U.row_order[j+1]);i=1;k=1
    while i<=_probe_sbu_degree(U,source)
        h=_probe_sbu_row_handle(U,source,i);cid=_probe_sbu_cid(U,h)
        if U.column_position[cid]>j
            isnothing(visit) || visit(cid)
            while k<=_probe_sbu_degree(U,target) && _probe_sbu_cid(U,_probe_sbu_row_handle(U,target,k))<cid;k+=1;end
            t=k<=_probe_sbu_degree(U,target) ? _probe_sbu_row_handle(U,target,k) : Int32(0)
            present=t!=0 && _probe_sbu_cid(U,t)==cid
            old=present ? _probe_sbu_tuple(U,t)[1] : 0.0
            value=_track_upper_value!(f,old-m*_probe_sbu_tuple(U,h)[1])
            if present
                if iszero(value)
                    _probe_sbu_delete!(U,target,k,t)
                else
                    b,offset=_probe_sbu_decode(t);U.values[Int(U.slab[b])][Int(U.start[b])+offset-1]=value;k+=1
                end
            elseif !iszero(value)
                _probe_sbu_insert_at!(U,target,cid,value,k,h,allocate,limit);k+=1
            end
        end
        i+=1
    end
    return nothing
end
function _probe_sbg_delete_handle!(U,h::Int32)
    v,r,p=_probe_sbu_tuple(U,h);rid=Int(r)
    rank=Int(p)<U.gap_first[rid] ? Int(p) : Int(p)-Int(U.gap_length[rid])
    _probe_sbu_delete!(U,rid,rank,h);return nothing
end
function _probe_split_bg_replace!(f,direction,pivot_row,zero_tolerance;allocate=_probe_sbu_allocate,limit::Integer=typemax(Int32))
    position=_probe_sbg_prepare_spike!(f,direction,pivot_row,zero_tolerance)
    _probe_sbg_begin_update!(f,position);_probe_sbg_replace_column!(f,position,allocate,limit)
    # Same observable private scratch as the reference after packing.
    fill!(f.spike,0.0)
    steps=isempty(f.recycled_updates) ? BartelsGolubStep{Float64}[] : pop!(f.recycled_updates).steps
    run_start=0;run_last=0;completed_through=position-1;U=f.upper
    for j in position:U.n-1
        j<=completed_through && continue
        last_pure=_probe_sbg_last_pure(U,j)
        if last_pure>j
            _probe_sbu_rotate_rows!(U,j,last_pure+1)
            run_start==0 && (run_start=j)
            run_last=last_pure;completed_through=last_pure;continue
        end
        swapped=_pivot_magnitude(_probe_sbg_value(U,j+1,j))>_pivot_magnitude(_probe_sbg_value(U,j,j))
        swapped && _probe_sbu_swap_rows!(U,j)
        pivot=_probe_sbg_value(U,j,j)
        iszero(pivot) && throw(LinearAlgebra.ZeroPivotException(j))
        slot=_probe_sbg_entry(U,j+1,j)
        old=slot==0 ? 0.0 : _probe_sbu_tuple(U,slot)[1];multiplier=old/pivot
        slot==0 || _probe_sbg_delete_handle!(U,slot)
        iszero(multiplier) || _probe_sbg_eliminate_row!(f,j,multiplier;allocate,limit)
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
function replace_column!(f::ProbeSplitBGFactor,direction::Vector{Float64},pivot_row::Integer;
                          zero_tolerance::Real=_positive_tolerance(Float64,1//10^12))
    return _probe_split_bg_replace!(f,direction,pivot_row,zero_tolerance)
end
replace_column!(f::ProbeSplitBGFactor,direction,pivot_row;kwargs...)=throw(ArgumentError("block BG requires dense Float64 direction"))
function _probe_split_bg_copy_with(f::ProbeSplitBGFactor,copier)
    # All allocations first; shared-prefix bookkeeping changes only on success.
    upper=copier(f.upper);shared=length(f.updates)
    candidate=ProbeSplitBGFactor(_copy_backend(f.base),upper,copy(f.updates),similar(f.work),similar(f.spike),
        BartelsGolubUpdate{Float64}[],shared,_copy_triangular_row_cache(f))
    f.shared_update_count=shared;return candidate
end
copy_basis_factorization(f::ProbeSplitBGFactor)=_probe_split_bg_copy_with(f,_probe_sbu_copy)
function _probe_split_bg_refactor_with_exporter!(f::ProbeSplitBGFactor,B::AbstractMatrix{Float64},exporter;build=_probe_sbu_build)
    candidate=_probe_split_bg_with_exporter(B,Val(_direct_requested_backend(f.base)),f.base.pivot_policy,
        exporter;normalize=f.base.normalize_requested,build)
    typeof(candidate)===typeof(f) || throw(ArgumentError("block BG refactorization type changed"))
    for name in fieldnames(typeof(f));setfield!(f,name,getfield(candidate,name));end
    return f
end
refactorize!(f::ProbeSplitBGFactor,B::AbstractMatrix{Float64})=_probe_split_bg_refactor_with_exporter!(f,B,_export_basis_lu)
refactorize!(f::ProbeSplitBGFactor,B)=throw(ArgumentError("block BG requires Float64 matrix"))

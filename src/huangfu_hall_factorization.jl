# Middle product form (Huangfu--Hall, ERGO-13-001, section 3.1.2).
# In native scaled/permuted coordinates: P*S*B*Q = L*T1*...*Tk*U.
# Factors and live/shared update records are immutable; private retired arrays may be reused.
struct HHBase{T<:Real}
    lower::SparseMatrixCSC{T,Int}
    upper::SparseMatrixCSC{T,Int}
    rows::Vector{Int}
    columns::Vector{Int}
    positions::Vector{Int}
    scaling::Vector{T}
    divide_scaling::Bool
    upper_rowptr::Vector{Int}
    upper_columns::Vector{Int}
end
struct HHUpdate{T<:Real}
    u_indices::Vector{Int}
    u_values::Vector{T}
    v_indices::Vector{Int}
    v_values::Vector{T}
    pivot::T
end
# Each pool retains at most 4 MiB of fixed-size index/value payload and 256 pairs.
# Arbitrary-precision values have variable payload sizes and are not retained.
# Exact-length reuse avoids hidden oversized vector capacity and resize overhead.
mutable struct HHPool{T<:Real}
    pairs::Vector{Tuple{Vector{Int},Vector{T}}}
    entries::Int
end
HHPool(::Type{T}=Float64) where {T<:Real}=HHPool(Tuple{Vector{Int},Vector{T}}[],0)
function _hh_retire_pair!(pool::HHPool{T},indices,values) where {T}
    n=length(indices)
    if isbitstype(T) && length(pool.pairs)<256 &&
       pool.entries+n<=div(4*1024^2,sizeof(Int)+sizeof(T))
        push!(pool.pairs,(indices,values));pool.entries+=n
    end
    nothing
end
_hh_take_pair!(::Nothing,n,::Type{T}=Float64) where {T}=(Vector{Int}(undef,n),Vector{T}(undef,n))
function _hh_take_pair!(pool::HHPool{T},n,::Type{T}=T) where {T}
    for i in length(pool.pairs):-1:1
        pair=pool.pairs[i]
        if length(pair[1])==n
            pool.pairs[i]=pool.pairs[end];pop!(pool.pairs);pool.entries-=n
            return pair
        end
    end
    _hh_take_pair!(nothing,n,T)
end

struct HHUnitWorkspace{T<:Real}
    values::Vector{T}
    marked::BitVector
    indices::Vector{Int}
end
HHUnitWorkspace(n,::Type{T}=Float64) where {T}=HHUnitWorkspace(zeros(T,n),falses(n),Int[])

# Private CSR extraction scratch; output L/U never alias these buffers.
mutable struct HHExtractWorkspace
    rowptr::Vector{Int}
    columns::Vector{Int}
    values::Vector{Float64}
end
HHExtractWorkspace()=HHExtractWorkspace(Int[],Int[],Float64[])
function _hh_extract_buffers!(w::HHExtractWorkspace,n,lnz)
    # Bound retained payload to 8 MiB and avoid keeping a much denser old shape.
    if 8*(n+1+2lnz)<=8*1024^2
        length(w.rowptr)==n+1 || (w.rowptr=Vector{Int}(undef,n+1))
        if !(lnz<=length(w.columns)<=max(2lnz,16)) || length(w.columns)!=length(w.values) || 8*(n+1+2length(w.columns))>8*1024^2
            columns=Vector{Int}(undef,lnz);values=Vector{Float64}(undef,lnz)
            w.columns=columns;w.values=values
        end
        Lp,Lj,Lx=w.rowptr,w.columns,w.values
    else
        w.rowptr=Int[];w.columns=Int[];w.values=Float64[]
        Lp=Vector{Int}(undef,n+1);Lj=Vector{Int}(undef,lnz);Lx=Vector{Float64}(undef,lnz)
    end
    Lp,Lj,Lx
end
function _hh_extract_parts(F::SparseArrays.UMFPACK.UmfpackLU{Float64,Int64},w::HHExtractWorkspace)
    Int===Int64 || error("Native extraction requires 64-bit workspace indices")
    api=SparseArrays.UMFPACK
    lnz,unz,m,n,_=api.umf_lunz(F)
    m==n || throw(DimensionMismatch("Basis must be square"))
    Lp,Lj,Lx=_hh_extract_buffers!(w,n,lnz)
    length(Lp)==n+1 && length(Lj)==length(Lx)>=lnz || error("Invalid extraction scratch")
    Up=Vector{Int}(undef,n+1);Ui=Vector{Int}(undef,unz);Ux=Vector{Float64}(undef,unz)
    p=Vector{Int}(undef,n);q=similar(p);scaling=Vector{Float64}(undef,n)
    status=api.umfpack_dl_get_numeric(Lp,Lj,Lx,Up,Ui,Ux,p,q,C_NULL,C_NULL,scaling,F.numeric)
    api.umferror(status)
    for i in eachindex(Lp);Lp[i]+=1;end
    for i in 1:lnz;Lj[i]+=1;end
    for a in (Up,Ui,p,q),i in eachindex(a);a[i]+=1;end
    # Convert only live CSR entries, in the same row order as SparseArrays transpose.
    colptr=zeros(Int,n+1)
    for k in 1:lnz;colptr[Lj[k]+1]+=1;end
    colptr[1]=1
    for i in 1:n;colptr[i+1]+=colptr[i];end
    rows=Vector{Int}(undef,lnz);values=Vector{Float64}(undef,lnz)
    for i in 1:n,k in Lp[i]:(Lp[i+1]-1)
        j=Lj[k];slot=colptr[j];colptr[j]+=1;rows[slot]=i;values[slot]=Lx[k]
    end
    for j in n:-1:2;colptr[j]=colptr[j-1];end
    colptr[1]=1
    L=SparseMatrixCSC(n,n,colptr,rows,values)
    L,SparseMatrixCSC(n,n,Up,Ui,Ux),p,q,scaling
end

mutable struct HuangfuHallFactorization{T<:Real,F,R}
    base::HHBase{T}
    updates::Vector{HHUpdate{T}}
    work::Vector{T}
    auxiliary::Vector{T}
    prepared_partial::Vector{T}
    prepared_direction::Vector{T}
    prepared_valid::Bool
    # Private native scratch; extracted L/U and saved copies never alias it.
    refactor_workspace::Union{Nothing,F}
    unit_workspace::HHUnitWorkspace{T}
    shared_update_count::Int
    u_pool::HHPool{T}
    v_pool::HHPool{T}
    extract_workspace::HHExtractWorkspace
end
_backend_dimension(b::HHBase)=length(b.rows)
_backend_storage_count(b::HHBase)=nnz(b.lower)+nnz(b.upper)
sparse_solve_view(::HHBase)=nothing
_factor_storage_count(f::HuangfuHallFactorization)=_backend_storage_count(f.base)+
    sum(t->length(t.u_values)+length(t.v_values),f.updates;init=0)
_factor_growth_reference(::HuangfuHallFactorization{T}) where {T}=one(T)
_factor_growth_measure(f::HuangfuHallFactorization{T}) where {T}=maximum(t->
    max(maximum(abs,t.u_values;init=one(T)),maximum(abs,t.v_values;init=one(T)),abs(inv(t.pivot))),f.updates;init=one(T))
_finite_updated_factor(f::HuangfuHallFactorization)=all(t->isfinite(t.pivot) &&
    all(isfinite,t.u_values) && all(isfinite,t.v_values),f.updates)

function _hh_stored_precision(f::HuangfuHallFactorization{BigFloat})
    base_bits = max(maximum(precision,f.base.lower.nzval;init=2),
        maximum(precision,f.base.upper.nzval;init=2),
        maximum(precision,f.base.scaling;init=2))
    return maximum(t->max(precision(t.pivot),
        maximum(precision,t.u_values;init=2),maximum(precision,t.v_values;init=2)),
        f.updates;init=base_bits)
end

# Match the tested Julia 1.13/aarch64 SparseArrays fused CSC accumulation.
# Exact-product tests gate portability; no abs.(A) sparse matrix copy is needed.
function _hh_abs_mul!(out,A,x)
    fill!(out,0.0)
    @inbounds for j in axes(A,2)
        value=abs(x[j])
        for k in nzrange(A,j)
            i=A.rowval[k];out[i]=fma(abs(A.nzval[k]),value,out[i])
        end
    end
    out
end
function _hh_scale_mode(F,L,U,p,q,scaling,work,auxiliary)
    all(==(1.0),scaling) && return false
    all(x->isfinite(x) && x>0,scaling) || return nothing
    index=firstindex(scaling);largest=abs(log2(scaling[index]))
    for i in eachindex(scaling)
        magnitude=abs(log2(scaling[i]))
        if magnitude>largest;index=i;largest=magnitude;end
    end
    coefficient=scaling[index];n=length(p)
    fill!(work,0.0);work[index]=min(1.0,coefficient)
    rhs_value=work[index]
    ldiv!(auxiliary,F,work)
    all(isfinite,auxiliary) && any(!iszero,auxiliary) || return nothing
    # Only these two short-lived vectors are needed in addition to solve scratch.
    permuted=Vector{Float64}(undef,n);transformed=similar(permuted)
    for i in eachindex(permuted);permuted[i]=auxiliary[q[i]];end
    mul!(work,U,permuted);mul!(transformed,L,work)
    _hh_abs_mul!(work,U,permuted);_hh_abs_mul!(auxiliary,L,work)
    all(isfinite,transformed) && all(isfinite,auxiliary) || return nothing
    target=findfirst(==(index),p)
    multiply,divide=coefficient*rhs_value,rhs_value/coefficient
    function matches(expected)
        isfinite(expected) && expected>0 || return false
        for i in eachindex(transformed)
            reference=i==target ? expected : 0.0
            allowance=64n*eps(Float64)*max(auxiliary[i],abs(reference))
            abs(transformed[i]-reference)<=allowance || return false
        end
        true
    end
    multiplicative,divisive=matches(multiply),matches(divide)
    multiplicative==divisive && return nothing
    divisive
end

function _hh_extract_parts(F::LinearAlgebra.LU{T},::HHExtractWorkspace) where {T}
    n=size(F,1)
    sparse(F.L),sparse(F.U),F.p,collect(1:n),ones(T,n)
end
# Fold the trailing core's row pivots into the sparse L and outer permutation.
# If P*B*Q = Ls*diag(I,C)*Us and Pc*C = Lc*Uc, the full lower-left
# block is Pc*Ls21; the sparse U rows keep their original column coordinates.
function _hh_extract_parts(F::MarkowitzBackend{T},::HHExtractWorkspace) where {T}
    n,k=F.dimension,F.sparse_pivots
    core_order=F.core.p
    core_positions=invperm(core_order)
    rows=copy(F.row_order)
    for i in eachindex(core_order)
        rows[k+i]=F.row_order[k+core_order[i]]
    end
    li,lj,lv=collect(1:n),collect(1:n),ones(T,n)
    ui,uj,uv=Int[],Int[],T[]
    for pivot in 1:k
        push!(ui,pivot);push!(uj,pivot);push!(uv,F.diagonal[pivot])
        lower,upper=F.lower[pivot],F.upper[pivot]
        for j in eachindex(lower.indices)
            row=lower.indices[j]
            row>k && (row=k+core_positions[row-k])
            push!(li,row);push!(lj,pivot);push!(lv,lower.values[j])
        end
        for j in eachindex(upper.indices)
            push!(ui,pivot);push!(uj,upper.indices[j]);push!(uv,upper.values[j])
        end
    end
    # Read the existing dense LU storage, without forming another dense matrix.
    core=F.core.factors
    for j in axes(core,2), i in axes(core,1)
        value=core[i,j]
        iszero(value) && continue
        if i>j
            push!(li,k+i);push!(lj,k+j);push!(lv,value)
        else
            push!(ui,k+i);push!(uj,k+j);push!(uv,value)
        end
    end
    return sparse(li,lj,lv,n,n),sparse(ui,uj,uv,n,n),rows,copy(F.column_order),ones(T,n)
end
_hh_base_scale_mode(F::MarkowitzBackend,args...)=false
_hh_base_scale_mode(F::LinearAlgebra.LU,args...)=false
_hh_base_scale_mode(F::Float64UMFPACK,args...)=_hh_scale_mode(F,args...)

function _hh_extract_base(F,work::Vector{T},auxiliary,extract_workspace=HHExtractWorkspace()) where {T}
    isnothing(F) && return HHBase(spzeros(T,0,0),spzeros(T,0,0),Int[],Int[],Int[],T[],false,[1],Int[])
    L,U,p,q,s=_hh_extract_parts(F,extract_workspace)
    divide=_hh_base_scale_mode(F,L,U,p,q,s,work,auxiliary)
    isnothing(divide) && throw(_UnreliableBasisSolve())
    n=length(p)
    all(i->L.rowval[L.colptr[i]]==i && L.nzval[L.colptr[i]]==one(T) &&
        U.rowval[U.colptr[i+1]-1]==i && isfinite(U.nzval[U.colptr[i+1]-1]) &&
        !iszero(U.nzval[U.colptr[i+1]-1]),1:n) || throw(_UnreliableBasisSolve())
    # Outgoing edges of U's rows; numeric evaluation still uses original CSC order.
    rowptr=zeros(Int,n+1)
    for j in 1:n, k in U.colptr[j]:(U.colptr[j+1]-2)
        rowptr[U.rowval[k]+1]+=1
    end
    rowptr[1]=1
    for i in 1:n;rowptr[i+1]+=rowptr[i];end
    columns=Vector{Int}(undef,rowptr[end]-1);next=copy(rowptr)
    for j in 1:n, k in U.colptr[j]:(U.colptr[j+1]-2)
        i=U.rowval[k];columns[next[i]]=j;next[i]+=1
    end
    HHBase(L,U,p,q,invperm(q),s,divide,rowptr,columns)
end
# Dense native LU preserves every non-Float64 scalar, like the other managers.
_hh_native_lu(B::AbstractMatrix{T}) where {T}=lu!(Matrix{T}(B))
_hh_native_lu(B::AbstractMatrix{Float64})=lu(convert(SparseMatrixCSC{Float64,Int},B))
_hh_initial_lu(B::AbstractMatrix)=_hh_native_lu(B)
_hh_initial_lu(B::AbstractMatrix{Float64})=iszero(size(B,1)) ? nothing : _hh_native_lu(B)
_hh_workspace_type(::Nothing)=Float64UMFPACK
_hh_workspace_type(F)=typeof(F)

_hh_initial_lu(B,::Val{:native})=_hh_initial_lu(B)
_hh_initial_lu(B,::Val{:markowitz})=MarkowitzBackend(B)

function HuangfuHallFactorization(B::AbstractMatrix{T},backend::Val{R}=Val(:native)) where {T<:Real,R}
    _validate_huangfu_hall(T,backend)
    size(B,1)==size(B,2) || throw(DimensionMismatch("Basis must be square"))
    n=size(B,1);F=_hh_initial_lu(B,backend)
    work=zeros(T,n);auxiliary=zeros(T,n);extraction=HHExtractWorkspace()
    HuangfuHallFactorization{T,_hh_workspace_type(F),R}(_hh_extract_base(F,work,auxiliary,extraction),HHUpdate{T}[],work,auxiliary,zeros(T,n),zeros(T,n),false,F,HHUnitWorkspace(n,T),0,HHPool(T),HHPool(T),extraction)
end

function _hh_lower!(x,b::HHBase,transposed::Bool)
    L=b.lower;n=length(x)
    # Extracted L has one explicit unit diagonal in each column.
    nnz(L) == n && n == size(L,1) && return x
    if transposed
        for j in n:-1:1
            value=x[j]
            @inbounds for k in (L.colptr[j]+1):(L.colptr[j+1]-1)
                value-=L.nzval[k]*x[L.rowval[k]]
            end
            x[j]=value
        end
    else
        for j in 1:n
            value=x[j]
            @inbounds for k in (L.colptr[j]+1):(L.colptr[j+1]-1)
                x[L.rowval[k]]-=L.nzval[k]*value
            end
        end
    end
    x
end
function _hh_upper!(x,b::HHBase,transposed::Bool)
    U=b.upper;n=length(x)
    if transposed
        for j in 1:n
            value=x[j];last=U.colptr[j+1]-1
            @inbounds for k in U.colptr[j]:(last-1)
                value-=U.nzval[k]*x[U.rowval[k]]
            end
            x[j]=value/U.nzval[last]
        end
    else
        for j in n:-1:1
            last=U.colptr[j+1]-1;value=x[j]/U.nzval[last];x[j]=value
            @inbounds for k in U.colptr[j]:(last-1)
                x[U.rowval[k]]-=U.nzval[k]*value
            end
        end
    end
    x
end
function _hh_unit_transpose!(f::HuangfuHallFactorization{T},p) where {T}
    w=f.unit_workspace;b=f.base;U=b.upper
    for i in w.indices;w.values[i]=zero(T);w.marked[i]=false;end
    empty!(w.indices);push!(w.indices,p);w.marked[p]=true
    cursor=1
    while cursor<=length(w.indices)
        i=w.indices[cursor];cursor+=1
        for k in b.upper_rowptr[i]:(b.upper_rowptr[i+1]-1)
            j=b.upper_columns[k]
            if !w.marked[j];w.marked[j]=true;push!(w.indices,j);end
        end
    end
    sort!(w.indices)
    for j in w.indices
        value=j==p ? one(T) : zero(T);last=U.colptr[j+1]-1
        @inbounds for k in U.colptr[j]:(last-1)
            value-=U.nzval[k]*w.values[U.rowval[k]]
        end
        w.values[j]=value/U.nzval[last]
    end
    w
end

@inline function _hh_apply!(x,t::HHUpdate{T},transposed::Bool) where {T}
    rows,values=transposed ? (t.u_indices,t.u_values) : (t.v_indices,t.v_values)
    value=zero(T)
    @inbounds for i in eachindex(rows);value+=values[i]*x[rows[i]];end
    value/=t.pivot
    if !iszero(value)
        rows,values=transposed ? (t.v_indices,t.v_values) : (t.u_indices,t.u_values)
        @inbounds for i in eachindex(rows);x[rows[i]]-=value*values[i];end
    end
    x
end
function _hh_dimensions(destination,f,rhs)
    length(destination)==length(rhs)==length(f.work) || throw(DimensionMismatch("Solve dimensions"))
    destination===f.work && throw(ArgumentError("Destination aliases private solve scratch"))
    nothing
end
function _hh_forward!(destination::Vector{T},f::HuangfuHallFactorization{T},rhs,prepare::Bool) where {T}
    _hh_dimensions(destination,f,rhs)
    b=f.base;x=f.work
    source=rhs===x ? copyto!(f.auxiliary,rhs) : rhs
    for i in eachindex(x)
        row=b.rows[i]
        x[i]=b.divide_scaling ? source[row]/b.scaling[row] : source[row]*b.scaling[row]
    end
    _hh_lower!(x,b,false)
    for t in f.updates;_hh_apply!(x,t,false);end
    prepare && copyto!(f.prepared_partial,x)
    _hh_upper!(x,b,false)
    for i in eachindex(x);destination[b.columns[i]]=x[i];end
    if prepare
        copyto!(f.prepared_direction,destination);f.prepared_valid=true
    end
    destination
end
forward_solve!(destination::Vector{T},f::HuangfuHallFactorization{T},rhs::AbstractVector) where {T}=
    _hh_forward!(destination,f,rhs,true)
_ordinary_forward_solve!(destination::Vector{T},f::HuangfuHallFactorization{T},rhs::AbstractVector) where {T}=
    _hh_forward!(destination,f,rhs,false)
forward_solve(f::HuangfuHallFactorization{T},rhs::AbstractVector) where {T}=forward_solve!(zeros(T,length(rhs)),f,rhs)
function _unit_transpose_rhs(f::HuangfuHallFactorization{T}, rhs::Vector{T},
                             row::Int) where {T<:Union{Float32,Float64}}
    checkbounds(rhs, row)
    return _UnitTransposeRHS(rhs, row)
end
function _prepare_transpose_rhs!(f::HuangfuHallFactorization, rhs)
    for i in eachindex(f.work); f.work[i] = rhs[f.base.columns[i]]; end
end
function _prepare_transpose_rhs!(f::HuangfuHallFactorization{T}, rhs::_UnitTransposeRHS{T}) where {T<:Real}
    fill!(f.work, zero(T))
    f.work[f.base.positions[rhs.row]] = one(T)
end
function transpose_solve!(destination::Vector{T},f::HuangfuHallFactorization{T},rhs::AbstractVector) where {T}
    _hh_dimensions(destination,f,rhs)
    b=f.base;x=f.work
    source=rhs===x ? copyto!(f.auxiliary,rhs) : rhs
    _prepare_transpose_rhs!(f,source)
    _hh_upper!(x,b,true)
    for t in Iterators.reverse(f.updates);_hh_apply!(x,t,true);end
    _hh_lower!(x,b,true)
    for i in eachindex(x)
        row=b.rows[i]
        destination[row]=b.divide_scaling ? x[i]/b.scaling[row] : x[i]*b.scaling[row]
    end
    destination
end
transpose_solve(f::HuangfuHallFactorization{T},rhs::AbstractVector) where {T}=transpose_solve!(zeros(T,length(rhs)),f,rhs)

# Count and pack in ascending index order without temporary bit masks.
function _hh_pack_update(u,w::HHUnitWorkspace{T},pivot,u_pool=nothing,v_pool=nothing) where {T}
    nu=0;nv=0;finite=true;v=w.values
    @inbounds @simd for i in eachindex(u)
        finite &= isfinite(u[i]);nu += !iszero(u[i])
    end
    @inbounds for i in w.indices
        finite &= isfinite(v[i]);nv += !iszero(v[i])
    end
    finite || throw(_UnreliableBasisSolve())
    ui,uv=_hh_take_pair!(u_pool,nu,T)
    vi,vv=_hh_take_pair!(v_pool,nv,T)
    ju=0;jv=0
    @inbounds for i in eachindex(u)
        if !iszero(u[i]);ju+=1;ui[ju]=i;uv[ju]=u[i];end
    end
    @inbounds for i in w.indices
        if !iszero(v[i]);jv+=1;vi[jv]=i;vv[jv]=v[i];end
    end
    HHUpdate(ui,uv,vi,vv,pivot)
end

# Hardware vectors allow independent finite/equality predicates in one pass.
# Generic inputs keep their original validation and comparison order.
_hh_direction_status(direction, prepared, valid) = (all(isfinite, direction), nothing)
function _hh_direction_status(direction::Vector{T},prepared::Vector{T},valid::Bool) where {T<:Union{Float32,Float64}}
    valid && length(direction) == length(prepared) || return (all(isfinite,direction),false)
    finite = true
    matched = true
    count = length(direction)
    first_index = 1
    # Stop comparing prepared values after the first mismatching block, while
    # still validating every remaining direction entry before pivot handling.
    while first_index <= count
        last_index = min(first_index + 127, count)
        @inbounds @simd for index in first_index:last_index
            value = direction[index]
            finite &= isfinite(value)
            matched &= isequal(value,prepared[index])
        end
        if !matched
            @inbounds @simd for index in (last_index+1):count
                finite &= isfinite(direction[index])
            end
            return finite,false
        end
        first_index = last_index+1
    end
    return finite,matched
end

function replace_column!(f::HuangfuHallFactorization{T},direction::AbstractVector,pivot_row::Integer;
                         zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                             _positive_tolerance(T,1//10^12)) where {T}
    tolerance=convert(T,zero_tolerance)
    isfinite(tolerance) && tolerance>=zero(T) || throw(ArgumentError("Invalid pivot tolerance"))
    n=length(f.work);length(direction)==n || throw(DimensionMismatch("Update dimensions"))
    checkbounds(direction,pivot_row)
    finite,prepared = _hh_direction_status(direction,f.prepared_direction,f.prepared_valid)
    finite || throw(ArgumentError("Nonfinite direction"))
    mu=convert(T,direction[pivot_row]);_pivot_magnitude(mu)>tolerance || throw(LinearAlgebra.ZeroPivotException(pivot_row))
    b=f.base;p=b.positions[pivot_row];u=f.auxiliary;v=f.work
    if isnothing(prepared) ? f.prepared_valid && isequal(direction,f.prepared_direction) : prepared
        copyto!(u,f.prepared_partial)
    else
        # Interface fallback for independently corrected or supplied directions.
        # U*d is the same partial direction in the current middle coordinates.
        for i in 1:n;v[i]=direction[b.columns[i]];end
        mul!(u,b.upper,v)
    end
    for k in nzrange(b.upper,p);u[b.upper.rowval[k]]-=b.upper.nzval[k];end
    unit=_hh_unit_transpose!(f,p)
    candidate=_hh_pack_update(u,unit,mu,f.u_pool,f.v_pool)
    push!(f.updates,candidate)
    f.prepared_valid=false
    f
end
_hh_refactor_lu!(F::Float64UMFPACK,B)=
    lu!(F,convert(SparseMatrixCSC{Float64,Int},B);reuse_symbolic=false)
_hh_refactor_lu!(F::LinearAlgebra.LU,B)=_hh_native_lu(B)

function _hh_refactor_backend(F,B,::Val{:native})
    size(B,1)==0 && return nothing
    (isnothing(F) || size(F)!=size(B)) && return _hh_native_lu(B)
    return _hh_refactor_lu!(F,B)
end
_hh_refactor_backend(F,B,::Val{:markowitz}) =
    isnothing(F) ? MarkowitzBackend(B) : _refactorize_backend(F,B)

function refactorize!(f::HuangfuHallFactorization{T,FType,R},B::AbstractMatrix{T}) where {T,FType,R}
    size(B,1)==size(B,2) || throw(DimensionMismatch("Basis must be square"))
    n=size(B,1);F=f.refactor_workspace
    local base
    try
        # Extracted L/U own their storage; failed backend construction cannot
        # damage the active factors or copies. Preserve backend choice on retry.
        F=_hh_refactor_backend(F,B,Val(R))
        # Borrow only disposable solve scratch, never the prepared direction.
        work=length(f.work)==n ? f.work : zeros(T,n)
        auxiliary=length(f.auxiliary)==n ? f.auxiliary : zeros(T,n)
        base=_hh_extract_base(F,work,auxiliary,f.extract_workspace)
    catch
        f.refactor_workspace=nothing
        rethrow()
    end
    # Retire only the private suffix, and only after the candidate LU is valid.
    if length(f.work)==n
        for k in (f.shared_update_count+1):length(f.updates)
            t=f.updates[k]
            _hh_retire_pair!(f.u_pool,t.u_indices,t.u_values)
            _hh_retire_pair!(f.v_pool,t.v_indices,t.v_values)
        end
    else
        empty!(f.u_pool.pairs);f.u_pool.entries=0
        empty!(f.v_pool.pairs);f.v_pool.entries=0
    end
    n==0 && (f.extract_workspace=HHExtractWorkspace())
    f.shared_update_count=0
    f.base=base;f.refactor_workspace=F
    for scratch in (f.work,f.auxiliary,f.prepared_partial,f.prepared_direction)
        resize!(scratch,n)
    end
    if length(f.unit_workspace.values)!=n
        f.unit_workspace=HHUnitWorkspace(n,T)
    end
    empty!(f.updates);f.prepared_valid=false
    f
end
function copy_basis_factorization(f::HuangfuHallFactorization{T,F,R}) where {T,F,R}
    n=length(f.work)
    f.shared_update_count=length(f.updates)
    HuangfuHallFactorization{T,F,R}(f.base,copy(f.updates),zeros(T,n),zeros(T,n),zeros(T,n),zeros(T,n),false,nothing,HHUnitWorkspace(n,T),length(f.updates),HHPool(T),HHPool(T),HHExtractWorkspace())
end

# Keep unsupported combinations explicit even for internal factory callers.
function _basis_factorization(B::AbstractMatrix{T}, ::Val{:huangfu_hall},
                              ::Val{R}) where {T,R}
    _validate_huangfu_hall(T, Val(R))
    return HuangfuHallFactorization(B,Val(R))
end
_basis_factorization(B, mode::Val{:huangfu_hall}) =
    _basis_factorization(B, mode, Val(:native))

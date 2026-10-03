# Middle product form (Huangfu--Hall, ERGO-13-001, section 3.1.2).
# In native scaled/permuted coordinates: P*S*B*Q = L*T1*...*Tk*U.
# Factors and live/shared update records are immutable; private retired arrays may be reused.
struct HHBase
    lower::SparseMatrixCSC{Float64,Int}
    upper::SparseMatrixCSC{Float64,Int}
    rows::Vector{Int}
    columns::Vector{Int}
    positions::Vector{Int}
    scaling::Vector{Float64}
    divide_scaling::Bool
    upper_rowptr::Vector{Int}
    upper_columns::Vector{Int}
end
struct HHUpdate
    u_indices::Vector{Int}
    u_values::Vector{Float64}
    v_indices::Vector{Int}
    v_values::Vector{Float64}
    pivot::Float64
end
# Each pool retains at most 4 MiB of index/value payload and 256 array pairs.
# Exact-length reuse avoids hidden oversized vector capacity and resize overhead.
mutable struct HHPool
    pairs::Vector{Tuple{Vector{Int},Vector{Float64}}}
    entries::Int
end
HHPool()=HHPool(Tuple{Vector{Int},Vector{Float64}}[],0)
function _hh_retire_pair!(pool::HHPool,indices,values)
    n=length(indices)
    if length(pool.pairs)<256 && pool.entries+n<=262144
        push!(pool.pairs,(indices,values));pool.entries+=n
    end
    nothing
end
_hh_take_pair!(::Nothing,n)=(Vector{Int}(undef,n),Vector{Float64}(undef,n))
function _hh_take_pair!(pool::HHPool,n)
    for i in length(pool.pairs):-1:1
        pair=pool.pairs[i]
        if length(pair[1])==n
            pool.pairs[i]=pool.pairs[end];pop!(pool.pairs);pool.entries-=n
            return pair
        end
    end
    _hh_take_pair!(nothing,n)
end

struct HHUnitWorkspace
    values::Vector{Float64}
    marked::BitVector
    indices::Vector{Int}
end
HHUnitWorkspace(n)=HHUnitWorkspace(zeros(n),falses(n),Int[])

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

mutable struct HuangfuHallFactorization
    base::HHBase
    updates::Vector{HHUpdate}
    work::Vector{Float64}
    auxiliary::Vector{Float64}
    prepared_partial::Vector{Float64}
    prepared_direction::Vector{Float64}
    prepared_valid::Bool
    # Private native scratch; extracted L/U and saved copies never alias it.
    refactor_workspace::Union{Nothing,Float64UMFPACK}
    unit_workspace::HHUnitWorkspace
    shared_update_count::Int
    u_pool::HHPool
    v_pool::HHPool
    extract_workspace::HHExtractWorkspace
end
_backend_dimension(b::HHBase)=length(b.rows)
_backend_storage_count(b::HHBase)=nnz(b.lower)+nnz(b.upper)
sparse_solve_view(::HHBase)=nothing
_factor_storage_count(f::HuangfuHallFactorization)=_backend_storage_count(f.base)+
    sum(t->length(t.u_values)+length(t.v_values),f.updates;init=0)
_factor_growth_reference(::HuangfuHallFactorization)=1.0
_factor_growth_measure(f::HuangfuHallFactorization)=maximum(t->
    max(maximum(abs,t.u_values;init=1.0),maximum(abs,t.v_values;init=1.0),abs(inv(t.pivot))),f.updates;init=1.0)
_finite_updated_factor(f::HuangfuHallFactorization)=all(t->isfinite(t.pivot) &&
    all(isfinite,t.u_values) && all(isfinite,t.v_values),f.updates)

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

function _hh_extract_base(F,work,auxiliary,extract_workspace=HHExtractWorkspace())
    isnothing(F) && return HHBase(spzeros(0,0),spzeros(0,0),Int[],Int[],Int[],Float64[],false,[1],Int[])
    L,U,p,q,s=_hh_extract_parts(F,extract_workspace)
    divide=_hh_scale_mode(F,L,U,p,q,s,work,auxiliary)
    isnothing(divide) && throw(_UnreliableBasisSolve())
    n=length(p)
    all(i->L.rowval[L.colptr[i]]==i && L.nzval[L.colptr[i]]==1.0 &&
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
function HuangfuHallFactorization(B::AbstractMatrix{Float64})
    size(B,1)==size(B,2) || throw(DimensionMismatch("Basis must be square"))
    n=size(B,1);F=n==0 ? nothing : lu(convert(SparseMatrixCSC{Float64,Int}, B))
    work=zeros(n);auxiliary=zeros(n);extraction=HHExtractWorkspace()
    HuangfuHallFactorization(_hh_extract_base(F,work,auxiliary,extraction),HHUpdate[],work,auxiliary,zeros(n),zeros(n),false,F,HHUnitWorkspace(n),0,HHPool(),HHPool(),extraction)
end

function _hh_lower!(x,b::HHBase,transposed::Bool)
    L=b.lower;n=length(x)
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
function _hh_unit_transpose!(f,p)
    w=f.unit_workspace;b=f.base;U=b.upper
    for i in w.indices;w.values[i]=0.0;w.marked[i]=false;end
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
        value=j==p ? 1.0 : 0.0;last=U.colptr[j+1]-1
        @inbounds for k in U.colptr[j]:(last-1)
            value-=U.nzval[k]*w.values[U.rowval[k]]
        end
        w.values[j]=value/U.nzval[last]
    end
    w
end

@inline function _hh_apply!(x,t::HHUpdate,transposed::Bool)
    rows,values=transposed ? (t.u_indices,t.u_values) : (t.v_indices,t.v_values)
    value=0.0
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
function _hh_forward!(destination::Vector{Float64},f::HuangfuHallFactorization,rhs,prepare::Bool)
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
forward_solve!(destination::Vector{Float64},f::HuangfuHallFactorization,rhs::AbstractVector)=
    _hh_forward!(destination,f,rhs,true)
_ordinary_forward_solve!(destination::Vector{Float64},f::HuangfuHallFactorization,rhs::AbstractVector)=
    _hh_forward!(destination,f,rhs,false)
forward_solve(f::HuangfuHallFactorization,rhs::AbstractVector)=forward_solve!(zeros(length(rhs)),f,rhs)
function transpose_solve!(destination::Vector{Float64},f::HuangfuHallFactorization,rhs::AbstractVector)
    _hh_dimensions(destination,f,rhs)
    b=f.base;x=f.work
    source=rhs===x ? copyto!(f.auxiliary,rhs) : rhs
    for i in eachindex(x);x[i]=source[b.columns[i]];end
    _hh_upper!(x,b,true)
    for t in Iterators.reverse(f.updates);_hh_apply!(x,t,true);end
    _hh_lower!(x,b,true)
    for i in eachindex(x)
        row=b.rows[i]
        destination[row]=b.divide_scaling ? x[i]/b.scaling[row] : x[i]*b.scaling[row]
    end
    destination
end
transpose_solve(f::HuangfuHallFactorization,rhs::AbstractVector)=transpose_solve!(zeros(length(rhs)),f,rhs)

# Count and pack in ascending index order without temporary bit masks.
function _hh_pack_update(u,w::HHUnitWorkspace,pivot,u_pool=nothing,v_pool=nothing)
    nu=0;nv=0;finite=true;v=w.values
    @inbounds @simd for i in eachindex(u)
        finite &= isfinite(u[i]);nu += !iszero(u[i])
    end
    @inbounds for i in w.indices
        finite &= isfinite(v[i]);nv += !iszero(v[i])
    end
    finite || throw(_UnreliableBasisSolve())
    ui,uv=_hh_take_pair!(u_pool,nu)
    vi,vv=_hh_take_pair!(v_pool,nv)
    ju=0;jv=0
    @inbounds for i in eachindex(u)
        if !iszero(u[i]);ju+=1;ui[ju]=i;uv[ju]=u[i];end
    end
    @inbounds for i in w.indices
        if !iszero(v[i]);jv+=1;vi[jv]=i;vv[jv]=v[i];end
    end
    HHUpdate(ui,uv,vi,vv,pivot)
end

function replace_column!(f::HuangfuHallFactorization,direction::AbstractVector,pivot_row::Integer;
                         zero_tolerance::Real=1e-12)
    isfinite(zero_tolerance) && zero_tolerance>=0 || throw(ArgumentError("Invalid pivot tolerance"))
    n=length(f.work);length(direction)==n || throw(DimensionMismatch("Update dimensions"))
    checkbounds(direction,pivot_row)
    all(isfinite,direction) || throw(ArgumentError("Nonfinite direction"))
    mu=Float64(direction[pivot_row]);abs(mu)>zero_tolerance || throw(LinearAlgebra.ZeroPivotException(pivot_row))
    b=f.base;p=b.positions[pivot_row];u=f.auxiliary;v=f.work
    if f.prepared_valid && isequal(direction,f.prepared_direction)
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
function refactorize!(f::HuangfuHallFactorization,B::AbstractMatrix{Float64})
    size(B,1)==size(B,2) || throw(DimensionMismatch("Basis must be square"))
    n=size(B,1);F=f.refactor_workspace
    local base
    try
        if n==0
            F=nothing
        elseif isnothing(F) || size(F)!=size(B)
            F=lu(convert(SparseMatrixCSC{Float64,Int}, B))
        else
            # Repeat symbolic analysis as in fresh LU; only reuse native workspace.
            # A failed candidate cannot damage the independent active L/U.
            lu!(F,convert(SparseMatrixCSC{Float64,Int}, B);reuse_symbolic=false)
        end
        # Borrow only disposable solve scratch, never the prepared direction.
        work=length(f.work)==n ? f.work : zeros(n)
        auxiliary=length(f.auxiliary)==n ? f.auxiliary : zeros(n)
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
        f.unit_workspace=HHUnitWorkspace(n)
    end
    empty!(f.updates);f.prepared_valid=false
    f
end
function copy_basis_factorization(f::HuangfuHallFactorization)
    n=length(f.work)
    f.shared_update_count=length(f.updates)
    HuangfuHallFactorization(f.base,copy(f.updates),zeros(n),zeros(n),zeros(n),zeros(n),false,nothing,HHUnitWorkspace(n),length(f.updates),HHPool(),HHPool(),HHExtractWorkspace())
end

# Keep unsupported combinations explicit even for internal factory callers.
function _basis_factorization(B::AbstractMatrix{T}, ::Val{:huangfu_hall},
                              ::Val{R}) where {T,R}
    _validate_huangfu_hall(T, Val(R))
    return HuangfuHallFactorization(B)
end
_basis_factorization(B, mode::Val{:huangfu_hall}) =
    _basis_factorization(B, mode, Val(:native))

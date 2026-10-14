# Candidate only. P*S*B*Q=L*U; lower backend represents inv(S)*P'*L*D.
# Direct native solves do NOT retain UMFPACK combined-solve refinement.
struct DirectLowerBackend{R,F}
    lower::SparseMatrixCSC{Float64,Int}
    row_order::Vector{Int}
    scaling::Vector{Float64}
    divide_scaling::Bool
    diagonal::Union{Nothing,Vector{Float64}}
    normalize_requested::Bool
    fallback::Union{Nothing,F}
    work::Vector{Float64}
end
_direct_requested_backend(::DirectLowerBackend{R}) where {R}=R
_backend_dimension(b::DirectLowerBackend)=isnothing(b.fallback) ? length(b.work) : _backend_dimension(b.fallback)
_backend_storage_count(b::DirectLowerBackend)=isnothing(b.fallback) ?
    nnz(b.lower)+(isnothing(b.diagonal) ? 0 : length(b.diagonal)) : _backend_storage_count(b.fallback)
sparse_solve_view(::DirectLowerBackend)=nothing
function _copy_backend(b::DirectLowerBackend{R,F}) where {R,F}
    # Extracted lower values/permutations/scaling/D are read-only. No upper data here.
    fallback=isnothing(b.fallback) ? nothing : _copy_backend(b.fallback)
    return DirectLowerBackend{R,F}(b.lower,b.row_order,b.scaling,b.divide_scaling,
        b.diagonal,b.normalize_requested,fallback,similar(b.work))
end

function _backend_forward_solve!(destination::Vector,b::DirectLowerBackend,rhs::AbstractVector)
    isnothing(b.fallback) || return _backend_forward_solve!(destination,b.fallback,rhs)
    L,D=b.lower,b.diagonal
    if !isnothing(D) && nnz(L)==length(destination)
        for row in eachindex(destination)
            original=b.row_order[row]
            value=b.divide_scaling ? rhs[original]/b.scaling[original] : rhs[original]*b.scaling[original]
            destination[row]=value/D[row]
        end
        return destination
    end
    for row in eachindex(destination)
        original=b.row_order[row]
        destination[row]=b.divide_scaling ? rhs[original]/b.scaling[original] : rhs[original]*b.scaling[original]
    end
    for col in eachindex(destination)
        value=destination[col]
        @inbounds for slot in (L.colptr[col]+1):(L.colptr[col+1]-1)
            destination[L.rowval[slot]]-=L.nzval[slot]*value
        end
    end
    if !isnothing(D)
        for row in eachindex(destination); destination[row]/=D[row]; end
    end
    return destination
end
function _backend_transpose_solve!(destination::Vector,b::DirectLowerBackend,rhs::AbstractVector)
    isnothing(b.fallback) || return _backend_transpose_solve!(destination,b.fallback,rhs)
    L,D,work=b.lower,b.diagonal,b.work
    if isnothing(D)
        copyto!(work,rhs)
    else
        for row in eachindex(work); work[row]=rhs[row]/D[row]; end
    end
    # Canonical L has one explicit unit diagonal first in each column.
    if nnz(L)!=length(work)
        for col in reverse(eachindex(work))
            value=work[col]
            @inbounds for slot in (L.colptr[col]+1):(L.colptr[col+1]-1)
                value-=L.nzval[slot]*work[L.rowval[slot]]
            end
            work[col]=value
        end
    end
    for row in eachindex(work)
        original=b.row_order[row]
        destination[original]=b.divide_scaling ? work[row]/b.scaling[original] : work[row]*b.scaling[original]
    end
    return destination
end

# Validate every new value before changing the owned upper coefficient buffer.
function _direct_normalize_upper!(U::SparseMatrixCSC{Float64,Int})
    n=size(U,1);D=Vector{Float64}(undef,n)
    for col in 1:n
        D[col]=U[col,col]
        isfinite(D[col]) && !iszero(D[col]) || return nothing
    end
    values=similar(U.nzval)
    for slot in eachindex(values)
        old=U.nzval[slot];value=old/D[U.rowval[slot]]
        (!isfinite(value) || (!iszero(old) && iszero(value))) && return nothing
        values[slot]=value
    end
    copyto!(U.nzval,values)
    return D
end

function _direct_packed_upper(U,::Type{F}) where {F}
    n=size(U,1)
    if F===BartelsGolubFactorization
        order=UpperRowOrder(n)
        return [PackedUpperColumn{Float64}(UpperRowIndices(copy(@view U.rowval[nzrange(U,j)]),order),
                copy(@view U.nzval[nzrange(U,j)])) for j in 1:n]
    end
    return [PackedUpperColumn{Float64}(copy(@view U.rowval[nzrange(U,j)]),
            copy(@view U.nzval[nzrange(U,j)])) for j in 1:n]
end
function _init_direct_manager(::Type{ForrestTomlinFactorization},base,upper,q)
    n=_backend_dimension(base)
    return ForrestTomlinFactorization{Float64,typeof(base)}(base,upper,q,invperm(q),
        ForrestTomlinUpdate{Float64}[],zeros(n),zeros(n),Vector{Int}[],
        ForrestTomlinUpdate{Float64}[],0,nothing,TriangularRowCache(Float64,n))
end
function _init_direct_manager(::Type{SuhlSuhlFactorization},base,upper,q)
    n=_backend_dimension(base)
    return SuhlSuhlFactorization{Float64,typeof(base)}(base,upper,q,invperm(q),
        SuhlSuhlUpdate{Float64}[],zeros(n),zeros(n),Vector{Int}[],
        SuhlSuhlUpdate{Float64}[],0,nothing,TriangularRowCache(Float64,n))
end
function _init_direct_manager(::Type{BartelsGolubFactorization},base,upper,q)
    n=_backend_dimension(base)
    return BartelsGolubFactorization{Float64,typeof(base)}(base,upper,q,invperm(q),
        BartelsGolubUpdate{Float64}[],zeros(n),zeros(n),[Int[] for _ in 1:n],Int[],
        BartelsGolubUpdate{Float64}[],0,nothing,TriangularRowCache(Float64,n),false)
end

function _direct_lu_factor_with_exporter(Factor,B::AbstractMatrix{Float64},backend::Val{R},
                                         exporter;normalize::Bool=true) where {R}
    Factor in (ForrestTomlinFactorization,SuhlSuhlFactorization,BartelsGolubFactorization) ||
        throw(ArgumentError("Unsupported direct LU manager"))
    R in (:native,:markowitz) || throw(ArgumentError("Unsupported direct LU backend"))
    ordinary=_factorize_basis(B,backend) # Exactly one factorization.
    parts=exporter(ordinary)
    F=typeof(ordinary)
    if isnothing(parts)
        n=_backend_dimension(ordinary)
        base=DirectLowerBackend{R,F}(spzeros(0,0),Int[],Float64[],false,nothing,
                                    normalize,ordinary,Float64[])
        upper=Factor===BartelsGolubFactorization ? _identity_upper(Float64,n,Val(:stable)) : _identity_upper(Float64,n)
        return _init_direct_manager(Factor,base,upper,collect(1:n))
    end
    D=normalize ? _direct_normalize_upper!(parts.upper) : nothing
    base=DirectLowerBackend{R,F}(parts.lower,parts.rows,parts.scaling,parts.divide_scaling,
                                D,normalize,nothing,zeros(length(parts.rows)))
    upper=_direct_packed_upper(parts.upper,Factor)
    # q is owned by the export and transferred; temporary CSC U and ordinary
    # backend/workspace are not retained by the constructed manager.
    return _init_direct_manager(Factor,base,upper,parts.columns)
end
_direct_lu_factor(Factor,B::AbstractMatrix{Float64},backend::Val;normalize::Bool=true)=
    _direct_lu_factor_with_exporter(Factor,B,backend,_export_basis_lu;normalize)
_direct_lu_factor(Factor,B::AbstractMatrix{T},backend::Val;normalize::Bool=true) where {T<:Real}=
    Factor(B,backend)

const DirectLUFactor=Union{ForrestTomlinFactorization{Float64,<:DirectLowerBackend},
    SuhlSuhlFactorization{Float64,<:DirectLowerBackend},BartelsGolubFactorization{Float64,<:DirectLowerBackend}}
_direct_mode(f::DirectLUFactor)=!isnothing(f.base.fallback) ? :fallback :
    isnothing(f.base.diagonal) ? :direct : :normalized
function _direct_refactorize_with_exporter!(f::DirectLUFactor,B::AbstractMatrix{Float64},exporter)
    Factor=getfield(@__MODULE__,nameof(typeof(f)))
    candidate=_direct_lu_factor_with_exporter(Factor,B,Val(_direct_requested_backend(f.base)),
                                            exporter;normalize=f.base.normalize_requested)
    typeof(candidate)===typeof(f) || throw(ArgumentError("Direct refactorization type changed"))
    # All potentially throwing construction has finished; concrete fields match.
    for name in fieldnames(typeof(f));setfield!(f,name,getfield(candidate,name));end
    return f
end
refactorize!(f::DirectLUFactor,B::AbstractMatrix{Float64})=
    _direct_refactorize_with_exporter!(f,B,_export_basis_lu)

# Candidate only: included in an ordinary isolated JSimplex source overlay.
# No production dispatch replacement. Float64 leaves are immutable values.
struct BasisLUExport
    lower::SparseMatrixCSC{Float64,Int}
    upper::SparseMatrixCSC{Float64,Int}
    rows::Vector{Int}
    columns::Vector{Int}
    scaling::Vector{Float64}
    divide_scaling::Bool
end

function _check_export_permutation(p::Vector{Int},n::Int,seen::BitVector)
    length(p)==n || throw(ArgumentError("Export permutation dimension"))
    fill!(seen,false)
    for row in p
        1<=row<=n || throw(ArgumentError("Export permutation range"))
        seen[row] && throw(ArgumentError("Duplicate export permutation entry"))
        seen[row]=true
    end
    return nothing
end

function _check_export_triangle(A::SparseMatrixCSC{Float64,Int},n::Int,lower::Bool)
    size(A)==(n,n) || throw(ArgumentError("Export factor dimension"))
    length(A.colptr)==n+1 && length(A.rowval)==length(A.nzval) ||
        throw(ArgumentError("Export CSC storage"))
    A.colptr[1]==1 && A.colptr[end]==length(A.nzval)+1 ||
        throw(ArgumentError("Export CSC endpoints"))
    for col in 1:n
        first,last=A.colptr[col],A.colptr[col+1]-1
        1<=first<=last+1<=length(A.nzval)+1 || throw(ArgumentError("Export CSC pointers"))
        previous=0; diagonal=false
        for slot in first:last
            row,value=A.rowval[slot],A.nzval[slot]
            previous<row<=n || throw(ArgumentError("Export CSC row ordering"))
            (lower ? row>=col : row<=col) || throw(ArgumentError("Export triangular structure"))
            isfinite(value) || throw(ArgumentError("Nonfinite export coefficient"))
            if row==col
                (lower ? value==1.0 : !iszero(value)) || throw(ArgumentError("Export diagonal"))
                diagonal=true
            end
            previous=row
        end
        diagonal || throw(ArgumentError("Missing export diagonal"))
    end
    return nothing
end

function _checked_basis_lu(L::SparseMatrixCSC{Float64,Int},U::SparseMatrixCSC{Float64,Int},
                           p::Vector{Int},q::Vector{Int},scaling::Vector{Float64},divide::Bool)
    n=size(L,1)
    _check_export_triangle(L,n,true)
    _check_export_triangle(U,n,false)
    seen=falses(n)
    _check_export_permutation(p,n,seen)
    _check_export_permutation(q,n,seen)
    length(scaling)==n && all(s->isfinite(s) && s>0.0,scaling) ||
        throw(ArgumentError("Export scaling"))
    return BasisLUExport(L,U,p,q,scaling,divide)
end

_export_basis_lu(backend)=nothing
function _export_basis_lu(backend::UMFPACKBackend)
    F=backend.factorization
    if isnothing(F)
        backend.dimension==0 || throw(ArgumentError("Missing nonempty native factor"))
        return _checked_basis_lu(spzeros(0,0),spzeros(0,0),Int[],Int[],Float64[],false)
    end
    issuccess(F) || throw(LinearAlgebra.SingularException(0))
    L,U,p,q,s=_hh_extract_parts(F,HHExtractWorkspace())
    # Validate once, before the orientation helper traverses the extracted data.
    _checked_basis_lu(L,U,p,q,s,false)
    work=Vector{Float64}(undef,length(p)); auxiliary=similar(work)
    divide=_hh_scale_mode(F,L,U,p,q,s,work,auxiliary)
    isnothing(divide) && return nothing
    return BasisLUExport(L,U,p,q,s,divide)
end
function _export_basis_lu(backend::MarkowitzBackend{Float64})
    L,U,p,q,s=_hh_extract_parts(backend,HHExtractWorkspace())
    return _checked_basis_lu(L,U,p,q,s,false)
end

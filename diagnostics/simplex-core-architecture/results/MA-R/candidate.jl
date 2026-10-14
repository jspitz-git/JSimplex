# UNEXECUTED. Include into MADenseProbe with Base.include after reference.jl.
# Stdlib-derived loops below: Julia MIT license in JULIA-LICENSE.md.
# No methods are added to Base, LinearAlgebra or JSimplex.
function _dense_ma_eligible(dest, backend, rhs)::Bool
    dest isa Vector{BigFloat} && rhs isa Vector{BigFloat} || return false
    backend isa DenseLUBackend{BigFloat,LU{BigFloat,Matrix{BigFloat},Vector{Int}}} || return false
    n = size(backend.factorization, 1)
    n >= 16 && size(backend.factorization, 2) == n && length(dest) == n && length(rhs) == n || return false
    return Base.MPFR.rounding_raw(BigFloat) == Base.MPFR.ROUNDING_MODE[]
end
@inline _dense_ma_mul!(product::BigFloat, a::BigFloat, b::BigFloat) =
    MA.operate_to!(product, *, a, b)

function candidate_forward!(dest, backend, rhs)
    _dense_ma_eligible(dest, backend, rhs) || return reference_forward!(dest, backend, rhs)
    product = BigFloat()
    require_one_based_indexing(dest, rhs)
    _ma_lu_forward!(backend.factorization, copyto!(dest, rhs), product)
    return dest
end
function candidate_transpose!(dest, backend, rhs)
    _dense_ma_eligible(dest, backend, rhs) || return reference_transpose!(dest, backend, rhs)
    product = BigFloat()
    require_one_based_indexing(dest, rhs)
    _ma_lu_transpose!(transpose(backend.factorization), copyto!(dest, rhs), product)
    return dest
end

_ma_apply_ma_ipiv_rows!(A::LU, B::AbstractVecOrMat) = _ma_ipiv_rows!(A, 1 : length(A.ipiv), B)
_ma_inverse_ma_ipiv_rows!(A::LU, B::AbstractVecOrMat) = _ma_ipiv_rows!(A, length(A.ipiv) : -1 : 1, B)

function _ma_ipiv_rows!(A::LU, order::OrdinalRange, B::AbstractVecOrMat)
    for i = order
        if i != A.ipiv[i]
            _ma_swap_rows!(B, i, A.ipiv[i])
        end
    end
    B
end

function _ma_swap_rows!(B::AbstractVector, i::Integer, j::Integer)
    B[i], B[j] = B[j], B[i]
    B
end

function _ma_lu_forward!(A::LU, B::AbstractVecOrMat, product::BigFloat)
    _ma_apply_ma_ipiv_rows!(A, B)
    _ma_triangular!(UpperTriangular(A.factors), _ma_triangular!(UnitLowerTriangular(A.factors), B, product), product)
end

function _ma_lu_transpose!(transA::LA.TransposeFactorization{<:Any,<:LU}, B::AbstractVecOrMat, product::BigFloat)
    A = transA.parent
    _ma_triangular!(transpose(UnitLowerTriangular(A.factors)), _ma_triangular!(transpose(UpperTriangular(A.factors)), B, product), product)
    _ma_inverse_ma_ipiv_rows!(A, B)
end

function _ma_triangular!(A::LA.AbstractTriangular, B::AbstractVecOrMat, product::BigFloat)
    if istriu(A)
        _ma_ldiv!(B, LA.uppertriangular(A), B, product)
    else
        _ma_ldiv!(B, LA.lowertriangular(A), B, product)
    end
end

_ma_ldiv!(C::AbstractVecOrMat, A::LA.UpperOrLowerTriangular, B::AbstractVecOrMat, product::BigFloat) =
    _ma_generic_trimatdiv!(C, LA.uplo_char(A), LA.isunit_char(A), LA._wrapperop(parent(A)), LA._unwrap_at(parent(A)), B, product)

function _ma_generic_trimatdiv!(C::AbstractVecOrMat, uploc, isunitc, tfun::Function, A::AbstractMatrix, B::AbstractVecOrMat, product::BigFloat)
    require_one_based_indexing(C, A, B)
    mA, nA = size(A)
    m = size(B, 1)
    if nA != m
        throw(DimensionMismatch(lazy"second dimension of left hand side A, $nA, and first dimension of right hand side B, $m, must be equal"))
    end
    if size(C) != size(B)
        throw(DimensionMismatch(lazy"size of output, $(size(C)), does not match size of right hand side, $(size(B))"))
    end
    iszero(mA) && return C
    oA = oneunit(eltype(A))
    @inbounds if uploc == 'U'
        if isunitc == 'N'
            if tfun === identity
                for k in axes(B,2)
                    amm = A[m,m]
                    iszero(amm) && throw(SingularException(m))
                    Cm = C[m,k] = amm \ B[m,k]
                    # fill C-column
                    for i in reverse(axes(B,1))[2:end]
                        C[i,k] = oA \ B[i,k] - _dense_ma_mul!(product, _ustrip(A[i,m]), Cm)
                    end
                    for j in reverse(axes(B,1))[2:end]
                        ajj = A[j,j]
                        iszero(ajj) && throw(SingularException(j))
                        Cj = C[j,k] = _ustrip(ajj) \ C[j,k]
                        for i in j-1:-1:firstindex(B,1)
                            C[i,k] -= _dense_ma_mul!(product, _ustrip(A[i,j]), Cj)
                        end
                    end
                end
            else # tfun in (adjoint, transpose)
                for k in axes(B,2)
                    for j in axes(B,1)
                        ajj = A[j,j]
                        iszero(ajj) && throw(SingularException(j))
                        Bj = B[j,k]
                        for i in firstindex(A,1):j-1
                            Bj -= _dense_ma_mul!(product, tfun(A[i,j]), C[i,k])
                        end
                        C[j,k] = tfun(ajj) \ Bj
                    end
                end
            end
        else # isunitc == 'U'
            if tfun === identity
                for k in axes(B,2)
                    Cm = C[m,k] = oA \ B[m,k]
                    # fill C-column
                    for i in reverse(axes(B,1))[2:end]
                        C[i,k] = oA \ B[i,k] - _dense_ma_mul!(product, _ustrip(A[i,m]), Cm)
                    end
                    for j in reverse(axes(B,1))[2:end]
                        Cj = C[j,k]
                        for i in firstindex(A,1):j-1
                            C[i,k] -= _dense_ma_mul!(product, _ustrip(A[i,j]), Cj)
                        end
                    end
                end
            else # tfun in (adjoint, transpose)
                for k in axes(B,2)
                    for j in axes(B,1)
                        Bj = B[j,k]
                        for i in firstindex(A,1):j-1
                            Bj -= _dense_ma_mul!(product, tfun(A[i,j]), C[i,k])
                        end
                        C[j,k] = oA \ Bj
                    end
                end
            end
        end
    else # uploc == 'L'
        if isunitc == 'N'
            if tfun === identity
                for k in axes(B,2)
                    a11 = A[1,1]
                    iszero(a11) && throw(SingularException(1))
                    C1 = C[1,k] = a11 \ B[1,k]
                    # fill C-column
                    for i in axes(B,1)[2:end]
                        C[i,k] = oA \ B[i,k] - _dense_ma_mul!(product, _ustrip(A[i,1]), C1)
                    end
                    for j in axes(B,1)[2:end]
                        ajj = A[j,j]
                        iszero(ajj) && throw(SingularException(j))
                        Cj = C[j,k] = _ustrip(ajj) \ C[j,k]
                        for i in j+1:lastindex(A,1)
                            C[i,k] -= _dense_ma_mul!(product, _ustrip(A[i,j]), Cj)
                        end
                    end
                end
            else # tfun in (adjoint, transpose)
                for k in axes(B,2)
                    for j in reverse(axes(B,1))
                        ajj = A[j,j]
                        iszero(ajj) && throw(SingularException(j))
                        Bj = B[j,k]
                        for i in j+1:lastindex(A,1)
                            Bj -= _dense_ma_mul!(product, tfun(A[i,j]), C[i,k])
                        end
                        C[j,k] = tfun(ajj) \ Bj
                    end
                end
            end
        else # isunitc == 'U'
            if tfun === identity
                for k in axes(B,2)
                    C1 = C[1,k] = oA \ B[1,k]
                    # fill C-column
                    for i in axes(B,1)[2:end]
                        C[i,k] = oA \ B[i,k] - _dense_ma_mul!(product, _ustrip(A[i,1]), C1)
                    end
                    for j in axes(B,1)[2:end]
                        Cj = C[j,k]
                        for i in j+1:lastindex(A,1)
                            C[i,k] -= _dense_ma_mul!(product, _ustrip(A[i,j]), Cj)
                        end
                    end
                end
            else # tfun in (adjoint, transpose)
                for k in axes(B,2)
                    for j in reverse(axes(B,1))
                        Bj = B[j,k]
                        for i in j+1:lastindex(A,1)
                            Bj -= _dense_ma_mul!(product, tfun(A[i,j]), C[i,k])
                        end
                        C[j,k] = oA \ Bj
                    end
                end
            end
        end
    end
    return C
end

# UNEXECUTED fixtures and independent exact Float64-token oracles.
module DirectLUFixtures
using LinearAlgebra, SparseArrays
const Q = Rational{BigInt}

function coupled_basis()
    C0 = [i == j ? 8.0 : (-1.0)^(i+j)/8 for i in 1:4, j in 1:4]
    C = C0[[4,2,3,1], :]
    E = zeros(4,4)
    E[1,1] = E[2,2] = E[3,3] = E[1,4] = 1/8
    E[4,4] = 1/2
    return sparse([Matrix{Float64}(I,4,4) zeros(4,4); E C]), sparse(C)
end

function export_fixtures()
    mixed, core = coupled_basis()
    n = 16
    A = Matrix(Tridiagonal(fill(-0.5,n-1),fill(4.0,n),fill(0.25,n-1)))
    p = [1+mod(i-1+3,n) for i in 1:n]
    scaled = Diagonal([2.0^((i%7)-3) for i in 1:n])*A[p,n:-1:1]
    stored = SparseMatrixCSC(4,4,collect(1:4:17),repeat(collect(1:4),4),
                             vec(Matrix(Diagonal([2.0,3.0,4.0,5.0]))))
    return [(name=:empty,B=spzeros(0,0)),
            (name=:singleton,B=sparse(reshape([2.0],1,1))),
            (name=:diagonal,B=spdiagm(0=>collect(2.0:9.0))),
            (name=:coupled,B=mixed), (name=:core,B=core),
            (name=:scaled,B=sparse(scaled)), (name=:stored_zeros,B=stored)]
end

function singular_basis()
    B = Matrix{Float64}(I,4,4)
    B[4,:] = B[3,:]
    return sparse(B)
end

function replacement(B,t)
    n = size(B,1)
    j = 1+mod(7*t,n)
    a = Vector(B[:,j])
    a[1+mod(j,n)] += 1/32
    return j,a
end

# These checks derive expectations from the explicit input matrix, not solves
# or multiplication helpers supplied by the candidate.
function export_identity(B,e)
    n = size(B,1)
    L,U = Q.(Matrix(e.lower)),Q.(Matrix(e.upper))
    target = [Q(B[e.rows[i],e.columns[j]]) *
              (e.divide_scaling ? inv(Q(e.scaling[e.rows[i]])) : Q(e.scaling[e.rows[i]]))
              for i in 1:n,j in 1:n]
    residual = abs.(L*U-target)
    allowance = (128*n*Q(eps(Float64))).*(abs.(L)*abs.(U)+abs.(target))
    return all(residual .<= allowance)
end

matrix_infnorm(A) = maximum((sum(abs,A[i,:];init=zero(Q)) for i in axes(A,1));init=zero(Q))
vector_infnorm(x) = maximum(abs,x;init=zero(Q))
function solve_residual(B,x,rhs;transposed=false)
    all(isfinite,x) || return false
    M = Q.(Matrix(transposed ? transpose(B) : B))
    qx,qrhs = Q.(x),Q.(rhs)
    bound = 128*size(B,1)*Q(eps(Float64))*max(one(Q),matrix_infnorm(M)*vector_infnorm(qx),vector_infnorm(qrhs))
    return vector_infnorm(M*qx-qrhs) <= bound
end
end

using Test, SparseArrays, Random

# Keep the scalar CSC traversal as an independent arithmetic-order oracle.
function reference_csc_price!(out::Vector{T}, A::SparseMatrixCSC{T,Int}, rho::Vector{T}) where T
    m,n = size(A)
    for j in 1:n
        value = zero(T)
        for p in A.colptr[j]:(A.colptr[j+1]-1)
            value += rho[A.rowval[p]] * A.nzval[p]
        end
        out[j] = value
    end
    for i in 1:m
        out[n+i] = -rho[i]
    end
    return nothing
end

@testset "CSC pricing preserves scalar arithmetic" begin
    rng = MersenneTwister(349)
    for T in (Float32,Float64,BigFloat,Rational{Int},Rational{BigInt})
        for (m,n) in ((0,0),(0,4),(4,0),(1,1),(9,13),(31,8))
            A = sparse(T.(rand(rng,-3:3,m,n)))
            rho = T.(rand(rng,-5:5,m+2))
            out = fill(T(17),m+n+3)
            expected = copy(out)
            saved_A, saved_rho = copy(A), copy(rho)
            reference_csc_price!(expected,A,rho)
            @test JSimplex._csc_price!(out,A,rho) === nothing
            @test isequal(out,expected)
            @test isequal(A,saved_A)
            @test isequal(rho,saved_rho)
        end
    end
    for T in (Float32,Float64)
        # Cancellation, stored zeros, exceptional values, and empty columns.
        for rho in (T[1,1,1,1], T[0.0,-0.0,1,-1],
                    T[Inf,1,-Inf,NaN], T[nextfloat(zero(T)),floatmax(T),1,1])
            large = ldexp(one(T),precision(T))
            A = SparseMatrixCSC(4,4,[1,5,7,7,9],[1,2,3,4,1,2,3,4],
                T[large,1,-large,-1,0.0,-0.0,1,-1])
            expected = zeros(T,8)
            reference_csc_price!(expected,A,rho)
            out = fill(T(17),8)
            JSimplex._csc_price!(out,A,rho)
            @test isequal(out,expected)
        end
        # Fusing the second product with the sum would produce -eps(T)^2.
        A = sparse(reshape(T[1,1-eps(T)],2,1))
        out = zeros(T,3)
        JSimplex._csc_price!(out,A,T[-1,1+eps(T)])
        @test isequal(out,T[0,1,-(1+eps(T))])
        # Existing aliasing order is retained when the same vector is supplied.
        A = sparse(T[1 2; 3 4])
        rho = T[2,-1,7,9]
        expected = copy(rho)
        reference_csc_price!(expected,A,expected)
        JSimplex._csc_price!(rho,A,rho)
        @test isequal(rho,expected)
    end
end

@testset "CSC pricing validates dimensions before unchecked access" begin
    A = sparse([1.0 0.0; 0.0 1.0])
    @test_throws DimensionMismatch JSimplex._csc_price!(zeros(3),A,ones(2))
    @test_throws DimensionMismatch JSimplex._csc_price!(zeros(4),A,ones(1))
    @test_throws DimensionMismatch JSimplex._csc_price!(zeros(1),spzeros(2,0),ones(2))
end

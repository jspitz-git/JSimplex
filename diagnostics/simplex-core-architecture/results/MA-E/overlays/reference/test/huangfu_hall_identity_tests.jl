using Test, JSimplex, SparseArrays, LinearAlgebra

# Count actual element access rather than asserting a wall-clock threshold.
mutable struct HHAccessVector{T} <: AbstractVector{T}
    data::Vector{T}
    reads::Int
    writes::Int
end
Base.size(v::HHAccessVector)=size(v.data)
Base.IndexStyle(::Type{<:HHAccessVector})=IndexLinear()
Base.getindex(v::HHAccessVector,i::Int)=(v.reads+=1;v.data[i])
Base.setindex!(v::HHAccessVector,x,i::Int)=(v.writes+=1;v.data[i]=x)

@testset "Identity HH lower solves do not traverse their vectors" begin
    for T in (Float16,Float32,Float64,BigFloat,Rational{Int},Rational{BigInt}), n in (0,1,17)
        L=spdiagm(0=>ones(T,n));ids=collect(1:n)
        b=JSimplex.HHBase(L,copy(L),ids,copy(ids),copy(ids),ones(T,n),false,ones(Int,n+1),Int[])
        data=T[isodd(i) ? i : -i for i in 1:n]
        if T <: AbstractFloat && n>1;data[2]=-zero(T);end
        if T <: AbstractFloat && n>5;data[3]=T(Inf);data[4]=T(-Inf);data[5]=T(NaN);end
        for transposed in (false,true)
            v=HHAccessVector(copy(data),0,0)
            @test JSimplex._hh_lower!(v,b,transposed)===v
            @test isequal(v.data,data)
            @test v.reads==0
            @test v.writes==0
        end
    end
end

@testset "Nonidentity HH lower factors retain every stored operation" begin
    for T in (Float32,Float64,BigFloat,Rational{Int},Rational{BigInt})
        L=sparse(T[1 0 0;2 1 0;-1 3 1]);ids=collect(1:3)
        b=JSimplex.HHBase(L,spdiagm(0=>ones(T,3)),ids,copy(ids),copy(ids),ones(T,3),false,ones(Int,4),Int[])
        for transposed in (false,true)
            v=HHAccessVector(T[1,4,5],0,0)
            expected=(transposed ? transpose(UnitLowerTriangular(Matrix(L))) : UnitLowerTriangular(Matrix(L)))\v.data
            JSimplex._hh_lower!(v,b,transposed)
            @test v.data==expected
            @test v.reads>0
        end
        # Stored off-diagonal zeros must not be mistaken for absent entries.
        L.nzval[2]=zero(T)
        x=T[1,4,5];expected=UnitLowerTriangular(Matrix(L))\x
        @test JSimplex._hh_lower!(x,b,false)==expected
    end
end

@testset "Stored lower zeros preserve nonfinite propagation" begin
    L=SparseMatrixCSC(3,3,[1,3,4,5],[1,2,2,3],[1.0,0.0,1.0,1.0])
    ids=collect(1:3)
    b=JSimplex.HHBase(L,spdiagm(0=>ones(3)),ids,copy(ids),copy(ids),ones(3),false,ones(Int,4),Int[])
    for transposed in (false,true)
        v=HHAccessVector(transposed ? [1.0,Inf,2.0] : [Inf,1.0,2.0],0,0)
        JSimplex._hh_lower!(v,b,transposed)
        @test isnan(v.data[transposed ? 1 : 2])
        @test v.reads>0 && v.writes>0
    end
end

@testset "HH lower structure follows refactorization" begin
    for T in (Float32,Float64)
        T === Float64 && Int !== Int64 && continue
        f=JSimplex.HuangfuHallFactorization(spdiagm(0=>ones(T,2)))
        for B in (Matrix{T}(I,2,2),T[4 1;1 3],Matrix{T}(I,2,2))
            JSimplex.refactorize!(f,sparse(B))
            for transposed in (false,true)
                rhs=T[1,-2]
                x=transposed ? JSimplex.transpose_solve(f,rhs) : JSimplex.forward_solve(f,rhs)
                @test isapprox((transposed ? transpose(B) : B)*x,rhs;atol=20eps(T))
                v=HHAccessVector(copy(rhs),0,0)
                JSimplex._hh_lower!(v,f.base,transposed)
                @test (v.reads==0)==(nnz(f.base.lower)==2)
            end
        end
    end
end

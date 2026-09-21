# Investigation only; does not modify JSimplex source.
using JSimplex, LinearAlgebra, SparseArrays, Test, TOML
include(joinpath(pwd(),"dev","allocations.jl"))
using .JSimplexAllocations: measure_allocations
BLAS.set_num_threads(1)
mutable struct DenseReuseProbe{F,M}
    active::F
    spare::F
    matrix::M
end
function probe_state(A)
    DenseReuseProbe(JSimplex._factorize_dense_basis(A).factorization,
                   JSimplex._factorize_dense_basis(A).factorization,A)
end
function fresh!(s)
    s.active=JSimplex._factorize_dense_basis(s.matrix).factorization
    nothing
end
function reuse!(s)
    candidate=lu!(s.spare,s.matrix)
    s.spare=s.active
    s.active=candidate
    nothing
end
rows=Dict{String,Any}[]
@testset "Dense LU candidate feasibility" begin
    for T in (Float32,Float64,BigFloat,Rational{Int},Rational{BigInt})
        sizes=T <: Union{Float32,Float64} ? (64,512,1024) : (16,64)
        for n in sizes, storage in ("dense","sparse")
            A=Matrix{T}(I,n,n)
            for i in 1:n-1
                A[i,i+1]=T(1//4)
                # A pivot swap exercises ipiv without fraction growth.
            end
            A[[1,2],:]=A[[2,1],:]
            input=storage=="dense" ? A : sparse(A)
            s=probe_state(input)
            saved=s.active
            rhs=A*ones(T,n)
            transpose_rhs=transpose(A)*ones(T,n)
            expected=saved \ rhs
            reuse!(s)
            @test s.active \ rhs ≈ expected
            @test transpose(s.active) \ transpose_rhs ≈ ones(T,n)
            @test saved \ rhs ≈ expected
            @test s.active.factors !== saved.factors
            @test s.active.ipiv !== saved.ipiv
            for (name,run) in (("fresh",fresh!),("reuse",reuse!))
                row=measure_allocations(run;setup=()->probe_state(input),samples=3)
                merge!(row,Dict("type"=>string(T),"dimension"=>n,"storage"=>storage,"mode"=>name))
                push!(rows,row)
            end
            println(T," ",n," ",storage," ",[(r["allocations"],r["bytes"]) for r in rows[end-1:end]])
            flush(stdout)
        end
    end
    for T in (Float32,BigFloat,Rational{Int},Rational{BigInt})
        s=probe_state(Matrix{T}(I,3,3)); saved=s.active
        s.matrix[1,1]=zero(T)
        @test_throws SingularException reuse!(s)
        @test s.active === saved
        @test s.active \ ones(T,3) == ones(T,3)
    end
end
open(io->TOML.print(io,Dict("julia"=>string(VERSION),"blas_threads"=>BLAS.get_num_threads(),"rows"=>rows);sorted=true),"diagnostics/dense-lu-reuse-feasibility.toml","w")

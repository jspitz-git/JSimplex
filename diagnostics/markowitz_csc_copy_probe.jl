# Throwaway counterfactual: only this process replaces the CSC copy with convert.
using JSimplex, SparseArrays, LinearAlgebra, TOML, Test
include(joinpath(pwd(), "dev", "allocations.jl"))
using .JSimplexAllocations: measure_allocations
mode=ARGS[1]
mode in ("before","borrow") || error("mode must be before or borrow")
if mode in ("before","borrow")
    source=read("src/markowitz_factorization.jl",String)
    start=findfirst("function MarkowitzBackend(B::AbstractMatrix",source).start
    stop=findnext("\nfunction _backend_forward_solve!",source,start).start
    body=source[start:prevind(source,stop)]
    copying="sparse_basis = SparseMatrixCSC{T,Int}(B)"
    borrowing="sparse_basis = convert(SparseMatrixCSC{T,Int}, B)"
    @assert occursin(copying,body) || occursin(borrowing,body)
    body=mode=="borrow" ? replace(body,copying=>borrowing) : replace(body,borrowing=>copying)
    Base.include_string(JSimplex,body,"throwaway-markowitz-csc-borrow.jl")
end
rows=Dict{String,Any}[]
@testset "Borrowed CSC feasibility" begin
    for n in (64,256), kind in ("diagonal","band","dense")
        B=kind=="dense" ? sparse(fill(1.0,n,n)+Matrix{Float64}(I,n,n)*n) :
          kind=="band" ? spdiagm(-1=>fill(-1.0,n-1),0=>fill(4.0,n),1=>fill(-1.0,n-1)) :
                         spdiagm(0=>fill(4.0,n))
        result=measure_allocations(_->JSimplex.MarkowitzBackend(B);samples=3)
        merge!(result,Dict("dimension"=>n,"pattern"=>kind))
        push!(rows,result)
        original=copy(B)
        backend=JSimplex.MarkowitzBackend(B)
        @test B==original
        rhs=original*ones(n)
        fill!(B.nzval,0.0)
        x=zeros(n)
        JSimplex._backend_forward_solve!(x,backend,rhs)
        @test x ≈ ones(n)
    end
end
open(io->TOML.print(io,Dict("mode"=>mode,"rows"=>rows);sorted=true),ARGS[2],"w")

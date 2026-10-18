# UNEXECUTED Task1 tests. Include into an admitted ordinary staged process only.
# No automatic calls. Candidate definitions must be loaded in JSimplex first.
module BGExportWorkspaceTests
using Test, LinearAlgebra, SparseArrays, JSimplex
const X=JSimplex
mutable struct Owner
    workspace::Union{Nothing,X.BGExportWorkspace}
end
Owner()=Owner(nothing)
mutable struct Allocator
    calls::Int
    fail_at::Int
    sentinel::Exception
    requests::Vector{Tuple{Any,Int}}
end
Allocator(fail_at=0)=Allocator(0,fail_at,ErrorException("private allocation failure"),Tuple{Any,Int}[])
function (a::Allocator)(::Type{T},n::Int) where T
    a.calls+=1
    push!(a.requests,(T,n))
    a.calls==a.fail_at && throw(a.sentinel)
    X._bgx_allocate(T,n)
end
caught(f)=try; f(); nothing; catch err; err; end

# Owned test type only: no overwrite of any production solve method.
struct OrientationSolve
    mode::Symbol
    calls::Base.RefValue{Int}
    sentinel::Exception
end
function LinearAlgebra.ldiv!(out::Vector{Float64},f::OrientationSolve,rhs::Vector{Float64})
    f.calls[]+=1
    f.mode===:throw && throw(f.sentinel)
    for i in eachindex(rhs)
        out[i]=f.mode===:zero ? 0.0 : f.mode===:nonfinite ? Inf : 2.0*rhs[i]
    end
    out
end
function orientation_parts(n)
    # Explicit structural zeros make both valid triangles large enough to cache.
    ptrL=Int[1];ptrU=Int[1];rowsL=Int[];rowsU=Int[];vL=Float64[];vU=Float64[]
    for j in 1:n
        for i in j:n;push!(rowsL,i);push!(vL,i==j ? 1.0 : 0.0);end
        for i in 1:j;push!(rowsU,i);push!(vU,i==j ? 1.0 : 0.0);end
        push!(ptrL,length(rowsL)+1);push!(ptrU,length(rowsU)+1)
    end
    (SparseMatrixCSC(n,n,ptrL,rowsL,vL),SparseMatrixCSC(n,n,ptrU,rowsU,vU),collect(1:n),collect(1:n),fill(2.0,n))
end
function run_workspace_tests()
    @testset "scratch_budget_boundaries" begin
        for (n,l,u) in ((0,0,0),(1,1,1),(32,32,32),(64,2080,2080),(128,8256,8256))
            b=X._bgx_budget(n,l,u)
            @test b.limit==min(1048576,(16*(l+u)+8*(n+1))÷16)
            @test b.seen_bytes==8*cld(n,64)
            @test b.orientation_bytes==32*n
            @test b.keep_seen==(n>0 && 512+b.seen_bytes<=b.limit)
            @test b.keep_orientation==(b.keep_seen && 512+b.seen_bytes+32*n<=b.limit)
        end
        # n=64: l+u=487 yields B=519,488 gives520,489 gives521.
        for total in (487,488,489)
            o=Owner();a=Allocator();v=X._bgx_scratch!(o,:seen,64,total-64,64;allocate=a)
            @test length(v)==64 && v isa BitVector
            @test isnothing(o.workspace)==(total==487)
            @test a.calls==1
            if total>=488;@test o.workspace.charged_bytes==520;end
        end
        @test X._bgx_budget(100000,10000000,10000000).limit==1048576
        @test_throws OverflowError X._bgx_budget(typemax(Int),1,1)
        @test_throws OverflowError X._bgx_budget(1,typemax(Int),1)
        @test_throws ArgumentError X._bgx_budget(-1,1,1)
        o=Owner();v=X._bgx_scratch!(o,:seen,64,2080,2080);saved=o.workspace
        @test_throws ArgumentError X._bgx_scratch!(o,:orientation,64,2080,2080)
        @test o.workspace===saved && saved.seen===v
    end
    @testset "scratch_reuse_and_shrink" begin
        o=Owner();a=Allocator();v=X._bgx_scratch!(o,:seen,64,2080,2080;allocate=a)
        @test X._bgx_scratch!(o,:seen,64,2080,2080;allocate=a)===v && a.calls==1
        v2=X._bgx_scratch!(o,:seen,128,8256,8256;allocate=a)
        @test v2!==v && length(v2)==128 && o.workspace.dimension==128
        X._bgx_scratch!(o,:seen,128,128,128;allocate=a)
        @test isnothing(o.workspace)
        X._bgx_scratch!(o,:seen,0,0,0;allocate=a)
        @test isnothing(o.workspace)
        o=Owner();a=Allocator(1)
        @test caught(()->X._bgx_scratch!(o,:seen,64,2080,2080;allocate=a))===a.sentinel
        @test isnothing(o.workspace)
    end
    @testset "orientation_staged_early_exit and atomic retention" begin
        L,U,p,q,s=orientation_parts(64);n=64;l=nnz(L);u=nnz(U)
        for mode in (:throw,:zero,:nonfinite)
            o=Owner();a=Allocator();f=OrientationSolve(mode,Ref(0),ErrorException("solve boundary"))
            result=caught(()->begin
                answer=X._bgx_scale_mode(f,L,U,p,q,s,o,n,l,u;allocate=a)
                @test isnothing(answer)
            end)
            @test mode===:throw ? result===f.sentinel : isnothing(result)
            @test a.calls==2 && sum(last,a.requests)==2*n && f.calls[]==1
            @test isnothing(o.workspace)
        end
        for failed in 1:4
            o=Owner();a=Allocator(failed);f=OrientationSolve(:ok,Ref(0),ErrorException("unused"))
            @test caught(()->X._bgx_scale_mode(f,L,U,p,q,s,o,n,l,u;allocate=a))===a.sentinel
            @test a.calls==failed && f.calls[]==(failed<=2 ? 0 : 1)
            @test isnothing(o.workspace)
        end
        o=Owner();a=Allocator();f=OrientationSolve(:ok,Ref(0),ErrorException("unused"))
        @test X._bgx_scale_mode(f,L,U,p,q,s,o,n,l,u;allocate=a)===false
        @test a.calls==4 && sum(last,a.requests)==4*n
        group=o.workspace.orientation
        @test length(group)==4 && all(length(v)==n for v in group)
        @test X._bgx_scale_mode(f,L,U,p,q,s,o,n,l,u;allocate=a)===false
        @test a.calls==4 && all(group[i]===o.workspace.orientation[i] for i in 1:4)
        @test o.workspace.charged_bytes<=X._bgx_budget(n,l,u).limit
        # First allocate seen, then shrink budget to keep seen but evict orientation.
        X._bgx_scratch!(o,:seen,n,l,u);seen=o.workspace.seen
        @test X._bgx_scratch!(o,:seen,n,424,64)===seen
        @test isnothing(o.workspace.orientation) && o.workspace.charged_bytes==520
        a=Allocator();f=OrientationSolve(:throw,Ref(0),ErrorException("must not solve"))
        @test X._bgx_scale_mode(f,L,U,p,q,ones(n),o,n,l,u;allocate=a)===false
        @test a.calls==0 && f.calls[]==0
        # Nonretained small case still stages requests; full case makes exactly4.
        L2,U2,p2,q2,s2=orientation_parts(2);o2=Owner();a2=Allocator()
        @test X._bgx_scale_mode(OrientationSolve(:ok,Ref(0),ErrorException("unused")),L2,U2,p2,q2,s2,o2,2,3,3;allocate=a2)===false
        @test a2.calls==4 && isnothing(o2.workspace)
    end
end
end

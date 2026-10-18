from pathlib import Path
R=Path.cwd();C=R/'diagnostics/direct-bg-export-workspace/reproduce';C.mkdir(parents=True)
workspace=r'''# UNEXECUTED Task1 tests. Include into an admitted ordinary staged process only.
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
'''
imports=r'''# UNEXECUTED Task1 tests. No automatic run; no factor wrapper/Task2 here.
module BGExportImportTests
using Test, LinearAlgebra, SparseArrays, JSimplex
using ..BGExportWorkspaceTests: Owner, Allocator, caught
const X=JSimplex
include("../../direct-lu-policy-adapters/reproduce/fixtures.jl")
using .DirectLUFixtures: export_fixtures, export_identity
bits(v)=reinterpret(UInt64,v)
snapshot(U)=(size(U),copy(U.colptr),copy(U.rowval),copy(bits(U.nzval)))
packed_snapshot(v)=[(collect(c.indices),copy(bits(c.values))) for c in v]
function reference_import(U,normalize)
    raw=copy(U);d=normalize ? X._direct_normalize_upper!(raw) : nothing
    X._direct_packed_upper(raw,X.BartelsGolubFactorization),d
end
function check_import(U,normalize)
    before=snapshot(U);owners=(U.colptr,U.rowval,U.nzval);a=Allocator()
    expected,d=reference_import(U,normalize)
    actual,e=X._bgx_import_upper(U,normalize;allocate=a)
    @test isequal(packed_snapshot(actual),packed_snapshot(expected))
    @test isnothing(d) ? isnothing(e) : !isnothing(e) && bits(d)==bits(e)
    @test snapshot(U)==before
    @test all(x===y for (x,y) in zip(owners,(U.colptr,U.rowval,U.nzval)))
    @test all(c.values!==U.nzval && c.indices.ids!==U.rowval for c in actual)
    @test isempty(actual) || all(c.indices.order===actual[1].indices.order for c in actual)
    # Allocator request payload: final Float64 values + optional D, no u-temp.
    @test sum(n for (T,n) in a.requests if T===Float64)==nnz(U)+(normalize ? size(U,1) : 0)
    actual,e,a
end
function run_import_tests()
    @testset "fused_import_bits_and_counts" begin
        inputs=(spzeros(0,0),sparse(reshape([2.0],1,1)),
            SparseMatrixCSC(3,3,[1,2,4,7],[1,1,2,1,2,3],[2.0,-0.0,4.0,0.0,-0.0,8.0]),
            sparse([2.0 3.0 4.0;0.0 -8.0 1.0;0.0 0.0 16.0]))
        for U in inputs, normalize in (false,true);check_import(U,normalize);end
    end
    @testset "normalization_rejection_first_middle_last_offdiagonal" begin
        # Upper CSC off-diagonal slots2,4,5. All three can reject with finite inputs.
        for bad in (2,4,5), mode in (:overflow,:underflow)
            v=[1.0,0.0,1.0,0.0,0.0,1.0];rows=[1,1,2,1,2,3]
            row=rows[bad];diagonal=row==1 ? 1 : 3
            v[diagonal]=mode===:overflow ? floatmin(Float64) : floatmax(Float64)
            v[bad]=mode===:overflow ? floatmax(Float64) : nextfloat(0.0)
            U=SparseMatrixCSC(3,3,[1,2,4,7],rows,v)
            X._check_export_triangle(U,3,false)
            actual,d,a=check_import(U,true)
            @test isnothing(d)
            @test v[1]/v[1]==1.0 && v[end]/v[end]==1.0
            @test [x for c in actual for x in c.values]==v
        end
        for diagonal in (0.0,-0.0,Inf,NaN)
            U=sparse(reshape([diagonal],1,1));_,d,_=check_import(U,true)
            @test isnothing(d)
        end
        U=sparse([2.0 3.0;0.0 4.0]);before=snapshot(U)
        a=Allocator();X._bgx_import_upper(U,true;allocate=a)
        # Includes D, order maps, outer column vector and every per-column array.
        for failed in 1:a.calls
            f=Allocator(failed)
            @test caught(()->X._bgx_import_upper(U,true;allocate=f))===f.sentinel
            @test f.calls==failed && snapshot(U)==before
        end
    end
    @testset "validated_export_invariants" begin
        valid()=(spdiagm(0=>ones(2)),spdiagm(0=>ones(2)),[1,2],[1,2],ones(2))
        changes=(x->pop!(x[1].colptr),x->pop!(x[2].rowval),x->(x[2].colptr[1]=0),
            x->(x[2].colptr[end]=99),x->(x[1].colptr[2]=0),x->(x[1].rowval[1]=2),
            x->(x[2].rowval[2]=0),x->(x[1].nzval[1]=NaN),x->(x[2].nzval[1]=Inf),
            x->(x[1].nzval[1]=2.0),x->(x[2].nzval[1]=0.0),x->pop!(x[3]),
            x->(x[3][1]=2),x->(x[4][1]=0),x->(x[4][2]=3),x->pop!(x[5]),x->(x[5][1]=0.0))
        for change! in changes
            x=valid();change!(x);o=Owner()
            ref=caught(()->X._checked_basis_lu(x...,false))
            got=caught(()->X._bgx_checked_basis_lu(x...,false,o))
            @test ref isa ArgumentError && typeof(got)===typeof(ref)
            @test sprint(showerror,got)==sprint(showerror,ref)
            @test isnothing(o.workspace)
        end
        o=Owner();X._bgx_scratch!(o,:seen,64,2080,2080)
        @test isnothing(X._bgx_export(nothing,o)) && isnothing(o.workspace)
        # p must be rejected before q/scaling; retain original error order.
        x=valid();x[3][1]=0;x[4][1]=0;x[5][1]=0
        @test sprint(showerror,caught(()->X._bgx_checked_basis_lu(x...,false,Owner())))=="ArgumentError: Export permutation range"
    end
    @testset "seven original fixtures both policies; raw export ownership and core witness" begin
        for fixture in export_fixtures(), (backend,policy) in ((:native,X._NATIVE_PIVOT_ONE),(:markowitz,X._NATIVE_PIVOT_DEFAULT))
            B=fixture.B;before=snapshot(B);f=X._factorize_basis(B,Val(backend),policy)
            o=Owner();a=Allocator();e=X._bgx_export(f,o;allocate=a);ref=X._export_basis_lu(f)
            @test e isa X.BasisLUExport && ref isa X.BasisLUExport
            @test export_identity(B,e)
            @test snapshot(e.lower)==snapshot(ref.lower) && snapshot(e.upper)==snapshot(ref.upper)
            @test e.rows==ref.rows && e.columns==ref.columns && bits(e.scaling)==bits(ref.scaling) && e.divide_scaling==ref.divide_scaling
            @test e.upper!==ref.upper && e.upper.nzval!==ref.upper.nzval && e.lower.nzval!==ref.lower.nzval
            @test backend!==:markowitz || all(T===Bool for (T,n) in a.requests)
            old=snapshot(e.upper);check_import(e.upper,true);@test snapshot(e.upper)==old
            # Poison independent export, then scratch, without changing e.
            ref.upper.nzval .= 7.0
            if !isnothing(o.workspace)
                !isnothing(o.workspace.seen) && fill!(o.workspace.seen,true)
                if !isnothing(o.workspace.orientation)
                    for v in o.workspace.orientation;fill!(v,NaN);end
                end
            end
            @test snapshot(e.upper)==old && export_identity(B,e)
            if backend===:markowitz && fixture.name===:coupled
                k=f.sparse_pivots
                @test k==2 && f.row_order[1:2]==[4,3]
                @test f.core.p!=collect(1:length(f.core.p))
                wrongL=copy(e.lower);wrongL[(k+1):end,1:k].=0.0
                for j in 1:k, slot in eachindex(f.lower[j].indices)
                    row=f.lower[j].indices[slot]
                    row>k && (wrongL[row,j]=f.lower[j].values[slot])
                end
                wrong=X.BasisLUExport(wrongL,e.upper,e.rows,e.columns,e.scaling,e.divide_scaling)
                @test !export_identity(B,wrong)
            end
            @test snapshot(B)==before
        end
    end
end
end
'''
(C/'workspace-tests.jl').write_text(workspace);(C/'import-tests.jl').write_text(imports)
print('Wrote UNEXECUTED tests before candidate; no Julia invoked')

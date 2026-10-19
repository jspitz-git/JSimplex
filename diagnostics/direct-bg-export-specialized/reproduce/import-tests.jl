# UNEXECUTED Task1 tests. No automatic run; no factor wrapper/Task2 here.
module BGSpecializedExportImportTests
using Test, LinearAlgebra, SparseArrays, JSimplex
using ..BGSpecializedExportWorkspaceTests: Owner, Allocator, caught
const X=JSimplex
include("../../direct-lu-policy-adapters/reproduce/fixtures.jl")
using .DirectLUFixtures: export_fixtures, export_identity
bits(v)=reinterpret(UInt64,v)
snapshot(U)=(size(U),copy(U.colptr),copy(U.rowval),copy(bits(U.nzval)))
packed_snapshot(v)=[(collect(c.indices),copy(bits(c.values))) for c in v]
export_snapshot(e)=(snapshot(e.lower),snapshot(e.upper),copy(e.rows),copy(e.columns),copy(bits(e.scaling)),e.divide_scaling)
export_arrays(e)=(e.lower.colptr,e.lower.rowval,e.lower.nzval,e.upper.colptr,e.upper.rowval,e.upper.nzval,e.rows,e.columns,e.scaling)
function reference_import(U,normalize)
    raw=copy(U);d=normalize ? X._direct_normalize_upper!(raw) : nothing
    X._direct_packed_upper(raw,X.BartelsGolubFactorization),d
end
function check_import(U,normalize)
    before=snapshot(U);owners=(U.colptr,U.rowval,U.nzval);a=Allocator()
    expected,d=reference_import(U,normalize)
    actual,e=X._bgxs_import_upper(U,normalize;allocate=a)
    @test isequal(packed_snapshot(actual),packed_snapshot(expected))
    @test isnothing(d) ? isnothing(e) : !isnothing(e) && bits(d)==bits(e)
    @test snapshot(U)==before
    @test all(x===y for (x,y) in zip(owners,(U.colptr,U.rowval,U.nzval)))
    @test all(c.values!==U.nzval && c.indices.ids!==U.rowval for c in actual)
    @test isempty(actual) || all(c.indices.order===actual[1].indices.order for c in actual)
    # Allocator request payload: final Float64 values + optional D, no u-temp.
    @test sum((n for (T,n) in a.requests if T===Float64);init=0)==nnz(U)+(normalize ? size(U,1) : 0)
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
        a=Allocator();X._bgxs_import_upper(U,true;allocate=a)
        # Includes D, order maps, outer column vector and every per-column array.
        for failed in 1:a.calls
            f=Allocator(failed)
            @test caught(()->X._bgxs_import_upper(U,true;allocate=f))===f.sentinel
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
            got=caught(()->X._bgxs_checked_basis_lu(x...,false,o))
            @test ref isa ArgumentError && typeof(got)===typeof(ref)
            @test sprint(showerror,got)==sprint(showerror,ref)
            @test isnothing(o.workspace)
        end
        o=Owner();X._bgxs_scratch!(o,:seen,64,2080,2080)
        @test isnothing(X._bgxs_export(nothing,o)) && isnothing(o.workspace)
        # p must be rejected before q/scaling; retain original error order.
        x=valid();x[3][1]=0;x[4][1]=0;x[5][1]=0
        @test sprint(showerror,caught(()->X._bgxs_checked_basis_lu(x...,false,Owner())))=="ArgumentError: Export permutation range"
    end
    @testset "seven original fixtures both policies; raw export ownership and core witness" begin
        for fixture in export_fixtures(), (backend,policy) in ((:native,X._NATIVE_PIVOT_ONE),(:markowitz,X._NATIVE_PIVOT_DEFAULT))
            B=fixture.B;before=snapshot(B);input_owners=(B.colptr,B.rowval,B.nzval);f=X._factorize_basis(B,Val(backend),policy)
            o=Owner();a=Allocator();e=X._bgxs_export(f,o;allocate=a);ref=X._export_basis_lu(f)
            @test e isa X.BasisLUExport && ref isa X.BasisLUExport
            @test export_identity(B,e)
            @test snapshot(e.lower)==snapshot(ref.lower) && snapshot(e.upper)==snapshot(ref.upper)
            @test e.rows==ref.rows && e.columns==ref.columns && bits(e.scaling)==bits(ref.scaling) && e.divide_scaling==ref.divide_scaling
            @test all(a!==b for (a,b) in zip(export_arrays(e),export_arrays(ref)))
            frozen=export_snapshot(e);export_owners=export_arrays(e)
            @test backend!==:markowitz || all(T===Bool for (T,n) in a.requests)
            check_import(e.upper,true);@test isequal(export_snapshot(e),frozen)
            # Poison independent export, then scratch, without changing e.
            ref.upper.nzval .= 7.0
            if !isnothing(o.workspace)
                !isnothing(o.workspace.seen) && fill!(o.workspace.seen,true)
                if !isnothing(o.workspace.orientation)
                    for v in o.workspace.orientation;fill!(v,NaN);end
                end
            end
            @test isequal(export_snapshot(e),frozen) && export_identity(B,e)
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
            # Restore the ORIGINAL source-backend mutation ownership witness.
            # Six native source refactors and six Markowitz mutation cases are
            # prospective test work, not part of candidate export/import work.
            if size(B,1)>0
                if backend===:native
                    refactor_input=copy(B)
                    refactor_input.nzval .*= 2.0
                    @test refactor_input.colptr==B.colptr && refactor_input.rowval==B.rowval
                    @test all(a!==b for (a,b) in zip((refactor_input.colptr,refactor_input.rowval,refactor_input.nzval),input_owners))
                    @test all(isequal(refactor_input.nzval[k],2.0*B.nzval[k]) for k in eachindex(B.nzval))
                    lu!(f.factorization,refactor_input)
                    @test issuccess(f.factorization)
                else
                    f.core.factors .= 7.0
                    f.diagonal .+= 1.0
                    reverse!(f.row_order)
                    for v in f.lower;v.values .+= 1.0;end
                    for v in f.upper;v.values .+= 1.0;end
                end
                @test isequal(export_snapshot(e),frozen)
                @test export_identity(B,e)
            end
            @test all(a===b for (a,b) in zip(export_arrays(e),export_owners))
            @test snapshot(B)==before
            @test all(a===b for (a,b) in zip((B.colptr,B.rowval,B.nzval),input_owners))
        end
    end
end
end
